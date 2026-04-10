import sys
import os
import ctypes
import tempfile
import shutil
import atexit
from tkinter import *
from tkinter import font as tkfont
from tkinter import messagebox
from PIL import Image, ImageTk
import secure_delete
import CombineAntivirus
import flash_encryption
import watcher
BG_COLOR = "#1a1a1a"
BG_SECONDARY = "#2a2a2a"
BUTTON_COLOR = "#2a2a2a"
BUTTON_ACTIVE_COLOR = "#3a3a3a"
TEXT_COLOR = "#e0e0e0"
TITLE_COLOR = "#3a6ea5"
BUTTON_TEXT_COLOR = "#2a4a7a"
FONT_FAMILY = "Segoe UI"
def resource_path(relative_path):
    if hasattr(sys, '_MEIPASS'):
        return os.path.join(sys._MEIPASS, relative_path)
    return os.path.join(os.path.abspath("."), relative_path)
def extract_temp_image(image_path):
    if not hasattr(sys, '_MEIPASS'):
        return image_path
    temp_dir = os.path.join(tempfile.gettempdir(), "satellite_images")
    os.makedirs(temp_dir, exist_ok=True)
    filename = os.path.basename(image_path)
    temp_path = os.path.join(temp_dir, filename)
    if os.path.exists(temp_path):
        return temp_path
    try:
        shutil.copy2(image_path, temp_path)
        return temp_path
    except Exception:
        return None
def cleanup_temp_files():
    temp_dir = os.path.join(tempfile.gettempdir(), "satellite_images")
    shutil.rmtree(temp_dir, ignore_errors=True)
atexit.register(cleanup_temp_files)
class SatelliteApp:
    def __init__(self):
        self.win = Tk()
        try:
            icon_path = resource_path("ico.png")
            if os.path.exists(icon_path):
                temp_icon = extract_temp_image(icon_path)
                if temp_icon and os.path.exists(temp_icon):
                    img = Image.open(temp_icon)
                    img = img.resize((32, 32), Image.Resampling.LANCZOS)
                    icon = ImageTk.PhotoImage(img)
                    self.win.iconphoto(True, icon)
                    self.icon = icon
        except Exception:
            pass
        self.win.title("satellite")
        self.win.configure(bg=BG_COLOR)
        self.win.attributes('-fullscreen', True)
        self.setup_fonts()
        self.load_images()
        self.create_main_interface()
    def setup_fonts(self):
        try:
            self.title_font = tkfont.Font(family=FONT_FAMILY, size=72, weight="bold")
            self.button_font = tkfont.Font(family=FONT_FAMILY, size=16, weight="bold")
        except Exception:
            self.title_font = tkfont.Font(size=72, weight="bold")
            self.button_font = tkfont.Font(size=16, weight="bold")

    def restore_main_interface(self):
        for widget in self.win.winfo_children():
            widget.destroy()
        self.create_main_interface()
    def load_images(self):
        self.images = {}
        icon_names = ["filee", "rubish", "sand", "flash"]
        for name in icon_names:
            try:
                img_path = resource_path(f"{name}.png")
                temp_path = extract_temp_image(img_path)
                if temp_path and os.path.exists(temp_path):
                    img = Image.open(temp_path)
                    img = img.resize((80, 80), Image.Resampling.LANCZOS)
                    self.images[name] = ImageTk.PhotoImage(img)
                else:
                    self.images[name] = None
            except Exception:
                self.images[name] = None
    def create_button(self, parent, text, icon_name, command):
        btn = Button(parent,
                     text=text,
                     image=self.images.get(icon_name),
                     compound=TOP,
                     font=self.button_font,
                     bg=BUTTON_COLOR,
                     fg=BUTTON_TEXT_COLOR,
                     activebackground=BUTTON_ACTIVE_COLOR,
                     activeforeground=BUTTON_TEXT_COLOR,
                     relief=FLAT,
                     bd=0,
                     command=command)
        return btn
    def placeholder(self, name):
        messagebox.showinfo("Заглушка", f"Кнопка: {name}\nЛогика будет добавлена позже")
    def create_main_interface(self):
        main_frame = Frame(self.win, bg=BG_COLOR)
        main_frame.pack(fill=BOTH, expand=True, padx=80, pady=50)
        title = Label(main_frame,
                      text="SATELLITE",
                      font=self.title_font,
                      fg=TITLE_COLOR,
                      bg=BG_COLOR)
        title.pack(pady=(40, 60))
        buttons_frame = Frame(main_frame, bg=BG_COLOR)
        buttons_frame.pack(expand=True, fill=BOTH)
        buttons_frame.grid_columnconfigure(0, weight=1, uniform="col")
        buttons_frame.grid_columnconfigure(1, weight=1, uniform="col")
        buttons_frame.grid_rowconfigure(0, weight=1, uniform="row")
        buttons_frame.grid_rowconfigure(1, weight=1, uniform="row")
        btn1 = self.create_button(buttons_frame, "ПРОВЕРИТЬ ФАЙЛ", "filee",lambda: CombineAntivirus.open_antivirus(self.win, self.restore_main_interface))
        btn2 = self.create_button(buttons_frame, "БЕЗВОЗВРАТНОЕ УДАЛЕНИЕ", "rubish", lambda: secure_delete.secure_delete_file())
        btn3 = self.create_button(buttons_frame, "Мониторинг директорий".upper(), "sand",
                                  lambda: watcher.open_file_monitor(self.win, self.restore_main_interface))
        btn4 = self.create_button(buttons_frame, "ШИФРОВАНИЕ/ДЕШИФРОВАНИЕ ФАЙЛОВ\nС ПОМОЩЬЮ ФЛЕШКИ", "flash",
                                  lambda: flash_encryption.show_encryption_interface(self.win, self.restore_main_interface))
        btn1.grid(row=0, column=0, padx=25, pady=25, sticky="nsew")
        btn2.grid(row=0, column=1, padx=25, pady=25, sticky="nsew")
        btn3.grid(row=1, column=0, padx=25, pady=25, sticky="nsew")
        btn4.grid(row=1, column=1, padx=25, pady=25, sticky="nsew")
    def run(self):
        self.win.mainloop()
def require_admin():
    try:
        if ctypes.windll.shell32.IsUserAnAdmin():
            return True
        else:
            ctypes.windll.shell32.ShellExecuteW(None, "runas", sys.executable, " ".join(sys.argv), None, None, 1)
            return False
    except Exception:
        return True
if require_admin():
    app = SatelliteApp()
    app.run()
else:
    sys.exit()