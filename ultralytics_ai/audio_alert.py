"""
Audio alert module for playing MP3 files on Bluetooth speaker
Works with YOLO detection to trigger alerts based on detection results
"""

import pygame
import os
import time
from datetime import datetime

class AudioAlert:
    
    def __init__(self, cooldown_seconds=5):
        """
        Initialize the audio alert system
        
        Parameters:
        -----------
        cooldown_seconds : int
            Minimum seconds between alerts (prevents spam)
        """
        self.cooldown_seconds = cooldown_seconds
        self.last_played = 0
        pygame.mixer.init()
    
    def play_alert(self, mp3_file_path, volume=0.8, force=False):
        """
        Play an MP3 file on the default audio output (Bluetooth speaker if connected).
        
        Parameters:
        -----------
        mp3_file_path : str
            Path to the .mp3 file to play
        volume : float
            Volume level from 0.0 to 1.0 (default: 0.8)
        force : bool
            If True, ignore cooldown period
        
        Returns:
        --------
        bool : True if audio played successfully, False otherwise
        """
        
        # Check cooldown period
        current_time = time.time()
        if not force and (current_time - self.last_played) < self.cooldown_seconds:
            print(f"Cooldown active. Wait {self.cooldown_seconds - (current_time - self.last_played):.1f}s")
            return False
        
        # Check if file exists
        if not os.path.exists(mp3_file_path):
            print(f"Error: Audio file not found at {mp3_file_path}")
            return False
        
        try:
            # Load and play the MP3
            pygame.mixer.music.load(mp3_file_path)
            pygame.mixer.music.set_volume(volume)
            pygame.mixer.music.play()
            
            self.last_played = current_time
            timestamp = datetime.now().strftime("%H:%M:%S")
            print(f"[{timestamp}] 🔊 Playing alert: {os.path.basename(mp3_file_path)}")
            
            return True
            
        except Exception as e:
            print(f"Error playing audio: {e}")
            return False
    
    def wait_until_done(self):
        """Wait until current audio finishes playing"""
        while pygame.mixer.music.get_busy():
            time.sleep(0.1)
    
    def stop(self):
        """Stop currently playing audio"""
        pygame.mixer.music.stop()

if __name__ == "__main__":
    # Test the audio alert
    print("Testing audio alert system...")
    
    # Example: Create a test alert
    alert = AudioAlert(cooldown_seconds=3)
    
    # Test with a sample file (replace with your actual MP3)
    test_file = "alert.mp3"
    
    if os.path.exists(test_file):
        alert.play_alert(test_file, volume=0.7)
        alert.wait_until_done()
    else:
        print(f"Please create a test MP3 file named '{test_file}' to test the system")
