import numpy as np
import mediapipe as mp

mp_face_mesh = mp.solutions.face_mesh
face_mesh = mp_face_mesh.FaceMesh(refine_landmarks=True, 
                                   max_num_faces=1,
                                   min_detection_confidence=0.5,
                                   min_tracking_confidence=0.5)

LEFT_EYE = [33, 160, 158, 133, 153, 144]
RIGHT_EYE = [362, 385, 387, 263, 373, 380]

# NEW: Additional landmarks for stress detection
EYEBROW_LEFT = [70, 63, 105, 66, 107]
EYEBROW_RIGHT = [336, 296, 334, 293, 300]
MOUTH = [61, 291, 0, 17, 314, 405]
JAW = [172, 136, 150, 176, 148, 152]

def euclidean_distance(p1, p2):
    return np.linalg.norm(np.array(p1) - np.array(p2))

def calculate_EAR(eye_points, landmarks, w, h):
    """Calculate Eye Aspect Ratio"""
    p1 = np.array([landmarks[eye_points[0]].x * w, landmarks[eye_points[0]].y * h])
    p2 = np.array([landmarks[eye_points[1]].x * w, landmarks[eye_points[1]].y * h])
    p3 = np.array([landmarks[eye_points[2]].x * w, landmarks[eye_points[2]].y * h])
    p4 = np.array([landmarks[eye_points[3]].x * w, landmarks[eye_points[3]].y * h])
    p5 = np.array([landmarks[eye_points[4]].x * w, landmarks[eye_points[4]].y * h])
    p6 = np.array([landmarks[eye_points[5]].x * w, landmarks[eye_points[5]].y * h])
    
    ear = (euclidean_distance(p2, p6) + euclidean_distance(p3, p5)) / \
          (2.0 * euclidean_distance(p1, p4) + 1e-6)
    return ear

def extract_stress_features(landmarks, w, h):
    """Extract facial features for stress detection"""
    features = []
    
    # 1. Eyebrow height (furrowed = stress)
    left_brow = np.mean([landmarks[i].y * h for i in EYEBROW_LEFT])
    right_brow = np.mean([landmarks[i].y * h for i in EYEBROW_RIGHT])
    left_eye_center = np.mean([landmarks[i].y * h for i in LEFT_EYE])
    right_eye_center = np.mean([landmarks[i].y * h for i in RIGHT_EYE])
    
    brow_eye_dist_left = abs(left_eye_center - left_brow)
    brow_eye_dist_right = abs(right_eye_center - right_brow)
    features.extend([brow_eye_dist_left, brow_eye_dist_right])
    
    # 2. Eyebrow furrow (distance between eyebrows)
    brow_center_left = landmarks[70]
    brow_center_right = landmarks[300]
    brow_distance = euclidean_distance(
        [brow_center_left.x * w, brow_center_left.y * h],
        [brow_center_right.x * w, brow_center_right.y * h]
    )
    features.append(brow_distance)
    
    # 3. Mouth tension (lip tightness)
    mouth_width = euclidean_distance(
        [landmarks[61].x * w, landmarks[61].y * h],
        [landmarks[291].x * w, landmarks[291].y * h]
    )
    mouth_height = euclidean_distance(
        [landmarks[0].x * w, landmarks[0].y * h],
        [landmarks[17].x * w, landmarks[17].y * h]
    )
    mouth_ratio = mouth_height / (mouth_width + 1e-6)
    features.append(mouth_ratio)
    
    # 4. Jaw clenching (jaw width)
    jaw_width = euclidean_distance(
        [landmarks[172].x * w, landmarks[172].y * h],
        [landmarks[397].x * w, landmarks[397].y * h]
    )
    features.append(jaw_width)
    
    # 5. Eye squinting (modified EAR)
    left_ear = calculate_EAR(LEFT_EYE, landmarks, w, h)
    right_ear = calculate_EAR(RIGHT_EYE, landmarks, w, h)
    features.extend([left_ear, right_ear])
    
    return np.array(features)

