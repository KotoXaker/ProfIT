import tkinter as tk
from tkinter import filedialog, ttk
from PIL import Image, ImageTk, ImageDraw
import threading
import cv2
from backend import process_video

class ViolationViewer(tk.Toplevel):
    def __init__(self, parent, violation_data):
        super().__init__(parent)
        self.title("Тайминги нарушений")
        self.geometry("800x600")
        self.violation_data = violation_data

        self.filter_var = tk.StringVar(self)
        self.filter_var.set("Все")
        self.filter_menu = tk.OptionMenu(self, self.filter_var, "Все", "Под поездом", "Возле поезда", "На поезде", command=self.filter_violations)
        self.filter_menu.pack()

        self.sort_var = tk.StringVar(self)
        self.sort_var.set("По времени")
        self.sort_menu = tk.OptionMenu(self, self.sort_var, "По времени", "По типу", command=self.sort_violations)
        self.sort_menu.pack()

        self.listbox = tk.Listbox(self, width=50, height=20)
        self.listbox.pack(side=tk.LEFT, fill=tk.BOTH, expand=True)
        self.listbox.bind('<<ListboxSelect>>', self.on_select_violation)

        self.frame_label = tk.Label(self)
        self.frame_label.pack(side=tk.RIGHT, fill=tk.BOTH, expand=True)

        self.export_button = tk.Button(self, text="Экспортировать в Excel", command=self.export_to_excel)
        self.export_button.pack(side=tk.BOTTOM)

        for time_tag in violation_data.keys():
            self.listbox.insert(tk.END, time_tag)

    def filter_violations(self, filter_type):
        self.listbox.delete(0, tk.END)
        for time_tag, (label, frame) in self.violation_data.items():
            if filter_type == "Все" or label == filter_type:
                self.listbox.insert(tk.END, time_tag)

    def sort_violations(self, sort_type):
        violations = list(self.violation_data.items())
        if sort_type == "По времени":
            violations.sort()
        elif sort_type == "По типу":
            violations.sort(key=lambda x: x[1][0])
        self.listbox.delete(0, tk.END)
        for time_tag, (label, frame) in violations:
            self.listbox.insert(tk.END, time_tag)

    def on_select_violation(self, event):
        selected_time = self.listbox.get(self.listbox.curselection())
        frame = self.violation_data[selected_time][1]
        frame_rgb = cv2.cvtColor(frame, cv2.COLOR_BGR2RGB)
        img = Image.fromarray(frame_rgb)
        img = ImageTk.PhotoImage(img)
        self.frame_label.config(image=img)
        self.frame_label.image = img

    def export_to_excel(self):
        import pandas as pd
        df = pd.DataFrame(self.violation_data.items(), columns=['Время нарушения', 'Тип нарушения'])
        df.to_excel('violation_times.xlsx', index=False)
        print("Тайминги нарушений экспортированы в violation_times.xlsx")

def select_files(filetypes, title):
    file_paths = filedialog.askopenfilenames(filetypes=filetypes, title=title)
    return list(file_paths)

def on_add_videos():
    global video_paths
    video_paths = select_files(filetypes=[("Video files", "*.mp4;*.avi;*.mov")], title="Выберите видеофайлы")
    if video_paths:
        add_video_label.config(text="Видео выбраны")

def on_start_processing():
    threading.Thread(target=process_videos_thread, args=(video_paths,)).start()

def process_videos_thread(video_paths):
    progress_window = create_progress_window()
    all_violation_times, all_violation_frames, all_violation_labels = process_video(video_paths, frame_skip=1)
    violation_data.update({time: (label, frame) for time, frame, label in zip(all_violation_times, all_violation_frames, all_violation_labels)})
    progress_window.destroy()
    open_violation_viewer()

def open_violation_viewer():
    ViolationViewer(root, violation_data)

def create_rounded_rectangle(w, h, radius=25, color=(255, 255, 255, 200)):
    image = Image.new("RGBA", (w, h), (255, 255, 255, 0))
    draw = ImageDraw.Draw(image)
    draw.rounded_rectangle((0, 0, w, h), radius, fill=color)
    return ImageTk.PhotoImage(image)

def create_progress_window():
    progress_window = tk.Toplevel(root)
    progress_window.title("Обработка видео")
    progress_window.geometry("300x100")
    progress_window.transient(root)
    progress_window.grab_set()
    progress_label = tk.Label(progress_window, text="Идет обработка, пожалуйста, подождите...")
    progress_label.pack(pady=10)
    progress_bar = ttk.Progressbar(progress_window, orient='horizontal', mode='indeterminate', length=250)
    progress_bar.pack(pady=10)
    progress_bar.start()
    root.withdraw()
    return progress_window

root = tk.Tk()
root.title("Анализатор видео с регистратора")
root.geometry("1280x720")
root.resizable(False, False)

# Центрирование окна
window_width = 1280
window_height = 720
screen_width = root.winfo_screenwidth()
screen_height = root.winfo_screenheight()
position_top = int(screen_height/2 - window_height/2)
position_right = int(screen_width/2 - window_width/2)
root.geometry(f'{window_width}x{window_height}+{position_right}+{position_top}')

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
