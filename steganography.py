# steganography.py

import subprocess
import os
import zipfile
from encryption import calculate_file_hash


# === Embed Files into Image ===
def embed_file_in_image(enc_file, sig_file, cover_image, output_image='stegofile.jpeg', passphrase="mysecret"):
    zip_file = "payload.zip"

    # Step 1: Generate hash of encrypted file (for integrity check later)
    calculate_file_hash(enc_file, write_to_file=True)

    # Step 2: Create ZIP containing encrypted file + signature + public key + hash
    with zipfile.ZipFile(zip_file, 'w') as zipf:
        zipf.write(enc_file, arcname=os.path.basename(enc_file))
        zipf.write(sig_file, arcname=os.path.basename(sig_file))
        zipf.write("public_key.pem", arcname="public_key.pem")
        zipf.write("file_hash.txt", arcname="file_hash.txt")
        print(f"[+] Created zip archive: {zip_file}")

    # Step 3: If output image already exists, remove it (avoids manual overwrite prompt)
    if os.path.exists(output_image):
        os.remove(output_image)

    # Step 4: Embed ZIP inside image using steghide
    command = [
        "steghide", "embed",
        "-cf", cover_image,     # cover image
        "-ef", zip_file,        # file to hide
        "-sf", output_image,    # output stego image
        "-p", passphrase        # password
    ]

    subprocess.run(command, check=True)

    print(f"[+] ZIP embedded into image as: {output_image}")
    return output_image


# === Extract ZIP from Image ===
def extract_file_from_image(stego_image='stegofile.jpeg', passphrase="mysecret"):
    print("[*] Extracting payload from image...")

    # Remove old payload if exists
    if os.path.exists("payload.zip"):
        os.remove("payload.zip")
        print("[*] Old payload.zip removed.")

    # Extract hidden ZIP using steghide
    command = [
        "steghide", "extract",
        "-sf", stego_image,
        "-p", passphrase
    ]

    subprocess.run(command, check=True)

    # Unzip extracted data
    with zipfile.ZipFile("payload.zip", 'r') as zipf:
        zipf.extractall()
        print("[+] Extracted and unzipped payload successfully.")

        # Find encrypted file inside ZIP
        enc_files = [f for f in zipf.namelist() if f.endswith('.enc')]

        if enc_files:
            return enc_files[0]
        else:
            raise FileNotFoundError("Encrypted file (.enc) not found in extracted payload.")