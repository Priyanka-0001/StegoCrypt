# main.py

import tkinter as tk
from gui import SecureFileTransferApp
from logger import init_db 

if __name__ == "__main__":
    # Step 1: Initialize database (creates tables if not already present)
    init_db()

    # Step 2: Launch the GUI
    root = tk.Tk()
    app = SecureFileTransferApp(root)
    root.mainloop()