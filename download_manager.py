#!/usr/bin/env python3
import threading
import time
import os
import platform
import requests
import tempfile
import shutil
import subprocess
import tarfile
import tkinter as tk
from tkinter import Toplevel, Label, Button, Frame
from base_manager import BaseManager

class DownloadManager(BaseManager):
    def __init__(self, config_manager, status_callback=None):
        super().__init__(status_callback)
        self.config_manager = config_manager
        self.update_manager = None  # Will be set by the main app
        # Track ongoing downloads
        self.ongoing_downloads = {}  # {item: {progress: 0, version: "", type: "game/flash"}}
        # Track UI elements for progress updates
        self.ui_elements = {}  # {item: {progress_label, download_btn, frame, active}}
        self.is_downloading = False
    
    def set_update_manager(self, update_manager):
        """Set the update manager instance to check for ongoing updates."""
        self.update_manager = update_manager
    
    def is_download_in_progress(self):
        """Check if any download is currently in progress"""
        return self.is_downloading or len(self.ongoing_downloads) > 0
    
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
    
    def _create_progress_dialog(self, parent, title, item_name):
        """Create a progress dialog window"""
        dialog = Toplevel(parent)
        dialog.title(title)
        dialog.geometry("350x120")
        dialog.resizable(False, False)
        dialog.transient(parent)
        dialog.grab_set()
        
        # Center the dialog
        self.center_window(dialog, parent)
        
        # Create UI elements
        Label(dialog, text=f"Downloading {item_name}...", pady=10).pack()
        
        progress_label = Label(dialog, text="0%", pady=5)
        progress_label.pack()
        
        return dialog, progress_label
    
    def _update_progress(self, item, progress, downloaded=None, total=None):
        """Update download progress for an item - THREAD SAFE"""
        # Ensure progress is within bounds
        progress = min(max(progress, 0), 100)
        
        # Update ongoing_downloads tracking
        if item in self.ongoing_downloads:
            self.ongoing_downloads[item]['progress'] = progress
        
        # Update status bar - THREAD SAFE
        if progress < 100:
            if downloaded and total:
                downloaded_mb = downloaded / (1024 * 1024)
                total_mb = total / (1024 * 1024)
                status_msg = f"Downloading {item}: {progress}% ({downloaded_mb:.1f}/{total_mb:.1f} MB)"
            else:
                status_msg = f"Downloading {item}: {progress}%"
        else:
            status_msg = f"Download complete: {item}"
            # Remove from ongoing_downloads when complete
            if item in self.ongoing_downloads and progress >= 100:
                del self.ongoing_downloads[item]
        
        # Update status using callback (thread safe)
        if self.status_callback:
            try:
                self.status_callback(status_msg)
            except RuntimeError:
                # If we're not in main thread, this will fail silently
                # The UI update will happen through the dialog.after() calls
                pass
        
        # Update UI elements if they exist
        if item in self.ui_elements:
            self._update_ui_elements(item, progress, downloaded, total)
    
    def _update_ui_elements(self, item, progress, downloaded=None, total=None):
        """Update UI elements for download progress"""
        ui_data = self.ui_elements.get(item)
        if not ui_data or not ui_data.get('active', False):
            return
            
        try:
            # Update progress label with more detailed info
            progress_text = f"{progress}%"
            if downloaded and total and total > 0:
                downloaded_mb = downloaded / (1024 * 1024)
                total_mb = total / (1024 * 1024)
                progress_text = f"{progress}% ({downloaded_mb:.1f}/{total_mb:.1f} MB)"
            
            if 'progress_label' in ui_data:
                ui_data['progress_label'].config(text=progress_text)
            
            # Update button state if exists
            if 'download_btn' in ui_data and ui_data['download_btn'] is not None:
                if progress < 100:
                    ui_data['download_btn'].config(text="Downloading...", state=tk.DISABLED)
                else:
                    ui_data['download_btn'].config(text="Downloaded", state=tk.DISABLED)
                    
        except (tk.TclError, RuntimeError, Exception) as e:
            # Widget was destroyed or other error occurred
            ui_data['active'] = False
            print(f"Error updating UI for {item}: {str(e)}")
    
    def download_game(self, game, parent=None):
        """Download a game with progress dialog"""
        if self.is_download_in_progress():
            self.show_dialog(parent, "Download in Progress", 
                           "Another download is already in progress. Please wait.", 
                           dialog_type="info")
            return None
        
        # Check if the updater is running
        if self.update_manager and self.update_manager.is_updating:
            self.show_dialog(parent, "Update in Progress",
                           "An update is currently in progress. Please wait.",
                           dialog_type="info")
            return None
        
        try:
            # Get the URL
            if game not in self.config_manager.config["game_urls"]:
                self.show_dialog(parent, "Error", f"Game '{game}' not found in configuration", 
                               dialog_type="error")
                return None
                
            url = self.config_manager.config["game_urls"][game]
            
            # Create progress dialog
            dialog, progress_label = self._create_progress_dialog(parent, f"Downloading {game}", game)
            
            # Set up UI tracking
            self.ui_elements[game] = {
                'progress_label': progress_label,
                'download_btn': None,
                'frame': dialog,
                'active': True
            }
            
            # Initialize download tracking
            self.ongoing_downloads[game] = {'progress': 0, 'version': "", 'type': 'game'}
            self.is_downloading = True
            
            # Result storage
            result = [None]
            
            def download_thread():
                try:
                    # Create a request to get headers
                    response = requests.head(url, timeout=30)
                    response.raise_for_status()
                    
                    # Extract filename and version
                    _, version = self._extract_filename_and_version(url, response)
                    
                    # Create filename
                    game_filename = f"{game}.swf"
                    file_path = os.path.join(self.config_manager.games_dir, game_filename)
                    
                    # Download the file with progress updates
                    with requests.get(url, stream=True, timeout=30) as r:
                        r.raise_for_status()
                        
                        # Get total file size
                        total_size = int(r.headers.get('content-length', 0))
                        downloaded = 0
                        
                        with open(file_path, 'wb') as f:
                            for chunk in r.iter_content(chunk_size=8192):
                                if chunk:
                                    f.write(chunk)
                                    downloaded += len(chunk)
                                    
                                    # Update progress
                                    if total_size > 0:
                                        progress = int((downloaded / total_size) * 100)
                                        # Schedule UI update in main thread
                                        dialog.after(0, lambda p=progress, d=downloaded, t=total_size: 
                                                    self._update_progress(game, p, d, t))
                                        
                                        # Small delay for smoother progress display
                                        time.sleep(0.01)
                    
                    # Update version information
                    self.config_manager.version["games"][game] = version
                    self.config_manager.save_version_info()
                    
                    # Final progress update
                    dialog.after(0, lambda: self._update_progress(game, 100))
                    
                    result[0] = file_path
                    
                    # Close dialog after delay
                    def close_dialog():
                        try:
                            dialog.destroy()
                        except tk.TclError:
                            pass
                    
                    dialog.after(1000, close_dialog)
                    
                except Exception as e:
                    error_msg = f"Failed to download {game}: {str(e)}"
                    dialog.after(0, lambda: self.set_status(f"Failed to download {game}"))
                    
                    def show_error():
                        try:
                            self.show_dialog(parent, "Download Error", error_msg, dialog_type="error")
                            dialog.destroy()
                        except tk.TclError:
                            pass
                    
                    dialog.after(0, show_error)
                
                finally:
                    # Clean up
                    self.is_downloading = False
                    if game in self.ui_elements:
                        self.ui_elements[game]['active'] = False
                        del self.ui_elements[game]
                    if game in self.ongoing_downloads:
                        del self.ongoing_downloads[game]
            
            # Set up dialog close handler
            def close_dialog():
                if game in self.ui_elements:
                    self.ui_elements[game]['active'] = False
                self.is_downloading = False
                dialog.destroy()
            
            dialog.protocol("WM_DELETE_WINDOW", close_dialog)
            
            # Start download thread
            thread = threading.Thread(target=download_thread)
            thread.daemon = True
            thread.start()
            
            # Wait for dialog to close
            try:
                parent.wait_window(dialog)
            except tk.TclError:
                pass
            
            return result[0]
            
        except Exception as e:
            self.is_downloading = False
            self.show_dialog(parent, "Error", f"Failed to start download: {str(e)}", 
                           dialog_type="error")
            return None
    
    def download_flash_player(self, parent=None):
        """Download Flash Player with progress dialog"""
        if self.is_download_in_progress():
            self.show_dialog(parent, "Download in Progress", 
                           "Another download is already in progress. Please wait.", 
                           dialog_type="info")
            return None

        # Check if the updater is running
        if self.update_manager and self.update_manager.is_updating:
            self.show_dialog(parent, "Update in Progress",
                           "An update is currently in progress. Please wait.",
                           dialog_type="info")
            return None
        
        try:
            # Get download info
            download_info = self.config_manager.get_flash_download_info()
            if not download_info:
                self.show_dialog(parent, "Error", "Unsupported operating system", 
                               dialog_type="error")
                return None
            
            # Create Flash Player directory
            flash_dir = self.config_manager.get_flash_dir()
            if not flash_dir:
                self.show_dialog(parent, "Error", "Unsupported operating system", 
                               dialog_type="error")
                return None
            
            os.makedirs(flash_dir, exist_ok=True)
            
            # Create progress dialog
            dialog, progress_label = self._create_progress_dialog(parent, "Downloading Flash Player", "Flash Player")
            
            # Set up UI tracking
            self.ui_elements["flash_player"] = {
                'progress_label': progress_label,
                'download_btn': None,
                'frame': dialog,
                'active': True
            }
            
            # Initialize download tracking
            self.ongoing_downloads["flash_player"] = {'progress': 0, 'version': "", 'type': 'flash'}
            self.is_downloading = True
            
            # Result storage
            result = [None]
            
            def download_thread():
                try:
                    # Try primary URL first
                    url_to_use = download_info["url"]
                    
                    try:
                        # Schedule status update in main thread
                        dialog.after(0, lambda: self.set_status("Downloading Flash Player from primary source..."))
                        
                        with requests.get(url_to_use, stream=True, timeout=30) as r:
                            r.raise_for_status()
                            
                            # Get total file size
                            total_size = int(r.headers.get('content-length', 0))
                            downloaded = 0
                            
                            with open(download_info["full_path"], 'wb') as f:
                                for chunk in r.iter_content(chunk_size=8192):
                                    if chunk:
                                        f.write(chunk)
                                        downloaded += len(chunk)
                                        
                                        # Update progress
                                        if total_size > 0:
                                            progress = int((downloaded / total_size) * 100)
                                            # Schedule UI update in main thread
                                            dialog.after(0, lambda p=progress, d=downloaded, t=total_size: 
                                                        self._update_progress("flash_player", p, d, t))
                                            
                                            # Small delay for smoother progress display
                                            time.sleep(0.01)
                                            
                    except Exception as e:
                        # Try fallback URL if available
                        if "fallback_url" in download_info:
                            # Schedule status update in main thread
                            dialog.after(0, lambda: self.set_status("Primary download failed, trying fallback source..."))
                            print(f"Primary download failed: {str(e)}")
                            
                            with requests.get(download_info["fallback_url"], stream=True, timeout=30) as r:
                                r.raise_for_status()
                                
                                # Get total file size
                                total_size = int(r.headers.get('content-length', 0))
                                downloaded = 0
                                
                                with open(download_info["full_path"], 'wb') as f:
                                    for chunk in r.iter_content(chunk_size=8192):
                                        if chunk:
                                            f.write(chunk)
                                            downloaded += len(chunk)
                                            
                                            # Update progress
                                            if total_size > 0:
                                                progress = int((downloaded / total_size) * 100)
                                                # Schedule UI update in main thread
                                                dialog.after(0, lambda p=progress, d=downloaded, t=total_size: 
                                                            self._update_progress("flash_player", p, d, t))
                                                
                                                # Small delay for smoother progress display
                                                time.sleep(0.01)
                        else:
                            raise
                    
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
                        
                        # Check if the binary exists
                        if not os.path.exists(flash_bin):
                            # Try to find the binary in the extracted files
                            for root, dirs, files in os.walk(flash_dir):
                                for file in files:
                                    if file == download_info["bin_name"]:
                                        flash_bin = os.path.join(root, file)
                                        break
                        
                        # If we found the binary, make it executable
                        if os.path.exists(flash_bin):
                            os.chmod(flash_bin, 0o755)
                            # If the binary is not in the expected location, move it there
                            expected_path = os.path.join(flash_dir, download_info["bin_name"])
                            if flash_bin != expected_path:
                                shutil.move(flash_bin, expected_path)
                        else:
                            raise Exception(f"Could not find Flash Player binary after extraction. Expected: {download_info['bin_name']}")
                    
                    # Update version information
                    self.config_manager.version["flash_player"] = self.config_manager.config["flash_player"]["fallback_version"]
                    self.config_manager.save_version_info()
                    
                    # Final progress update
                    dialog.after(0, lambda: self._update_progress("flash_player", 100))
                    
                    result[0] = self.config_manager.get_flash_player_path()
                    
                    # Close dialog after delay
                    def close_dialog():
                        try:
                            dialog.destroy()
                        except tk.TclError:
                            pass
                    
                    dialog.after(1000, close_dialog)
                    
                except Exception as e:
                    error_msg = f"Failed to download Flash Player: {str(e)}"
                    dialog.after(0, lambda: self.set_status("Failed to download Flash Player"))
                    
                    def show_error():
                        try:
                            self.show_dialog(parent, "Download Error", error_msg, dialog_type="error")
                            dialog.destroy()
                        except tk.TclError:
                            pass
                    
                    dialog.after(0, show_error)
                
                finally:
                    # Clean up
                    self.is_downloading = False
                    if "flash_player" in self.ui_elements:
                        self.ui_elements["flash_player"]['active'] = False
                        del self.ui_elements["flash_player"]
                    if "flash_player" in self.ongoing_downloads:
                        del self.ongoing_downloads["flash_player"]
            
            # Set up dialog close handler
            def close_dialog():
                if "flash_player" in self.ui_elements:
                    self.ui_elements["flash_player"]['active'] = False
                self.is_downloading = False
                dialog.destroy()
            
            dialog.protocol("WM_DELETE_WINDOW", close_dialog)
            
            # Start download thread
            thread = threading.Thread(target=download_thread)
            thread.daemon = True
            thread.start()
            
            # Wait for dialog to close
            try:
                parent.wait_window(dialog)
            except tk.TclError:
                pass
            
            return result[0]
            
        except Exception as e:
            self.is_downloading = False
            self.show_dialog(parent, "Error", f"Failed to start Flash Player download: {str(e)}", 
                           dialog_type="error")
            return None
