import os
from pathlib import Path
import sys
import logging
import httpx

BIN_API_URL = os.environ["BIN_API_URL"]

TIMEOUT = 10

def main():
    # Make GET request to BIN_API_URL
    cert_file = Path(__file__).resolve().parent / "cert.pem"
    with httpx.Client(verify=cert_file) as client:
        r = client.get(BIN_API_URL, timeout=TIMEOUT)
        if r.status_code != 200:
            raise Exception(f"Failed to fetch bin data: {r.status_code} {r.text}")


if __name__ == "__main__":
    try:
        main()
    except Exception as e:
        logging.error(f"ERROR: {e}")
        sys.exit(1)


