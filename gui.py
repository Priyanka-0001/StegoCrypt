# gui.py

import tkinter as tk  
from tkinter import filedialog, messagebox, ttk, scrolledtext  
import os  
import urllib.request  
import threading  
import zipfile  
import magic  
from inotify_simple import INotify, flags  
  
import importlib
import encryption
importlib.reload(encryption)

import os
from dotenv import load_dotenv

load_dotenv()


from encryption import (  
    encrypt_and_sign,  
    decrypt_and_verify_signature,  
    decrypt_passphrase,  
    encrypt_passphrase,  
    calculate_file_hash,  
    generate_rsa_keys,  
    generate_symmetric_key,  
)  
  
from steganography import embed_file_in_image, extract_file_from_image  
from network import send_file_to_receiver, receive_file  
from logger import log_event, export_logs_to_csv, fetch_logs, fetch_virustotal_logs  
from notifier import send_push_notification  
from utils import scan_with_virustotal  
  
VIRUSTOTAL_API_KEY = os.getenv("VIRUSTOTAL_API_KEY")
if not VIRUSTOTAL_API_KEY:
    raise ValueError("VirusTotal API key not found. Set it in .env file.")
  
class SecureFileTransferApp:  
    def __init__(self, root):  
        self.root = root  
        self.root.title("StegoCrypt - Secure File Transfer")  
        self.root.geometry("580x560")  
  
        self.font = ("Segoe UI", 10)  
  
        self.colors = {  
            "bg": "#f9f9ff",  
            "section_bg": "#f0f8ff",  
            "accent": "#4A90E2",  
            "text": "#000000",  
            "button": "#e1eaff",  
        }  
  
        self.status_var = tk.StringVar()  
        self.selected_file_label = None  
        self.progress = None  
  
        self.create_widgets()  
  
    def create_widgets(self):  
        self.root.configure(bg=self.colors["bg"])  
  
        header = tk.Label(  
            self.root,  
            text="🔐 StegoCrypt",  
            font=("Segoe UI", 20, "bold"),  
            bg=self.colors["bg"],  
            fg=self.colors["text"],  
        )  
        header.pack(pady=(10, 5))  
  
        file_frame = tk.LabelFrame(  
            self.root,  
            text="[ 📂 File Operations ]",  
            font=self.font,  
            bg=self.colors["section_bg"],  
        )  
        file_frame.pack(padx=10, pady=10, fill="both")  
  
        tk.Button(  
            file_frame,  
            text="🔒 Encrypt & Send 📤",  
            font=self.font,  
            bg=self.colors["button"],  
            command=self.encrypt_and_send,  
        ).pack(pady=5)  
  
        tk.Button(  
            file_frame,  
            text="📥 Receive & Decrypt 🔓",  
            font=self.font,  
            bg=self.colors["button"],  
            command=self.receive_and_decrypt,  
        ).pack(pady=5)  
  
        tk.Button(  
            file_frame,  
            text="⬇️ Download + Display Decrypted File 📄",  
            font=self.font,  
            bg=self.colors["button"],  
            command=self.display_decrypted_file,  
        ).pack(pady=5)  
  
        self.selected_file_label = tk.Label(  
            file_frame,  
            text="No file selected",  
            font=("Segoe UI", 9),  
            bg=self.colors["section_bg"],  
            fg="gray",  
        )  
        self.selected_file_label.pack(pady=2)  
  
        log_frame = tk.LabelFrame(  
            self.root,  
            text="[ 📃 Logs ]",  
            font=self.font,  
            bg=self.colors["section_bg"],  
        )  
        log_frame.pack(padx=10, pady=10, fill="both")  
  
        tk.Button(  
            log_frame,  
            text="📜 View Logs",  
            font=self.font,  
            bg=self.colors["button"],  
            command=self.show_logs_window,  
        ).pack(pady=5)  
  
        tk.Button(  
            log_frame,  
            text="💾 Export Logs to CSV",  
            font=self.font,  
            bg=self.colors["button"],  
            command=self.export_logs_with_status,  
        ).pack(pady=5)  
  
        sys_frame = tk.LabelFrame(  
            self.root,  
            text="[ ⚙️ System ]",  
            font=self.font,  
            bg=self.colors["section_bg"],  
        )  
        sys_frame.pack(padx=10, pady=10, fill="both")  
  
        tk.Button(  
            sys_frame,  
            text="♻️ Reset Environment",  
            font=self.font,  
            bg=self.colors["button"],  
            command=self.reset_environment,  
        ).pack(pady=5)  
  
        tk.Button(  
            sys_frame,  
            text="❌ Exit",  
            font=self.font,  
            bg=self.colors["button"],  
            command=self.root.quit,  
        ).pack(pady=5)  
  
        self.progress = ttk.Progressbar(self.root, orient="horizontal", mode="indeterminate")  
        self.progress.pack(pady=5, fill="x", padx=10)  
  
        status_bar = tk.Label(  
            self.root,  
            textvariable=self.status_var,  
            font=("Segoe UI", 9),  
            relief=tk.SUNKEN,  
            anchor="w",  
            bg="#eaeaea",  
        )  
        status_bar.pack(side="bottom", fill="x")  
  
    def update_status(self, message):  
        self.status_var.set(message)  
        log_event(message)  
  
    def download_cover_image(self):  
        url = "https://images.pexels.com/photos/34950/pexels-photo.jpg"  
        image_name = "cover_large.jpeg"  
  
        if not os.path.exists(image_name):  
            try:  
                req = urllib.request.Request(url, headers={"User-Agent": "Mozilla/5.0"})  
                with urllib.request.urlopen(req) as res, open(image_name, 'wb') as f:  
                    f.write(res.read())  
                print("[+] Cover image downloaded.")  
            except Exception as e:  
                print(f"[!] Failed to download image: {e}")  
                raise  
  
        return image_name  
  
    def encrypt_and_send(self):  
        file_path = filedialog.askopenfilename(title="Select File to Send")  
        if not file_path:  
            return  
  
        self.selected_file_label.config(text=os.path.basename(file_path))  
        self.progress.start()  
  
        try:  
            generate_rsa_keys()  
            generate_symmetric_key()  
  
            encrypted_file, sig_file, original_name = encrypt_and_sign(file_path)  
  
            cover_image = self.download_cover_image()  
  
            # Embed encrypted data into image  
            steg_file = embed_file_in_image(encrypted_file, sig_file, cover_image)  
  
            # Encrypt passphrase using receiver public key  
            encrypt_passphrase("mysecret")  
  
            package_name = "final_package.zip"  
  
            with zipfile.ZipFile(package_name, 'w') as zf:  
                zf.write(steg_file)  
                zf.write("encrypted_passphrase.bin")  
  
            send_file_to_receiver(package_name)  
  
            self.update_status("File sent successfully.")  
            messagebox.showinfo("Success", "File encrypted, hidden, and sent!")  
  
        except Exception as e:  
            messagebox.showerror("Error", str(e))  
  
        finally:  
            # prevent crash  
            if self.progress.winfo_exists():  
                self.progress.stop()  
  
    def receive_and_decrypt(self):  
        self.progress.start()  
  
        try:  
            zip_file = receive_file()  
  
            with zipfile.ZipFile(zip_file, 'r') as zf:  
                zf.extractall("received")  
  
            os.remove(zip_file)  
  
            steg_file = os.path.join("received", "stegofile.jpeg")  
            pass_file = os.path.join("received", "encrypted_passphrase.bin")  
  
            print("Calling decrypt_passphrase with:", pass_file)
            # remove duplicate extraction  
            encryption.decrypted_pass = decrypt_passphrase(pass_file)  
  
            extract_file_from_image(steg_file)  
  
            enc_file = next(f for f in os.listdir() if f.endswith(".enc"))  
            sig_file = next(f for f in os.listdir() if f.endswith(".sig"))  
  
            original_name = enc_file.replace(".enc", "")  
  
            decrypted_file = decrypt_and_verify_signature(enc_file, sig_file, original_name)  
  
            scan_with_virustotal(decrypted_file, VIRUSTOTAL_API_KEY)  
  
            actual_mime = magic.from_file(decrypted_file, mime=True)  
            if not actual_mime.startswith("text") and not actual_mime.startswith("application"):  
                raise Exception("Unexpected file type: " + actual_mime)  
  
            with open("file_hash.txt", "r") as f:  
                original_hash = f.read().strip()  
  
            current_hash = calculate_file_hash(enc_file, write_to_file=False)  
  
            if original_hash != current_hash:  
                raise Exception("File integrity check failed!")  
  
            self.update_status("File format and integrity validated.")  
  
            self.monitor_file(decrypted_file)  
  
            os.remove("payload.zip")  
  
            messagebox.showinfo("Success", f"File validated and ready: {decrypted_file}")  
  
        except Exception as e:  
            send_push_notification(f"File error: {e}")  
            messagebox.showerror("Error", str(e))  
  
        finally:  
            # prevent crash  
            if self.progress.winfo_exists():  
                self.progress.stop()  
  
    def monitor_file(self, filepath):  
        try:  
            notify = INotify()  
            watch_flags = flags.MODIFY | flags.DELETE_SELF | flags.MOVE_SELF  
  
            notify.add_watch(filepath, watch_flags)  
  
            log_event(f"Monitoring {filepath} for changes...")  
  
            def watch():  
                for event in notify.read():  
                    log_event(f"[MONITOR] File change detected: {event}")  
                    send_push_notification(f"File change detected: {filepath}")  
                    break  
  
            threading.Thread(target=watch, daemon=True).start()  
  
        except Exception as e:  
            print("[!] Monitoring setup failed:", e)  
  
    def display_decrypted_file(self):  
        try:  
            decrypted_file = next(  
                f for f in os.listdir()  
                if f.startswith("sample.decrypted.") or f.endswith(".decrypted.txt") or f.endswith(".decrypted.pdf")  
            )  
  
            if decrypted_file.endswith(".txt"):  
                with open(decrypted_file, "r") as f:  
                    content = f.read()  
  
                viewer = tk.Toplevel(self.root)  
                viewer.title("Decrypted File Viewer")  
  
                text_area = scrolledtext.ScrolledText(viewer, wrap=tk.WORD, font=("Segoe UI", 10))  
                text_area.insert(tk.END, content)  
                text_area.pack(expand=True, fill="both")  
  
            elif decrypted_file.endswith(".pdf"):  
                messagebox.showinfo("Info", f"Open PDF manually: {decrypted_file}")  
  
            else:  
                messagebox.showerror("Unsupported Format", "Only .txt or .pdf supported.")  
  
        except StopIteration:  
            messagebox.showwarning("No File", "No decrypted file found.")  
  
    def show_logs_window(self):
        log_win = tk.Toplevel(self.root)
        log_win.title("System Logs")
        log_win.geometry("800x400")

        notebook = ttk.Notebook(log_win)
        notebook.pack(expand=True, fill="both")

    # === Activity Logs Tab ===
        activity_tab = ttk.Frame(notebook)
        notebook.add(activity_tab, text="Activity Logs")

        activity_text = scrolledtext.ScrolledText(activity_tab)
        activity_text.pack(fill="both", expand=True)

        for log in fetch_logs():
            activity_text.insert(tk.END, f"[{log[1]}] {log[2]}\n")

    # === VirusTotal Logs Tab ===
        vt_tab = ttk.Frame(notebook)
        notebook.add(vt_tab, text="VirusTotal Logs")

        vt_text = scrolledtext.ScrolledText(vt_tab)
        vt_text.pack(fill="both", expand=True)

        for vt in fetch_virustotal_logs():
            vt_text.insert(
            tk.END,
            f"[{vt[2]}] {vt[1]} → Harmless: {vt[3]}, Malicious: {vt[4]}, Suspicious: {vt[5]}, Undetected: {vt[6]}\n"
        )


    def export_logs_with_status(self):  
        export_logs_to_csv()  
        self.update_status("Logs exported to CSV.")  
  
    def reset_environment(self):  
        if not messagebox.askyesno("Reset", "Delete temporary files?"):  
            return  
  
        try:  
            for file in os.listdir():  
                if file.endswith((  
                    ".enc", ".sig", ".decrypted.txt", ".decrypted.pdf",  
                    "payload.zip", "stegofile.jpeg", "file_hash.txt",  
                    "final_package.zip", "cover_large.jpeg",  
                    "encrypted_passphrase.bin"  
                )):  
                    os.remove(file)  
  
            if os.path.exists("received"):  
                for f in os.listdir("received"):  
                    os.remove(os.path.join("received", f))  
                os.rmdir("received")  
  
            self.update_status("Environment reset done.")  
  
        except Exception as e:  
            log_event(f"[!] Reset error: {e}")  
  
  
def run_gui():  
    root = tk.Tk()  
    app = SecureFileTransferApp(root)  
    root.mainloop()