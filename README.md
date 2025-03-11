# Simple DNS Server

This tool is a simple DNS server that can handle and reconstruct chunked data sent via DNS queries. It listens for incoming DNS requests, logs them, and processes special DNS queries formatted to transmit chunked binary data.

## Features
- Handles standard DNS A record queries.
- Supports receiving chunked data encoded in DNS subdomains.
- Reconstructs and saves received binary data into incrementally numbered files.
- Logs all DNS queries.

## Installation
### Prerequisites
Ensure you have Python installed:

```bash
pip install -r requirements.txt
```

### Running the Server
You can run the server using the following command:

```bash
python eDNS.py
```

### Command-line Options
- `-v, --verbose` : Enable verbose logging.
- `-i, --interface` : Set the interface to listen on (default: `0.0.0.0`).
- `-p, --port` : Set the port to listen on (default: `53`).

Example:

```bash
python eDNS.py -v -i 0.0.0.0 -p 53
```

## How It Works
1. The server listens for incoming DNS queries.
2. If a query follows the chunked data format (`packet_id-total_chunks-chunk_id.hex_data.example.com`), the server reconstructs the original binary data.
3. Once all chunks are received, the server merges and saves the data into the `data/` directory with an incrementing filename (e.g., `1.bin`, `2.bin`, etc.).

## Example Chunked Data Transmission
To send data via DNS queries, you can use a script to encode and send data piece by piece.

## Logs
All DNS queries are logged in `dns_queries.log`.

## License
This project is open-source and available for modification and distribution.