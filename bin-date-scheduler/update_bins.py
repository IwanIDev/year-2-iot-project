import os
import sys
import logging
import httpx

BIN_API_URL = os.environ["BIN_API_URL"]

TIMEOUT = 10

def main():
    # Make GET request to BIN_API_URL
    r = httpx.get(BIN_API_URL, timeout=TIMEOUT)
    if r.status_code != 200:
        raise Exception(f"Failed to fetch bin data: {r.status_code} {r.text}")


if __name__ == "__main__":
    try:
        main()
    except Exception as e:
        logging.error(f"ERROR: {e}")
        sys.exit(1)


