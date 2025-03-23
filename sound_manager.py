#!/usr/bin/env python3
import pygame
import os

class SoundManager:
    def __init__(self, config_manager=None):
        # Initialize pygame mixer for sound effects
        pygame.mixer.init()
        
        # Define sound files
        sound_files = {
            "on": "resources/on.mp3",
            "off": "resources/off.mp3",
            "opentab": "resources/opentab.mp3",
            "closetab": "resources/closetab.mp3"
        }
        
        # Load sounds lazily
        self.sounds = {}
        for sound_name, sound_path in sound_files.items():
            if os.path.exists(sound_path):
                try:
                    self.sounds[sound_name] = pygame.mixer.Sound(sound_path)
                except Exception as e:
                    print(f"Error loading sound {sound_name}: {str(e)}")
        
        # Load sound enabled setting from config if available
        self.enabled = True
        if config_manager:
            settings = config_manager.load_settings()
            if "sound_enabled" in settings:
                self.enabled = settings["sound_enabled"]
    
    def play_sound(self, sound_name):
        """Play a sound effect"""
        if not self.enabled or sound_name not in self.sounds:
            return
            
        try:
            self.sounds[sound_name].play()
        except Exception as e:
            print(f"Error playing sound: {str(e)}")
    
    def set_enabled(self, enabled):
        """Enable or disable sound effects"""
        self.enabled = enabled
