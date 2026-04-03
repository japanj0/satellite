import os
from tkinter import filedialog, messagebox
def secure_delete_file():
    file_path = filedialog.askopenfilename(
        title="Выберите файл для безвозвратного удаления",
        filetypes=[("Все файлы", "*.*")]
    )
    if not file_path:
        return False
    try:
        file_size = os.path.getsize(file_path)
        with open(file_path, 'wb') as f:
            for i in range(3):
                f.seek(0)
                f.write(os.urandom(file_size))
                f.flush()
                os.fsync(f.fileno())
        os.remove(file_path)
        messagebox.showinfo("Успех", f"Файл безвозвратно удален:\n{file_path}")
        return True
    except Exception as e:
        messagebox.showerror("Ошибка", f"Не удалось удалить файл:\n{str(e)}")
        return False