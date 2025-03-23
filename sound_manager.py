import pygame
import os
from utils import get_resource_path, logger

# Global variables with proper naming
sound_cache = {}
sound_enabled = True

def init_sound():
    try:
        pygame.mixer.init()
        return True
    except pygame.error:
        logger.warning("Sound initialization failed")
        return False

def set_sound_enabled(enabled):
    global sound_enabled
    sound_enabled = enabled
    logger.info(f"Sound {'enabled' if enabled else 'disabled'}")

def get_sound_enabled():
    return sound_enabled

def play_sound(file):
    if not sound_enabled:
        return
        
    try:
        if file not in sound_cache:
            sound_path = get_resource_path(file)
            if not os.path.exists(sound_path):
                logger.warning(f"Sound file not found: {file}")
                return
            sound_cache[file] = pygame.mixer.Sound(sound_path)
        
        sound_cache[file].play()
    except Exception as e:
        logger.error(f"Error playing sound {file}: {str(e)}")