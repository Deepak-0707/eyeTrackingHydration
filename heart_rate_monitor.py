import numpy as np
from scipy import signal
from scipy.fft import fft
from collections import deque
import cv2

class HeartRateMonitor:
    def __init__(self, fps=30, buffer_seconds=15):
        self.fps = fps
        self.buffer_size = fps * buffer_seconds
        self.rgb_buffer = deque(maxlen=self.buffer_size)
        self.time_buffer = deque(maxlen=self.buffer_size)
        self.current_hr = 0
        self.hr_history = deque(maxlen=20)
        self.calibration_offset =10#Add offset to bring readings to normal range 
        
    def add_frame(self, frame, face_landmarks, w, h):
        """Extract ROI and add to buffer"""
        if face_landmarks is None:
            return
        
        # Extract forehead region (best for rPPG)
        forehead_indices = [10, 338, 297, 332, 284, 251, 389, 356, 454, 323, 
                           361, 288, 397, 365, 379, 378, 400, 377, 152, 148, 
                           176, 149, 150, 136, 172, 58, 132, 93, 234, 127]
        
        # Get forehead coordinates
        forehead_points = []
        for idx in forehead_indices:
            x = int(face_landmarks.landmark[idx].x * w)
            y = int(face_landmarks.landmark[idx].y * h)
            forehead_points.append([x, y])
        
        forehead_points = np.array(forehead_points)
        
        # Create mask for forehead region
        mask = np.zeros((h, w), dtype=np.uint8)
        cv2.fillConvexPoly(mask, forehead_points, 255)
        
        # Extract mean RGB values from forehead
        mean_rgb = cv2.mean(frame, mask=mask)[:3]
        
        self.rgb_buffer.append(mean_rgb)
        self.time_buffer.append(cv2.getTickCount() / cv2.getTickFrequency())
    
    def calculate_heart_rate(self):
        """Calculate heart rate using rPPG with improved calibration"""
        if len(self.rgb_buffer) < self.fps * 10:  # Need at least 10 seconds
            return self.current_hr
        
        # Extract green channel (best for rPPG)
        green_signal = np.array([rgb[1] for rgb in self.rgb_buffer])
        
        # Detrend
        detrended = signal.detrend(green_signal)
        
        # Bandpass filter (0.8-3.5 Hz = 48-210 BPM) - adjusted range
        sos = signal.butter(4, [0.8, 3.5], btype='band', fs=self.fps, output='sos')
        filtered = signal.sosfilt(sos, detrended)
        
        # Apply Hamming window
        windowed = filtered * signal.windows.hamming(len(filtered))
        
        # FFT
        fft_data = fft(windowed)
        frequencies = np.fft.fftfreq(len(windowed), 1/self.fps)
        
        # Find peak in valid range (focus on 60-100 BPM range)
        valid_idx = np.where((frequencies >= 1.0) & (frequencies <= 2.0))[0]  # 60-120 BPM
        if len(valid_idx) == 0:
            return self.current_hr
        
        peak_idx = valid_idx[np.argmax(np.abs(fft_data[valid_idx]))]
        peak_freq = frequencies[peak_idx]
        
        # Convert to BPM with calibration
        heart_rate = abs(peak_freq * 60) + self.calibration_offset
        
        # Validate range (60-120 is more realistic for resting/computer work)
        if 55 <= heart_rate <= 120:
            self.hr_history.append(heart_rate)
            # Median filter for stability
            self.current_hr = int(np.median(self.hr_history))
        
        return self.current_hr
    
    def get_hr_variability(self):
        """Calculate HRV (simplified)"""
        if len(self.hr_history) < 5:
            return 0
        
        return int(np.std(self.hr_history))