import os
import ctypes
import base64
import threading
import time
from tkinter import filedialog, ttk, Label, Button, Frame
from tkinter import font as tkfont
from cryptography.hazmat.primitives.ciphers.aead import AESGCM
import wmi
import pythoncom
from secure_delete import secure_delete_file
BG_COLOR = "#1a1a1a"
BG_SECONDARY = "#2a2a2a"
BUTTON_COLOR = "#2a2a2a"
BUTTON_ACTIVE_COLOR = "#3a3a3a"
TEXT_COLOR = "#e0e0e0"
TITLE_COLOR = "#3a6ea5"
BUTTON_TEXT_COLOR = "#2a4a7a"
FONT_FAMILY = "Segoe UI"
SYSTEM_KEY_DIR = "C:/satellite"
FLASH_HIDDEN_FOLDER = "System Volume Information"
KEY_FILENAME = "master.stllite"
CHUNK_SIZE = 64 * 1024
def hide_folder(folder_path):
    try:
        ctypes.windll.kernel32.SetFileAttributesW(folder_path, 0x02)
    except:
        pass
    try:
        os.system(f'attrib +h +s "{folder_path}"')
    except:
        pass
def create_hidden_folder(folder_path):
    if not os.path.exists(folder_path):
        os.makedirs(folder_path, exist_ok=True)
        hide_folder(folder_path)
    return os.path.exists(folder_path)
class USBDetector:
    def __init__(self):
        self.detected_drive = None
        self.stop_event = threading.Event()
        self.listening = False
    def wait_for_usb(self, timeout=120):
        self.detected_drive = None
        self.listening = True
        self.stop_event.clear()
        result = None
        def listen_thread():
            nonlocal result
            pythoncom.CoInitialize()
            try:
                c = wmi.WMI()
                start_time = time.time()
                while self.listening and not self.stop_event.is_set():
                    if timeout and (time.time() - start_time) > timeout:
                        break
                    disks = c.Win32_LogicalDisk(DriveType=2)
                    for disk in disks:
                        result = disk.DeviceID
                        self.listening = False
                        return
                    time.sleep(1)
            finally:
                pythoncom.CoUninitialize()
        thread = threading.Thread(target=listen_thread, daemon=True)
        thread.start()
        while self.listening and not self.stop_event.is_set() and result is None:
            time.sleep(0.5)
        self.listening = False
        return result
class FlashEncryption:
    def __init__(self):
        self.system_key_path = os.path.join(SYSTEM_KEY_DIR, KEY_FILENAME)
        self.flash_drive = None
        self.master_key = None
    def _ensure_system_folder(self):
        if not os.path.exists(SYSTEM_KEY_DIR):
            try:
                os.makedirs(SYSTEM_KEY_DIR, exist_ok=True)
                hide_folder(SYSTEM_KEY_DIR)
            except:
                pass
    def _generate_master_key(self):
        return os.urandom(32)
    def _split_key(self, full_key):
        part1 = base64.urlsafe_b64encode(full_key[:20]).decode()
        part2 = base64.urlsafe_b64encode(full_key[20:]).decode()
        return part1, part2
    def _join_key(self, part1, part2):
        return base64.urlsafe_b64decode(part1) + base64.urlsafe_b64decode(part2)
    def _save_key_to_flash(self, flash_drive, key_part):
        flash_hidden_path = os.path.join(flash_drive, FLASH_HIDDEN_FOLDER)
        create_hidden_folder(flash_hidden_path)
        key_file_path = os.path.join(flash_hidden_path, KEY_FILENAME)
        with open(key_file_path, 'w') as f:
            f.write(key_part)
        hide_folder(key_file_path)
        return True
    def _read_key_from_flash(self, flash_drive):
        flash_hidden_path = os.path.join(flash_drive, FLASH_HIDDEN_FOLDER)
        key_file_path = os.path.join(flash_hidden_path, KEY_FILENAME)
        if os.path.exists(key_file_path):
            with open(key_file_path, 'r') as f:
                return f.read().strip()
        return None
    def _save_key_to_system(self, key_part):
        self._ensure_system_folder()
        with open(self.system_key_path, 'w') as f:
            f.write(key_part)
        hide_folder(self.system_key_path)
        return True
    def _read_key_from_system(self):
        if os.path.exists(self.system_key_path):
            with open(self.system_key_path, 'r') as f:
                return f.read().strip()
        return None
    def check_key_integrity(self):
        system_part = self._read_key_from_system()
        if system_part is None:
            return "missing_system", "Системная половина ключа отсутствует"
        if len(system_part.strip()) < 10:
            return "corrupted_system", "Системная половина ключа повреждена"
        return "ok", None
    def check_flash_key_integrity(self, flash_drive):
        flash_part = self._read_key_from_flash(flash_drive)
        if flash_part is None:
            return "missing_flash", "На флешке отсутствует половина ключа"
        if len(flash_part.strip()) < 10:
            return "corrupted_flash", "Половина ключа на флешке повреждена"
        return "ok", None
    def initialize_key(self):
        system_part = self._read_key_from_system()
        if system_part is None:
            full_key = self._generate_master_key()
            flash_part, system_part = self._split_key(full_key)
            self._save_key_to_system(system_part)
            detector = USBDetector()
            flash_drive = detector.wait_for_usb(120)
            if flash_drive is None:
                if os.path.exists(self.system_key_path):
                    os.remove(self.system_key_path)
                return False, "Флешка не обнаружена. Инициализация отменена."
            self._save_key_to_flash(flash_drive, flash_part)
            self.flash_drive = flash_drive
            self.master_key = full_key
            return True, "Ключ успешно создан. Флешка готова к использованию."
        return True, "Ключ уже существует"
    def has_key(self):
        return os.path.exists(self.system_key_path)
    def load_key_from_flash(self):
        system_part = self._read_key_from_system()
        if system_part is None:
            return False, "Системная половина ключа не найдена"
        detector = USBDetector()
        flash_drive = detector.wait_for_usb(120)
        if flash_drive is None:
            return False, "Флешка не обнаружена"
        flash_part = self._read_key_from_flash(flash_drive)
        if flash_part is None:
            return False, "На флешке не найдена половина ключа. Возможно, это не та флешка."
        self.master_key = self._join_key(flash_part, system_part)
        self.flash_drive = flash_drive
        return True, "Ключ успешно загружен"
    def ensure_valid_key(self):
        system_status, system_msg = self.check_key_integrity()
        if system_status != "ok":
            return False, system_msg
        detector = USBDetector()
        flash_drive = detector.wait_for_usb(120)
        if flash_drive is None:
            return False, "Флешка не обнаружена"
        flash_status, flash_msg = self.check_flash_key_integrity(flash_drive)
        if flash_status != "ok":
            return False, flash_msg
        self.flash_drive = flash_drive
        flash_part = self._read_key_from_flash(flash_drive)
        system_part = self._read_key_from_system()
        self.master_key = self._join_key(flash_part, system_part)
        return True, "Ключ успешно загружен"
    def encrypt_file(self, file_path, progress_callback=None):
        if self.master_key is None:
            return False, "Ключ не загружен."
        if not os.path.exists(file_path):
            return False, "Файл не существует"
        encrypted_path = file_path + ".satellite"
        try:
            nonce = os.urandom(12)
            file_size = os.path.getsize(file_path)
            processed = 0
            aesgcm = AESGCM(self.master_key)
            with open(file_path, 'rb') as fin:
                with open(encrypted_path, 'wb') as fout:
                    fout.write(nonce)
                    while True:
                        chunk = fin.read(CHUNK_SIZE)
                        if not chunk:
                            break
                        encrypted_chunk = aesgcm.encrypt(nonce, chunk, None)
                        fout.write(encrypted_chunk)
                        processed += len(chunk)
                        if progress_callback:
                            progress_callback(processed, file_size)
            secure_delete_file(file_path, show_dialog=False)
            return True, f"Файл зашифрован: {encrypted_path}"
        except Exception as e:
            if os.path.exists(encrypted_path):
                os.remove(encrypted_path)
            return False, f"Ошибка шифрования: {str(e)}"
    def decrypt_file(self, file_path, progress_callback=None):
        if self.master_key is None:
            return False, "Ключ не загружен."
        if not file_path.endswith('.satellite'):
            return False, "Файл не имеет расширения .satellite"
        original_path = file_path[:-10]
        try:
            with open(file_path, 'rb') as fin:
                nonce = fin.read(12)
                if len(nonce) != 12:
                    return False, "Неверный формат зашифрованного файла"
                file_size = os.path.getsize(file_path) - 12
                processed = 0
                aesgcm = AESGCM(self.master_key)
                with open(original_path, 'wb') as fout:
                    while True:
                        encrypted_chunk = fin.read(CHUNK_SIZE + 16)
                        if not encrypted_chunk:
                            break
                        decrypted_chunk = aesgcm.decrypt(nonce, encrypted_chunk, None)
                        fout.write(decrypted_chunk)
                        processed += len(encrypted_chunk)
                        if progress_callback:
                            progress_callback(processed, file_size)
            secure_delete_file(file_path, show_dialog=False)
            return True, f"Файл расшифрован: {original_path}"
        except Exception as e:
            return False, f"Ошибка дешифрования: {str(e)}.\nВозможно, вставлена не та флешка."
class EncryptionFrame(Frame):
    def __init__(self, parent, on_back):
        super().__init__(parent, bg=BG_COLOR)
        self.on_back = on_back
        self.encryption = FlashEncryption()
        self.setup_fonts()
        self.create_interface()
    def setup_fonts(self):
        try:
            self.title_font = tkfont.Font(family=FONT_FAMILY, size=72, weight="bold")
            self.button_font = tkfont.Font(family=FONT_FAMILY, size=16, weight="bold")
            self.text_font = tkfont.Font(family=FONT_FAMILY, size=24, weight="bold")
            self.result_font = tkfont.Font(family=FONT_FAMILY, size=28, weight="bold")
            self.status_font = tkfont.Font(family=FONT_FAMILY, size=28, weight="bold")
            self.progress_font = tkfont.Font(family=FONT_FAMILY, size=28, weight="bold")
        except:
            self.title_font = tkfont.Font(size=72, weight="bold")
            self.button_font = tkfont.Font(size=16, weight="bold")
            self.text_font = tkfont.Font(size=24, weight="bold")
            self.result_font = tkfont.Font(size=28, weight="bold")
            self.status_font = tkfont.Font(size=12)
            self.progress_font = tkfont.Font(size=10)
    def create_interface(self):
        self.main_frame = Frame(self, bg=BG_COLOR)
        self.main_frame.pack(fill="both", expand=True, padx=80, pady=50)
        title = Label(self.main_frame, text="SATELLITE", font=self.title_font, fg=TITLE_COLOR, bg=BG_COLOR)
        title.pack(pady=(40, 60))
        self.content_frame = Frame(self.main_frame, bg=BG_COLOR)
        self.content_frame.pack(expand=True, fill="both")
        self.show_main_buttons()
    def show_main_buttons(self):
        for widget in self.content_frame.winfo_children():
            widget.destroy()
        btn_frame = Frame(self.content_frame, bg=BG_COLOR)
        btn_frame.pack(expand=True, fill="both")
        btn_frame.grid_columnconfigure(0, weight=1)
        btn_frame.grid_columnconfigure(1, weight=1)
        btn_frame.grid_rowconfigure(0, weight=1)
        encrypt_btn = Button(btn_frame, text="ШИФРОВАНИЕ ФАЙЛА", font=self.button_font,
                             bg=BUTTON_COLOR, fg=BUTTON_TEXT_COLOR,
                             activebackground=BUTTON_ACTIVE_COLOR,
                             activeforeground=BUTTON_TEXT_COLOR,
                             relief="flat", bd=0, padx=40, pady=30,
                             command=self.encrypt_file)
        encrypt_btn.grid(row=0, column=0, padx=50, pady=50, sticky="nsew")
        decrypt_btn = Button(btn_frame, text="ДЕШИФРОВАНИЕ ФАЙЛА", font=self.button_font,
                             bg=BUTTON_COLOR, fg=BUTTON_TEXT_COLOR,
                             activebackground=BUTTON_ACTIVE_COLOR,
                             activeforeground=BUTTON_TEXT_COLOR,
                             relief="flat", bd=0, padx=40, pady=30,
                             command=self.decrypt_file)
        decrypt_btn.grid(row=0, column=1, padx=50, pady=50, sticky="nsew")
        back_btn = Button(self.content_frame, text="← ВЕРНУТЬСЯ", font=self.button_font,
                          bg=BUTTON_COLOR, fg=BUTTON_TEXT_COLOR,
                          activebackground=BUTTON_ACTIVE_COLOR,
                          activeforeground=BUTTON_TEXT_COLOR,
                          relief="flat", bd=0, padx=20, pady=10,
                          command=self.on_back)
        back_btn.pack(side="bottom", pady=20)
    def show_progress(self, title_text):
        for widget in self.content_frame.winfo_children():
            widget.destroy()
        self.status_label = Label(self.content_frame, text=title_text, font=self.status_font, fg=TEXT_COLOR,
                                  bg=BG_COLOR)
        self.status_label.pack(pady=30)
        self.progress_bar = ttk.Progressbar(self.content_frame, length=400, mode='determinate')
        self.progress_info = Label(self.content_frame, text="", font=self.progress_font, fg=TEXT_COLOR, bg=BG_COLOR)
    def update_progress(self, current, total):
        if total > 0:
            percent = int((current / total) * 100)
            self.progress_bar['value'] = percent
            self.progress_info.config(text=f"Обработано: {current // 1024} КБ из {total // 1024} КБ ({percent}%)")
            self.update_idletasks()
    def update_status(self, text):
        self.status_label.config(text=text)
        self.update_idletasks()
    def show_message(self, title, msg, is_error=False):
        for widget in self.content_frame.winfo_children():
            widget.destroy()
        color = "#ff4444" if is_error else "#44ff44"
        result_label = Label(self.content_frame, text=title, font=self.result_font, fg=color, bg=BG_COLOR)
        result_label.pack(pady=30)
        msg_label = Label(self.content_frame, text=msg, font=self.text_font, fg=TEXT_COLOR, bg=BG_COLOR, wraplength=600)
        msg_label.pack(pady=20)
        ok_btn = Button(self.content_frame, text="OK", font=self.button_font,
                        bg=BUTTON_COLOR, fg=BUTTON_TEXT_COLOR,
                        activebackground=BUTTON_ACTIVE_COLOR,
                        activeforeground=BUTTON_TEXT_COLOR,
                        relief="flat", bd=0, padx=30, pady=10,
                        command=self.show_main_buttons)
        ok_btn.pack(pady=20)
    def encrypt_file(self):
        file_path = filedialog.askopenfilename(title="Выберите файл для шифрования", parent=self)
        if not file_path:
            return
        self.start_encryption(file_path)
    def decrypt_file(self):
        file_path = filedialog.askopenfilename(title="Выберите файл для дешифрования",
                                               filetypes=[("Satellite files", "*.satellite")], parent=self)
        if not file_path:
            return
        self.start_decryption(file_path)
    def start_encryption(self, file_path):
        self.show_progress("ПРОВЕРКА КЛЮЧА, ВСТАВЬТЕ ФЛЕШКУ...")
        def process():
            success, msg = self.encryption.ensure_valid_key()
            if not success:
                self.after(0, lambda: self.show_message("ОШИБКА", msg, True))
                return
            self.after(0, lambda: self.update_status("ШИФРОВАНИЕ..."))
            self.after(0, lambda: self.progress_bar.pack(pady=10))
            self.after(0, lambda: self.progress_info.pack())
            success, msg = self.encryption.encrypt_file(file_path, self.update_progress)
            if success:
                self.after(0, lambda: self.show_message("УСПЕХ", msg, False))
            else:
                self.after(0, lambda: self.show_message("ОШИБКА", msg, True))
        threading.Thread(target=process, daemon=True).start()
    def start_decryption(self, file_path):
        self.show_progress("ЗАГРУЗКА КЛЮЧА, ВСТАВЬТЕ ФЛЕШКУ...")
        def process():
            if not self.encryption.has_key():
                self.after(0, lambda: self.show_message("ОШИБКА", "Ключ не инициализирован.", True))
                return
            success, msg = self.encryption.load_key_from_flash()
            if not success:
                self.after(0, lambda: self.show_message("ОШИБКА", msg, True))
                return
            self.after(0, lambda: self.update_status("ДЕШИФРОВАНИЕ..."))
            self.after(0, lambda: self.progress_bar.pack(pady=10))
            self.after(0, lambda: self.progress_info.pack())
            success, msg = self.encryption.decrypt_file(file_path, self.update_progress)
            if success:
                self.after(0, lambda: self.show_message("УСПЕХ", msg, False))
            else:
                self.after(0, lambda: self.show_message("ОШИБКА", msg, True))
        threading.Thread(target=process, daemon=True).start()
def show_encryption_interface(parent, on_back):
    for widget in parent.winfo_children():
        widget.destroy()
    frame = EncryptionFrame(parent, on_back)
    frame.pack(fill="both", expand=True)