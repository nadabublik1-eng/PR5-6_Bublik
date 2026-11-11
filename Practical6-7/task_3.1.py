from flask import Flask, request, jsonify
from datetime import datetime
import math

app = Flask(__name__)
app.json.ensure_ascii = False

students_db = {}
next_id = 1


def validate_student(data, partial=False, current_id=None):
    fields = {"name", "group", "email", "gpa"}

    if not isinstance(data, dict) or not data:
        return None, "Потрібен непорожній JSON-об'єкт"

    if not partial and not fields.issubset(data):
        return None, "Обов'язкові поля: name, group, email, gpa"

    if set(data) - fields:
        return None, "Невідомі поля у запиті"

    cleaned = {}

    for key in ("name", "group", "email"):
        if key in data:
            if not isinstance(data[key], str) or not data[key].strip():
                return None, f"Поле {key} не може бути порожнім"

            cleaned[key] = data[key].strip()

    if "gpa" in data:
        try:
            if isinstance(data["gpa"], bool):
                raise ValueError
            gpa = float(data["gpa"])
        except (ValueError, TypeError):
            return None, "gpa має бути числом"

        if not math.isfinite(gpa) or not 0 <= gpa <= 100:
            return None, "gpa має бути від 0 до 100"

        cleaned["gpa"] = gpa

    if "email" in cleaned:
        if "@" not in cleaned["email"]:
            return None, "Некоректний email"

        if any(
            student["email"].lower() == cleaned["email"].lower()
            and student_id != current_id
            for student_id, student in students_db.items()
        ):
            return None, "Email уже використовується"

    return cleaned, None


@app.route("/api/students", methods=["GET"])
def get_students():
    try:
        page = int(request.args.get("page", 1))
        per_page = int(request.args.get("per_page", 10))
        min_gpa = float(request.args.get("min_gpa", 0))
    except ValueError:
        return jsonify({"error": "Некоректні параметри"}), 400

    sort_by = request.args.get("sort_by", "name")
    order = request.args.get("order", "asc")

    if (
        page < 1
        or per_page < 1
        or not math.isfinite(min_gpa)
        or not 0 <= min_gpa <= 100
        or sort_by not in ("name", "gpa", "group")
        or order not in ("asc", "desc")
    ):
        return jsonify({"error": "Некоректні параметри"}), 400

    students = list(students_db.values())

    group = request.args.get("group")

    if group:
        students = [s for s in students if s["group"] == group]

    students = [s for s in students if s["gpa"] >= min_gpa]

    students.sort(
        key=lambda s: s[sort_by],
        reverse=order == "desc"
    )

    count = len(students)
    students = students[
        (page - 1) * per_page:page * per_page
    ]

    return jsonify({
        "count": count,
        "page": page,
        "per_page": per_page,
        "students": students
    }), 200


@app.route("/api/students", methods=["POST"])
def create_student():
    global next_id

    data, error = validate_student(request.get_json(silent=True))

    if error:
        return jsonify({"error": error}), 400

    student = {
        **data,
        "id": next_id,
        "created_at": datetime.now().isoformat(timespec="seconds")
    }

    students_db[next_id] = student
    next_id += 1

    return jsonify(student), 201


@app.route("/api/students/<int:student_id>", methods=["GET"])
def get_student(student_id):
    if student_id not in students_db:
        return jsonify({"error": "Студента не знайдено"}), 404

    return jsonify(students_db[student_id]), 200


@app.route("/api/students/<int:student_id>", methods=["PUT"])
def update_student(student_id):
    if student_id not in students_db:
        return jsonify({"error": "Студента не знайдено"}), 404

    data, error = validate_student(
        request.get_json(silent=True),
        current_id=student_id
    )

    if error:
        return jsonify({"error": error}), 400

    students_db[student_id] = {
        **data,
        "id": student_id,
        "created_at": students_db[student_id]["created_at"]
    }

    return jsonify(students_db[student_id]), 200


@app.route("/api/students/<int:student_id>", methods=["PATCH"])
def patch_student(student_id):
    if student_id not in students_db:
        return jsonify({"error": "Студента не знайдено"}), 404

    data, error = validate_student(
        request.get_json(silent=True),
        partial=True,
        current_id=student_id
    )

    if error:
        return jsonify({"error": error}), 400

    students_db[student_id].update(data)

    return jsonify(students_db[student_id]), 200


@app.route("/api/students/<int:student_id>", methods=["DELETE"])
def delete_student(student_id):
    if student_id not in students_db:
        return jsonify({"error": "Студента не знайдено"}), 404

    del students_db[student_id]

    return "", 204


@app.route("/api/students/stats", methods=["GET"])
def students_stats():
    students = list(students_db.values())
    groups = {}

    for student in students:
        group = student["group"]
        groups[group] = groups.get(group, 0) + 1

    avg_gpa = (
        round(sum(s["gpa"] for s in students) / len(students), 2)
        if students else 0
    )

    top_students = sorted(
        students,
        key=lambda s: s["gpa"],
        reverse=True
    )[:3]

    return jsonify({
        "total": len(students),
        "avg_gpa": avg_gpa,
        "groups": groups,
        "top_students": top_students
    }), 200


@app.errorhandler(404)
def not_found(error):
    return jsonify({
        "error": "Ресурс не знайдено",
        "status": 404
    }), 404


@app.errorhandler(400)
def bad_request(error):
    return jsonify({
        "error": "Некоректний запит",
        "status": 400
    }), 400


@app.errorhandler(422)
def unprocessable(error):
    return jsonify({
        "error": "Помилка валідації",
        "status": 422
    }), 422


if __name__ == "__main__":
    test_students = [
        {
            "name": "Іваненко О.",
            "group": "КІ-21",
            "email": "ivan@kpi.ua",
            "gpa": 85.5
        },
        {
            "name": "Петренко М.",
            "group": "КІ-21",
            "email": "petro@kpi.ua",
            "gpa": 92.0
        },
        {
            "name": "Сидоренко А.",
            "group": "КІ-22",
            "email": "syd@kpi.ua",
            "gpa": 78.3
        },
        {
            "name": "Коваль Л.",
            "group": "КІ-22",
            "email": "koval@kpi.ua",
            "gpa": 95.1
        }
    ]

    for student in test_students:
        students_db[next_id] = {
            **student,
            "id": next_id,
            "created_at": datetime.now().isoformat(timespec="seconds")
        }
        next_id += 1

    app.run(debug=True, port=5005)