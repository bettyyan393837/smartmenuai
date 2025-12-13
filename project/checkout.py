# checkout_module.py

def calculate_total(cart):
    """
    Calculate total price of items in cart.
    """
    total = sum(item["price"] for item in cart)
    return round(total, 2)


def generate_receipt(cart):
    """
    Generate a clean receipt string.
    No print, no input — UI handles everything.
    """
    total = calculate_total(cart)

    lines = []
    lines.append("---- Receipt ----")

    for item in cart:
        lines.append(f"{item['name']} - RM{item['price']}")

    lines.append(f"\nTotal: RM{total}")

    return "\n".join(lines)

if __name__ == "__main__":
    cart = [
        {"name": "Fried Rice", "price": 10.9},
        {"name": "Lemon Tea", "price": 4.9}
    ]
    print(generate_receipt(cart))
