import numpy as np
import mediapipe as mp

mp_face_mesh = mp.solutions.face_mesh
face_mesh = mp_face_mesh.FaceMesh(refine_landmarks=True)

LEFT_EYE = [33, 160, 158, 133, 153, 144]
RIGHT_EYE = [362, 385, 387, 263, 373, 380]

def euclidean_distance(p1, p2):
    return np.linalg.norm(np.array(p1) - np.array(p2))

def calculate_EAR(eye_points, landmarks, w, h):
    p1 = np.array([landmarks[eye_points[0]].x * w, landmarks[eye_points[0]].y * h])
    p2 = np.array([landmarks[eye_points[1]].x * w, landmarks[eye_points[1]].y * h])
    p3 = np.array([landmarks[eye_points[2]].x * w, landmarks[eye_points[2]].y * h])
    p4 = np.array([landmarks[eye_points[3]].x * w, landmarks[eye_points[3]].y * h])
    p5 = np.array([landmarks[eye_points[4]].x * w, landmarks[eye_points[4]].y * h])
    p6 = np.array([landmarks[eye_points[5]].x * w, landmarks[eye_points[5]].y * h])
    ear = (euclidean_distance(p2, p6) + euclidean_distance(p3, p5)) / (2.0 * euclidean_distance(p1, p4) + 1e-6)
    return ear
