#!/usr/bin/env python3
import os
import time
from tkinter import messagebox
from base_manager import BaseManager

class GameManager(BaseManager):
    def __init__(self, config_manager, flash_manager, download_manager=None, status_callback=None, update_manager=None):
        super().__init__(status_callback)
        self.config_manager = config_manager
        self.flash_manager = flash_manager
        self.download_manager = download_manager
        self._update_manager = update_manager
    
    def set_update_manager(self, update_manager):
        """Set the update manager reference to avoid circular imports"""
        self._update_manager = update_manager
    
    def download_game(self, game, parent=None):
        """Download or update a game using DownloadManager"""
        # Use the download manager if it's available
        if self.download_manager:
            return self.download_manager.download_game(game, parent)
        elif self._update_manager:
            # Fallback to update manager for backward compatibility
            return self._update_manager.download_game(game, parent=parent)
        else:
            self.set_status("Download manager not available")
            return None
    
    def find_game_path(self, game):
        """Find the path to the latest version of a game"""
        try:
            games_dir = self.config_manager.games_dir
            
            # Create a list to store potential paths to check
            paths_to_check = []
            
            """# 1. First check if the specific version from config exists
            game_version = self.config_manager.version["games"].get(game, "")
            if game_version:
                paths_to_check.append(os.path.join(games_dir, f"{game}-v{game_version}.swf"))"""
            
            # 2. Check for legacy format (no version in filename)
            paths_to_check.append(os.path.join(games_dir, f"{game}.swf"))
            
            # Check if any of the specific paths exist
            for path in paths_to_check:
                if os.path.exists(path):
                    return path
            
            # 3. Find the latest version by checking file modification times
            latest_path = None
            latest_time = 0
            
            # Only scan for files that match our pattern
            prefix = f"{game}-v"
            suffix = ".swf"
            
            # Get all matching files in one operation
            matching_files = [f for f in os.listdir(games_dir) 
                             if f.startswith(prefix) and f.endswith(suffix)]
            
            # Find the most recently modified file
            for filename in matching_files:
                file_path = os.path.join(games_dir, filename)
                file_time = os.path.getmtime(file_path)
                
                if file_time > latest_time:
                    latest_time = file_time
                    latest_path = file_path
            
            return latest_path
            
        except Exception as e:
            self.set_status(f"Error finding game: {str(e)}")
            return None
    
    def play_game(self, game, parent=None):
        """Play the specified game"""
        # Find the game path
        game_path = self.find_game_path(game)
        
        # If game not found or doesn't exist, offer to download
        if not game_path or not os.path.exists(game_path):
            # Use the show_dialog method from BaseManager
            result = self.show_dialog(parent, "Game not found", 
                                    f"{game} is not downloaded.\nDo you want to download it now?")
            if result:
                game_path = self.download_game(game, parent)
                if not game_path:
                    return False
            else:
                return False
        
        # Launch the game with Flash Player
        self.set_status(f"Launching {game}...")
        result = self.flash_manager.launch_game(game_path, parent)
        
        if result:
            self.set_status(f"{game} launched")
            return True
        else:
            self.set_status(f"Failed to launch {game}")
            return False
    
    def check_and_download_games(self):
        """Check if games are downloaded and download if not"""
        games_downloaded = 0
        games_to_check = self.config_manager.version["games"].keys()
        
        for game in games_to_check:
            game_path = self.find_game_path(game)
            if not game_path or not os.path.exists(game_path):
                self.set_status(f"{game} not found. Downloading...")
                if self.download_game(game):
                    games_downloaded += 1
        
        if games_downloaded > 0:
            self.set_status(f"Downloaded {games_downloaded} games")
        else:
            self.set_status("All games are already downloaded")
        
        return games_downloaded
