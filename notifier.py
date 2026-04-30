# notifier.py

import os
from pushbullet import Pushbullet
from logger import log_event
from dotenv import load_dotenv

# Load environment variables (.env file)
load_dotenv()

# Get Pushbullet API token
PB_ACCESS_TOKEN = os.getenv("PUSHBULLET_TOKEN")


def send_push_notification(message, title="Secure File Transfer Alert"):
    """
    Sends push notification using Pushbullet
    """

    # If token not available → skip safely
    if not PB_ACCESS_TOKEN:
        print("[!] Pushbullet token not set. Skipping notification.")
        log_event("Push notification skipped (token not set).")
        return

    try:
        # Initialize Pushbullet client
        pb = Pushbullet(PB_ACCESS_TOKEN)

        # Send notification
        pb.push_note(title, message)

        print("[+] Push notification sent.")
        log_event(f"Push notification: {message}")

    except Exception as e:
        # Handle API issues (network, inactive account, etc.)
        print(f"[!] Notification failed: {e}")

        # Keep system stable (no crash)
        log_event(f"Push notification failed: {e}")