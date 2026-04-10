import os
import time
import queue
from tkinter import *
from tkinter import font as tkfont
from tkinter import filedialog, messagebox
import psutil
from watchdog.observers import Observer
from watchdog.events import FileSystemEventHandler
from datetime import datetime
BG_COLOR = "#1a1a1a"
BG_SECONDARY = "#2a2a2a"
BUTTON_COLOR = "#2a2a2a"
BUTTON_ACTIVE_COLOR = "#3a3a3a"
TEXT_COLOR = "#e0e0e0"
TITLE_COLOR = "#3a6ea5"
WARNING_COLOR = "#ff4444"
SUCCESS_COLOR = "#44ff44"
BUTTON_TEXT_COLOR = "#2a4a7a"
FONT_FAMILY = "Segoe UI"
DEFAULT_FOLDERS = [
    os.path.expanduser("~\\Documents"),
    os.path.expanduser("~\\Desktop"),
    os.path.expanduser("~\\Downloads"),
]
EXCLUDED_PATTERNS = [
    "*.tmp", "*.temp", "*.log", "*.cache", "*.crdownload",
    "~*", "Thumbs.db", "desktop.ini"
]
EXCLUDED_DIRS = [
    "cache", "temp", "tmp", "logs", ".git", "__pycache__"
]
class FileChangeHandler(FileSystemEventHandler):
    def __init__(self, log_queue):
        super().__init__()
        self.log_queue = log_queue
    def should_ignore(self, path):
        path_lower = path.lower()
        for pattern in EXCLUDED_PATTERNS:
            if pattern.startswith('*'):
                if path_lower.endswith(pattern[1:]):
                    return True
            elif pattern.startswith('~'):
                if os.path.basename(path).startswith('~'):
                    return True
        for dir_name in EXCLUDED_DIRS:
            if f"\\{dir_name}\\" in f"\\{path_lower}\\" or path_lower.startswith(dir_name):
                return True
        return False
    def get_file_size(self, path):
        try:
            if os.path.exists(path):
                size = os.path.getsize(path)
                if size < 1024:
                    return f"{size} B"
                elif size < 1024 * 1024:
                    return f"{size / 1024:.2f} KB"
                else:
                    return f"{size / (1024 * 1024):.2f} MB"
        except:
            pass
        return "Неизвестно"
    def get_process_name(self, path):
        try:
            time.sleep(0.05)
            for proc in psutil.process_iter(['pid', 'name']):
                try:
                    for file in proc.open_files():
                        if file.path == path:
                            return proc.info['name']
                except (psutil.NoSuchProcess, psutil.AccessDenied):
                    continue
        except:
            pass
        return "неизвестно"
    def process(self, event):
        if event.is_directory or self.should_ignore(event.src_path):
            return
        timestamp = datetime.now().strftime('%H:%M:%S')
        filename = os.path.basename(event.src_path)
        file_size = self.get_file_size(event.src_path)
        process_name = ""
        if event.event_type == 'created':
            action = "СОЗДАН"
            color = "#44ff44"
            process_name = self.get_process_name(event.src_path)
        elif event.event_type == 'modified':
            action = "ИЗМЕНЕН"
            color = "#ffaa00"
            process_name = self.get_process_name(event.src_path)
        elif event.event_type == 'deleted':
            action = "УДАЛЕН"
            color = "#ff4444"
            process_name = "N/A"
        elif event.event_type == 'moved':
            action = "ПЕРЕМЕЩЕН"
            color = "#aa66ff"
            process_name = self.get_process_name(event.dest_path) if hasattr(event, 'dest_path') else "N/A"
        else:
            return
        log_entry = f"[{timestamp}] {action}: {filename} ({file_size}) | Процесс: {process_name}"
        self.log_queue.put((log_entry, color))
    def on_created(self, event):
        self.process(event)
    def on_modified(self, event):
        self.process(event)
    def on_deleted(self, event):
        self.process(event)
    def on_moved(self, event):
        self.process(event)
class FileMonitorFrame(Frame):
    def __init__(self, parent, on_back):
        super().__init__(parent, bg=BG_COLOR)
        self.on_back = on_back
        self.observer = None
        self.is_monitoring = False
        self.event_queue = queue.Queue()
        self.watched_folders = []
        self.setup_fonts()
        self.create_interface()
        self.add_default_folders()
    def setup_fonts(self):
        try:
            self.title_font = tkfont.Font(family=FONT_FAMILY, size=72, weight="bold")
            self.button_font = tkfont.Font(family=FONT_FAMILY, size=16, weight="bold")
            self.status_font = tkfont.Font(family=FONT_FAMILY, size=14, weight="bold")
            self.list_font = tkfont.Font(family=FONT_FAMILY, size=11)
        except:
            self.title_font = tkfont.Font(size=72, weight="bold")
            self.button_font = tkfont.Font(size=16, weight="bold")
            self.status_font = tkfont.Font(size=14, weight="bold")
            self.list_font = tkfont.Font(size=11)
    def create_interface(self):
        main_frame = Frame(self, bg=BG_COLOR)
        main_frame.pack(fill=BOTH, expand=True, padx=80, pady=50)
        title = Label(main_frame, text="SATELLITE", font=self.title_font, fg=TITLE_COLOR, bg=BG_COLOR)
        title.pack(pady=(40, 20))
        status_label = Label(main_frame, text="МОНИТОРИНГ ФАЙЛОВОЙ СИСТЕМЫ", font=self.status_font, fg=SUCCESS_COLOR,
                             bg=BG_COLOR)
        status_label.pack(pady=(0, 20))
        control_frame = Frame(main_frame, bg=BG_COLOR)
        control_frame.pack(fill=X, pady=(0, 10))
        listbox_frame = Frame(control_frame, bg=BG_SECONDARY)
        listbox_frame.pack(side=LEFT, fill=BOTH, expand=True, padx=(0, 10))
        scrollbar_list = Scrollbar(listbox_frame)
        scrollbar_list.pack(side=RIGHT, fill=Y)
        self.folder_listbox = Listbox(listbox_frame, font=self.list_font, bg=BG_SECONDARY, fg=TEXT_COLOR,
                                      selectbackground=TITLE_COLOR, selectforeground=TEXT_COLOR,
                                      yscrollcommand=scrollbar_list.set, relief=FLAT, bd=0, height=5)
        self.folder_listbox.pack(side=LEFT, fill=BOTH, expand=True)
        scrollbar_list.config(command=self.folder_listbox.yview)
        btn_panel = Frame(control_frame, bg=BG_COLOR)
        btn_panel.pack(side=RIGHT, fill=Y)
        add_btn = Button(btn_panel, text="ДОБАВИТЬ", font=self.button_font,
                         bg=BUTTON_COLOR, fg=BUTTON_TEXT_COLOR,
                         activebackground=BUTTON_ACTIVE_COLOR,
                         activeforeground=BUTTON_TEXT_COLOR,
                         relief=FLAT, bd=0, padx=15, pady=5,
                         command=self.add_folder)
        add_btn.pack(fill=X, pady=2)
        remove_btn = Button(btn_panel, text="УДАЛИТЬ", font=self.button_font,
                            bg=BUTTON_COLOR, fg=BUTTON_TEXT_COLOR,
                            activebackground=BUTTON_ACTIVE_COLOR,
                            activeforeground=BUTTON_TEXT_COLOR,
                            relief=FLAT, bd=0, padx=15, pady=5,
                            command=self.remove_selected_folder)
        remove_btn.pack(fill=X, pady=2)
        default_btn = Button(btn_panel, text="СТАНДАРТНЫЕ", font=self.button_font,
                             bg=BUTTON_COLOR, fg=BUTTON_TEXT_COLOR,
                             activebackground=BUTTON_ACTIVE_COLOR,
                             activeforeground=BUTTON_TEXT_COLOR,
                             relief=FLAT, bd=0, padx=15, pady=5,
                             command=self.add_default_folders)
        default_btn.pack(fill=X, pady=2)
        apply_btn = Button(btn_panel, text="ПРИМЕНИТЬ", font=self.button_font,
                           bg=BUTTON_COLOR, fg=BUTTON_TEXT_COLOR,
                           activebackground=BUTTON_ACTIVE_COLOR,
                           activeforeground=BUTTON_TEXT_COLOR,
                           relief=FLAT, bd=0, padx=15, pady=5,
                           command=self.apply_changes)
        apply_btn.pack(fill=X, pady=2)
        back_btn = Button(btn_panel, text="ВЕРНУТЬСЯ", font=self.button_font,
                          bg=BUTTON_COLOR, fg=BUTTON_TEXT_COLOR,
                          activebackground=BUTTON_ACTIVE_COLOR,
                          activeforeground=BUTTON_TEXT_COLOR,
                          relief=FLAT, bd=0, padx=15, pady=5,
                          command=self.cleanup_and_back)
        back_btn.pack(fill=X, pady=2)
        log_container = Frame(main_frame, bg=BG_COLOR, height=300)
        log_container.pack(fill=BOTH, pady=(0, 20))
        log_container.pack_propagate(False)
        self.log_frame = Frame(log_container, bg=BG_SECONDARY)
        self.log_frame.pack(fill=BOTH, expand=True)
        scrollbar_log = Scrollbar(self.log_frame)
        scrollbar_log.pack(side=RIGHT, fill=Y)
        self.log_text = Text(self.log_frame, font=("Consolas", 11), bg=BG_SECONDARY, fg=TEXT_COLOR,
                             yscrollcommand=scrollbar_log.set, wrap=WORD, relief=FLAT, bd=0,
                             state='disabled')
        self.log_text.pack(side=LEFT, fill=BOTH, expand=True)
        scrollbar_log.config(command=self.log_text.yview)
        btn_frame = Frame(main_frame, bg=BG_COLOR)
        btn_frame.pack(fill=X, pady=(10, 0))
        btn_frame.grid_columnconfigure(0, weight=1)
        btn_frame.grid_columnconfigure(1, weight=1)
        self.toggle_btn = Button(btn_frame, text="ЗАПУСТИТЬ", font=self.button_font,
                                 bg=BUTTON_COLOR, fg=BUTTON_TEXT_COLOR,
                                 activebackground=BUTTON_ACTIVE_COLOR,
                                 activeforeground=BUTTON_TEXT_COLOR,
                                 relief=FLAT, bd=0, padx=30, pady=10,
                                 command=self.toggle_monitoring)
        self.toggle_btn.grid(row=0, column=0, padx=10, sticky="ew")
        self.clear_btn = Button(btn_frame, text="ОЧИСТИТЬ ЛОГ", font=self.button_font,
                                bg=BUTTON_COLOR, fg=BUTTON_TEXT_COLOR,
                                activebackground=BUTTON_ACTIVE_COLOR,
                                activeforeground=BUTTON_TEXT_COLOR,
                                relief=FLAT, bd=0, padx=30, pady=10,
                                command=self.clear_log)
        self.clear_btn.grid(row=0, column=1, padx=10, sticky="ew")
    def add_folder(self):
        folder = filedialog.askdirectory(title="Выберите папку для мониторинга")
        if folder:
            normalized = os.path.normpath(folder)
            if normalized not in self.watched_folders:
                self.watched_folders.append(normalized)
                self.folder_listbox.insert(END, normalized)
    def remove_selected_folder(self):
        selection = self.folder_listbox.curselection()
        if selection:
            index = selection[0]
            folder = self.folder_listbox.get(index)
            self.watched_folders.remove(folder)
            self.folder_listbox.delete(index)
    def add_default_folders(self):
        added = False
        for folder in DEFAULT_FOLDERS:
            normalized = os.path.normpath(folder)
            if os.path.exists(normalized) and normalized not in self.watched_folders:
                self.watched_folders.append(normalized)
                self.folder_listbox.insert(END, normalized)
                added = True
        if not added:
            messagebox.showinfo("Информация", "Стандартные папки уже в списке или не существуют.")
        return added
    def apply_changes(self):
        if self.is_monitoring:
            self.stop_monitoring()
        self.log_event("Применение изменений и запуск мониторинга...", TITLE_COLOR)
        self.start_monitoring()
    def start_monitoring(self):
        if self.is_monitoring:
            return
        if not self.watched_folders:
            self.log_event("Нет папок для мониторинга. Добавьте хотя бы одну.", WARNING_COLOR)
            return
        self.is_monitoring = True
        self.toggle_btn.config(text="ОСТАНОВИТЬ")
        self.event_handler = FileChangeHandler(self.event_queue)
        self.observer = Observer()
        for folder in self.watched_folders:
            if os.path.exists(folder):
                try:
                    self.observer.schedule(self.event_handler, folder, recursive=True)
                    self.log_event(f"Начат мониторинг: {folder}", TITLE_COLOR)
                except Exception as e:
                    self.log_event(f"Ошибка мониторинга {folder}: {str(e)}", WARNING_COLOR)
            else:
                self.log_event(f"Папка не существует: {folder}", WARNING_COLOR)
        self.observer.start()
        self.after(100, self.process_queue)
    def stop_monitoring(self):
        if self.observer:
            self.observer.stop()
            self.observer.join()
            self.observer = None
        self.is_monitoring = False
        self.toggle_btn.config(text="ЗАПУСТИТЬ")
        self.log_event("Мониторинг остановлен", TITLE_COLOR)
    def toggle_monitoring(self):
        if self.is_monitoring:
            self.stop_monitoring()
        else:
            self.start_monitoring()
    def process_queue(self):
        try:
            while True:
                entry, color = self.event_queue.get_nowait()
                self._insert_log(entry, color)
        except queue.Empty:
            pass
        finally:
            if self.is_monitoring:
                self.after(100, self.process_queue)
    def _insert_log(self, message, color):
        self.log_text.config(state='normal')
        self.log_text.insert(END, message + "\n")
        last_line = int(self.log_text.index('end-1c').split('.')[0])
        tag = f"tag_{last_line}"
        self.log_text.tag_config(tag, foreground=color)
        self.log_text.tag_add(tag, f"{last_line}.0", f"{last_line}.end")
        self.log_text.see(END)
        self.log_text.config(state='disabled')
    def log_event(self, message, color):
        self._insert_log(message, color)
    def clear_log(self):
        self.log_text.config(state='normal')
        self.log_text.delete(1.0, END)
        self.log_text.config(state='disabled')
    def cleanup_and_back(self):
        self.stop_monitoring()
        self.destroy()
        self.on_back()
def open_file_monitor(parent, on_back):
    for widget in parent.winfo_children():
        widget.destroy()
    frame = FileMonitorFrame(parent, on_back)
    frame.pack(fill="both", expand=True)