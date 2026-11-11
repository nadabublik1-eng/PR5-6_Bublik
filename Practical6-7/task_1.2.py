from flask import Flask, request, jsonify, abort
from functools import wraps
import math

app = Flask(__name__)

items_db = {
    1: {"id": 1, "name": "Ноутбук", "price": 25000, "category": "електроніка"},
    2: {"id": 2, "name": "Книга Python", "price": 500, "category": "книги"},
    3: {"id": 3, "name": "Навушники", "price": 2000, "category": "електроніка"},
}

next_id = 4


def validate_json(required_fields):
    def decorator(f):
        @wraps(f)
        def wrapper(*args, **kwargs):
            data = request.get_json(silent=True)

            if not isinstance(data, dict):
                return jsonify({"error": "Очікується JSON-об'єкт"}), 400

            missing = [
                field for field in required_fields
                if field not in data
            ]

            if missing:
                return jsonify({
                    "error": f"Відсутні поля: {', '.join(missing)}"
                }), 400

            return f(*args, **kwargs)

        return wrapper
    return decorator


def check_item_data(data):
    name = data["name"]
    price = data["price"]
    category = data["category"]

    if not isinstance(name, str) or not name.strip():
        return "Назва товару не може бути порожньою"

    if (
        isinstance(price, bool)
        or not isinstance(price, (int, float))
        or not math.isfinite(price)
        or price <= 0
    ):
        return "Ціна повинна бути додатним числом"

    if not isinstance(category, str) or not category.strip():
        return "Категорія не може бути порожньою"

    return None


@app.route("/api/items", methods=["GET"])
def get_items():
    items = list(items_db.values())

    category = request.args.get("category")
    sort = request.args.get("sort", "name")
    order = request.args.get("order", "asc")

    try:
        min_price = (
            float(request.args["min_price"])
            if "min_price" in request.args else None
        )
        max_price = (
            float(request.args["max_price"])
            if "max_price" in request.args else None
        )
    except ValueError:
        return jsonify({"error": "Некоректна ціна"}), 400

    if any(
        value is not None and not math.isfinite(value)
        for value in (min_price, max_price)
    ):
        return jsonify({"error": "Некоректна ціна"}), 400

    if sort not in ("name", "price"):
        return jsonify({"error": "Некоректне поле сортування"}), 400

    if order not in ("asc", "desc"):
        return jsonify({"error": "Некоректний порядок сортування"}), 400

    if category:
        items = [
            item for item in items
            if item["category"] == category
        ]

    if min_price is not None:
        items = [
            item for item in items
            if item["price"] >= min_price
        ]

    if max_price is not None:
        items = [
            item for item in items
            if item["price"] <= max_price
        ]

    items.sort(
        key=lambda item: item[sort],
        reverse=(order == "desc"),
    )

    return jsonify({
        "items": items,
        "count": len(items),
        "sort": sort,
        "order": order,
    }), 200


@app.route("/api/items", methods=["POST"])
@validate_json(["name", "price", "category"])
def create_item():
    global next_id

    data = request.get_json()
    error = check_item_data(data)

    if error:
        return jsonify({"error": error}), 400

    item = {
        "id": next_id,
        "name": data["name"].strip(),
        "price": data["price"],
        "category": data["category"].strip(),
    }

    items_db[next_id] = item
    next_id += 1

    return jsonify(item), 201


@app.route("/api/items/<int:item_id>", methods=["GET"])
def get_item(item_id):
    if item_id not in items_db:
        abort(404)

    return jsonify(items_db[item_id]), 200


@app.route("/api/items/<int:item_id>", methods=["PUT"])
@validate_json(["name", "price", "category"])
def update_item(item_id):
    if item_id not in items_db:
        abort(404)

    data = request.get_json()
    error = check_item_data(data)

    if error:
        return jsonify({"error": error}), 400

    items_db[item_id] = {
        "id": item_id,
        "name": data["name"].strip(),
        "price": data["price"],
        "category": data["category"].strip(),
    }

    return jsonify(items_db[item_id]), 200


@app.route("/api/items/<int:item_id>", methods=["DELETE"])
def delete_item(item_id):
    if item_id not in items_db:
        abort(404)

    del items_db[item_id]
    return "", 204


@app.errorhandler(404)
def not_found(error):
    return jsonify({"error": "Ресурс не знайдено"}), 404


@app.errorhandler(400)
def bad_request(error):
    return jsonify({"error": "Некоректний запит"}), 400


if __name__ == "__main__":
    app.run(debug=True, port=5001)