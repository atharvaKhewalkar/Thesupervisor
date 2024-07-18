import cv2
from fer import FER
import numpy as np
import os

try:
    from scipy.spatial import distance as dist
except ImportError:
    print("scipy is not installed. Please install it using 'pip install scipy'.")

try:
    import dlib
    from imutils import face_utils
except ImportError:
    print("dlib and imutils are not installed. Please install them using 'pip install dlib imutils'.")

# Function to compute stress level based on emotions
def compute_stress_level(emotions):
    dominant_emotion = max(emotions, key=emotions.get)

    # Enhanced stress mapping
    stress_mapping = {
        'angry': 80,
        'disgust': 70,
        'fear': 90,
        'happy': 10,
        'sad': 70,
        'surprise': 50,
        'neutral': 30
    }

    stress_level = stress_mapping.get(dominant_emotion, 0)

    # Consider the intensity of the emotion
    emotion_intensity = emotions[dominant_emotion]
    stress_level = int(stress_level * emotion_intensity)

    return stress_level, dominant_emotion

# Function to detect significant motion
def detect_motion(prev_frame, curr_frame, threshold=1000):
    prev_gray = cv2.cvtColor(prev_frame, cv2.COLOR_BGR2GRAY)
    curr_gray = cv2.cvtColor(curr_frame, cv2.COLOR_BGR2GRAY)

    flow = cv2.calcOpticalFlowFarneback(prev_gray, curr_gray, None, 0.5, 3, 15, 3, 5, 1.2, 0)
    mag, _ = cv2.cartToPolar(flow[..., 0], flow[..., 1])

    return np.sum(mag) > threshold

# Preprocessing function
def preprocess_frame(frame):
    gray = cv2.cvtColor(frame, cv2.COLOR_BGR2GRAY)
    equalized = cv2.equalizeHist(gray)
    return cv2.cvtColor(equalized, cv2.COLOR_GRAY2BGR)

# Function to align face for better emotion detection
def align_face(image, face_rect, predictor_path="shape_predictor_68_face_landmarks.dat"):
    predictor = dlib.shape_predictor(predictor_path)

    x, y, w, h = face_rect
    rect = dlib.rectangle(x, y, x + w, y + h)
    shape = predictor(image, rect)
    shape = face_utils.shape_to_np(shape)

    (lStart, lEnd) = face_utils.FACIAL_LANDMARKS_IDXS["left_eye"]
    (rStart, rEnd) = face_utils.FACIAL_LANDMARKS_IDXS["right_eye"]
    leftEyePts = shape[lStart:lEnd]
    rightEyePts = shape[rStart:rEnd]

    leftEyeCenter = leftEyePts.mean(axis=0).astype("int")
    rightEyeCenter = rightEyePts.mean(axis=0).astype("int")
    dY = rightEyeCenter[1] - leftEyeCenter[1]
    dX = rightEyeCenter[0] - leftEyeCenter[0]
    angle = np.degrees(np.arctan2(dY, dX)) - 180

    desiredLeftEye = (0.35, 0.35)
    desiredFaceWidth = 256
    desiredFaceHeight = 256
    desiredDist = (1.0 - 2 * desiredLeftEye[0]) * desiredFaceWidth
    dist = np.sqrt((dX ** 2) + (dY ** 2))
    scale = desiredDist / dist

    eyesCenter = (int((leftEyeCenter[0] + rightEyeCenter[0]) // 2),
                  int((leftEyeCenter[1] + rightEyeCenter[1]) // 2))

    M = cv2.getRotationMatrix2D(eyesCenter, angle, scale)
    tX = desiredFaceWidth * 0.5
    tY = desiredFaceHeight * desiredLeftEye[1]
    M[0, 2] += (tX - eyesCenter[0])
    M[1, 2] += (tY - eyesCenter[1])

    output = cv2.warpAffine(image, M, (desiredFaceWidth, desiredFaceHeight), flags=cv2.INTER_CUBIC)

    return output

# Main function for live stress level detection
def detect_stress():
    cap = cv2.VideoCapture(0)
    detector = FER(mtcnn=True)

    ret, prev_frame = cap.read()
    if not ret or prev_frame is None:
        print("Error: Unable to capture from camera.")
        return
    prev_frame = preprocess_frame(cv2.flip(prev_frame, 1))

    while True:
        ret, frame = cap.read()
        if not ret or frame is None:
            print("Error: Unable to capture from camera.")
            break

        frame = preprocess_frame(cv2.flip(frame, 1))  # Flip frame to match user's perspective
        motion_detected = detect_motion(prev_frame, frame)
        prev_frame = frame.copy()

        result = detector.detect_emotions(frame)

        if result:
            for face in result:
                x, y, w, h = face["box"]
                emotions = face["emotions"]
                aligned_face = align_face(frame, face["box"])
                stress_level, dominant_emotion = compute_stress_level(emotions)

                if motion_detected:
                    stress_level += 10  # Increase stress level due to significant motion

                print(f'Dominant Emotion: {dominant_emotion}, Stress Level: {stress_level}')

                cv2.rectangle(frame, (x, y), (x+w, y+h), (255, 0, 0), 2)
                cv2.putText(frame, f'Stress Level: {stress_level}', (x, y-10), cv2.FONT_HERSHEY_SIMPLEX, 0.9, (0, 255, 0), 2)

        cv2.imshow('Live Stress Detection', frame)

        if cv2.waitKey(1) & 0xFF == ord('q'):
            break

    cap.release()
    cv2.destroyAllWindows()

# Ensure the predictor file is in the correct path
predictor_path = "shape_predictor_68_face_landmarks.dat"
if not os.path.exists(predictor_path):
    print(f"Error: The predictor file {predictor_path} does not exist.")
else:
    # Run the live stress detection function
    detect_stress()
