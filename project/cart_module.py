from copy import deepcopy
from typing import List, Dict, Any


def _find_index_by_id(cart: List[Dict[str, Any]], item_id: Any):
    # Locate the index of an item in the cart using its ID.
    # Returns the index if found, otherwise None.
    for idx, itm in enumerate(cart):
        if itm.get("id") == item_id:
            return idx
    return None


def add_item(cart: List[Dict[str, Any]], item: Dict[str, Any]) -> None:
    # Add an item to the cart (ID-based matching).
    # If the ID already exists in the cart, increase quantity by 1.Otherwise insert the item as a new entry with quantity = 1
    # or use the item's provided quantity if it exists
    #Matches the UI's usage; no return value.
    if not isinstance(cart, list):
        raise TypeError("cart must be a list")
    if not isinstance(item, dict):
        raise TypeError("item must be a dict")

    item_id = item.get("id")
    if item_id is None:
        raise ValueError("item must contain 'id'")

    idx = _find_index_by_id(cart, item_id)

    if idx is not None:
        # Existing item → increase quantity
        existing = cart[idx]
        existing_qty = int(existing.get("quantity", 1))
        existing["quantity"] = existing_qty + 1
    else:
        # New item → add a deepcopy to avoid mutating the original menu item
        new_item = deepcopy(item)
        try:
            q = int(new_item.get("quantity", 1))
            if q < 1:
                q = 1
        except:
            q = 1
        new_item["quantity"] = q
        cart.append(new_item)


def remove_item(cart: List[Dict[str, Any]], name: str) -> bool:
    # UI passes a name, so we must locate the item by matching its name.
    # If quantity > 1 → decrease quantity by 1
    # - quantity == 1 → remove the whole item entry
    # - item not found → return False
    if not isinstance(cart, list):
        raise TypeError("cart must be a list")

    target_idx = None
    for idx, itm in enumerate(cart):
        if isinstance(itm.get("name"), str) and itm["name"].strip().lower() == name.strip().lower():
            target_idx = idx
            break

    if target_idx is None:
        return False

    item = cart[target_idx]
    qty = int(item.get("quantity", 1))

    if qty > 1:
        item["quantity"] = qty - 1
    else:
        cart.pop(target_idx)

    return True


def get_cart_items(cart: List[Dict[str, Any]]) -> List[Dict[str, Any]]:
    # Return a deepcopy of the cart items.
    # Ensures each item has a 'quantity' field.
    result = []
    for itm in cart:
        cp = deepcopy(itm)
        cp["quantity"] = int(cp.get("quantity", 1))
        result.append(cp)
    return result


def get_cart_total(cart: List[Dict[str, Any]]) -> float:
    # Calculate the total amount of the cart.
    # total = sum(price × quantity), rounded to 2 decimals.
    total = 0.0
    for itm in cart:
        try:
            price = float(itm.get("price", 0))
        except:
            price = 0.0

        try:
            qty = int(itm.get("quantity", 1))
        except:
            qty = 1

        if qty < 0:
            qty = 0

        total += price * qty

    return round(total, 2)
