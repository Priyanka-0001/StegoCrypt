# network.py

import shutil
import os
import zipfile   


def send_file_to_receiver(zip_file, destination_folder="received"):
    """
    Simulates sending the final ZIP file to receiver
    """

    # Create receiver folder if it doesn't exist
    os.makedirs(destination_folder, exist_ok=True)

    # Copy ZIP file to receiver folder (acts like network transfer)
    destination_path = os.path.join(destination_folder, os.path.basename(zip_file))
    shutil.copy(zip_file, destination_path)

    print(f"[+] Sent {zip_file} to '{destination_folder}'.")


def receive_file(source_folder="received"):
    """
    Simulates receiving file from sender
    """

    # dynamically find any ZIP file instead of hardcoding name
    files = [f for f in os.listdir(source_folder) if f.endswith(".zip")]

    if not files:
        raise FileNotFoundError("No ZIP file found in 'received/'")

    # Pick the first ZIP file found
    final_zip = os.path.join(source_folder, files[0])

    print(f"[+] {files[0]} received.")

    return final_zip