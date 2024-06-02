import tensorflow as tf
import cv2
import numpy as np
from datetime import timedelta

def load_model(model_path):
    model = tf.keras.models.load_model(model_path)
    return model

def load_object_detection_model():
    prototxt_path = 'deploy.prototxt'
    model_path = 'mobilenet_iter_73000.caffemodel'
    net = cv2.dnn.readNetFromCaffe(prototxt_path, model_path)
    return net

def process_frame(frame, model, net, frame_number, violation_times, violation_frames, violation_labels):
    input_size = model.input_shape[1:3]
    resized_frame = cv2.resize(frame, (input_size[1], input_size[0]))
    normalized_frame = resized_frame / 255.0
    input_data = np.expand_dims(normalized_frame, axis=0)
    predictions = model.predict(input_data)
    label = classify_violation(predictions)

    (h, w) = frame.shape[:2]
    blob = cv2.dnn.blobFromImage(cv2.resize(frame, (300, 300)), 0.007843, (300, 300), 127.5)
    net.setInput(blob)
    detections = net.forward()

    violation_detected = False
    person_detected = False
    train_detected = False

    for i in range(detections.shape[2]):
        confidence = detections[0, 0, i, 2]
        if confidence > 0.2:
            idx = int(detections[0, 0, i, 1])
            box = detections[0, 0, i, 3:7] * np.array([w, h, w, h])
            (startX, startY, endX, endY) = box.astype("int")
            if idx == 15:  # Person
                person_detected = True
            elif idx == 7:  # Train
                train_detected = True

            if person_detected and train_detected:
                violation_detected = True
                break

    if violation_detected:
        timestamp = frame_number / 30.0  # Assuming 30 FPS
        time_tag = str(timedelta(seconds=timestamp))
        violation_times.append(time_tag)
        violation_frames.append(frame)
        violation_labels.append(label)

    return frame

def classify_violation(predictions):
    class_names = ["под поездом", "возле поезда", "на поезде"]
    class_idx = np.argmax(predictions)
    return class_names[class_idx]

def process_video(video_paths, model_path):
    model = load_model(model_path)
    net = load_object_detection_model()

    all_violation_times = []
    all_violation_frames = []
    all_violation_labels = []

    for video_path in video_paths:
        cap = cv2.VideoCapture(video_path)
        frame_count = int(cap.get(cv2.CAP_PROP_FRAME_COUNT))
        video_violation_times = []
        video_violation_frames = []
        video_violation_labels = []

        while cap.isOpened():
            ret, frame = cap.read()
            if not ret:
                break

            frame_number = int(cap.get(cv2.CAP_PROP_POS_FRAMES))

            if frame_number % 5 == 0:  # Process every 5th frame to speed up
                frame = process_frame(frame, model, net, frame_number, video_violation_times, video_violation_frames, video_violation_labels)

        cap.release()
        all_violation_times.append(video_violation_times)
        all_violation_frames.append(video_violation_frames)
        all_violation_labels.append(video_violation_labels)

    return all_violation_times, all_violation_frames, all_violation_labels
