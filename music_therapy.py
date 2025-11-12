import pygame
import os
import random

class MusicTherapy:
    def __init__(self, music_folder="assets/music"):
        self.music_folder = music_folder
        self.current_stress_level = "Low"
        self.is_playing = False
        self.current_track = None
        
        # Music categories
        self.music_library = {
            "Low": [],      # Ambient/background
            "Medium": [],   # Calming music
            "High": []      # Active relaxation
        }
        
        self._load_music_library()
        
    def _load_music_library(self):
        """Load available music files"""
        if not os.path.exists(self.music_folder):
            os.makedirs(self.music_folder)
            print(f"Created {self.music_folder} - Please add music files!")
            return
        
        # Scan for music files
        for file in os.listdir(self.music_folder):
            if file.endswith(('.mp3', '.wav', '.ogg')):
                full_path = os.path.join(self.music_folder, file)
                
                # Categorize by filename keywords
                file_lower = file.lower()
                if any(word in file_lower for word in ['calm', 'relax', 'ambient', 'low']):
                    self.music_library["Low"].append(full_path)
                elif any(word in file_lower for word in ['medium', 'peace', 'nature']):
                    self.music_library["Medium"].append(full_path)
                elif any(word in file_lower for word in ['high', 'meditation', 'deep', 'binaural']):
                    self.music_library["High"].append(full_path)
                else:
                    # Default to medium
                    self.music_library["Medium"].append(full_path)
        
        print(f"Music library loaded: {sum(len(v) for v in self.music_library.values())} tracks")
    
    def update_stress_level(self, stress_score, stress_text):
        """Update music based on stress level"""
        new_level = stress_text
        
        # Start/change music if stress level changed
        if new_level != self.current_stress_level:
            self.current_stress_level = new_level
            
            if stress_score >= 40:  # Medium or High stress
                self.play_relaxation_music()
            else:
                self.stop_music()
    
    def play_relaxation_music(self):
        """Play appropriate music for current stress level"""
        if not self.music_library[self.current_stress_level]:
            print(f"No music available for {self.current_stress_level} stress level")
            return
        
        # Choose random track from appropriate category
        track = random.choice(self.music_library[self.current_stress_level])
        
        if self.current_track != track:
            try:
                pygame.mixer.music.load(track)
                pygame.mixer.music.play(-1)  # Loop
                pygame.mixer.music.set_volume(0.5)
                self.is_playing = True
                self.current_track = track
                print(f"Playing: {os.path.basename(track)}")
            except Exception as e:
                print(f"Error playing music: {e}")
    
    def stop_music(self):
        """Stop music playback"""
        if self.is_playing:
            pygame.mixer.music.stop()
            self.is_playing = False
            self.current_track = None

