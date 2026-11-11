from flask import Flask, request, render_template_string, redirect, url_for, flash, abort
from datetime import datetime

app = Flask(__name__)
app.secret_key = "blog-secret-key"

posts_db = []
next_id = 1

LIST_TEMPLATE = """
<h1>Публікації</h1>

{% for message in get_flashed_messages() %}
<p style="color:green">{{ message }}</p>
{% endfor %}

<a href="{{ url_for('post_create') }}">+ Нова публікація</a>
<hr>

{% for post in posts %}
    <h2>
        <a href="{{ url_for('post_detail', post_id=post.id) }}">
            {{ post.title }}
        </a>
    </h2>
    <p>{{ post.content[:100] }}</p>
    <small>{{ post.author }} | {{ post.created_at }}</small>
    <hr>
{% else %}
    <p>Публікацій поки немає.</p>
{% endfor %}

<p>Сторінка {{ page }}</p>

{% if page > 1 %}
<a href="{{ url_for('post_list', page=page-1) }}">Назад</a>
{% endif %}

{% if has_next %}
<a href="{{ url_for('post_list', page=page+1) }}">Далі</a>
{% endif %}
"""

FORM_TEMPLATE = """
<h1>Створення публікації</h1>

{% for message in get_flashed_messages() %}
<p style="color:red">{{ message }}</p>
{% endfor %}

<form method="POST">
    <p>
        <label>Заголовок:</label>
        <input type="text" name="title" required>
    </p>

    <p>
        <label>Автор:</label>
        <input type="text" name="author" required>
    </p>

    <p>
        <label>Зміст:</label><br>
        <textarea name="content" rows="8" cols="50" required></textarea>
    </p>

    <button type="submit">Створити</button>
</form>

<a href="{{ url_for('post_list') }}">Назад</a>
"""


@app.route("/posts")
def post_list():
    page = max(1, request.args.get("page", 1, type=int))
    per_page = 2
    start = (page - 1) * per_page

    posts = posts_db[start:start + per_page]
    has_next = start + per_page < len(posts_db)

    return render_template_string(
        LIST_TEMPLATE,
        posts=posts,
        page=page,
        has_next=has_next
    )


@app.route("/posts/<int:post_id>")
def post_detail(post_id):
    post = next(
        (p for p in posts_db if p["id"] == post_id),
        None
    )

    if post is None:
        abort(404)

    return render_template_string("""
        <h1>{{ post.title }}</h1>

        {% for message in get_flashed_messages() %}
        <p style="color:green">{{ message }}</p>
        {% endfor %}

        <p>{{ post.content }}</p>
        <small>{{ post.author }} | {{ post.created_at }}</small>

        <p>
            <a href="{{ url_for('post_list') }}">До списку</a>
        </p>
    """, post=post)


@app.route("/posts/create", methods=["GET", "POST"])
def post_create():
    global next_id

    if request.method == "POST":
        title = request.form.get("title", "").strip()
        author = request.form.get("author", "").strip()
        content = request.form.get("content", "").strip()

        if not title or not author or not content:
            flash("Усі поля обов'язкові!")
            return redirect(url_for("post_create"))

        post = {
            "id": next_id,
            "title": title,
            "author": author,
            "content": content,
            "created_at": datetime.now().strftime("%Y-%m-%d %H:%M")
        }

        posts_db.append(post)
        next_id += 1

        flash("Публікацію успішно створено!")

        return redirect(
            url_for("post_detail", post_id=post["id"])
        )

    return render_template_string(FORM_TEMPLATE)


if __name__ == "__main__":
    app.run(debug=True, port=5003)