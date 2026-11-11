from flask import (
    Flask,
    request,
    make_response,
    session,
    redirect,
    url_for,
    jsonify,
    render_template_string,
    abort,
)
import os

app = Flask(__name__)
app.secret_key = os.environ.get(
    "FLASK_SECRET_KEY",
    "development-only-secret-key"
)

products_db = {
    1: {"name": "Ноутбук", "price": 25000},
    2: {"name": "Смартфон", "price": 12000},
    3: {"name": "Навушники", "price": 2000},
}


@app.route("/set-theme/<theme>")
def set_theme(theme):
    if theme not in ("light", "dark"):
        return jsonify({"error": "Некоректна тема"}), 400

    response = make_response(jsonify({
        "message": "Тему збережено",
        "theme": theme,
    }))

    response.set_cookie(
        "theme",
        theme,
        max_age=30 * 24 * 60 * 60,
        httponly=True,
        samesite="Lax",
    )

    return response


@app.route("/get-theme")
def get_theme():
    theme = request.cookies.get("theme", "light")
    return jsonify({"theme": theme})


@app.route("/set-language/<lang>")
def set_language(lang):
    response = make_response(jsonify({
        "message": "Мову збережено",
        "language": lang,
    }))

    response.set_cookie(
        "language",
        lang,
        max_age=30 * 24 * 60 * 60,
        httponly=True,
        samesite="Lax",
    )

    return response


@app.route("/preferences")
def preferences():
    return jsonify({
        "theme": request.cookies.get("theme", "light"),
        "language": request.cookies.get("language", "uk"),
    })


@app.route("/cart/add/<int:product_id>")
def add_to_cart(product_id):
    if product_id not in products_db:
        abort(404)

    cart = session.get("cart", [])
    cart.append(product_id)
    session["cart"] = cart

    return jsonify({
        "message": "Товар додано до кошика",
        "product": products_db[product_id]["name"],
        "cart_count": len(cart),
    })


@app.route("/cart")
def view_cart():
    cart = session.get("cart", [])

    items = [
        {"id": product_id, **products_db[product_id]}
        for product_id in cart
        if product_id in products_db
    ]

    total = sum(item["price"] for item in items)

    return jsonify({
        "items": items,
        "count": len(items),
        "total": total,
    })


@app.route("/cart/clear")
def clear_cart():
    session.pop("cart", None)

    return jsonify({
        "message": "Кошик очищено",
        "cart": [],
    })


@app.route("/login", methods=["GET", "POST"])
def login():
    if request.method == "GET":
        return render_template_string("""
        <!DOCTYPE html>
        <html lang="uk">
        <head>
            <meta charset="UTF-8">
            <title>Вхід</title>
        </head>
        <body>
            <h1>Авторизація</h1>
            <form method="POST">
                <input
                    name="username"
                    placeholder="Ім'я користувача"
                    required
                >
                <button type="submit">Увійти</button>
            </form>
        </body>
        </html>
        """)

    data = request.get_json(silent=True) if request.is_json else None

    if isinstance(data, dict):
        username = data.get("username", "")
    else:
        username = request.form.get("username", "")

    if not isinstance(username, str) or not username.strip():
        return jsonify({"error": "Вкажіть ім'я користувача"}), 400

    session["username"] = username.strip()

    return redirect(url_for("profile"))


@app.route("/logout")
def logout():
    session.pop("username", None)

    return jsonify({"message": "Вихід виконано"})


@app.route("/profile")
def profile():
    username = session.get("username")

    if not username:
        return redirect(url_for("login"))

    return jsonify({
        "username": username,
        "message": "Користувач авторизований",
    })


if __name__ == "__main__":
    app.run(debug=True, port=5002)