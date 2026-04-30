# utils.py

import requests
import time
import magic
from logger import log_virustotal_result

def scan_with_virustotal(file_path, api_key):
    """
    Upload file → wait → fetch result → log it
    """

    print(f"[*] Scanning '{file_path}' with VirusTotal...")

    # Basic validation
    if not file_path or not api_key:
        print("[!] Missing file path or API key.")
        return

    url = 'https://www.virustotal.com/api/v3/files'
    headers = {"x-apikey": api_key}

    try:
        # Upload file
        with open(file_path, 'rb') as f:
            files = {'file': (file_path, f)}
            response = requests.post(url, headers=headers, files=files)

        # Check response
        if response.status_code != 200:
            print("[!] VirusTotal API error:", response.status_code, response.text)
            return

        result = response.json()
        analysis_id = result["data"]["id"]
        print(f"[+] File uploaded successfully. Analysis ID: {analysis_id}")

        # Wait for analysis (free API is slow)
        analysis_url = f"https://www.virustotal.com/api/v3/analyses/{analysis_id}"
        time.sleep(20)  # improved wait time

        # Get result
        result_response = requests.get(analysis_url, headers=headers)

        if result_response.status_code == 200:
            analysis = result_response.json()

            # Safe access (prevents crash)
            stats = analysis.get('data', {}).get('attributes', {}).get('stats', {})

            harmless = stats.get('harmless', 0)
            malicious = stats.get('malicious', 0)
            suspicious = stats.get('suspicious', 0)
            undetected = stats.get('undetected', 0)

            print(f"[+] VirusTotal Scan Results for '{file_path}':")
            print(f"    Harmless: {harmless}")
            print(f"    Malicious: {malicious}")
            print(f"    Suspicious: {suspicious}")
            print(f"    Undetected: {undetected}")

            # Log results
            log_virustotal_result(file_path, harmless, malicious, suspicious, undetected)

        else:
            print("[!] Failed to retrieve analysis result.")

    except Exception as e:
        print(f"[!] Error during VirusTotal scan: {e}")


def validate_file_type(file_path, expected_mime_prefix="text"):
    """
    Validate file type using python-magic
    """
    try:
        mime = magic.from_file(file_path, mime=True)
        print(f"[+] Detected MIME type: {mime}")
        return mime.startswith(expected_mime_prefix)
    except Exception as e:
        print(f"[!] Failed to detect MIME type: {e}")
        return False 