# ASWATHAMA CLASSES

AI-powered coaching web platform built with Flask + Google Sheets + OpenAI.

## Features

- Role-based login (Teacher/Admin and Student/User)
- Session authentication with logout
- Teacher modules: dashboard, students, attendance, videos, subjects, announcements, AI tools
- Student modules: dashboard, videos, attendance view, chatbot, announcements
- Google Sheets as cloud data backend
- OpenAI features:
  - Doubt solver
  - Study chatbot
  - Attendance analysis
  - Video summary
  - Quiz generator
  - Announcement generator

## Project Structure

```bash
app.py
requirements.txt
README.md
static/
  style.css
  script.js
templates/
  base.html
  login.html
  teacher/
    dashboard.html
    students.html
    attendance.html
    videos.html
    subjects.html
    announcements.html
    ai_tools.html
  student/
    student_dashboard.html
    my_videos.html
    attendance_view.html
    chatbot.html
    announcements_view.html
```

## Setup Guide

### 1) Create Google Sheet
Create a spreadsheet with 5 worksheets and exact names:

1. `students` with columns:
   - id, name, class, roll, phone, email, parent
2. `attendance` with columns:
   - date, student_id, status
3. `videos` with columns:
   - date, subject, drive_link
4. `subjects` with columns:
   - subject_name
5. `announcements` with columns:
   - date, message

Copy the spreadsheet ID from URL (optional if you want to use an existing sheet):

`https://docs.google.com/spreadsheets/d/<SHEET_ID>/edit`

If `GOOGLE_SHEET_ID` is empty, the app will automatically create a new spreadsheet and store the generated ID in `generated_sheet_id.txt`.

### 2) Enable Google Sheets API

1. Go to Google Cloud Console.
2. Create/select project.
3. Enable **Google Sheets API** and **Google Drive API**.
4. Create a **Service Account**.
5. Download JSON key file.

### 3) Place JSON key

- Put the key file in project root, for example:
  - `/workspace/kuchbhi/service_account.json`
- Ensure this JSON key belongs to the service account that has Editor access to your sheet.

### 4) Place OpenAI API key

Create a `.env` file:

```env
FLASK_SECRET_KEY=replace-with-strong-secret
GOOGLE_CREDENTIALS_FILE=service_account.json
# Optional fallback if file path is not used:
# GOOGLE_SERVICE_ACCOUNT_JSON={"type":"service_account",...}
GOOGLE_SHEET_ID=your_google_sheet_id   # optional; leave empty to auto-create
GOOGLE_SHEET_NAME=ASWATHAMA_CLASSES_DB
GOOGLE_OWNER_EMAIL=lovelyaayush4u@gmail.com
OPENAI_API_KEY=your_openai_api_key
OPENAI_MODEL=gpt-4o-mini

TEACHER_USERNAME=teacher
TEACHER_PASSWORD=teacher123
STUDENT_USERNAME=student
STUDENT_PASSWORD=student123
```

### 5) Run Flask locally

```bash
python -m venv .venv
source .venv/bin/activate
pip install -r requirements.txt
python app.py
```

Open: `http://127.0.0.1:5000`

### 6) Deploy on Render

1. Push code to GitHub.
2. Create **Web Service** on Render.
3. Build command:
   - `pip install -r requirements.txt`
4. Start command:
   - `gunicorn app:app`
5. Add environment variables from `.env` in Render dashboard.
6. Upload service account JSON securely (or mount as secret file) and set `GOOGLE_CREDENTIALS_FILE` path.
7. Set `GOOGLE_OWNER_EMAIL` so the created sheet is automatically shared to your account.

## AI Prompt Templates Used in Code

- Doubt solver prompt:
  - "Explain this concept in very simple words for a school student"
- Quiz generator prompt:
  - "Generate 5 MCQ questions with answers"
- Announcement prompt:
  - "Write a professional coaching class announcement"
- Attendance insight prompt:
  - "Analyze attendance data and provide insights"
- Video summary prompt:
  - "Generate summary notes for revision"

## Notes

- Use strong secrets and production credentials.
- Replace default usernames/passwords before deployment.
- Keep service account JSON private and never commit real secrets.
