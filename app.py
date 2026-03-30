import os
from datetime import datetime
from functools import wraps
from typing import Dict, List

import gspread
from dotenv import load_dotenv
from flask import (
    Flask,
    jsonify,
    redirect,
    render_template,
    request,
    session,
    url_for,
)
from google.oauth2.service_account import Credentials
from openai import OpenAI

load_dotenv()

app = Flask(__name__)
app.secret_key = os.getenv("FLASK_SECRET_KEY", "change-this-secret-in-production")

# ---------------------------------
# Configuration
# ---------------------------------
GOOGLE_CREDENTIALS_FILE = os.getenv("GOOGLE_CREDENTIALS_FILE", "service_account.json")
GOOGLE_SHEET_ID = os.getenv("GOOGLE_SHEET_ID", "")
OPENAI_MODEL = os.getenv("OPENAI_MODEL", "gpt-4o-mini")

TEACHER_USERNAME = os.getenv("TEACHER_USERNAME", "teacher")
TEACHER_PASSWORD = os.getenv("TEACHER_PASSWORD", "teacher123")
STUDENT_USERNAME = os.getenv("STUDENT_USERNAME", "student")
STUDENT_PASSWORD = os.getenv("STUDENT_PASSWORD", "student123")


class SheetsService:
    """Simple helper class for CRUD operations on Google Sheets."""

    def __init__(self, credentials_file: str, spreadsheet_id: str):
        self.credentials_file = credentials_file
        self.spreadsheet_id = spreadsheet_id
        self.client = None
        self.sheet = None

    def connect(self):
        if self.client and self.sheet:
            return

        scopes = [
            "https://www.googleapis.com/auth/spreadsheets",
            "https://www.googleapis.com/auth/drive",
        ]
        creds = Credentials.from_service_account_file(self.credentials_file, scopes=scopes)
        self.client = gspread.authorize(creds)
        self.sheet = self.client.open_by_key(self.spreadsheet_id)

    def ws(self, name: str):
        self.connect()
        return self.sheet.worksheet(name)

    # ------------ Students ------------
    def get_students(self) -> List[Dict]:
        records = self.ws("students").get_all_records()
        return records

    def add_student(self, data: Dict):
        ws = self.ws("students")
        rows = ws.get_all_values()
        next_id = str(len(rows))  # header is first row; row count gives next id
        ws.append_row(
            [
                next_id,
                data.get("name", ""),
                data.get("class", ""),
                data.get("roll", ""),
                data.get("phone", ""),
                data.get("email", ""),
                data.get("parent", ""),
            ]
        )

    def update_student(self, student_id: str, data: Dict) -> bool:
        ws = self.ws("students")
        rows = ws.get_all_values()
        for i, row in enumerate(rows[1:], start=2):
            if row and row[0] == str(student_id):
                ws.update(f"A{i}:G{i}", [[
                    student_id,
                    data.get("name", row[1]),
                    data.get("class", row[2]),
                    data.get("roll", row[3]),
                    data.get("phone", row[4]),
                    data.get("email", row[5]),
                    data.get("parent", row[6]),
                ]])
                return True
        return False

    def delete_student(self, student_id: str) -> bool:
        ws = self.ws("students")
        rows = ws.get_all_values()
        for i, row in enumerate(rows[1:], start=2):
            if row and row[0] == str(student_id):
                ws.delete_rows(i)
                return True
        return False

    # ------------ Attendance ------------
    def save_attendance(self, attendance_rows: List[List[str]]):
        ws = self.ws("attendance")
        for row in attendance_rows:
            ws.append_row(row)

    def get_attendance(self) -> List[Dict]:
        return self.ws("attendance").get_all_records()

    # ------------ Videos ------------
    def add_video(self, date: str, subject: str, drive_link: str):
        self.ws("videos").append_row([date, subject, drive_link])

    def get_videos(self) -> List[Dict]:
        return self.ws("videos").get_all_records()

    # ------------ Subjects ------------
    def get_subjects(self) -> List[Dict]:
        return self.ws("subjects").get_all_records()

    def add_subject(self, subject_name: str):
        self.ws("subjects").append_row([subject_name])

    def update_subject(self, old_name: str, new_name: str) -> bool:
        ws = self.ws("subjects")
        rows = ws.get_all_values()
        for i, row in enumerate(rows[1:], start=2):
            if row and row[0] == old_name:
                ws.update(f"A{i}", [[new_name]])
                return True
        return False

    def delete_subject(self, subject_name: str) -> bool:
        ws = self.ws("subjects")
        rows = ws.get_all_values()
        for i, row in enumerate(rows[1:], start=2):
            if row and row[0] == subject_name:
                ws.delete_rows(i)
                return True
        return False

    # ------------ Announcements ------------
    def add_announcement(self, message: str, date: str):
        self.ws("announcements").append_row([date, message])

    def get_announcements(self) -> List[Dict]:
        return self.ws("announcements").get_all_records()


class AIService:
    def __init__(self):
        self.client = OpenAI(api_key=os.getenv("OPENAI_API_KEY"))

    def ask(self, prompt: str) -> str:
        response = self.client.chat.completions.create(
            model=OPENAI_MODEL,
            messages=[{"role": "user", "content": prompt}],
            temperature=0.6,
        )
        return response.choices[0].message.content.strip()


sheets = SheetsService(GOOGLE_CREDENTIALS_FILE, GOOGLE_SHEET_ID)
ai_service = AIService()


def login_required(role=None):
    def decorator(f):
        @wraps(f)
        def wrapped(*args, **kwargs):
            if not session.get("logged_in"):
                return redirect(url_for("login"))
            if role and session.get("role") != role:
                return redirect(url_for("login"))
            return f(*args, **kwargs)

        return wrapped

    return decorator


@app.context_processor
def inject_user_context():
    return {
        "current_role": session.get("role"),
        "current_user": session.get("username"),
    }


# -----------------------
# Authentication Routes
# -----------------------
@app.route("/", methods=["GET", "POST"])
def login():
    if request.method == "POST":
        username = request.form.get("username", "").strip()
        password = request.form.get("password", "").strip()
        role = request.form.get("role", "student").strip()

        if role == "teacher" and username == TEACHER_USERNAME and password == TEACHER_PASSWORD:
            session["logged_in"] = True
            session["role"] = "teacher"
            session["username"] = username
            return redirect(url_for("teacher_dashboard"))

        if role == "student" and username == STUDENT_USERNAME and password == STUDENT_PASSWORD:
            session["logged_in"] = True
            session["role"] = "student"
            session["username"] = username
            return redirect(url_for("student_dashboard"))

        return render_template("login.html", error="Invalid credentials. Please try again.")

    return render_template("login.html")


@app.route("/logout")
def logout():
    session.clear()
    return redirect(url_for("login"))


# -----------------------
# Teacher pages
# -----------------------
@app.route("/teacher/dashboard")
@login_required(role="teacher")
def teacher_dashboard():
    students = sheets.get_students()
    attendance = sheets.get_attendance()
    announcements = sheets.get_announcements()

    today = datetime.utcnow().strftime("%Y-%m-%d")
    today_attendance = [x for x in attendance if x.get("date") == today]

    recent_activity = sorted(
        announcements,
        key=lambda x: x.get("date", ""),
        reverse=True,
    )[:5]

    return render_template(
        "teacher/dashboard.html",
        total_students=len(students),
        today_attendance=len(today_attendance),
        recent_activity=recent_activity,
    )


@app.route("/teacher/students")
@login_required(role="teacher")
def teacher_students():
    return render_template("teacher/students.html")


@app.route("/teacher/attendance")
@login_required(role="teacher")
def teacher_attendance():
    return render_template("teacher/attendance.html")


@app.route("/teacher/videos")
@login_required(role="teacher")
def teacher_videos():
    return render_template("teacher/videos.html")


@app.route("/teacher/subjects")
@login_required(role="teacher")
def teacher_subjects():
    return render_template("teacher/subjects.html")


@app.route("/teacher/announcements")
@login_required(role="teacher")
def teacher_announcements():
    return render_template("teacher/announcements.html")


@app.route("/teacher/ai-tools")
@login_required(role="teacher")
def teacher_ai_tools():
    return render_template("teacher/ai_tools.html")


# -----------------------
# Student pages
# -----------------------
@app.route("/student/dashboard")
@login_required(role="student")
def student_dashboard():
    announcements = sheets.get_announcements()[:5]
    return render_template("student/student_dashboard.html", announcements=announcements)


@app.route("/student/videos")
@login_required(role="student")
def student_videos():
    return render_template("student/my_videos.html")


@app.route("/student/attendance")
@login_required(role="student")
def student_attendance():
    return render_template("student/attendance_view.html")


@app.route("/student/chatbot")
@login_required(role="student")
def student_chatbot():
    return render_template("student/chatbot.html")


@app.route("/student/announcements")
@login_required(role="student")
def student_announcements():
    return render_template("student/announcements_view.html")


# -----------------------
# REST APIs
# -----------------------
@app.route("/api/students", methods=["GET", "POST"])
@login_required(role="teacher")
def api_students():
    if request.method == "GET":
        q = request.args.get("q", "").lower().strip()
        students = sheets.get_students()
        if q:
            students = [s for s in students if q in str(s).lower()]
        return jsonify(students)

    data = request.json or {}
    sheets.add_student(data)
    return jsonify({"status": "ok", "message": "Student added"})


@app.route("/api/students/<student_id>", methods=["PUT", "DELETE"])
@login_required(role="teacher")
def api_student_by_id(student_id):
    if request.method == "PUT":
        updated = sheets.update_student(student_id, request.json or {})
        return jsonify({"status": "ok" if updated else "error", "updated": updated})

    deleted = sheets.delete_student(student_id)
    return jsonify({"status": "ok" if deleted else "error", "deleted": deleted})


@app.route("/api/attendance", methods=["GET", "POST"])
@login_required()
def api_attendance():
    if request.method == "GET":
        rows = sheets.get_attendance()
        if session.get("role") == "student":
            sid = request.args.get("student_id", "")
            rows = [r for r in rows if str(r.get("student_id")) == str(sid)] if sid else rows
        return jsonify(rows)

    if session.get("role") != "teacher":
        return jsonify({"error": "forbidden"}), 403

    attendance_rows = request.json.get("rows", [])
    sheets.save_attendance(attendance_rows)
    return jsonify({"status": "ok", "saved": len(attendance_rows)})


@app.route("/api/videos", methods=["GET", "POST"])
@login_required()
def api_videos():
    if request.method == "GET":
        return jsonify(sheets.get_videos())

    if session.get("role") != "teacher":
        return jsonify({"error": "forbidden"}), 403

    data = request.json
    sheets.add_video(data.get("date"), data.get("subject"), data.get("drive_link"))
    return jsonify({"status": "ok"})


@app.route("/api/subjects", methods=["GET", "POST", "PUT", "DELETE"])
@login_required()
def api_subjects():
    if request.method == "GET":
        return jsonify(sheets.get_subjects())

    if session.get("role") != "teacher":
        return jsonify({"error": "forbidden"}), 403

    data = request.json or {}
    if request.method == "POST":
        sheets.add_subject(data.get("subject_name", ""))
        return jsonify({"status": "ok"})

    if request.method == "PUT":
        updated = sheets.update_subject(data.get("old_name", ""), data.get("new_name", ""))
        return jsonify({"status": "ok" if updated else "error", "updated": updated})

    deleted = sheets.delete_subject(data.get("subject_name", ""))
    return jsonify({"status": "ok" if deleted else "error", "deleted": deleted})


@app.route("/api/announcements", methods=["GET", "POST"])
@login_required()
def api_announcements():
    if request.method == "GET":
        return jsonify(sheets.get_announcements())

    if session.get("role") != "teacher":
        return jsonify({"error": "forbidden"}), 403

    data = request.json or {}
    date = data.get("date", datetime.utcnow().strftime("%Y-%m-%d"))
    sheets.add_announcement(data.get("message", ""), date)
    return jsonify({"status": "ok"})


# -----------------------
# AI APIs
# -----------------------
@app.route("/api/ai/doubt-solver", methods=["POST"])
@login_required()
def ai_doubt_solver():
    question = request.json.get("question", "")
    prompt = (
        "Explain this concept in very simple words for a school student. "
        "If it is math, provide a step-by-step solution.\n\n"
        f"Question: {question}"
    )
    answer = ai_service.ask(prompt)
    return jsonify({"answer": answer})


@app.route("/api/ai/chatbot", methods=["POST"])
@login_required(role="student")
def ai_chatbot():
    message = request.json.get("message", "")
    prompt = (
        "You are a friendly AI tutor for school students. Help with concept doubts, "
        "exam prep and study tips in simple language.\n\n"
        f"Student message: {message}"
    )
    answer = ai_service.ask(prompt)
    return jsonify({"answer": answer})


@app.route("/api/ai/attendance-analysis", methods=["POST"])
@login_required(role="teacher")
def ai_attendance_analysis():
    attendance_data = sheets.get_attendance()
    prompt = (
        "Analyze attendance data and provide insights. "
        "Include irregular students, attendance percentage and recommended action.\n\n"
        f"Attendance Data: {attendance_data}"
    )
    answer = ai_service.ask(prompt)
    return jsonify({"answer": answer})


@app.route("/api/ai/video-summary", methods=["POST"])
@login_required(role="teacher")
def ai_video_summary():
    topic = request.json.get("topic", "")
    prompt = (
        "Generate summary notes for revision. Include key points and quick revision notes.\n\n"
        f"Topic: {topic}"
    )
    answer = ai_service.ask(prompt)
    return jsonify({"answer": answer})


@app.route("/api/ai/quiz-generator", methods=["POST"])
@login_required(role="teacher")
def ai_quiz_generator():
    subject = request.json.get("subject", "")
    topic = request.json.get("topic", "")
    prompt = (
        "Generate 5 MCQ questions with answers for school students. "
        "Keep difficulty medium and exam-oriented.\n\n"
        f"Subject: {subject}\nTopic: {topic}"
    )
    answer = ai_service.ask(prompt)
    return jsonify({"answer": answer})


@app.route("/api/ai/announcement-generator", methods=["POST"])
@login_required(role="teacher")
def ai_announcement_generator():
    topic = request.json.get("topic", "")
    prompt = (
        "Write a professional coaching class announcement."
        f"\n\nTopic: {topic}"
    )
    answer = ai_service.ask(prompt)
    return jsonify({"answer": answer})


if __name__ == "__main__":
    app.run(host="0.0.0.0", port=5000, debug=True)
