import subprocess
import sys
import time
import webbrowser
import os
import socket
from pathlib import Path
import sys

PORT = 8601

def wait_for_streamlit(port, timeout=40):
    start = time.time()
    while time.time() - start < timeout:
        try:
            with socket.create_connection(("127.0.0.1", port), timeout=1):
                return True
        except OSError:
            time.sleep(0.5)
    return False

def get_app_path():
    """
    Returns absolute path to app.py whether running normally
    or from PyInstaller bundle.
    """
    if getattr(sys, "frozen", False):
        # Running inside PyInstaller bundle
        base = Path(sys._MEIPASS)
    else:
        # Normal Python run
        base = Path(__file__).parent

    return base / "app.py"

def main():
    # Prevent infinite relaunch
    if os.environ.get("STREAMLIT_ALREADY_RUNNING") == "1":
        return

    os.environ["STREAMLIT_ALREADY_RUNNING"] = "1"

    app_path = get_app_path()

    if not app_path.exists():
        print(f"❌ app.py not found at: {app_path}")
        return

    # Start Streamlit with absolute path
    subprocess.Popen(
        [
            sys.executable,
            "-m",
            "streamlit",
            "run",
            str(app_path),
            f"--server.port={PORT}",
            "--server.headless=true",
            "--browser.gatherUsageStats=false",
        ],
        stdout=subprocess.PIPE,
        stderr=subprocess.PIPE,
        cwd=app_path.parent,
    )

    # Wait until Streamlit is actually listening
    if wait_for_streamlit(PORT):
        webbrowser.open_new(f"http://localhost:{PORT}")
    else:
        print("❌ Streamlit did not start within timeout")

if __name__ == "__main__":
    main()
