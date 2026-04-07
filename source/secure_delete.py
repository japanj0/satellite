import os
from tkinter import filedialog, messagebox
def secure_delete_file(file_path=None, show_dialog=True):
    if file_path is None:
        file_path = filedialog.askopenfilename(
            title="Выберите файл для безвозвратного удаления",
            filetypes=[("Все файлы", "*.*")]
        )
        if not file_path:
            return False
        show_dialog = True
    try:
        if not os.path.exists(file_path):
            if show_dialog:
                messagebox.showerror("Ошибка", "Файл не существует")
            return False
        file_size = os.path.getsize(file_path)
        with open(file_path, 'wb') as f:
            for _ in range(3):
                f.seek(0)
                f.write(os.urandom(file_size))
                f.flush()
                os.fsync(f.fileno())
        os.remove(file_path)
        if show_dialog:
            messagebox.showinfo("Успех", f"Файл безвозвратно удален:\n{file_path}")
        return True
    except Exception as e:
        if show_dialog:
            messagebox.showerror("Ошибка", f"Не удалось удалить файл:\n{str(e)}")
        return False