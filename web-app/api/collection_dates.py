from dataclasses import dataclass
from datetime import datetime
from enum import Enum
from typing import Dict, List, Optional
from flask import current_app as app
import httpx
import logging
from users.Users import Users
import ssl
import truststore

class BinType(Enum):
    GARDEN_WASTE = "garden_waste"
    GENERAL_WASTE = "general_waste"
    PAPER = "paper"
    PLASTIC = "plastic"

@dataclass
class BinCollection:
    bin_type: BinType
    collection_date: datetime

def parse_collection_dates(collection_dates: Dict[str, str]) -> List[BinCollection]:
    """
    Parse a dictionary of bin types and collection dates into BinCollection objects.
    Expects dates in ISO 8601 format and Bin types to match BinType enum.
    """
    parsed_collections = []
    for bin_type_str, date_str in collection_dates.items():
        try:
            bin_type = BinType(bin_type_str)
        except ValueError:
            raise ValueError(f"Invalid bin type: {bin_type_str}. Must be one of {[bt.value for bt in BinType]}")
        
        try:
            collection_date = datetime.fromisoformat(date_str)
        except ValueError:
            raise ValueError(f"Invalid date format for {bin_type_str}: {date_str}. Must be in ISO 8601 format")
        
        parsed_collections.append(BinCollection(bin_type=bin_type, collection_date=collection_date))
    return parsed_collections

def update_collection_dates_in_thingsboard(device_id: str, collection_dates: List[BinCollection], tb_auth) -> bool:
    """
    Update the collection dates for a device in ThingsBoard as shared attributes.
    Returns True if the update was successful, False otherwise.
    """
    thingsboard_payload = {
        "collection_dates": {bc.bin_type.value: bc.collection_date.isoformat() for bc in collection_dates}
    }
    
    def _post_attributes(force_refresh=False):
        return httpx.post(
            f"{tb_auth.base_url}/api/plugins/telemetry/DEVICE/{device_id}/SHARED_SCOPE",
            json=thingsboard_payload,
            headers=tb_auth.auth_headers(force_refresh=force_refresh),
            timeout=10,
        )
    try:
        r = _post_attributes()
        if not r.is_success:
            logging.error(f"Failed to update Thingsboard device {device_id} with collection dates. Response: {r.text}")
            return False
        return True
    except Exception as exc:
        logging.error(f"ThingsBoard request failed for device {device_id}: {exc}")
        return False

def get_collection_dates_for_device(device_id: str, tb_auth) -> Dict[str, str]:
    """
    Retrieve the collection dates for a device from ThingsBoard shared attributes.
    Returns a dictionary of bin types and their corresponding collection dates in ISO 8601 format.
    """
    try:
        r = httpx.get(
            f"{tb_auth.base_url}/api/plugins/telemetry/DEVICE/{device_id}/values/attributes/SHARED_SCOPE",
            headers=tb_auth.auth_headers(),
            timeout=10,
        )
        if r.is_success:
            data = r.json()
            return data[0].get("value", {})
        else:
            logging.error(f"Failed to retrieve Thingsboard device {device_id} collection dates. Response: {r.text}")
            return {}
    except Exception as exc:
        logging.error(f"ThingsBoard request failed for device {device_id}: {exc}")
        return {}

def fetch_new_collection_dates(user: Users) -> List[Optional[BinCollection]]:
    """
    Get new collection dates from the Bin Collection API for a user.
    """
    council = user.council
    uprn = user.UPRN
    api_url = council.url
    council_name = council.collectionName
    url = app.config["BIN_COLLECTION_API"]
    
    if not api_url:
        logging.warning(f"No API URL configured for council {council_name}")

    if not council_name:
        logging.warning(f"No collection name configured for council {council_name}")

    bin_collection_api_url = f"{url}/api/bin_collection/{council_name}"
    api_params = {
        "uprn": uprn if uprn else None,
        "url": api_url if api_url else None
    }

    ctx = truststore.SSLContext(ssl.PROTOCOL_TLS_CLIENT)

    data = []

    with httpx.Client(verify=ctx) as client:
        r = httpx.get(
            bin_collection_api_url,
            params=api_params,
            timeout=10,
        )

        if not r.is_success:
            logging.error(f"Failed to fetch collection dates for user {user.id} from Bin Collection API. Response: {r.text}")
            return []

        # Parse the response for collection dates
        """
        Expected response format:
            "bins": [
                {"type": "Food", "collectionDate": "23/04/2026"},
                {"type": "Recycling", "collectionDate": "23/04/2026"},
                {"type": "General", "collectionDate": "30/04/2026"},
                {"type": "Glass", "collectionDate": "30/04/2026"},
                {"type": "Food", "collectionDate": "30/04/2026"},
                {"type": "Recycling", "collectionDate": "30/04/2026"}
            ]
        """
        data = r.json()

    bins = data.get("bins", [])
    collection_dates = []
    for bin in bins:
        bin_type_str = bin.get("type", "").lower().replace(" ", "_")
        try:
            bin_type = BinType(bin_type_str)
        except ValueError:
            logging.warning(f"Unknown bin type from API for user {user.id}: {bin_type_str}")
            continue
        
        date_str = bin.get("collectionDate", "")
        try:
            collection_date = datetime.strptime(date_str, "%d/%m/%Y")
        except ValueError:
            logging.warning(f"Invalid date format from API for user {user.id} bin type {bin_type_str}: {date_str}")
            continue
        
        collection_dates.append(BinCollection(bin_type=bin_type, collection_date=collection_date))
        
        return collection_dates

