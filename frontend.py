import tkinter as tk
from tkinter import filedialog, messagebox
from tkinter import ttk
from PIL import Image, ImageTk, ImageDraw
import threading
import cv2
import pandas as pd
from backend import process_video
import os
import time

class ViolationViewer(tk.Toplevel):
    def __init__(self, parent, violation_data):
        super().__init__(parent)
        self.title("Тайминги нарушений")
        self.geometry("800x600")
        self.violation_data = violation_data

        self.export_button = tk.Button(self, text="Экспортировать в Excel", command=self.export_to_excel)
        self.export_button.pack(side=tk.BOTTOM, pady=10)

        self.listbox = tk.Listbox(self, width=50, height=20)
        self.listbox.pack(side=tk.LEFT, fill=tk.BOTH, expand=True)
        self.listbox.bind('<<ListboxSelect>>', self.on_select_violation)

        self.frame_label = tk.Label(self)
        self.frame_label.pack(side=tk.RIGHT, fill=tk.BOTH, expand=True)

        for video_name, data in violation_data.items():
            for time_tag, info in data.items():
                label = info[1]
                self.listbox.insert(tk.END, f"{video_name}: {time_tag} - {label}")

    def on_select_violation(self, event):
        selected_item = self.listbox.get(self.listbox.curselection())
        video_name, rest = selected_item.split(": ")
        selected_time, label = rest.split(" - ")
        frame = self.violation_data[video_name][selected_time][0]
        frame_rgb = cv2.cvtColor(frame, cv2.COLOR_BGR2RGB)
        img = Image.fromarray(frame_rgb)
        img = ImageTk.PhotoImage(img)
        self.frame_label.config(image=img)
        self.frame_label.image = img
        self.title(f"Тайминги нарушений - {label}")

    def export_to_excel(self):
        data = []
        for video_name, violations in self.violation_data.items():
            for time_tag, (frame, label) in violations.items():
                data.append({"Видео": video_name, "Время": time_tag, "Тип нарушения": label})
        df = pd.DataFrame(data)
        export_path = filedialog.asksaveasfilename(defaultextension=".xlsx", filetypes=[("Excel files", "*.xlsx"), ("All files", "*.*")])
        if export_path:
            df.to_excel(export_path, index=False)
            messagebox.showinfo("Экспорт завершен", f"Тайм-коды экспортированы в {export_path}")

class ProcessingWindow(tk.Toplevel):
    def __init__(self, parent):
        super().__init__(parent)
        self.title("Обработка видео")
        self.geometry("300x100")
        self.label = tk.Label(self, text="Идет обработка видео, пожалуйста, подождите...")
        self.label.pack(pady=10)
        self.progress_bar = ttk.Progressbar(self, orient='horizontal', mode='indeterminate', length=250)
        self.progress_bar.pack(pady=10)
        self.progress_bar.start()

        self.progress_label = tk.Label(self, text="")
        self.progress_label.pack(pady=10)

    def update_progress(self, progress, elapsed_time):
        self.progress_bar['value'] = progress
        self.progress_label.config(text=f"Прогресс: {progress:.2f}% | Время: {elapsed_time:.2f} сек.")

def select_files(filetypes, title):
    file_paths = filedialog.askopenfilenames(filetypes=filetypes, title=title)
    return list(file_paths)

def on_add_videos():
    global video_paths
    video_paths = select_files(filetypes=[("Video files", "*.mp4;*.avi;*.mov")], title="Выберите видеофайлы")
    if video_paths:
        add_video_label.config(text="Видео выбраны")

def on_start_processing():
    if video_paths:
        global processing_window
        processing_window = ProcessingWindow(root)
        root.withdraw()
        threading.Thread(target=process_videos_thread, args=(video_paths,)).start()
    else:
        print("Видео не выбраны.")

def process_videos_thread(video_paths):
    model_path = 'C://Users//User//Desktop//детект//ProfIT//video_frame_classifier5.keras'
    start_time = time.time()
    all_violation_times, all_violation_frames, all_violation_labels = process_video(video_paths, model_path)
    elapsed_time = time.time() - start_time
    for video_path, times, frames, labels in zip(video_paths, all_violation_times, all_violation_frames, all_violation_labels):
        video_name = os.path.basename(video_path)
        violation_data[video_name] = {time: (frame, label) for time, frame, label in zip(times, frames, labels)}
    root.deiconify()
    processing_window.destroy()
    open_violation_viewer()
    messagebox.showinfo("Обработка завершена", f"Обработка видео завершена за {elapsed_time:.2f} секунд.")

def open_violation_viewer():
    ViolationViewer(root, violation_data)

def create_rounded_rectangle(w, h, radius=25, color=(255, 255, 255, 200)):
    image = Image.new("RGBA", (w, h), (255, 255, 255, 0))
    draw = ImageDraw.Draw(image)
    draw.rounded_rectangle((0, 0, w, h), radius, fill=color)
    return ImageTk.PhotoImage(image)

def center_window(window):
    window.update_idletasks()
    width = window.winfo_width()
    height = window.winfo_height()
    x = (window.winfo_screenwidth() // 2) - (width // 2)
    y = (window.winfo_screenheight() // 2) - (height // 2)
    window.geometry(f'{width}x{height}+{x}+{y}')
    window.resizable(False, False)

root = tk.Tk()
root.title("Анализатор видео с регистратора")
root.geometry("1280x720")
center_window(root)

image_path = "image.png"
bg_image = Image.open(image_path)
bg_image = bg_image.resize((1280, 720), Image.LANCZOS)
bg_photo = ImageTk.PhotoImage(bg_image)

canvas = tk.Canvas(root, width=1280, height=720)
canvas.pack(fill="both", expand=True)

canvas.create_image(0, 0, image=bg_photo, anchor="nw")

# Создаем полупрозрачный закругленный фон для кнопки "Добавить видео"
rounded_bg = create_rounded_rectangle(350, 250, radius=50)
canvas.create_image(640, 335, image=rounded_bg, anchor="center")

# Добавляем текст и плюсик
add_video_plus = canvas.create_text(640, 295, text="+", font=("Arial", 48), fill='black')
add_video_text = canvas.create_text(640, 355, text="Добавить видео", font=("Arial", 24), fill='black')

add_video_label = tk.Label(root, text="", font=("Arial", 14), bg='white')
add_video_label.place(relx=0.5, rely=0.55, anchor='center')

# Создаем полупрозрачный закругленный красный фон для кнопки "Начать обработку"
start_button_bg = create_rounded_rectangle(300, 50, radius=25, color=(211, 47, 47, 255))
canvas.create_image(640, 625, image=start_button_bg, anchor="center")

start_button_text = canvas.create_text(640, 625, text="Начать обработку", font=("Arial", 18), fill='white')

canvas.tag_bind(add_video_plus, '<ButtonPress-1>', lambda e: on_add_videos())
canvas.tag_bind(add_video_text, '<ButtonPress-1>', lambda e: on_add_videos())
canvas.tag_bind(start_button_bg, '<ButtonPress-1>', lambda e: on_start_processing())
canvas.tag_bind(start_button_text, '<ButtonPress-1>', lambda e: on_start_processing())

# Словарь для хранения кадров с нарушениями
violation_data = {}

root.mainloop()
