from dataclasses import dataclass
from datetime import datetime
from enum import Enum
from typing import Dict, List
import httpx
import logging

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
            f"{tb_auth.base_url}/api/plugins/telemetry/DEVICE/{device_id}/attributes/SHARED_SCOPE",
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
            f"{tb_auth.base_url}/api/plugins/telemetry/DEVICE/{device_id}/attributes/SHARED_SCOPE",
            headers=tb_auth.auth_headers(),
            timeout=10,
        )
        if r.is_success:
            data = r.json()
            return data.get("collection_dates", {})
        else:
            logging.error(f"Failed to retrieve Thingsboard device {device_id} collection dates. Response: {r.text}")
            return {}
    except Exception as exc:
        logging.error(f"ThingsBoard request failed for device {device_id}: {exc}")
        return {}

