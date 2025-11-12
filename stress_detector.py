import numpy as np
from sklearn.ensemble import RandomForestClassifier
from collections import deque
import time

class StressDetector:
    def __init__(self):
        self.model = self._create_baseline_model()
        self.feature_buffer = deque(maxlen=100)  # Store last 100 feature sets
        self.stress_scores = deque(maxlen=50)    # Store last 50 stress scores
        self.baseline_features = None
        self.calibration_samples = []
        
    def _create_baseline_model(self):
        """Create a simple baseline model (will be replaced with trained model)"""
        # For demo purposes - in production, load pre-trained model
        model = RandomForestClassifier(n_estimators=50, random_state=42)
        
        # Create synthetic training data (replace with real data)
        # Features: [brow_dist_l, brow_dist_r, brow_gap, mouth_ratio, jaw_width, left_ear, right_ear]
        
        # Relaxed samples (larger brow distance, relaxed mouth, higher EAR)
        X_relaxed = np.random.randn(100, 7) * [5, 5, 10, 0.1, 5, 0.05, 0.05] + \
                    [45, 45, 100, 0.3, 120, 0.25, 0.25]
        y_relaxed = np.zeros(100)
        
        # Stressed samples (smaller brow distance, tight mouth, lower EAR)
        X_stressed = np.random.randn(100, 7) * [3, 3, 8, 0.08, 4, 0.03, 0.03] + \
                     [35, 35, 80, 0.15, 110, 0.20, 0.20]
        y_stressed = np.ones(100)
        
        X_train = np.vstack([X_relaxed, X_stressed])
        y_train = np.hstack([y_relaxed, y_stressed])
        
        model.fit(X_train, y_train)
        return model
    
    def add_calibration_sample(self, features, is_stressed):
        """Add calibration sample for personalization"""
        self.calibration_samples.append((features, is_stressed))
        
        if len(self.calibration_samples) >= 20:
            self._retrain_model()
    
    def _retrain_model(self):
        """Retrain model with calibration data"""
        if len(self.calibration_samples) < 20:
            return
        
        X = np.array([s[0] for s in self.calibration_samples])
        y = np.array([s[1] for s in self.calibration_samples])
        
        self.model.fit(X, y)
        print(f"Model retrained with {len(self.calibration_samples)} samples")
    
    def calculate_stress(self, features):
        """Calculate stress level from facial features"""
        if features is None or len(features) != 7:
            return 0
        
        self.feature_buffer.append(features)
        
        # Need some history for stable prediction
        if len(self.feature_buffer) < 10:
            return 0
        
        # Predict stress probability
        features_reshaped = features.reshape(1, -1)
        stress_prob = self.model.predict_proba(features_reshaped)[0][1]
        
        # Convert to 0-100 scale
        stress_score = int(stress_prob * 100)
        
        # Smooth using recent history
        self.stress_scores.append(stress_score)
        smoothed_score = int(np.mean(self.stress_scores))
        
        return smoothed_score
    
    def get_stress_level_text(self, score):
        """Convert stress score to text"""
        if score < 30:
            return "Low"
        elif score < 60:
            return "Medium"
        else:
            return "High"

