import sys
import asyncio
import signal
import os

from masscan_runner import MasscanRunner
from tls_http_scanner import TLSHTTPScanner

MASSCAN_FILE = "masscanResults.txt"

def cleanup():
    if os.path.exists(MASSCAN_FILE):
        print("🧹 Removing", MASSCAN_FILE)
        os.remove(MASSCAN_FILE)

signal.signal(signal.SIGINT, lambda s, f: cleanup())
signal.signal(signal.SIGTERM, lambda s, f: cleanup())

if __name__ == "__main__":
    if len(sys.argv) < 2:
        print("Usage: python3 scanner.py <IP_RANGE_FILE>")
        sys.exit(1)

    ip_file = sys.argv[1]

    # Part 1 — run masscan
    runner = MasscanRunner(ip_file, MASSCAN_FILE)
    runner.run()

    # Part 2 — parse results and scan
    scanner = TLSHTTPScanner(MASSCAN_FILE)
    asyncio.run(scanner.extract_and_scan())

    cleanup()
