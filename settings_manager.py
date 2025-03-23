import json
import os
import tkinter as tk
from tkinter import ttk, messagebox, filedialog
from utils import get_resource_path, get_file_path, logger
from sound_manager import set_sound_enabled
from version_manager import load_versions, save_versions

# Default settings configuration
DEFAULT_SETTINGS = {
    "sound_enabled": True,
    "custom_flash_player": False
}

def select_flash_player():
    try:
        logger.info("Selecting custom Flash Player executable")
        file_path = filedialog.askopenfilename(
            title="Select Flash Player Executable",
            filetypes=[("Executable files", "*.exe"), ("All files", "*.*")]
        )
        
        if not file_path or not os.path.exists(file_path):
            logger.info("Flash Player selection cancelled or file doesn't exist")
            if file_path:
                messagebox.showerror("Error", "The selected file does not exist.")
            return None
            
        # Copy the selected file to the files directory
        try:
            destination = get_file_path("flashplayer_sa.exe")
            with open(file_path, 'rb') as src_file, open(destination, 'wb') as dst_file:
                dst_file.write(src_file.read())
            
            logger.info(f"Copied custom Flash Player from {file_path} to {destination}")
            
            # Update the version in versions.json
            versions = load_versions()
            versions["flash_player"] = "custom"
            save_versions(versions)
            
            messagebox.showinfo("Success", "Custom Flash Player has been set successfully.")
            return destination
        except Exception as e:
            logger.error(f"Error copying Flash Player: {str(e)}")
            messagebox.showerror("Error", f"Could not set custom Flash Player: {str(e)}")
            return None
    except Exception as e:
        logger.error(f"Error in select_flash_player: {str(e)}")
        messagebox.showerror("Error", f"An error occurred: {str(e)}")
        return None
        
def load_settings():
    try:
        # First try to load from user_settings.json (writable location)
        user_settings_path = get_file_path("user_settings.json")
        settings = DEFAULT_SETTINGS.copy()
        
        # Check if user settings file exists
        if os.path.exists(user_settings_path):
            try:
                with open(user_settings_path, 'r') as f:
                    loaded_settings = json.load(f)
                    
                if isinstance(loaded_settings, dict):
                    # Ensure all required keys exist
                    for key in DEFAULT_SETTINGS:
                        if key not in loaded_settings:
                            loaded_settings[key] = DEFAULT_SETTINGS[key]
                    logger.info(f"Loaded settings from {user_settings_path}")
                    return loaded_settings
                else:
                    logger.warning("user_settings.json is not valid, trying default settings")
            except Exception as e:
                logger.error(f"Error loading user settings: {str(e)}, trying default settings")
        
        # If user settings don't exist or couldn't be loaded, try default settings
        settings_path = get_resource_path("settings.json")
        if os.path.exists(settings_path):
            try:
                with open(settings_path, 'r') as f:
                    loaded_settings = json.load(f)
                    
                if isinstance(loaded_settings, dict):
                    # Ensure all required keys exist
                    for key in DEFAULT_SETTINGS:
                        if key not in loaded_settings:
                            loaded_settings[key] = DEFAULT_SETTINGS[key]
                    # Save to user settings for future use
                    save_settings(loaded_settings)
                    return loaded_settings
                else:
                    logger.warning("settings.json is not valid, using defaults")
            except Exception as e:
                logger.error(f"Error loading default settings: {str(e)}")
        
        # If all else fails, use default settings and save them
        logger.info("Creating new settings file")
        save_settings(settings)
        return settings
    except Exception as e:
        logger.error(f"Unexpected error in load_settings: {str(e)}")
        return DEFAULT_SETTINGS.copy()

def save_settings(settings):
    try:
        if not isinstance(settings, dict):
            logger.error("Cannot save settings: not a valid dictionary")
            return False
            
        # Use get_file_path instead of get_resource_path to ensure settings are saved to a writable location
        settings_path = get_file_path("user_settings.json")
        with open(settings_path, 'w') as f:
            json.dump(settings, f, indent=4)
        logger.info(f"Saved settings to {settings_path} successfully")
        return True
    except Exception as e:
        logger.error(f"Error saving settings: {str(e)}")
        return False

def reset_settings():
    try:
        settings = DEFAULT_SETTINGS.copy()
        save_settings(settings)
        logger.info("Reset settings to default values")
        return settings
    except Exception as e:
        logger.error(f"Error resetting settings: {str(e)}")
        return DEFAULT_SETTINGS.copy()

def show_settings_window(root):
    try:
        logger.info("Opening settings window")
        current_settings = load_settings()
        
        settings_window = tk.Toplevel()
        settings_window.title("PTD Launcher Settings")
        
        # Set icon if available
        try:
            icon_path = get_resource_path("favicon.ico")
            if os.path.exists(icon_path):
                settings_window.iconbitmap(icon_path)
        except Exception as e:
            logger.warning(f"Could not set window icon: {str(e)}")
            
        # Configure window
        window_width, window_height = 400, 200
        settings_window.geometry(f"{window_width}x{window_height}")
        settings_window.resizable(False, False)
        
        # Center window
        x = int((settings_window.winfo_screenwidth() - window_width) / 2)
        y = int((settings_window.winfo_screenheight() - window_height) / 2)
        settings_window.geometry(f"{window_width}x{window_height}+{x}+{y}")
        
        # Settings frame
        settings_frame = ttk.Frame(settings_window, padding=20)
        settings_frame.pack(fill=tk.BOTH, expand=True)
        
        ttk.Label(settings_frame, text="PTD Launcher Settings", font=("Arial", 14, "bold")).pack(pady=(0, 10))
        
        # Flash Player section
        flash_frame = ttk.Frame(settings_frame)
        flash_frame.pack(fill=tk.X, pady=5)
        
        flash_status_var = tk.StringVar(value="Custom Flash Player" if current_settings.get("custom_flash_player") else "Default Flash Player")
        ttk.Label(flash_frame, text="Flash Player:").pack(side=tk.LEFT, padx=(0, 10))
        ttk.Label(flash_frame, textvariable=flash_status_var).pack(side=tk.LEFT, padx=(0, 10))
        
        def select_custom_flash():
            if select_flash_player():
                current_settings["custom_flash_player"] = True
                save_settings(current_settings)
                flash_status_var.set("Custom Flash Player")
        
        ttk.Button(flash_frame, text="Select Custom Flash Player", command=select_custom_flash).pack(side=tk.LEFT)
        
        # Sound toggle
        sound_var = tk.BooleanVar(value=current_settings.get("sound_enabled", True))
        sound_frame = ttk.Frame(settings_frame)
        sound_frame.pack(fill=tk.X, pady=5)
        
        def toggle_sound():
            set_sound_enabled(sound_var.get())
            current_settings["sound_enabled"] = sound_var.get()
            save_settings(current_settings)
            logger.info(f"Sound {'enabled' if sound_var.get() else 'disabled'}")
        
        ttk.Label(sound_frame, text="Sound Effects:").pack(side=tk.LEFT, padx=(0, 10))
        ttk.Checkbutton(sound_frame, variable=sound_var, text="Enabled", command=toggle_sound).pack(side=tk.LEFT)
        
        # Reset button
        def reset_all_settings():
            if messagebox.askyesno("Reset Settings", "Are you sure you want to reset all settings to default?"):
                new_settings = reset_settings()
                sound_var.set(new_settings["sound_enabled"])
                flash_status_var.set("Default Flash Player")
                set_sound_enabled(new_settings["sound_enabled"])
                messagebox.showinfo("Reset", "Settings have been reset to defaults.")
        
        ttk.Button(settings_frame, text="Reset All Settings", command=reset_all_settings).pack(pady=10)
        
        # Make window modal
        settings_window.transient(root)
        settings_window.grab_set()
        settings_window.protocol("WM_DELETE_WINDOW", lambda: settings_window.destroy())
        
        # Apply current settings
        set_sound_enabled(current_settings.get("sound_enabled", True))
        
        root.wait_window(settings_window)
    except Exception as e:
        logger.error(f"Error showing settings window: {str(e)}")
        messagebox.showerror("Settings Error", f"An error occurred: {str(e)}")