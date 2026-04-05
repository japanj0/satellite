import sys
import os
import hashlib
import threading
from tkinter import *
from tkinter import font as tkfont
from tkinter import filedialog, messagebox
import pefile
import yara
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
class HashScanner:
    def __init__(self):
        self.malware_hashes = set()
        self.load_hashes()
    def load_hashes(self):
        hash_file = resource_path('malware_hashes.txt')
        if os.path.exists(hash_file):
            try:
                with open(hash_file, 'r', encoding='utf-8', errors='ignore') as f:
                    for line in f:
                        line = line.strip()
                        if not line:
                            continue
                        if ';' in line:
                            hash_value = line.split(';')[0].strip()
                        else:
                            hash_value = line
                        if len(hash_value) == 64:
                            self.malware_hashes.add(hash_value.lower())
            except:
                pass
    def get_sha256(self, file_path):
        sha256 = hashlib.sha256()
        with open(file_path, 'rb') as f:
            for chunk in iter(lambda: f.read(8192), b''):
                sha256.update(chunk)
        return sha256.hexdigest()
    def scan(self, file_path):
        file_hash = self.get_sha256(file_path)
        return file_hash in self.malware_hashes
class PeScanner:
    def scan(self, file_path):
        if not file_path.lower().endswith(('.exe', '.dll', '.sys', '.ocx')):
            return False
        try:
            pe = pefile.PE(file_path)
            suspicious_sections = {'.aspack', '.themida', '.upx', '.enigma', '.yoda', '.mpress'}
            for section in pe.sections:
                name = section.Name.decode('utf-8', errors='ignore').rstrip('\x00')
                if name.lower() in suspicious_sections:
                    return True
            if hasattr(pe, 'DIRECTORY_ENTRY_IMPORT'):
                suspicious_imports = {'VirtualAllocEx', 'WriteProcessMemory', 'CreateRemoteThread', 'SetWindowsHookEx'}
                for entry in pe.DIRECTORY_ENTRY_IMPORT:
                    for imp in entry.imports:
                        if imp.name and imp.name.decode('utf-8', errors='ignore') in suspicious_imports:
                            return True
            return False
        except:
            return False
class YaraScanner:
    def __init__(self):
        self.rules = None
        self.compile_rules()
    def compile_rules(self):
        rules_dir = resource_path('yara_rules')
        if not os.path.isdir(rules_dir):
            return False
        filepaths = {}
        for root, dirs, files in os.walk(rules_dir):
            for file in files:
                if file.endswith('.yar'):
                    full_path = os.path.join(root, file)
                    namespace = os.path.relpath(full_path, rules_dir).replace(os.sep, '_')
                    filepaths[namespace] = full_path
        if not filepaths:
            return False
        try:
            self.rules = yara.compile(filepaths=filepaths)
            return True
        except Exception:
            return False
    def scan(self, file_path):
        if self.rules is None:
            return False
        try:
            matches = self.rules.match(filepath=file_path)
            return len(matches) > 0
        except Exception:
            return False
class AntivirusScanner:
    def __init__(self):
        self.hash_scanner = HashScanner()
        self.pe_scanner = PeScanner()
        self.yara_scanner = YaraScanner()
    def scan(self, file_path):
        results = []
        if self.hash_scanner.scan(file_path):
            results.append('Вирусная База Данных')
        if self.pe_scanner.scan(file_path):
            results.append('PE-структура')
        if self.yara_scanner.scan(file_path):
            results.append('YARA-правила')
        return {
            'is_malicious': len(results) >= 1,
            'detected_count': len(results),
            'total_checks': 3,
            'detected_methods': results
        }
class AntivirusWindow:
    def __init__(self, parent=None):
        self.parent = parent
        if parent is None:
            self.root = Tk()
            self.win = self.root
        else:
            self.win = Toplevel(parent)
        self.win.title("satellite - Антивирус")
        self.win.configure(bg=BG_COLOR)
        self.win.attributes('-fullscreen', True)
        self.setup_fonts()
        self.create_interface()
        self.scanner = None
        self.selected_file = None
        self.scan_result = None
    def setup_fonts(self):
        try:
            self.title_font = tkfont.Font(family=FONT_FAMILY, size=72, weight="bold")
            self.button_font = tkfont.Font(family=FONT_FAMILY, size=16, weight="bold")
            self.text_font = tkfont.Font(family=FONT_FAMILY, size=24, weight="bold")
            self.result_font = tkfont.Font(family=FONT_FAMILY, size=28, weight="bold")
        except:
            self.title_font = tkfont.Font(size=72, weight="bold")
            self.button_font = tkfont.Font(size=16, weight="bold")
            self.text_font = tkfont.Font(size=24, weight="bold")
            self.result_font = tkfont.Font(size=28, weight="bold")
    def create_interface(self):
        main_frame = Frame(self.win, bg=BG_COLOR)
        main_frame.pack(fill=BOTH, expand=True, padx=80, pady=50)
        title_frame = Frame(main_frame, bg=BG_COLOR)
        title_frame.pack(pady=(40, 60))
        title_frame.pack_propagate(False)
        title_frame.config(width=600, height=100)
        glow_label1 = Label(title_frame, text="SATELLITE", font=self.title_font, fg="#1a4a7a", bg=BG_COLOR)
        glow_label1.place(relx=0.5, rely=0.5, anchor="center", x=10, y=10)
        glow_label2 = Label(title_frame, text="SATELLITE", font=self.title_font, fg="#2a5a8a", bg=BG_COLOR)
        glow_label2.place(relx=0.5, rely=0.5, anchor="center", x=6, y=6)
        glow_label3 = Label(title_frame, text="SATELLITE", font=self.title_font, fg="#3a6ea5", bg=BG_COLOR)
        glow_label3.place(relx=0.5, rely=0.5, anchor="center", x=3, y=3)
        title = Label(title_frame, text="SATELLITE", font=self.title_font, fg=TITLE_COLOR, bg=BG_COLOR)
        title.place(relx=0.5, rely=0.5, anchor="center")
        self.content_frame = Frame(main_frame, bg=BG_COLOR)
        self.content_frame.pack(expand=True, fill=BOTH)
        bottom_frame = Frame(main_frame, bg=BG_COLOR, height=60)
        bottom_frame.pack(side=BOTTOM, fill=X)
        bottom_frame.pack_propagate(False)
        self.back_button = Button(bottom_frame, text="← ВЕРНУТЬСЯ", font=self.button_font,
                                  bg=BUTTON_COLOR, fg=BUTTON_TEXT_COLOR,
                                  activebackground=BUTTON_ACTIVE_COLOR,
                                  activeforeground=BUTTON_TEXT_COLOR,
                                  relief=FLAT, bd=0, padx=20, pady=10,
                                  command=self.close_window)
        self.back_button.pack(expand=True)
        self.show_select_file()
    def clear_content(self):
        for widget in self.content_frame.winfo_children():
            widget.destroy()
    def show_select_file(self):
        self.clear_content()
        self.select_label = Label(self.content_frame, text="Выберите файл для проверки", font=self.text_font,
                                  fg=TEXT_COLOR, bg=BG_COLOR)
        self.select_label.pack(pady=50)
        self.select_button = Button(self.content_frame, text="ВЫБРАТЬ ФАЙЛ", font=self.button_font,
                                    bg=BUTTON_COLOR, fg=BUTTON_TEXT_COLOR,
                                    activebackground=BUTTON_ACTIVE_COLOR,
                                    activeforeground=BUTTON_TEXT_COLOR,
                                    relief=FLAT, bd=0, padx=40, pady=15,
                                    command=self.select_file)
        self.select_button.pack(pady=20)
        self.file_label = Label(self.content_frame, text="", font=self.button_font, fg=TITLE_COLOR, bg=BG_COLOR)
        self.file_label.pack(pady=10)
    def select_file(self):
        file_path = filedialog.askopenfilename(title="Выберите файл для проверки", parent=self.win)
        if file_path:
            self.selected_file = file_path
            self.file_label.config(text=f"Файл: {os.path.basename(file_path)}")
            self.select_button.config(state=DISABLED, text="ПРОВЕРКА...")
            self.win.update_idletasks()
            if self.scanner is None:
                self.scanner = AntivirusScanner()
            threading.Thread(target=self.run_scan, daemon=True).start()
    def run_scan(self):
        self.scan_result = self.scanner.scan(self.selected_file)
        self.win.after(0, self.show_result)
    def show_result(self):
        self.clear_content()
        file_hash = self.scanner.hash_scanner.get_sha256(self.selected_file)
        if file_hash == 'e3a733748ceb9dc57edc961d29193f06ad1fcb29e62cc2d948ab05120fb257f6':
            status_color = "#44ff44"
            status_text = "БЕЗОПАСНОЕ ПРИЛОЖЕНИЕ"
            verdict = "Файл признан безопасным (WhiteList Satellite)"
            status_label = Label(self.content_frame, text=status_text, font=self.result_font, fg=status_color,
                                 bg=BG_COLOR)
            status_label.pack(pady=30)
            verdict_label = Label(self.content_frame, text=verdict, font=self.button_font, fg=TEXT_COLOR, bg=BG_COLOR)
            verdict_label.pack(pady=15)
            scan_again_button = Button(self.content_frame, text="ПРОВЕРИТЬ ДРУГОЙ ФАЙЛ", font=self.button_font,
                                       bg=BUTTON_COLOR, fg=BUTTON_TEXT_COLOR,
                                       activebackground=BUTTON_ACTIVE_COLOR,
                                       activeforeground=BUTTON_TEXT_COLOR,
                                       relief=FLAT, bd=0, padx=40, pady=15,
                                       command=self.rescan)
            scan_again_button.pack(pady=15)
            return
        if self.scan_result['is_malicious']:
            status_color = "#ff4444"
            status_text = "ОПАСНЫЙ ФАЙЛ"
            verdict = "Файл признан вредоносным!"
        else:
            status_color = "#44ff44"
            status_text = "БЕЗОПАСНЫЙ ФАЙЛ"
            verdict = "Файл признан безопасным."
        status_label = Label(self.content_frame, text=status_text, font=self.result_font, fg=status_color, bg=BG_COLOR)
        status_label.pack(pady=20)
        verdict_label = Label(self.content_frame, text=verdict, font=self.button_font, fg=TEXT_COLOR, bg=BG_COLOR)
        verdict_label.pack(pady=10)
        if self.scan_result['detected_methods']:
            methods_text = "Обнаружено: " + ", ".join(self.scan_result['detected_methods'])
            methods_label = Label(self.content_frame, text=methods_text, font=("Segoe UI", 12), fg="#ff4444",
                                  bg=BG_COLOR)
            methods_label.pack(pady=10)
        if self.scan_result['is_malicious']:
            delete_button = Button(self.content_frame, text="БЕЗВОЗВРАТНО УДАЛИТЬ", font=self.button_font,
                                   bg="#ff4444", fg="white",
                                   activebackground="#cc0000",
                                   activeforeground="white",
                                   relief=FLAT, bd=0, padx=40, pady=15,
                                   command=self.delete_file)
            delete_button.pack(pady=20)
        scan_again_button = Button(self.content_frame, text="ПРОВЕРИТЬ ДРУГОЙ ФАЙЛ", font=self.button_font,
                                   bg=BUTTON_COLOR, fg=BUTTON_TEXT_COLOR,
                                   activebackground=BUTTON_ACTIVE_COLOR,
                                   activeforeground=BUTTON_TEXT_COLOR,
                                   relief=FLAT, bd=0, padx=40, pady=15,
                                   command=self.rescan)
        scan_again_button.pack(pady=15)
    def rescan(self):
        self.scanner = None
        self.selected_file = None
        self.scan_result = None
        self.show_select_file()
    def delete_file(self):
        try:
            if not os.path.exists(self.selected_file):
                messagebox.showerror("Ошибка", "Файл уже не существует")
                return
            file_size = os.path.getsize(self.selected_file)
            with open(self.selected_file, 'wb') as f:
                for _ in range(3):
                    f.seek(0)
                    f.write(os.urandom(file_size))
                    f.flush()
            os.remove(self.selected_file)
            messagebox.showinfo("Успех", "Файл безвозвратно удален!")
            self.rescan()
        except Exception as e:
            messagebox.showerror("Ошибка", f"Не удалось удалить файл: {str(e)}")
    def close_window(self):
        self.win.destroy()
def open_antivirus(parent=None):
    app = AntivirusWindow(parent)