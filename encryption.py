# encryption.py

import os
import hashlib

# Fernet → for symmetric encryption (AES-based)
from cryptography.fernet import Fernet

# RSA + hashing + serialization
from cryptography.hazmat.primitives import hashes, serialization
from cryptography.hazmat.primitives.asymmetric import rsa, padding


# === FILE NAMES (CONSTANTS) ===
SYM_KEY_FILE = "secret.key"
PRIVATE_KEY_FILE = "private_key.pem"
PUBLIC_KEY_FILE = "public_key.pem"
RECEIVER_PUBLIC_KEY_FILE = "receiver_public.pem"
RECEIVER_PRIVATE_KEY_FILE = "receiver_private.pem"


# === SYMMETRIC KEY FUNCTIONS ===
def generate_symmetric_key():
    """
    Generates a symmetric key (only if not already present)
    """
    if not os.path.exists(SYM_KEY_FILE):
        key = Fernet.generate_key()   # Generate AES key
        with open(SYM_KEY_FILE, 'wb') as f:
            f.write(key)
        print("[+] Symmetric key generated.")

    return load_symmetric_key()


def load_symmetric_key():
    """
    Loads existing symmetric key from file
    """
    with open(SYM_KEY_FILE, 'rb') as f:
        return f.read()


# === RSA KEY GENERATION ===
def generate_rsa_keys():
    """
    Generates RSA public/private key pair
    """
    if not os.path.exists(PRIVATE_KEY_FILE) or not os.path.exists(PUBLIC_KEY_FILE):

        # Create private key
        private_key = rsa.generate_private_key(
            public_exponent=65537,
            key_size=2048
        )

        # Generate public key from private key
        public_key = private_key.public_key()

        # Save private key
        with open(PRIVATE_KEY_FILE, "wb") as f:
            f.write(private_key.private_bytes(
                serialization.Encoding.PEM,
                serialization.PrivateFormat.PKCS8,
                serialization.NoEncryption()
            ))

        # Save public key
        with open(PUBLIC_KEY_FILE, "wb") as f:
            f.write(public_key.public_bytes(
                serialization.Encoding.PEM,
                serialization.PublicFormat.SubjectPublicKeyInfo
            ))

        print("[+] RSA keys generated.")


def load_private_key():
    """Loads sender private key"""
    with open(PRIVATE_KEY_FILE, "rb") as f:
        return serialization.load_pem_private_key(f.read(), password=None)


def load_public_key():
    """Loads sender public key"""
    with open(PUBLIC_KEY_FILE, "rb") as f:
        return serialization.load_pem_public_key(f.read())


# === ENCRYPT + DIGITAL SIGNATURE ===

def encrypt_and_sign(file_path):
    """
    1. Encrypt file using symmetric key
    2. Sign encrypted data using RSA private key
    """

    generate_symmetric_key()
    generate_rsa_keys()

    # Load symmetric key
    sym_key = load_symmetric_key()
    fernet = Fernet(sym_key)

    # Read file
    with open(file_path, 'rb') as f:
        plaintext = f.read()

    # Encrypt file
    encrypted_data = fernet.encrypt(plaintext)

    # Save encrypted file
    enc_file = file_path + ".enc"
    with open(enc_file, 'wb') as f:
        f.write(encrypted_data)

    # Load private key for signing
    private_key = load_private_key()

    # Create digital signature
    signature = private_key.sign(
        encrypted_data,
        padding.PSS(
            mgf=padding.MGF1(hashes.SHA256()),
            salt_length=padding.PSS.MAX_LENGTH
        ),
        hashes.SHA256()
    )

    # Save signature file
    sig_file = file_path + ".sig"
    with open(sig_file, 'wb') as f:
        f.write(signature)

    print("[+] File encrypted and signed.")

    return enc_file, sig_file, os.path.basename(file_path)


# === DECRYPT + VERIFY SIGNATURE ===
def decrypt_and_verify_signature(enc_file, sig_file, original_filename):
    """
    1. Verify digital signature
    2. Decrypt file
    """

    sym_key = load_symmetric_key()
    fernet = Fernet(sym_key)

    # Read encrypted data
    with open(enc_file, 'rb') as f:
        encrypted_data = f.read()

    # Read signature
    with open(sig_file, 'rb') as f:
        signature = f.read()

    # Load public key for verification
    public_key = load_public_key()

    # Verify signature (throws error if tampered)
    public_key.verify(
        signature,
        encrypted_data,
        padding.PSS(
            mgf=padding.MGF1(hashes.SHA256()),
            salt_length=padding.PSS.MAX_LENGTH
        ),
        hashes.SHA256()
    )

    print("[+] Signature verified.")

    # Decrypt file
    decrypted_data = fernet.decrypt(encrypted_data)

    # Save decrypted file
    name, ext = os.path.splitext(original_filename)
    output_file = f"{name}.decrypted{ext}"

    with open(output_file, 'wb') as f:
        f.write(decrypted_data)

    print(f"[+] File decrypted: {output_file}")

    return os.path.abspath(output_file)


# === PASSCODE ENCRYPTION (RSA) ===
def encrypt_passphrase(passphrase):
    """
    Encrypt passphrase using receiver's public key
    """
    with open(RECEIVER_PUBLIC_KEY_FILE, "rb") as f:
        pubkey = serialization.load_pem_public_key(f.read())

    encrypted = pubkey.encrypt(
        passphrase.encode(),
        padding.OAEP(
            mgf=padding.MGF1(algorithm=hashes.SHA256()),
            algorithm=hashes.SHA256(),
            label=None
        )
    )

    with open("encrypted_passphrase.bin", "wb") as f:
        f.write(encrypted)

    print("[+] Passphrase encrypted.")


def decrypt_passphrase(file_path="encrypted_passphrase.bin"):
    """
    Decrypt passphrase using receiver's private key
    """
    print("DEBUG: decrypt_passphrase called with:", file_path)
    
    with open(RECEIVER_PRIVATE_KEY_FILE, "rb") as f:
        privkey = serialization.load_pem_private_key(f.read(), password=None)

    with open(file_path, "rb") as f:
        encrypted = f.read()

    decrypted = privkey.decrypt(
        encrypted,
        padding.OAEP(
            mgf=padding.MGF1(algorithm=hashes.SHA256()),
            algorithm=hashes.SHA256(),
            label=None
        )
    )

    return decrypted.decode()


# === FILE HASH (INTEGRITY CHECK) ===
def calculate_file_hash(file_path, write_to_file=True):
    """
    Generate SHA256 hash of file
    """

    sha256 = hashlib.sha256()

    with open(file_path, "rb") as f:
        while chunk := f.read(4096):
            sha256.update(chunk)

    hash_value = sha256.hexdigest()

    if write_to_file:
        with open("file_hash.txt", "w") as f:
            f.write(hash_value)

        print(f"[+] Hash saved: {hash_value}")
        return "file_hash.txt"

    return hash_value