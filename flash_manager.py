#!/usr/bin/env python3
import os
import platform
import subprocess
import requests
import tempfile
import shutil
from tkinter import messagebox, Toplevel
import tarfile
from base_manager import BaseManager

class FlashManager(BaseManager):
    def __init__(self, config_manager, status_callback=None):
        super().__init__(status_callback)
        self.config_manager = config_manager
        self.is_downloading = False
    
    def is_download_in_progress(self):
        """Check if a download is currently in progress"""
        return self.is_downloading
    
    def check_flash_player(self, parent=None):
        """Check if Flash Player is installed and download if needed"""
        flash_path = self.config_manager.get_flash_player_path()
        
        # Check if Flash Player exists
        if not flash_path or not os.path.exists(flash_path):
            result = self.show_dialog(parent, "Flash Player", "Flash Player is not installed. Do you want to download it now?")
            if result:
                return self.download_flash_player(parent)
            else:
                return None
        
        return flash_path
    
    def download_flash_player(self, parent=None):
        """Download Flash Player for the current OS"""
        # If already downloading, don't start another download
        if self.is_downloading:
            return None
            
        self.is_downloading = True
        self.set_status("Downloading Flash Player...")
        
        # Create directory for Flash Player
        flash_dir = self.config_manager.get_flash_dir()
        if not flash_dir:
            self.show_dialog(parent, "Error", "Unsupported operating system", dialog_type="error")
            self.is_downloading = False
            return None
        
        os.makedirs(flash_dir, exist_ok=True)
        
        # Download Flash Player
        try:
            download_info = self.config_manager.get_flash_download_info()
            if not download_info:
                self.show_dialog(parent, "Error", "Unsupported operating system", dialog_type="error")
                self.is_downloading = False
                return None
            
            # Download the file
            with requests.get(download_info["url"], stream=True) as r:
                r.raise_for_status()
                with open(download_info["full_path"], 'wb') as f:
                    for chunk in r.iter_content(chunk_size=8192):
                        f.write(chunk)
            
            # Process the downloaded file based on OS
            system = platform.system()
            if system == "Darwin":  # macOS
                # Mount DMG and copy the app
                mount_point = tempfile.mkdtemp()
                subprocess.run(["hdiutil", "attach", download_info["full_path"], "-mountpoint", mount_point])
                app_path = os.path.join(mount_point, download_info["app_name"])
                dest_path = os.path.join(flash_dir, download_info["app_name"])
                shutil.copytree(app_path, dest_path)
                subprocess.run(["hdiutil", "detach", mount_point])
                shutil.rmtree(mount_point)
                os.remove(download_info["full_path"])
            elif system == "Linux":
                # Extract tar.gz file
                with tarfile.open(download_info["full_path"], "r:gz") as tar:
                    tar.extractall(path=flash_dir)
                os.remove(download_info["full_path"])
                # Make the binary executable
                flash_bin = os.path.join(flash_dir, download_info["bin_name"])
                os.chmod(flash_bin, 0o755)
            
            self.set_status("Flash Player downloaded successfully")
            self.show_dialog(parent, "Success", "Flash Player has been downloaded successfully", dialog_type="info")
            
            # Update version information
            self.config_manager.version["flash_player"] = self.config_manager.config["flash_player"]["fallback_version"]
            self.config_manager.save_version_info()
            
            # Reset downloading flag
            self.is_downloading = False
            
            return self.config_manager.get_flash_player_path()
            
        except Exception as e:
            self.set_status("Failed to download Flash Player")
            self.show_dialog(parent, "Error", f"Failed to download Flash Player: {str(e)}", dialog_type="error")
            
            # Reset downloading flag even if there's an error
            self.is_downloading = False
            
            return None
    
    def launch_game(self, game_path, parent=None):
        """Launch a game with Flash Player"""
        try:
            flash_path = self.check_flash_player(parent)
            if not flash_path:
                return False
            
            system = platform.system()
            cmd = None
            
            if system == "Windows":
                cmd = [flash_path, game_path]
            elif system == "Darwin":  # macOS
                cmd = ["open", "-a", flash_path, game_path]
            elif system == "Linux":
                cmd = [flash_path, game_path]
            else:
                self.show_dialog(parent, "Error", "Unsupported operating system", dialog_type="error")
                return False
                
            if cmd:
                subprocess.Popen(cmd)
                return True
            
            return False
            
        except Exception as e:
            self.show_dialog(parent, "Error", f"Failed to launch game: {str(e)}", dialog_type="error")
            return False
