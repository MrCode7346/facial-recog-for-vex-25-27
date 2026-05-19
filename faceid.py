import tkinter as tk
import threading
import cv2
import face_recognition
import os
from PIL import Image, ImageOps
import numpy as np
from tkinter import messagebox as mb
from signup import *
import time

cap = cv2.VideoCapture(0, cv2.CAP_DSHOW)

cap.set(cv2.CAP_PROP_FRAME_WIDTH, 640)
cap.set(cv2.CAP_PROP_FRAME_HEIGHT, 480)

cascade_model_path = "./haarcascade_frontalface_alt.xml"
cascade_model = cv2.CascadeClassifier(cascade_model_path)

FACE_DIR = "./faces"

person_name = tk.StringVar(value="")
new_user_name = tk.StringVar(value="")
new_pass_word = tk.StringVar(value="")

def signup_face():
    counter = 0
    signed_up = False
    while not signed_up:
        ret, frame = cap.read()
        if ret:
            counter += 1
            
            if counter % 10 == 0:
                gray = cv2.cvtColor(frame, cv2.COLOR_BGR2GRAY)
                faces = cascade_model.detectMultiScale(gray, scaleFactor=1.1, minNeighbors=5)

                if len(faces) == 0:
                    print("No face detected, please try again")
                    continue

                for (x,y,w,h) in faces:
                    print(f"Face found at coordinates: ({x}, {y}), width: {w} and height: {y}.")

                username, password = signup_main()

                if username == "Unknown" and password == "Unknown":
                    return

                if len(username) >= 4 and len(password) >= 8:
                    cv2.imwrite(f"{os.path.join(FACE_DIR, username)}.jpg", frame)
                    signed_up = True
            cv2.imshow("Facial detection in progress...", frame)
        key = cv2.waitKey(1)
        if key == ord("q"):
            break      


if not os.path.exists(FACE_DIR) or len(os.listdir(FACE_DIR)) == 0:
    if not os.path.exists(FACE_DIR):
        os.makedirs(FACE_DIR)
    signup =  mb.askyesno("No known faces found...", "Would you like to add a known face?")
    if signup == True:
        signup_face()
    elif signup == "no":
        quit()


counter  = 0

face_match = False
face_name = "Unknown"
# Load known faces
known_encodings = []
known_names = []

def load_rgb_image(path):
    '''used instead of cv2.imread() so that EXIF orientation is handled correctly'''
    img = Image.open(path)
    img = ImageOps.exif_transpose(img) 
    img = img.convert("RGB")
    return np.array(img)

# load and process known faces from the known faces directory

for file in os.listdir(FACE_DIR):
    path = os.path.join(FACE_DIR, file)

    if not os.path.isfile(path):
        continue

    try:
        img = load_rgb_image(path)
    except Exception as e:
        print(f"Could not read {file}: {e}")
        continue

    encodings = face_recognition.face_encodings(img)

    if len(encodings) == 0:
        print(f"No face found in {file}, skipping")
        continue

    known_encodings.append(encodings[0])
    known_names.append(os.path.splitext(file)[0])

if len(known_encodings) == 0:
    print("No valid known faces found in ./faces")
    exit()

def check_faces(test_img):
    global face_match
    global face_name
    TOLERANCE = 0.5
    locations = face_recognition.face_locations(test_img, number_of_times_to_upsample=2)

    if len(locations) == 0:
        print("No face detected in camera")
        face_match = False
        exit()

    test_encodings = face_recognition.face_encodings(test_img, locations)

    if len(test_encodings) == 0:
        print("Face found, but encoding failed")
        face_match = False
        exit()

    test_encoding = test_encodings[0]

    # Compare
    distances = face_recognition.face_distance(known_encodings, test_encoding)
    best_index = np.argmin(distances)

    # print("Known names:", known_names)
    # print("Distances:", distances)

    if distances[best_index] <= TOLERANCE:
        print(f"MATCH: {known_names[best_index]} (distance={distances[best_index]:.4f})")
        face_match = True
        face_name = known_names[best_index]
    else:
        print("Unknown person")
        face_match = False
        face_name = "Unknown"


def faceid_main():
    global counter
    while True:
        ret, frame = cap.read()

        if ret:
            if counter % 10 == 0:
                try:
                    threading.Thread(target=check_faces, args=(frame.copy(), )).start()
                except ValueError:
                    pass

            counter += 1

            if face_match:
                cv2.putText(frame, f"Welcome, {face_name}!", (20, 450), cv2.FONT_HERSHEY_COMPLEX, 2, (0, 255, 0), 3)
            else:
                cv2.putText(frame, "No match!", (20, 450), cv2.FONT_HERSHEY_COMPLEX, 2, (0, 0, 255), 3)
                if counter % 10 == 5:
                    save_face = mb.askyesno("Face not recognised...", "Your face was not recognised, would you like to sign up?")
                    if save_face:
                        signup_face()
                    else:
                        if counter % 60 == 30:
                            break
                        else:
                            continue
            
            cv2.imshow("Facial Recognition in progress...", frame)

        key = cv2.waitKey(1)
        if key == ord("q") or key == ord("Q") or key == 27 or face_match == True:
            break
    person_name.set(face_name)
    return face_name

if __name__ == "__main__":
    faceid_main()

time.sleep(0.5)
cv2.destroyAllWindows()
