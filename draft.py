import cv2
import numpy as np
import os
import time
import webbrowser
import tkinter as tk
from tkinter import messagebox

# Load the trained face recognition model and other configurations (not shown for brevity)

# Load YOLO
net = cv2.dnn.readNet("yolov3.weights", "yolov3.cfg")
layer_names = net.getUnconnectedOutLayersNames()
classes = []

with open("coco.names", "r") as f:
    classes = [line.strip() for line in f]

# Open a video capture object
cap = cv2.VideoCapture(0)  # 0 for default camera, or provide the path to a video file

# Set cooldown parameters
cooldown_time = 60  # seconds
last_alert_time = 0

def show_popup(class_name):
    global last_alert_time
    current_time = time.time()

    if current_time - last_alert_time >= cooldown_time:
        root = tk.Tk()
        root.withdraw()
        messagebox.showinfo("Non-Person Object Detected", f"Detected a non-person object: {class_name}")

        last_alert_time = current_time

while True:
    ret, frame = cap.read()

    if ret:
        gray = cv2.cvtColor(frame, cv2.COLOR_BGR2GRAY)
        height, width, channels = frame.shape

        # Your existing face detection and recognition code (not shown for brevity)
        faces = dlib_detector(gray, 1)
        for face in faces:
            # Your existing face recognition code goes here...
            id_, confidence = recognizer.predict(gray[y:y + h, x:x + w])

            # Your existing face recognition code goes here...

        # Your existing YOLO object detection code (not shown for brevity)
        blob = cv2.dnn.blobFromImage(frame, 0.00392, (416, 416), (0, 0, 0), True, crop=False)
        net.setInput(blob)
        outs = net.forward(layer_names)

        for out in outs:
            for detection in out:
                scores = detection[5:]
                class_id = np.argmax(scores)
                confidence = scores[class_id]

                if confidence > 0.5 and classes[class_id] != "person":
                    center_x = int(detection[0] * width)
                    center_y = int(detection[1] * height)
                    w = int(detection[2] * width)
                    h = int(detection[3] * height)

                    visibility_percentage = (w * h) / (width * height) * 100

                    if visibility_percentage > min_visibility_percentage:
                        x = int(center_x - w / 2)
                        y = int(center_y - h / 2)

                        detected_object = {
                            'class': classes[class_id],
                            'confidence': confidence,
                            'visibility_percentage': visibility_percentage,
                            'bounding_box': (x, y, x + w, y + h)
                        }

                        if detected_object["class"] == "cell phone" or detected_object["class"] == "book":
                            # Your existing code to close the exam tab (not shown for brevity)
                            break

                        message = f"{detected_object['class']} detected with confidence {detected_object['confidence']:.2f}"
                        show_popup(message)

                        color = (0, 255, 0)  # Green color for the bounding box
                        cv2.rectangle(frame, (x, y), (x + w, y + h), color, 2)
                        cv2.putText(frame, f"{classes[class_id]} {confidence:.2f}", (x, y - 10),
                                    cv2.FONT_HERSHEY_SIMPLEX, 0.5, color, 2)

        cv2.imshow("Object Detection", frame)

        if cv2.waitKey(1) & 0xFF == ord('q'):
            break

cap.release()
cv2.destroyAllWindows()