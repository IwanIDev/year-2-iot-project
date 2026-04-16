from dataclasses import dataclass
from datetime import datetime
from enum import Enum
from typing import Dict, List

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

