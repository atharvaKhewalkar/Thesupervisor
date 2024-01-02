import cv2
import numpy as np
import os
import time
import webbrowser
# Load YOLO
# Load the trained face recognition model
recognizer = cv2.face.LBPHFaceRecognizer_create()
recognizer.read('trainingData.yml')
face_cascade = cv2.CascadeClassifier('haarcascade.xml')
net = cv2.dnn.readNet("yolov3.weights", "yolov3.cfg")
classes = []

with open("coco.names", "r") as f:
    classes = [line.strip() for line in f]

layer_names = net.getUnconnectedOutLayersNames()

# Open a video capture object
cap = cv2.VideoCapture(0)  # 0 for default camera, or provide the path to a video file
user_detected = False
first_time_user = True
exam_tab_opened = False

exam_url = "https://github.com/atharvaKhewalkar/Thesupervisor"

def open_exam_tab():
    global exam_tab_opened
    # Open exam tab in the default web browser
    webbrowser.open_new(exam_url)
    print('Exam tab opened successfully')
    exam_tab_opened = True

def close_exam_tab():
    global exam_tab_opened
    # Close exam tab by simulating keyboard shortcuts (may not work in all scenarios)
    os.system("taskkill /F /IM chrome.exe")  # Terminate Chrome process
    print('Exam tab closed successfully')
    exam_tab_opened = False



    
    
# Exclude the "person" class
exclude_class = "person"

# Set the minimum percentage of object visibility for detection
min_visibility_percentage = 0.50

while True:
    # Read a frame from the camera
    ret, frame = cap.read()
    
    if ret:
        gray = cv2.cvtColor(frame, cv2.COLOR_BGR2GRAY)

        # Detect faces
        faces = face_cascade.detectMultiScale(gray, 1.3, 5)

        for (x, y, w, h) in faces:
            # Recognize the face
            roi_gray = gray[y:y + h, x:x + w]
            id_, confidence = recognizer.predict(roi_gray)

            if confidence < 70:  # You may need to adjust the confidence threshold
                name = f"User {id_}"
                cv2.putText(frame, name, (x, y - 10), cv2.FONT_HERSHEY_SIMPLEX, 0.9, (0, 255, 0), 2)

                if first_time_user and not exam_tab_opened:
                    open_exam_tab()
                    first_time_user = False

            else:
                cv2.putText(frame, "Unknown", (x, y - 10), cv2.FONT_HERSHEY_SIMPLEX, 0.9, (0, 0, 255), 2)

                if exam_tab_opened:
                        close_exam_tab()
                        break  # Terminate the loop and close the tab


    # Get the frame shape and prepare it for YOLO
    height, width, channels = frame.shape
    blob = cv2.dnn.blobFromImage(frame, 0.00392, (416, 416), (0, 0, 0), True, crop=False)
    net.setInput(blob)
    outs = net.forward(layer_names)

    # Process the outputs from YOLO
    for out in outs:
        for detection in out:
            scores = detection[5:]
            class_id = np.argmax(scores)
            confidence = scores[class_id]

            # Exclude the "person" class
            if confidence > 0.5 and classes[class_id] != exclude_class:
                # Object detected
                center_x = int(detection[0] * width)
                center_y = int(detection[1] * height)
                w = int(detection[2] * width)
                h = int(detection[3] * height)

                # Calculate the percentage of object visibility
                visibility_percentage = (w * h) / (width * height) * 100

                # Draw bounding box if visibility is more than the threshold
                if visibility_percentage > min_visibility_percentage:
                    # Rectangle coordinates
                    x = int(center_x - w / 2)
                    y = int(center_y - h / 2)

                    # Draw bounding box for all classes except "person"
                    color = (0, 255, 0)  # Green color for the bounding box
                    cv2.rectangle(frame, (x, y), (x + w, y + h), color, 2)
                    cv2.putText(frame, f"{classes[class_id]} {confidence:.2f}", (x, y - 10), cv2.FONT_HERSHEY_SIMPLEX, 0.5, color, 2)

    # Display the resulting frame
    cv2.imshow("Object Detection", frame)

    # Break the loop if 'q' key is pressed
    if cv2.waitKey(1) & 0xFF == ord('q'):
        break

# Release the video capture object and close all windows
cap.release()
cv2.destroyAllWindows()