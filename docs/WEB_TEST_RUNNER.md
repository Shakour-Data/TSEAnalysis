# Integrated Web Test Runner & CI/CD Module

This module replaces the legacy PyQt-based test runner with a modern, asynchronous, and AI-integrated web dashboard.

## Features
- **Asynchronous Execution:** Tests run in isolated subprocesses using the system's Python environment.
- **AI-Powered Diagnostics:** On failure, the project's internal AI logic analyzes logs to provide a "Diagnosis" and "Alarms".
- **Real-time Monitoring:** The Admin Panel (`/management`) polls for real-time updates and log streaming.
- **Database Integration:** All test results, logs, and AI summaries are persisted in SQLite for historical analysis.
- **Scheduler:** Built-in background service for automated health checks and regression testing.
- **Docker-Ready:** Subprocess execution ensures portability and isolation.

## Security
- Integrated into the Flask `management.html` template.
- Can be restricted via Flask middlewares for Admin-only access.

## CLI & CI/CD Integration
The runner saves results to the `test_results` table. For external CI/CD tool integration, you can use the JSON API endpoint:
`GET /api/tests/results?limit=1`

## How to use
1. Start the Flask application: `python app.py`
2. Navigate to `http://127.0.0.1:5000/management`
3. Click on **"اجرای کل تست‌ها"** or specific test buttons.
4. Review the AI analysis and full logs in the table below.

## Removal of PyQt
The `PyQt6` and `qt-material` dependencies have been completely removed from the project to reduce overhead and simplify deployment on Headless/Web servers.
