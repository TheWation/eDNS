import logging
import argparse
import signal
import socket
import sys
import threading
import os
import binascii
from collections import defaultdict
from dnslib import DNSRecord, DNSHeader, RR, QTYPE, A

parser = argparse.ArgumentParser(description="Simple DNS Server with Chunk Handling")
parser.add_argument("-v", "--verbose", action="store_true", help="Enable verbose mode")
parser.add_argument("-i", "--interface", type=str, default="0.0.0.0", help="Set the interface to listen on (default: 0.0.0.0)")
parser.add_argument("-p", "--port", type=int, default=53, help="Set the port to listen on (default: 53)")
args = parser.parse_args()
verbose = args.verbose
interface = args.interface
port = args.port

logger = logging.getLogger()
logger.setLevel(logging.INFO)
formatter = logging.Formatter("%(asctime)s - %(message)s")
file_handler = logging.FileHandler("dns_queries.log")
file_handler.setFormatter(formatter)
logger.addHandler(file_handler)

if verbose:
    stream_handler = logging.StreamHandler()
    stream_handler.setFormatter(formatter)
    logger.addHandler(stream_handler)

server_running = True
chunk_storage = defaultdict(lambda: {"total_chunks": None, "received_chunks": {}, "saved": False})

def sigint_handler(signum, frame):
    global server_running
    server_running = False
    print("Server shutting down gracefully.")
    sys.exit(0)

signal.signal(signal.SIGINT, sigint_handler)

def handle_dns_query(data, address, server_socket):
    global chunk_storage
    dns_request = DNSRecord.parse(data)
    query_name = str(dns_request.q.qname).strip('.')
    query_type = QTYPE[dns_request.q.qtype]
    logger.info(f"Received query: {query_name} (Type: {query_type}) from {address[0]}:{address[1]}")

    parts = query_name.split('.')
    if len(parts) > 3 and '-' in parts[0]:
        try:
            hex_data = parts[1];
            packet_id, total_chunks, chunk_id = parts[0].split('-')
            packet_id = int(packet_id, 16)
            total_chunks = int(total_chunks, 16)
            chunk_id = int(chunk_id, 16)

            if packet_id not in chunk_storage or chunk_storage[packet_id]["total_chunks"] is None:
                print(f"\n[~] Receiving chunked data from {address[0]}:{address[1]} (Packet ID: {packet_id}, Total Chunks: {total_chunks})")

            if chunk_storage[packet_id]["saved"]:
                return  # Ignore redundant chunks after data is already saved

            chunk_storage[packet_id]["total_chunks"] = total_chunks
            chunk_storage[packet_id]["received_chunks"][chunk_id] = binascii.unhexlify(hex_data)

            if len(chunk_storage[packet_id]["received_chunks"]) == total_chunks:
                sorted_chunks = [chunk_storage[packet_id]["received_chunks"][i] for i in sorted(chunk_storage[packet_id]["received_chunks"])]
                merged_data = b''.join(sorted_chunks)

                if not os.path.exists("data"):
                    os.mkdir("data")

                file_index = len(os.listdir("data")) + 1
                file_path = f"data/{file_index}.bin"
                with open(file_path, 'wb') as f:
                    f.write(merged_data)

                print(f"[+] Merged data saved to {file_path}")
                chunk_storage[packet_id]["saved"] = True
        except ValueError:
            pass  # Ignore malformed requests
    else:
        dns_response = DNSRecord(DNSHeader(id=dns_request.header.id, qr=1, aa=1, ra=1, rcode=0))
        dns_response.add_answer(RR(query_name, QTYPE.A, rdata=A("192.168.1.1"), ttl=60))
        server_socket.sendto(dns_response.pack(), address)

def handle_client_connection(data, address, server_socket):
    threading.Thread(target=handle_dns_query, args=(data, address, server_socket)).start()

def run_dns_server(host, port):
    global server_running
    server_socket = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
    server_socket.bind((host, port))
    server_socket.setblocking(False)
    print(f"DNS server listening on {host}:{port}...")

    while server_running:
        try:
            data, address = server_socket.recvfrom(512)
            handle_client_connection(data, address, server_socket)
        except BlockingIOError:
            continue

    print("Server stopped.")

if __name__ == "__main__":
    run_dns_server(interface, port)