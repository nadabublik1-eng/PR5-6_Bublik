from flask import Flask, request, jsonify, g
from datetime import datetime
from functools import wraps
import math
import time

app = Flask(__name__)
app.json.ensure_ascii = False


class APIError(Exception):
    def __init__(self, message: str, status_code: int = 400,
                 details: dict = None):
        self.message = message
        self.status_code = status_code
        self.details = details or {}


class StudentSerializer:

    @staticmethod
    def serialize(student: dict, fields: list[str] | None = None) -> dict:
        result = dict(student)

        if "created_at" in result:
            result["created_at"] = datetime.fromisoformat(
                result["created_at"]
            ).strftime("%d.%m.%Y %H:%M")

        result["performance"] = (
            "Високий" if result["gpa"] >= 90 else "Звичайний"
        )

        if fields is not None:
            return {field: result[field] for field in fields}

        return result

    @staticmethod
    def deserialize(data: dict) -> dict:
        required = {"name", "group", "email", "gpa"}

        if not isinstance(data, dict) or not required.issubset(data):
            raise APIError(
                "Обов'язкові поля: name, group, email, gpa",
                400
            )

        cleaned = {}

        for key in ("name", "group", "email"):
            if not isinstance(data[key], str) or not data[key].strip():
                raise APIError(f"Некоректне поле: {key}", 400)

            cleaned[key] = data[key].strip()

        if "@" not in cleaned["email"]:
            raise APIError("Некоректний email", 400)

        try:
            if isinstance(data["gpa"], bool):
                raise ValueError

            cleaned["gpa"] = float(data["gpa"])

        except (TypeError, ValueError):
            raise APIError("gpa має бути числом", 400)

        if (
            not math.isfinite(cleaned["gpa"])
            or not 0 <= cleaned["gpa"] <= 100
        ):
            raise APIError("gpa має бути від 0 до 100", 400)

        return cleaned

    @staticmethod
    def serialize_list(
        students: list[dict],
        fields: list[str] | None = None
    ) -> list[dict]:
        return [
            StudentSerializer.serialize(student, fields)
            for student in students
        ]


@app.before_request
def log_request():
    g.start_time = time.perf_counter()

    print(
        f"[{datetime.now().isoformat(timespec='seconds')}] "
        f"{request.method} {request.path}"
    )


@app.after_request
def add_headers(response):
    duration = time.perf_counter() - g.start_time

    response.headers["X-Request-Time"] = f"{duration:.4f}s"
    response.headers["Access-Control-Allow-Origin"] = "*"

    return response


def require_api_key(f):
    @wraps(f)
    def wrapper(*args, **kwargs):
        api_key = request.headers.get("X-API-Key")

        if api_key != "secret-api-key-123":
            raise APIError("Невірний API-ключ", 401)

        return f(*args, **kwargs)

    return wrapper


students_db = {
    1: {
        "id": 1,
        "name": "Іваненко О.",
        "group": "КІ-21",
        "email": "ivan@kpi.ua",
        "gpa": 85.5,
        "created_at": datetime.now().isoformat()
    },
    2: {
        "id": 2,
        "name": "Коваль Л.",
        "group": "КІ-22",
        "email": "koval@kpi.ua",
        "gpa": 95.1,
        "created_at": datetime.now().isoformat()
    }
}

next_id = 3


@app.route("/api/v2/students", methods=["GET"])
def get_students_v2():
    fields_param = request.args.get("fields")

    fields = (
        [f.strip() for f in fields_param.split(",")]
        if fields_param else None
    )

    allowed = {
        "id", "name", "group", "email",
        "gpa", "created_at", "performance"
    }

    if fields is not None and any(f not in allowed for f in fields):
        raise APIError("Невідоме поле в параметрі fields", 400)

    students = list(students_db.values())

    search = request.args.get("search", "").strip().lower()

    if search:
        students = [
            student for student in students
            if any(
                search in student[key].lower()
                for key in ("name", "group", "email")
            )
        ]

    sort_by = request.args.get("sort", "name")
    order = request.args.get("order", "asc")

    if (
        sort_by not in ("name", "group", "gpa")
        or order not in ("asc", "desc")
    ):
        raise APIError("Некоректне сортування", 400)

    students.sort(
        key=lambda student: student[sort_by],
        reverse=order == "desc"
    )

    return jsonify({
        "count": len(students),
        "students": StudentSerializer.serialize_list(students, fields)
    }), 200


@app.route("/api/v2/students", methods=["POST"])
@require_api_key
def create_student_v2():
    global next_id

    data = StudentSerializer.deserialize(
        request.get_json(silent=True)
    )

    if any(
        student["email"].lower() == data["email"].lower()
        for student in students_db.values()
    ):
        raise APIError("Email уже використовується", 400)

    student = {
        **data,
        "id": next_id,
        "created_at": datetime.now().isoformat()
    }

    students_db[next_id] = student
    next_id += 1

    return jsonify(StudentSerializer.serialize(student)), 201


@app.errorhandler(APIError)
def handle_api_error(error):
    response = {
        "error": error.message,
        "status": error.status_code,
        "details": error.details,
        "timestamp": datetime.now().isoformat()
    }

    return jsonify(response), error.status_code


if __name__ == "__main__":
    app.run(debug=True, port=5006)