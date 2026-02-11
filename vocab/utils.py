import json
from fsrs import Card

def card_data_to_dict(card_json) -> dict:
    """
    Normalize card_data to dict regardless of input type.
    Accepts: dict, JSON string, or FSRS Card object.
    """
    if isinstance(card_json, dict):
        return card_json
    if isinstance(card_json, str):
        return json.loads(card_json)
    if hasattr(card_json, 'to_json'):
        return json.loads(card_json.to_json())
    return {}
