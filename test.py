"""
Function to play an MP3 file on a connected Bluetooth speaker when certain parameters are met.
Requires: pip install pygame
"""

import pygame
import os
import time

def play_audio_alert(mp3_file_path, condition_met=True, volume=0.8):
    """
    Play an MP3 file on the default audio output (Bluetooth speaker if connected).
    
    Parameters:
    -----------
    mp3_file_path : str
        Path to the .mp3 file to play
    condition_met : bool
        Whether the condition to play audio is met (default: True)
    volume : float
        Volume level from 0.0 to 1.0 (default: 0.8)
    
    Returns:
    --------
    bool : True if audio played successfully, False otherwise
    
    Example usage:
    --------------
    # Play alert when hat is detected
    if hat_detected:
        play_audio_alert("alerts/hat_warning.mp3", condition_met=True, volume=0.9)
    """
    
    if not condition_met:
        print("Condition not met, skipping audio playback")
        return False
    
    # Check if file exists
    if not os.path.exists(mp3_file_path):
        print(f"Error: Audio file not found at {mp3_file_path}")
        return False
    
    try:
        # Initialize pygame mixer if not already initialized
        if not pygame.mixer.get_init():
            pygame.mixer.init()
        
        # Load and play the MP3
        pygame.mixer.music.load(mp3_file_path)
        pygame.mixer.music.set_volume(volume)
        pygame.mixer.music.play()
        
        print(f"Playing audio: {os.path.basename(mp3_file_path)}")
        
        # Wait for the audio to finish playing
        while pygame.mixer.music.get_busy():
            time.sleep(0.1)
        
        return True
        
    except Exception as e:
        print(f"Error playing audio: {e}")
        return False

# Example usage with detection logic
if __name__ == "__main__":
    # Test the function
    # Replace with your actual MP3 file path
    audio_file = "alert.mp3"  # Put your MP3 file here
    
    # Example condition: simulate hat detection
    hat_detected = True  # Replace with actual detection logic
    confidence = 0.85
    
    # Play alert if hat is detected with confidence > 0.7
    if hat_detected and confidence > 0.7:
        play_audio_alert(audio_file, condition_met=True, volume=0.8)
