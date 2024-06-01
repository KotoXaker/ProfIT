import tensorflow as tf
import cv2
import numpy as np
import pandas as pd
from tkinter import Tk, filedialog
from datetime import timedelta

# Функция для загрузки модели
def load_model(model_path):
    model = tf.keras.models.load_model(model_path)
    return model

# Функция для загрузки модели для детектирования объектов
def load_object_detection_model():
    prototxt_path = 'deploy.prototxt'  # Укажите правильный путь к файлу deploy.prototxt
    model_path = 'mobilenet_iter_73000.caffemodel'  # Укажите правильный путь к файлу mobilenet_iter_73000.caffemodel
    net = cv2.dnn.readNetFromCaffe(prototxt_path, model_path)
    return net

# Функция для обработки кадров видео
def process_frame(frame, model, net, cap, frame_number, violation_times):
    # Предобработка кадра для классификации нарушения
    input_size = model.input_shape[1:3]
    resized_frame = cv2.resize(frame, (input_size[1], input_size[0]))
    normalized_frame = resized_frame / 255.0
    input_data = np.expand_dims(normalized_frame, axis=0)
    predictions = model.predict(input_data)

    # Предобработка кадра для детектирования объектов
    (h, w) = frame.shape[:2]
    blob = cv2.dnn.blobFromImage(cv2.resize(frame, (300, 300)), 0.007843, (300, 300), 127.5)
    net.setInput(blob)
    detections = net.forward()

    # Проверка на наличие нарушений
    violation_detected = False
    person_detected = False
    train_detected = False
    for i in range(detections.shape[2]):
        confidence = detections[0, 0, i, 2]
        if confidence > 0.2:
            idx = int(detections[0, 0, i, 1])
            box = detections[0, 0, i, 3:7] * np.array([w, h, w, h])
            (startX, startY, endX, endY) = box.astype("int")
            if idx == 15:  # Если это человек (индекс 15 для MobileNet SSD)
                label = "Person"
                person_detected = True
                cv2.rectangle(frame, (startX, startY), (endX, endY), (0, 255, 0), 2)
                cv2.putText(frame, label, (startX, startY - 15), cv2.FONT_HERSHEY_SIMPLEX, 0.5, (0, 255, 0), 2)
            elif idx == 7:  # Если это поезд (индекс 7 для MobileNet SSD, проверьте точный индекс для вашей модели)
                label = "Train"
                train_detected = True
                cv2.rectangle(frame, (startX, startY), (endX, endY), (255, 0, 0), 2)
                cv2.putText(frame, label, (startX, startY - 15), cv2.FONT_HERSHEY_SIMPLEX, 0.5, (255, 0, 0), 2)

            # Проверка на близость человека к поезду
            if person_detected and train_detected:
                person_box = [startX, startY, endX, endY]
                for j in range(detections.shape[2]):
                    if j != i:
                        other_idx = int(detections[0, 0, j, 1])
                        if other_idx == 7:  # Предполагаем, что 7 - это поезд
                            other_box = detections[0, 0, j, 3:7] * np.array([w, h, w, h])
                            (other_startX, other_startY, other_endX, other_endY) = other_box.astype("int")
                            if (startX < other_endX and endX > other_startX and
                                startY < other_endY and endY > other_startY):
                                violation_detected = True

    if violation_detected:
        # Вычисление времени кадра
        timestamp = frame_number / cap.get(cv2.CAP_PROP_FPS)
        time_tag = str(timedelta(seconds=timestamp))
        cv2.putText(frame, 'Violation Detected', (10, 30), cv2.FONT_HERSHEY_SIMPLEX, 1, (0, 0, 255), 2, cv2.LINE_AA)
        violation_times.append(time_tag)  # Добавить тайм-тег

    return frame

# Основная функция для обработки видео
def process_video(video_path, model_path, output_excel_path, frame_skip=1):
    model = load_model(model_path)
    net = load_object_detection_model()
    cap = cv2.VideoCapture(video_path)

    frame_number = 0
    violation_times = []

    while cap.isOpened():
        ret, frame = cap.read()
        if not ret:
            break

        # Пропускаем кадры для понижения частоты кадров
        if frame_number % frame_skip == 0:
            frame = process_frame(frame, model, net, cap, frame_number, violation_times)
            cv2.imshow('Video', frame)
            if cv2.waitKey(1) & 0xFF == ord('q'):
                break

        frame_number += 1

    cap.release()
    cv2.destroyAllWindows()

    # Сохранение времени нарушений в Excel
    df = pd.DataFrame(violation_times, columns=['Violation Time (hh:mm:ss)'])
    df.to_excel(output_excel_path, index=False)
    print(f"Violation times saved to {output_excel_path}")

# Выбор видео и пути к модели
def select_file(filetypes, title):
    root = Tk()
    root.withdraw()  # Скрыть главное окно
    file_path = filedialog.askopenfilename(filetypes=filetypes, title=title)
    root.destroy()
    return file_path

video_path = select_file(filetypes=[("Video files", "*.mp4;*.avi;*.mov")], title="Select Video File")
model_path = select_file(filetypes=[("H5 files", "*.h5")], title="Select Model File")
output_excel_path = 'C://Users//User//Desktop//violation_times.xlsx'  # Укажите путь для сохранения файла Excel

if video_path and model_path:
    process_video(video_path, model_path, output_excel_path, frame_skip=2)  # Укажите желаемый шаг пропуска кадров
else:
    print("Видео или модель не выбраны.")
