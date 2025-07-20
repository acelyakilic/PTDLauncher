#!/usr/bin/env python3
import os
import platform
import subprocess
from tkinter import messagebox, Toplevel
from base_manager import BaseManager

class FlashManager(BaseManager):
    def __init__(self, config_manager, download_manager=None, status_callback=None):
        super().__init__(status_callback)
        self.config_manager = config_manager
        self.download_manager = download_manager
    
    def is_download_in_progress(self):
        """Check if a download is currently in progress"""
        if self.download_manager:
            return self.download_manager.is_download_in_progress()
        return False
    
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
        """Download Flash Player using DownloadManager"""
        if self.download_manager:
            return self.download_manager.download_flash_player(parent)
        else:
            self.show_dialog(parent, "Error", "Download manager not available", dialog_type="error")
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
