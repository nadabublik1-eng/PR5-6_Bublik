from flask import Flask, request, render_template_string, redirect, url_for, abort

app = Flask(__name__)

BASE_TEMPLATE = """
<!DOCTYPE html>
<html lang="uk">
<head>
    <meta charset="UTF-8">
    <title>{{ title }}</title>
</head>
<body>
    <h1>{{ title }}</h1>
    <nav>
        <a href="{{ url_for('index') }}">Головна</a> |
        <a href="{{ url_for('post_list') }}">Публікації</a> |
        <a href="{{ url_for('search') }}">Пошук</a>
    </nav>
    <hr>
    {{ content | safe }}
</body>
</html>
"""

posts_db = [
    {
        "id": 1,
        "title": "Вступ до Python",
        "content": "Python — потужна мова...",
        "author": "Іван",
    },
    {
        "id": 2,
        "title": "Flask для початківців",
        "content": "Flask — мікрофреймворк...",
        "author": "Марія",
    },
    {
        "id": 3,
        "title": "REST API",
        "content": "REST — архітектурний стиль...",
        "author": "Петро",
    },
]

next_id = 4


def render_page(title, template, **context):
    content = render_template_string(template, **context)
    return render_template_string(
        BASE_TEMPLATE, title=title, content=content
    )


@app.route("/")
def index():
    return render_page(
        "Головна сторінка",
        """
        <p>Вітаємо у Flask-застосунку!</p>
        <p>Кількість публікацій: {{ count }}</p>
        <a href="{{ url_for('post_create') }}">
            Створити публікацію
        </a>
        """,
        count=len(posts_db),
    )


@app.route("/posts")
def post_list():
    page = max(1, request.args.get("page", 1, type=int))
    per_page = max(1, min(50, request.args.get("per_page", 10, type=int)))

    start = (page - 1) * per_page
    posts = posts_db[start:start + per_page]

    return render_page(
        "Список публікацій",
        """
        <p>Сторінка: {{ page }} | На сторінці: {{ per_page }}</p>
        <ul>
        {% for post in posts %}
            <li>
                <a href="{{ url_for('post_detail', post_id=post.id) }}">
                    {{ post.title }}
                </a>
                — {{ post.author }}
            </li>
        {% else %}
            <li>Публікацій немає.</li>
        {% endfor %}
        </ul>
        <a href="{{ url_for('post_create') }}">
            Створити публікацію
        </a>
        """,
        posts=posts,
        page=page,
        per_page=per_page,
    )


@app.route("/posts/<int:post_id>")
def post_detail(post_id):
    post = next(
        (post for post in posts_db if post["id"] == post_id),
        None,
    )

    if post is None:
        abort(404)

    return render_page(
        post["title"],
        """
        <p>Автор: {{ post.author }}</p>
        <p>{{ post.content }}</p>
        """,
        post=post,
    )


@app.route("/posts/create", methods=["GET", "POST"])
def post_create():
    global next_id

    if request.method == "POST":
        title = request.form.get("title", "").strip()
        content = request.form.get("content", "").strip()
        author = request.form.get("author", "").strip()

        if not title or not content or not author:
            return "Усі поля обов'язкові", 400

        post = {
            "id": next_id,
            "title": title,
            "content": content,
            "author": author,
        }

        posts_db.append(post)
        next_id += 1

        return redirect(url_for("post_detail", post_id=post["id"]))

    return render_page(
        "Створення публікації",
        """
        <form method="POST">
            <p><input name="title" placeholder="Назва" required></p>
            <p><input name="author" placeholder="Автор" required></p>
            <p>
                <textarea name="content"
                    placeholder="Текст публікації"
                    required></textarea>
            </p>
            <button type="submit">Створити</button>
        </form>
        """,
    )


@app.route("/search")
def search():
    query = request.args.get("q", "").strip()

    results = [
        post for post in posts_db
        if query.lower() in post["title"].lower()
        or query.lower() in post["content"].lower()
    ] if query else []

    return render_page(
        "Пошук публікацій",
        """
        <form method="GET">
            <input name="q" value="{{ query }}" placeholder="Пошук">
            <button type="submit">Знайти</button>
        </form>

        <p>Знайдено: {{ results|length }}</p>

        <ul>
        {% for post in results %}
            <li>
                <a href="{{ url_for('post_detail', post_id=post.id) }}">
                    {{ post.title }}
                </a>
            </li>
        {% endfor %}
        </ul>
        """,
        query=query,
        results=results,
    )


@app.route("/archive/<int:year>/<int:month>")
def archive(year, month):
    if month < 1 or month > 12:
        abort(404)

    return render_page(
        "Архів публікацій",
        """
        <p>Архів за {{ month }} місяць {{ year }} року.</p>
        """,
        year=year,
        month=month,
    )


@app.route("/user/<string:username>")
def user_profile(username):
    posts = [
        post for post in posts_db
        if post["author"].lower() == username.lower()
    ]

    return render_page(
        "Профіль користувача",
        """
        <h2>{{ username }}</h2>
        <p>Кількість публікацій: {{ posts|length }}</p>

        <ul>
        {% for post in posts %}
            <li>{{ post.title }}</li>
        {% endfor %}
        </ul>
        """,
        username=username,
        posts=posts,
    )


if __name__ == "__main__":
    app.run(debug=True, port=5000)