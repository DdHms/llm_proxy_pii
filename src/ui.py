import os
import threading
from fastapi.responses import HTMLResponse
from src import constants

def get_dashboard_html():
    # Use absolute path relative to this file's location
    current_dir = os.path.dirname(os.path.abspath(__file__))
    file_path = os.path.join(current_dir, "dashboard.html")
    with open(file_path, "r") as f:
        return f.read()

def start_fastapi(app):
    import uvicorn
    constants.print_startup_urls()
    if constants.HOST in ("0.0.0.0", "::") and not constants.DASHBOARD_TOKEN:
        print(
            "[Warning] LLM Shield is listening on all interfaces without DASHBOARD_TOKEN. "
            "Dashboard/API endpoints may expose sensitive request logs to your network.",
            flush=True,
        )
    uvicorn.run(app, host=constants.HOST, port=constants.PORT, log_level="info")

def run_application(app):
    import webview
    # 1. Start FastAPI
    if os.getenv("HEADLESS", "false").lower() == "true":
        print("Running in HEADLESS mode (FastAPI only)...")
        start_fastapi(app)
    else:
        t = threading.Thread(target=start_fastapi, args=(app,))
        t.daemon = True
        t.start()

        # 2. Open a beautiful native GUI window for the user
        try:
            webview.create_window('Gemini Privacy Shield', f'http://127.0.0.1:{constants.PORT}/dashboard')
            webview.start()
        except Exception as e:
            print(f"GUI failed to start: {e}. Falling back to server only.")
            # If GUI fails (common in Docker), keep the thread alive or restart in main
            start_fastapi(app)
