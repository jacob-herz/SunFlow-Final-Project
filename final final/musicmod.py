import pygame
import os
from threading import Thread
import time

class MusicPlayer:
    def __init__(self):
        pygame.mixer.init()
        self.current_song = None
        self.is_playing = False
        self.volume = 1.0
        self.play_thread = None

    def load_song(self, file_path):
        try:
            pygame.mixer.music.load(file_path)
            self.current_song = file_path
            return True
        except pygame.error as e:
            print(f"Error loading audio file: {e}")
            return False

    def play(self, file_path=None):
        if file_path and file_path != self.current_song:
            if not self.load_song(file_path):
                return False
        
        pygame.mixer.music.play()
        self.is_playing = True
        self.play_thread = Thread(target=self._monitor_playback)
        self.play_thread.daemon = True
        self.play_thread.start()

    def _monitor_playback(self):
        while self.is_playing and pygame.mixer.music.get_busy():
            time.sleep(0.1)
        self.is_playing = False

    def pause(self):
        if self.is_playing:
            pygame.mixer.music.pause()
            self.is_playing = False

    def unpause(self):
        pygame.mixer.music.unpause()
        self.is_playing = True

    def stop(self):
        pygame.mixer.music.stop()
        self.is_playing = False

    def set_volume(self, volume):
        self.volume = max(0.0, min(1.0, volume))
        pygame.mixer.music.set_volume(self.volume)

    def get_current_song(self):
        if self.current_song:
            return os.path.basename(self.current_song)
        return None

    def is_song_playing(self):
        return self.is_playing

    def cleanup(self):
        pygame.mixer.quit()

if __name__ == "__main__":
    try:
        # Create music player instance
        player = MusicPlayer()
        
        # Play a song
        print("kahoot.mp3...")
        player.play("dutchmusic.mp3")
        
        # Keep the main thread running while music plays
        while player.is_song_playing():
            time.sleep(0.1)
            
            # You can add keyboard controls here if needed
            # For example: check for keyboard input to pause/stop
        
    except KeyboardInterrupt:
        print("\nStopping playback...")
        player.stop()
        player.cleanup()
    except Exception as e:
        print(f"An error occurred: {e}")
        player.cleanup()
