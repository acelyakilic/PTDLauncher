import tkinter as tk
from tkinter import ttk, messagebox
import sys
import os
import traceback

# Import from our modules
from utils import get_resource_path, ensure_directories, logger
from sound_manager import init_sound, play_sound, set_sound_enabled
from updater import show_update_window
from ui import create_main_ui
from settings_manager import load_settings

def main():
    try:
        # Ensure required directories exist
        logger.info("Starting PTD Launcher")
        ensure_directories()
        
        # Initialize pygame for sound
        sound_initialized = init_sound()
        
        # Load settings
        settings = load_settings()
        logger.info(f"Loaded settings: {settings}")
        
        # Apply settings
        set_sound_enabled(settings.get("sound_enabled", True))

        # Create main window
        root = tk.Tk()
        root.title("PTD Launcher")
        
        # Set icon with error handling
        try:
            icon_path = get_resource_path("favicon.ico")
            if os.path.exists(icon_path):
                root.iconbitmap(icon_path)
        except Exception as e:
            logger.warning(f"Could not set icon: {str(e)}")
            
        root.configure(bg="#e5e5e5")
        root.geometry("490x335")  # Increased height to accommodate all buttons
        root.resizable(False, False)
        
        # Play startup sound if sound is initialized and enabled
        if sound_initialized:
            play_sound("on.mp3")  # This will respect the sound_enabled setting

        # Center window on screen
        screen_width = root.winfo_screenwidth()
        screen_height = root.winfo_screenheight()
        window_width = 490
        window_height = 335  # Updated to match the new height
        position_top = int((screen_height - window_height) / 2)
        position_right = int((screen_width - window_width) / 2)
        root.geometry(f'{window_width}x{window_height}+{position_right}+{position_top}')

        # Show update window on startup
        root.after(500, lambda: show_update_window(root))

        # Create the main UI
        create_main_ui(root)

        # Start the main loop
        root.mainloop()
    except Exception as e:
        error_msg = f"Error starting PTD Launcher: {str(e)}\n\n{traceback.format_exc()}"
        print(error_msg)
        try:
            messagebox.showerror("PTD Launcher Error", f"An error occurred while starting the application:\n\n{str(e)}")
        except:
            # If even the messagebox fails, try a basic console output
            print("CRITICAL ERROR:", error_msg)

if __name__ == "__main__":
    main()
