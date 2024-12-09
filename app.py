import uuid
import math
import re

from flask import Flask, request, jsonify

app = Flask(__name__)

# In-memory storage for receipts
receipts = {}


def calculate_points(receipt):
    """
    Calculate points based on the receipt's properties.
    """
    points = 0

    # One point for every alphanumeric character in the retailer name
    points += sum(char.isalnum() for char in receipt["retailer"])

    # 50 points if the total is a round dollar amount with no cents
    total = float(receipt["total"])
    if total.is_integer():
        points += 50

    # 25 points if the total is a multiple of 0.25
    if total % 0.25 == 0:
        points += 25

    # 5 points for every two items on the receipt
    points += (len(receipt["items"]) // 2) * 5

    # Points for items with description length as a multiple of 3
    for item in receipt["items"]:
        description = item["shortDescription"].strip()
        if len(description) % 3 == 0:
            price = float(item["price"])
            points += math.ceil(price * 0.2)

    # 6 points if the day in the purchase date is odd
    purchase_date = receipt["purchaseDate"]
    day = int(purchase_date.split("-")[2])
    if day % 2 != 0:
        points += 6

    # 10 points if the time of purchase is between 2:00pm and 4:00pm
    purchase_time = receipt["purchaseTime"]
    hour, minute = map(int, purchase_time.split(":"))
    if 14 <= hour < 16:  # 2:00pm to 4:00pm
        points += 10

    return points

def validate_receipt(receipt):
    """
    Validates the structure and format of the receipt.
    """
    required_fields = {"retailer", "purchaseDate", "purchaseTime", "items", "total"}
    
    # Checks required fields
    if not all(field in receipt for field in required_fields):
        return "Missing required fields."

    # Validate purchaseDate format (YYYY-MM-DD)
    if not re.match(r"^\d{4}-\d{2}-\d{2}$", receipt["purchaseDate"]):
        return "Invalid purchaseDate format. Use YYYY-MM-DD."

    # Validate purchaseTime format (HH:MM in 24-hour format)
    if not re.match(r"^\d{2}:\d{2}$", receipt["purchaseTime"]):
        return "Invalid purchaseTime format. Use HH:MM."

    # Validate total format (e.g., "12.34")
    if not re.match(r"^\d+\.\d{2}$", receipt["total"]):
        return "Invalid total format. Use a decimal with two places."

    # Validate items
    if not isinstance(receipt["items"], list) or len(receipt["items"]) == 0:
        return "Items must be a non-empty list."

    for item in receipt["items"]:
        if "shortDescription" not in item or "price" not in item:
            return "Each item must have shortDescription and price."
        if not re.match(r"^\d+\.\d{2}$", item["price"]):
            return f"Invalid price format in item: {item}"

    return None

@app.route('/receipts/process', methods=['POST'])
def process_receipt():
    try:
        receipt = request.json

        # validate input
        error = validate_receipt(receipt)
        if error:
            print("Validation error:", error)
            return jsonify({"error": error}), 400

        # Generate id
        receipt_id = str(uuid.uuid4())
        points = calculate_points(receipt)

        # Store the receipt and points
        receipts[receipt_id] = {"receipt": receipt, "points": points}

        return jsonify({"id": receipt_id}), 200
    except Exception as e:
        return jsonify({"error": str(e)}), 500


@app.route('/receipts/<receipt_id>/points', methods=['GET'])
def get_points(receipt_id):

    try:
        if receipt_id not in receipts:
            return jsonify({"error": "Receipt not found"}), 404

        points = receipts[receipt_id]["points"]
        return jsonify({"points": points}), 200
    except Exception as e:
        return jsonify({"error": str(e)}), 500


if __name__ == '__main__':
    app.run(debug=True)
