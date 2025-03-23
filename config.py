#!/usr/bin/env python3
import os
import json
import platform
import sys
from tkinter import messagebox
from base_manager import BaseManager
from pathlib import Path

def resource_path(relative_path):
    """Get absolute path to resource, works for dev and for PyInstaller"""
    try:
        # PyInstaller creates a temp folder and stores path in _MEIPASS
        base_path = sys._MEIPASS
    except Exception:
        base_path = os.path.abspath(".")
    
    return os.path.join(base_path, relative_path)

class ConfigManager(BaseManager):
    def __init__(self, status_callback=None):
        super().__init__(status_callback)
        self.config = None
        self.version = None
        self.games_dir = None
        self.settings = {}
    
    def _get_os_specific_path(self, subdir):
        """Get OS-specific path for application data"""
        system = platform.system()
        if system == "Windows":
            return os.path.join(os.getenv("APPDATA"), "PTD Launcher", subdir)
        elif system == "Darwin":  # macOS
            return os.path.join(os.path.expanduser("~/Library/Application Support"), "PTD Launcher", subdir)
        elif system == "Linux":
            return os.path.join(os.path.expanduser("~/.local/share"), "PTD Launcher", subdir)
        else:
            self.show_dialog(None, "Error", "Unsupported operating system", dialog_type="error")
            sys.exit(1)
    
    def load_config(self):
        """Load configuration from config.json"""
        try:
            config_path = resource_path("resources/config.json")
            with open(config_path, "r") as f:
                self.config = json.load(f)
            
            # Get games directory path based on OS
            self.games_dir = self._get_os_specific_path("Games")
            
            # Create games directory if it doesn't exist
            os.makedirs(self.games_dir, exist_ok=True)
            
            # Load version information from games directory
            version_path = os.path.join(self.games_dir, "version.json")
            
            # If version.json doesn't exist in games directory but exists in resources, move it
            version_resource_path = resource_path("resources/version.json")
            if not os.path.exists(version_path) and os.path.exists(version_resource_path):
                try:
                    with open(version_resource_path, "r") as f:
                        version_data = json.load(f)
                    
                    with open(version_path, "w") as f:
                        json.dump(version_data, f, indent=4)
                except Exception:
                    # If moving fails, use default version data
                    pass
            
            # Load version information or use defaults
            if os.path.exists(version_path):
                with open(version_path, "r") as f:
                    self.version = json.load(f)
            else:
                # Default versions
                self.version = {
                    "flash_player": "",
                    "games": {
                        "PTD1": "",
                        "PTD1RF": "",
                        "PTD1_Hacked": "",
                        "PTD2": "",
                        "PTD2_Hacked": "",
                        "PTD3": "",
                        "PTD3_Hacked": ""
                    }
                }
                # Save default version file
                with open(version_path, "w") as f:
                    json.dump(self.version, f, indent=4)
            
            # Load settings from settings.json
            self.settings = self.load_settings()
            
            return True
                
        except Exception as e:
            self.show_dialog(None, "Error", f"Failed to load configuration: {str(e)}", dialog_type="error")
            sys.exit(1)
            return False
    
    def save_version_info(self):
        """Save version information to file"""
        try:
            version_path = os.path.join(self.games_dir, "version.json")
            with open(version_path, "w") as f:
                json.dump(self.version, f, indent=4)
            return True
        except Exception as e:
            print(f"Error saving version info: {str(e)}")
            return False
    
    def get_flash_player_path(self):
        """Get the path to Flash Player based on OS"""
        # Check if there's a custom path in settings
        if "flash_player_path" in self.settings and os.path.exists(self.settings["flash_player_path"]):
            return self.settings["flash_player_path"]
        
        # Otherwise use the default path
        system = platform.system()
        flash_dir = self.get_flash_dir()
        
        if not flash_dir:
            return None
            
        if system == "Windows":
            return os.path.join(flash_dir, self.config["flash_player"]["windows"]["filename"])
        elif system == "Darwin":  # macOS
            return os.path.join(flash_dir, self.config["flash_player"]["macos"]["filename"])
        elif system == "Linux":
            return os.path.join(flash_dir, self.config["flash_player"]["linux"]["filename"])
        else:
            return None
    
    def get_flash_dir(self):
        """Get the directory for Flash Player based on OS"""
        return self._get_os_specific_path("Flash")
    
    def get_flash_download_info(self):
        """Get Flash Player download information based on OS"""
        system = platform.system()
        flash_dir = self.get_flash_dir()
        
        if not flash_dir:
            return None
            
        if system == "Windows":
            info = {
                "url": self.config["flash_player"]["windows"]["primary_url"],
                "filename": self.config["flash_player"]["windows"]["filename"],
                "full_path": os.path.join(flash_dir, self.config["flash_player"]["windows"]["filename"])
            }
            # Add fallback URL if available
            if "fallback_url" in self.config["flash_player"]["windows"]:
                info["fallback_url"] = self.config["flash_player"]["windows"]["fallback_url"]
            return info
        elif system == "Darwin":  # macOS
            info = {
                "url": self.config["flash_player"]["macos"]["primary_url"],
                "filename": "flash_player.dmg",
                "full_path": os.path.join(flash_dir, "flash_player.dmg"),
                "app_name": self.config["flash_player"]["macos"]["filename"]
            }
            # Add fallback URL if available
            if "fallback_url" in self.config["flash_player"]["macos"]:
                info["fallback_url"] = self.config["flash_player"]["macos"]["fallback_url"]
            return info
        elif system == "Linux":
            info = {
                "url": self.config["flash_player"]["linux"]["primary_url"],
                "filename": "flash_player.tar.gz",
                "full_path": os.path.join(flash_dir, "flash_player.tar.gz"),
                "bin_name": self.config["flash_player"]["linux"]["filename"]
            }
            # Add fallback URL if available
            if "fallback_url" in self.config["flash_player"]["linux"]:
                info["fallback_url"] = self.config["flash_player"]["linux"]["fallback_url"]
            return info
        else:
            return None
    
    def save_settings(self, settings=None):
        """Save settings to settings.json in the Flash directory"""
        try:
            # Get the flash directory
            flash_dir = self.get_flash_dir()
            
            # Create the directory if it doesn't exist
            os.makedirs(flash_dir, exist_ok=True)
            
            # Create settings object if not provided
            if settings is None:
                settings = {}
            
            # Add Flash Player settings
            system = platform.system()
            if system == "Windows":
                settings["flash_player_path"] = os.path.join(flash_dir, 
                                                           self.config["flash_player"]["windows"]["filename"])
            elif system == "Darwin":  # macOS
                settings["flash_player_path"] = os.path.join(flash_dir, 
                                                           self.config["flash_player"]["macos"]["filename"])
            elif system == "Linux":
                settings["flash_player_path"] = os.path.join(flash_dir, 
                                                           self.config["flash_player"]["linux"]["filename"])
            
            # Save settings to file
            settings_path = os.path.join(flash_dir, "settings.json")
            with open(settings_path, "w") as f:
                json.dump(settings, f, indent=4)
            
            return True
        except Exception as e:
            print(f"Error saving settings: {str(e)}")
            return False
    
    def load_settings(self):
        """Load settings from settings.json in the Flash directory"""
        try:
            # Get the flash directory
            flash_dir = self.get_flash_dir()
            
            # Check if settings file exists
            settings_path = os.path.join(flash_dir, "settings.json")
            if not os.path.exists(settings_path):
                return {}
            
            # Load settings from file
            with open(settings_path, "r") as f:
                settings = json.load(f)
            
            return settings
        except Exception as e:
            print(f"Error loading settings: {str(e)}")
            return {}
