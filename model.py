import tensorflow as tf
from tensorflow.keras.models import Sequential
from tensorflow.keras.layers import Conv2D, MaxPooling2D, Flatten, Dense, Dropout
from sklearn.model_selection import train_test_split
import numpy as np
import os
import cv2
from google.colab import drive

# Подключение Google Диска
drive.mount('/content/drive')

# Параметры
img_height, img_width = 128, 128
batch_size = 32
epochs = 10

# Функция для извлечения кадров из видео
def extract_frames(video_path, label, images, labels):
    cap = cv2.VideoCapture(video_path)
    while cap.isOpened():
        ret, frame = cap.read()
        if not ret:
            break
        frame = cv2.resize(frame, (img_height, img_width))
        images.append(frame)
        labels.append(label)
    cap.release()

# Загрузка данных
def load_data(data_dir):
    images = []
    labels = []
    for label, folder in enumerate(['positive', 'negative']):
        label_dir = os.path.join(data_dir, folder)
        for video_name in os.listdir(label_dir):
            video_path = os.path.join(label_dir, video_name)
            extract_frames(video_path, label, images, labels)
    return np.array(images), np.array(labels)

# Указание пути к данным на Google Диске
data_dir = '/content/drive/MyDrive/нарезанный датасет'  # Обновите путь к вашему датасету
images, labels = load_data(data_dir)

# Нормализация данных
images = images / 255.0

# Разделение на обучающую и тестовую выборки
X_train, X_test, y_train, y_test = train_test_split(images, labels, test_size=0.2, random_state=42)

# Создание модели
model = Sequential([
    Conv2D(32, (3, 3), activation='relu', input_shape=(img_height, img_width, 3)),
    MaxPooling2D((2, 2)),
    Conv2D(64, (3, 3), activation='relu'),
    MaxPooling2D((2, 2)),
    Conv2D(128, (3, 3), activation='relu'),
    MaxPooling2D((2, 2)),
    Flatten(),
    Dense(512, activation='relu'),
    Dropout(0.5),
    Dense(1, activation='sigmoid')
])

# Компиляция модели
model.compile(optimizer='adam', loss='binary_crossentropy', metrics=['accuracy'])

# Обучение модели
model.fit(X_train, y_train, epochs=epochs, batch_size=batch_size, validation_split=0.2)

# Оценка модели
loss, accuracy = model.evaluate(X_test, y_test)
print(f'Test accuracy: {accuracy:.2f}')

# Сохранение модели
model.save('/content/drive/MyDrive/video_frame_classifier.h5')  # Сохраните модель на Google Диске
