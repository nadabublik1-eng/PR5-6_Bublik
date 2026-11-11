from flask import Flask, request, render_template_string, redirect, url_for, flash, abort

app = Flask(__name__)
app.secret_key = "blog-secret-key"

posts_db = [
    {
        "id": 1,
        "title": "Перша публікація",
        "content": "Зміст першої публікації",
        "author": "Іван",
        "created_at": "2025-01-15"
    },
    {
        "id": 2,
        "title": "Друга публікація",
        "content": "Зміст другої публікації",
        "author": "Марія",
        "created_at": "2025-01-20"
    }
]

FORM_TEMPLATE = """
<h1>Редагування публікації</h1>

{% for message in get_flashed_messages() %}
<p style="color:red">{{ message }}</p>
{% endfor %}

<form method="POST">
    <p>
        <label>Заголовок:</label>
        <input type="text" name="title"
               value="{{ post.title }}" required>
    </p>

    <p>
        <label>Автор:</label>
        <input type="text" name="author"
               value="{{ post.author }}" required>
    </p>

    <p>
        <label>Зміст:</label><br>
        <textarea name="content" rows="8" cols="50"
                  required>{{ post.content }}</textarea>
    </p>

    <button type="submit">Зберегти зміни</button>
    <a href="{{ url_for('post_detail', post_id=post.id) }}">
        Скасувати
    </a>
</form>
"""

DELETE_CONFIRM_TEMPLATE = """
<h1>Підтвердження видалення</h1>

<p>
    Ви дійсно бажаєте видалити публікацію
    "<strong>{{ post.title }}</strong>"?
</p>

<form method="POST">
    <button type="submit">Так, видалити</button>
    <a href="{{ url_for('post_detail', post_id=post.id) }}">
        Скасувати
    </a>
</form>
"""


def find_post(post_id):
    post = next(
        (p for p in posts_db if p["id"] == post_id),
        None
    )

    if post is None:
        abort(404)

    return post


@app.route("/posts")
def post_list():
    page = max(1, request.args.get("page", 1, type=int))
    per_page = 2
    start = (page - 1) * per_page
    posts = posts_db[start:start + per_page]

    return render_template_string("""
        <h1>Список публікацій</h1>

        {% for message in get_flashed_messages() %}
        <p style="color:green">{{ message }}</p>
        {% endfor %}

        {% for post in posts %}
            <h2>
                <a href="{{ url_for('post_detail', post_id=post.id) }}">
                    {{ post.title }}
                </a>
            </h2>
            <p>{{ post.content }}</p>
        {% else %}
            <p>Публікацій немає.</p>
        {% endfor %}

        {% if page > 1 %}
        <a href="{{ url_for('post_list', page=page-1) }}">Назад</a>
        {% endif %}

        {% if has_next %}
        <a href="{{ url_for('post_list', page=page+1) }}">Далі</a>
        {% endif %}
    """,
        posts=posts,
        page=page,
        has_next=start + per_page < len(posts_db)
    )


@app.route("/posts/<int:post_id>")
def post_detail(post_id):
    post = find_post(post_id)

    return render_template_string("""
        <h1>{{ post.title }}</h1>

        {% for message in get_flashed_messages() %}
        <p style="color:green">{{ message }}</p>
        {% endfor %}

        <p>{{ post.content }}</p>
        <p>Автор: {{ post.author }}</p>
        <p>Дата: {{ post.created_at }}</p>

        <a href="{{ url_for('post_edit', post_id=post.id) }}">
            Редагувати
        </a>

        <a href="{{ url_for('post_delete', post_id=post.id) }}">
            Видалити
        </a>

        <a href="{{ url_for('post_list') }}">
            До списку
        </a>
    """, post=post)


@app.route("/posts/<int:post_id>/edit", methods=["GET", "POST"])
def post_edit(post_id):
    post = find_post(post_id)

    if request.method == "POST":
        title = request.form.get("title", "").strip()
        author = request.form.get("author", "").strip()
        content = request.form.get("content", "").strip()

        if not title or not author or not content:
            flash("Усі поля обов'язкові!")
            return redirect(
                url_for("post_edit", post_id=post_id)
            )

        post["title"] = title
        post["author"] = author
        post["content"] = content

        flash("Публікацію успішно оновлено!")

        return redirect(
            url_for("post_detail", post_id=post_id)
        )

    return render_template_string(FORM_TEMPLATE, post=post)


@app.route("/posts/<int:post_id>/delete", methods=["GET", "POST"])
def post_delete(post_id):
    post = find_post(post_id)

    if request.method == "POST":
        posts_db.remove(post)

        flash("Публікацію успішно видалено!")

        return redirect(url_for("post_list"))

    return render_template_string(
        DELETE_CONFIRM_TEMPLATE,
        post=post
    )


if __name__ == "__main__":
    app.run(debug=True, port=5004)