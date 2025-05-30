#!/usr/bin/env python3
import threading
import time
import os
import platform
import requests
from tkinter import Toplevel
import tkinter as tk
from base_manager import BaseManager
from config import resource_path

class UpdateManager(BaseManager):
    def __init__(self, config_manager, game_manager, status_callback=None):
        super().__init__(status_callback)
        self.config_manager = config_manager
        self.game_manager = game_manager
        # Track ongoing downloads
        self.ongoing_downloads = {}  # {game: {progress: 0, version: ""}}
        # Track UI elements for progress updates
        self.ui_elements = {}  # {game: {progress_label, download_btn, frame, active}}
    
    def _extract_filename_and_version(self, url, response):
        """Extract filename and version from URL or response headers"""
        filename = ""
        version = ""
        
        # Try to get filename from content-disposition header
        if "content-disposition" in response.headers:
            try:
                filename = response.headers['content-disposition'].split('filename=')[1].strip('"')
            except (IndexError, KeyError):
                # If header parsing fails, use URL
                filename = url.split('/')[-1]
        else:
            # If no header, use URL
            filename = url.split('/')[-1]
        
        # Extract version from filename
        if '-v' in filename:
            try:
                version = filename.split('-v')[1].split('.swf')[0]
            except (IndexError, KeyError):
                # If version extraction fails, use timestamp
                version = str(int(time.time()))
        else:
            # If no version in filename, use timestamp
            version = str(int(time.time()))
            
        return filename, version
    
    def check_updates(self, root=None):
        """Check for updates to Flash Player and games"""
        self.set_status("Checking for updates...")
        
        # Start update check in a separate thread to avoid freezing the UI
        thread = threading.Thread(target=self._check_updates_thread, args=(root,))
        thread.daemon = True
        thread.start()
    
    def _check_updates_thread(self, root):
        """Background thread for checking updates"""
        try:
            updates_available = False
            update_messages = []
            
            # Check for game updates
            for game, current_version in self.config_manager.version["games"].items():
                if game in self.config_manager.config["game_urls"]:
                    try:
                        # Create a request to get headers
                        url = self.config_manager.config["game_urls"][game]
                        response = requests.head(url)
                        response.raise_for_status()
                        
                        # Extract filename and version using helper method
                        _, server_version = self._extract_filename_and_version(url, response)
                        
                        # Compare versions
                        if not current_version or current_version != server_version:
                            updates_available = True
                            update_messages.append(f"{game}: v{current_version or 'none'} → v{server_version}")
                    except Exception as e:
                        print(f"Error checking updates for {game}: {str(e)}")
            
            # Update UI in the main thread
            if updates_available and root:
                update_text = "Updates available: " + ", ".join(update_messages)
                root.after(0, lambda: self.set_status(update_text))
                
                # Show update dialog
                root.after(0, lambda: self._show_update_dialog(root, update_messages))
            else:
                if root:
                    root.after(0, lambda: self.set_status("No updates available"))
                else:
                    self.set_status("No updates available")
                
        except Exception as e:
            if root:
                root.after(0, lambda: self.set_status(f"Error checking updates: {str(e)}"))
            else:
                self.set_status(f"Error checking updates: {str(e)}")
    
    def _show_update_dialog(self, root, update_messages):
        """Show dialog with available updates"""
        update_window = tk.Toplevel(root)
        update_window.title("Updates Available")
        update_window.geometry("400x320")
        update_window.resizable(False, False)
        
        # Center the window on the parent window
        self.center_window(update_window, root)

        # Set the window icon
        if platform.system() == "Windows":
            update_window.iconbitmap(resource_path("resources/favicon-original.ico"))
        
        # Create content
        tk.Label(update_window, text="The following updates are available:").pack(pady=10)
        
        # Create a frame for the updates list
        updates_frame = tk.Frame(update_window)
        updates_frame.pack(fill=tk.BOTH, expand=True, padx=10, pady=5)
        
        # Dictionary to store game rows for later reference
        game_rows = {}
        
        # Check if any downloads are in progress
        any_downloads_in_progress = any(
            game in self.ongoing_downloads and self.ongoing_downloads[game]['progress'] < 100 
            for game in [msg.split(":")[0] for msg in update_messages]
        )
        
        # Add each update to the list
        for i, message in enumerate(update_messages):
            game = message.split(":")[0]
            
            # Create a frame for this game row
            game_frame = tk.Frame(updates_frame)
            game_frame.grid(row=i, column=0, sticky=tk.W+tk.E, pady=2)
            game_frame.columnconfigure(0, weight=1)  # Game info takes most space
            
            # Add label with game info
            game_label = tk.Label(game_frame, text=message, anchor=tk.W)
            game_label.grid(row=0, column=0, sticky=tk.W)
            
            # Add progress label (initially showing empty text or current progress)
            progress_text = ""
            if game in self.ongoing_downloads:
                progress_text = f"{self.ongoing_downloads[game]['progress']}%"
            
            progress_label = tk.Label(game_frame, text=progress_text, width=5, anchor=tk.E)
            progress_label.grid(row=0, column=1, sticky=tk.E, padx=5)
            
            # Add download button
            button_text = "Download"
            button_state = tk.NORMAL
            
            # Disable all download buttons if any download is in progress
            if any_downloads_in_progress:
                button_state = tk.DISABLED
                if game in self.ongoing_downloads and self.ongoing_downloads[game]['progress'] < 100:
                    button_text = "Downloading..."
            elif game in self.ongoing_downloads:
                if self.ongoing_downloads[game]['progress'] == 100:
                    # Download completed
                    button_text = "Downloaded"
                    button_state = tk.DISABLED
                elif self.ongoing_downloads[game]['progress'] < 100:
                    # Download in progress
                    button_text = "Downloading..."
                    button_state = tk.DISABLED
                
            download_btn = tk.Button(game_frame, text=button_text, state=button_state,
                                   command=lambda g=game, gf=game_frame: self._download_update(g, update_window, gf))
            download_btn.grid(row=0, column=2, padx=5, sticky=tk.E)
            
            # Store references to UI elements in both dictionaries
            ui_data = {
                'frame': game_frame,
                'progress_label': progress_label,
                'download_btn': download_btn,
                'active': True  # Flag to track if the widget is still active
            }
            game_rows[game] = ui_data
            self.ui_elements[game] = ui_data
        
        # Add buttons
        btn_frame = tk.Frame(update_window)
        btn_frame.pack(fill=tk.X, padx=10, pady=10)
        
        download_all_btn = tk.Button(btn_frame, text="Download All", 
                                   command=lambda: self._download_all_updates(update_messages, update_window, game_rows, download_all_btn))
        download_all_btn.pack(side=tk.LEFT, padx=5)
        
        # Disable Download All button if any downloads are already in progress
        if any_downloads_in_progress:
            download_all_btn.config(state=tk.DISABLED)
            
        # Store download_all_btn in the window for later access
        update_window.download_all_btn = download_all_btn
        
        close_btn = tk.Button(btn_frame, text="Close", command=lambda: self._close_update_window(update_window))
        close_btn.pack(side=tk.RIGHT, padx=5)
        
        # Store game_rows in the window for later access
        update_window.game_rows = game_rows
        
        # Set up protocol for window close event
        update_window.protocol("WM_DELETE_WINDOW", lambda: self._close_update_window(update_window))
        
        # Start a periodic update of the progress display
        self._start_progress_updates(update_window, game_rows)
    
    def _close_update_window(self, window):
        """Handle window close event by marking all game rows as inactive"""
        try:
            # Mark all game rows as inactive
            for game, row in window.game_rows.items():
                row['active'] = False
                # Also remove from ui_elements
                if game in self.ui_elements:
                    self.ui_elements[game]['active'] = False
            # Destroy the window
            window.destroy()
        except Exception as e:
            print(f"Error closing update window: {str(e)}")
            # Try to destroy the window anyway
            try:
                window.destroy()
            except:
                pass
    
    """def _delete_old_game_files(self, game, current_version):
        #Delete old versions of a game
        try:
            # Find all files for this game
            game_files = [f for f in os.listdir(self.config_manager.games_dir) 
                         if f.startswith(f"{game}-v") and f.endswith(".swf")]
            
            # Filter out the current version
            current_filename = f"{game}-v{current_version}.swf"
            old_files = [f for f in game_files if f != current_filename]
            
            # Delete old files
            for old_file in old_files:
                try:
                    old_path = os.path.join(self.config_manager.games_dir, old_file)
                    os.remove(old_path)
                    self.set_status(f"Deleted old version: {old_file}")
                except Exception as e:
                    print(f"Error deleting old file {old_file}: {str(e)}")
                    
            return len(old_files)
        except Exception as e:
            print(f"Error cleaning up old files for {game}: {str(e)}")
            return 0"""
    
    def _download_game_internal(self, game, progress_callback=None, parent=None):
        """
        Core download functionality used by both download_game and _download_with_progress
        
        Args:
            game: The game to download
            progress_callback: Optional callback function for progress updates (percent, downloaded, total)
            parent: Optional parent window for error dialogs
            
        Returns:
            tuple: (file_path, version) or (None, None) on failure
        """
        try:
            # Get the URL
            url = self.config_manager.config["game_urls"][game]
            
            # Create a request to get headers
            response = requests.head(url)
            response.raise_for_status()
            
            # Extract filename and version
            _, version = self._extract_filename_and_version(url, response)
            
            # Create filename with version
            game_filename = f"{game}.swf"
            file_path = os.path.join(self.config_manager.games_dir, game_filename)
            
            # Download the file with progress updates if callback provided
            with requests.get(url, stream=True) as r:
                r.raise_for_status()
                
                # Get total file size
                total_size = int(r.headers.get('content-length', 0))
                downloaded = 0
                
                with open(file_path, 'wb') as f:
                    for chunk in r.iter_content(chunk_size=8192):
                        if chunk:
                            f.write(chunk)
                            downloaded += len(chunk)
                            
                            # Update progress if callback provided
                            if progress_callback and total_size > 0:
                                progress = int((downloaded / total_size) * 100)
                                progress_callback(progress, downloaded, total_size)
                                
                                # Simulate slower download for testing if this is a UI download
                                if hasattr(progress_callback, '__self__') and progress_callback.__self__ is not None:
                                    time.sleep(0.01)
            
            # Update version information
            self.config_manager.version["games"][game] = version
            self.config_manager.save_version_info()
            
            # Delete old versions
            #deleted_count = self._delete_old_game_files(game, version)
            
            # Update status message
            #if deleted_count > 0:
            #    self.set_status(f"{game} v{version} downloaded successfully. Deleted {deleted_count} old version(s).")
            #else:
            self.set_status(f"{game} v{version} downloaded successfully")
                
            return file_path, version
            
        except Exception as e:
            error_msg = f"Failed to download {game}: {str(e)}"
            self.set_status(f"Failed to download {game}")
            
            if parent:
                self.show_dialog(parent, "Error", error_msg, dialog_type="error")
                
            return None, None
    
    # ---- REFACTORED DOWNLOAD AND PROGRESS TRACKING METHODS ----
    
    def _init_download(self, game):
        """Initialize download tracking for a game"""
        # Add to ongoing downloads
        self.ongoing_downloads[game] = {'progress': 0, 'version': ""}
        # Set initial status
        self.set_status(f"Downloading {game}...")
        # Initialize progress to 0%
        self._update_progress(game, 0)
    
    def _create_progress_callback(self, game, game_row=None):
        """Create a progress callback function for a game download
        
        Args:
            game: The game being downloaded
            game_row: Optional UI elements for the game
            
        Returns:
            function: A callback function for progress updates
        """
        def progress_callback(progress, downloaded, total):
            # Update progress in main thread if we have UI elements
            if game_row and 'progress_label' in game_row:
                game_row['progress_label'].after(0, lambda: self._update_progress(game, progress, downloaded, total))
            else:
                # Direct update if no UI element
                self._update_progress(game, progress, downloaded, total)
        
        return progress_callback
    
    def _update_progress(self, game, progress, downloaded=None, total=None):
        """
        Centralized method to update download progress for a game
        
        Args:
            game: Game name
            progress: Progress percentage (0-100)
            downloaded: Optional bytes downloaded
            total: Optional total bytes
        """
        # Ensure progress is within bounds
        progress = min(max(progress, 0), 100)
        
        # Update ongoing_downloads tracking
        if game in self.ongoing_downloads:
            self.ongoing_downloads[game]['progress'] = progress
        
        # Update status bar
        if progress < 100:
            self.set_status(f"Downloading {game}: {progress}%")
        else:
            self.set_status(f"Download complete: {game}")
            # Remove from ongoing_downloads when complete
            if game in self.ongoing_downloads and progress >= 100:
                del self.ongoing_downloads[game]
        
        # Update UI elements if they exist
        if game in self.ui_elements:
            self._update_ui_elements(game, progress)
    
    def _update_ui_elements(self, game, progress):
        """Update all UI elements for a game's download progress"""
        game_row = self.ui_elements.get(game)
        if not game_row or not game_row.get('active', False):
            return
            
        try:
            # Update progress label
            if 'progress_label' in game_row:
                game_row['progress_label'].config(text=f"{progress}%")
            
            # Update button state based on progress
            if 'download_btn' in game_row:
                if progress < 100:
                    game_row['download_btn'].config(text="Downloading...", state=tk.DISABLED)
                else:
                    game_row['download_btn'].config(text="Downloaded", state=tk.DISABLED)
                    # Schedule removal of this row after a short delay if frame exists
                    if 'frame' in game_row:
                        game_row['frame'].after(1000, lambda: self._remove_game_row(game_row))
        except (tk.TclError, RuntimeError, Exception) as e:
            # Widget was destroyed or other error occurred
            game_row['active'] = False
            print(f"Error updating UI for {game}: {str(e)}")
    
    def _remove_game_row(self, game_row):
        """Safely remove a game row"""
        try:
            if game_row.get('active', False):
                game_row['frame'].destroy()
                game_row['active'] = False
        except (tk.TclError, Exception):
            # Widget was already destroyed
            game_row['active'] = False
    
    def download_game(self, game, parent=None):
        """Download or update a game"""
        # Initialize download tracking
        self._init_download(game)
        
        # Create a progress callback
        progress_callback = self._create_progress_callback(game)
        
        # Use the internal download method with progress updates
        file_path, _ = self._download_game_internal(game, progress_callback, parent=parent)
        
        # Ensure progress shows 100% if download was successful
        if file_path:
            self._update_progress(game, 100)
            
        return file_path
    
    def _download_update(self, game, window, game_frame):
        """Download a specific game update with progress indicator"""
        # Get the game row UI elements
        game_row = window.game_rows.get(game)
        if not game_row:
            return
        
        # Disable download button
        game_row['download_btn'].config(state=tk.DISABLED)
        
        # Start download in a separate thread
        thread = threading.Thread(target=self._download_with_progress, 
                                 args=(game, game_row))
        thread.daemon = True
        thread.start()
    
    def _download_with_progress(self, game, game_row=None):
        """Download a game and update progress"""
        # Initialize download tracking
        self._init_download(game)
        
        # Create a progress callback
        progress_callback = self._create_progress_callback(game, game_row)
        
        # Use the internal download method with progress updates
        file_path, version = self._download_game_internal(game, progress_callback)
        
        if file_path:
            # Ensure progress shows 100% and triggers UI cleanup
            if game_row and 'progress_label' in game_row:
                game_row['progress_label'].after(0, lambda: self._update_progress(game, 100))
            else:
                self._update_progress(game, 100)
        else:
            # Show error in progress label and status
            self.set_status(f"Error downloading {game}")
            if game_row and game_row.get('active', False) and 'progress_label' in game_row:
                try:
                    game_row['progress_label'].config(text="Error!")
                except (tk.TclError, RuntimeError, Exception):
                    game_row['active'] = False
    
    def _start_progress_updates(self, window, game_rows):
        """Start periodic updates of the Download All button state"""
        def update_download_all_button():
            # Check if window still exists
            try:
                if not window.winfo_exists():
                    return  # Window was closed, stop updates
            except (tk.TclError, Exception):
                return  # Window was destroyed
                
            # Check if any downloads are in progress
            any_downloads_in_progress = any(
                game in self.ongoing_downloads and self.ongoing_downloads[game]['progress'] < 100 
                for game in game_rows.keys()
            )
            
            # Update Download All button state if it exists
            if hasattr(window, 'download_all_btn'):
                try:
                    if any_downloads_in_progress:
                        window.download_all_btn.config(state=tk.DISABLED, text="Downloading...")
                    else:
                        window.download_all_btn.config(state=tk.NORMAL, text="Download All")
                except (tk.TclError, RuntimeError, Exception) as e:
                    print(f"Error updating Download All button: {str(e)}")
            
            # Schedule next update
            window.after(500, update_download_all_button)
        
        # Start the first update
        window.after(500, update_download_all_button)
    
    def _download_all_updates(self, update_messages, window, game_rows, download_all_btn):
        """Download all available updates sequentially with progress indicators"""
        # Extract game names from update messages
        games = [msg.split(":")[0] for msg in update_messages]
        
        # Disable the Download All button
        download_all_btn.config(state=tk.DISABLED, text="Downloading...")
        
        # Disable all individual download buttons
        for game, row in game_rows.items():
            row['download_btn'].config(state=tk.DISABLED)
        
        # Start downloads in a separate thread
        thread = threading.Thread(target=self._download_all_with_progress, 
                                 args=(games, window, game_rows))
        thread.daemon = True
        thread.start()
    
    def _download_all_with_progress(self, games, window, game_rows):
        """Download all games sequentially with progress updates"""
        try:
            for i, game in enumerate(games):
                # Check if window still exists
                try:
                    window.winfo_exists()
                except tk.TclError:
                    # Window was closed, stop downloading
                    break
                
                # Get the game row UI elements
                game_row = game_rows.get(game)
                if game_row and game_row.get('active', False):
                    try:
                        # Update button text to show waiting status
                        game_row['download_btn'].config(text="Waiting...", state=tk.DISABLED)
                    except (tk.TclError, RuntimeError, Exception):
                        game_row['active'] = False
                
                # Download the game with progress using the centralized system
                self._download_with_progress(game, game_row)
                
                # Wait a moment between downloads
                time.sleep(0.5)
            
            # Update status when all downloads are complete
            self.set_status("All downloads completed")
            
            # Re-enable the Download All button if window still exists
            try:
                if window.winfo_exists() and hasattr(window, 'download_all_btn'):
                    window.download_all_btn.config(state=tk.NORMAL, text="Download All")
            except (tk.TclError, RuntimeError, Exception) as e:
                print(f"Error updating Download All button: {str(e)}")
                
        except Exception as e:
            print(f"Error in download all process: {str(e)}")
            # Try to re-enable the Download All button if window still exists
            try:
                if window.winfo_exists() and hasattr(window, 'download_all_btn'):
                    window.download_all_btn.config(state=tk.NORMAL, text="Download All")
            except:
                pass
