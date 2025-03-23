import webbrowser
import subprocess
import time
import ctypes
import pygetwindow as gw
import os
from tkinter import messagebox
from utils import get_resource_path, get_file_path, logger
from sound_manager import play_sound
from settings_manager import select_flash_player
from version_manager import load_versions

def open_website(url):
    try:
        logger.info(f"Opening website: {url}")
        play_sound("closetab.mp3")
        webbrowser.open(url)
    except Exception as e:
        logger.error(f"Error opening website {url}: {str(e)}")
        messagebox.showerror("Error", f"Could not open website: {str(e)}")

def open_flash(swf, name):
    try:
        logger.info(f"Opening Flash game: {swf} as {name}")
        play_sound("opentab.mp3")
        versions = load_versions()
        
        # Get file paths
        flash_player_path = get_file_path("flashplayer_sa.exe")
        swf_version = versions["games"].get(swf, "unknown")
        swf_path = get_file_path(f"{swf}-v{swf_version}.swf")
        
        # Check if Flash Player exists
        if not os.path.exists(flash_player_path):
            logger.error("Flash Player not found")
            if messagebox.askyesno("Flash Player Not Found", "Flash Player not found. Select custom executable?"):
                flash_player_path = select_flash_player()
                if not flash_player_path:
                    return
            else:
                messagebox.showerror("Error", "Flash Player not found. Restart launcher to download it.")
                return
        
        # Check if SWF file exists
        if not os.path.exists(swf_path):
            logger.error(f"SWF file not found: {swf_path}")
            messagebox.showerror("Error", f"Game file for {name} not found. Restart launcher to download it.")
            return
        
        # Launch Flash Player
        try:
            process = subprocess.Popen([flash_player_path, swf_path])
            logger.info(f"Launched Flash Player with PID: {process.pid if process else 'unknown'}")
        except Exception as e:
            logger.error(f"Error launching Flash Player: {str(e)}")
            messagebox.showerror("Error", f"Could not launch Flash Player: {str(e)}")
            return
        
        # Wait for Flash window to appear
        start_time = time.time()
        polling_interval = 0.1
        while time.time() - start_time < 5:  # 5 seconds timeout
            try:
                flash_windows = gw.getWindowsWithTitle("Adobe Flash Player")
                if flash_windows:
                    customize_flash_window(flash_windows, name)
                    break
                polling_interval = min(polling_interval * 1.5, 0.5)  # Exponential backoff
                time.sleep(polling_interval)
            except Exception as e:
                logger.warning(f"Error polling for Flash window: {str(e)}")
                time.sleep(0.2)
                
    except Exception as e:
        logger.error(f"Error in open_flash: {str(e)}")
        messagebox.showerror("Error", f"Error launching game: {str(e)}")

# Icon cache
_icon_cache = {}

def customize_flash_window(flash_windows, window_title):
    try:
        # Load icons if not cached
        icon_path = get_resource_path("favicon-flash.ico")
        if not os.path.exists(icon_path):
            logger.warning("Icon file not found")
            return
            
        if "small" not in _icon_cache:
            try:
                _icon_cache["small"] = ctypes.windll.user32.LoadImageW(None, icon_path, 1, 16, 16, 0x10)
                _icon_cache["large"] = ctypes.windll.user32.LoadImageW(None, icon_path, 1, 48, 48, 0x10)
            except Exception as e:
                logger.error(f"Error loading icons: {str(e)}")
                return
        
        # Apply customizations to each window
        success_count = 0
        for window in flash_windows:
            try:
                hwnd = window._hWnd
                
                # Set title and icons
                ctypes.windll.user32.SetWindowTextW(hwnd, window_title)
                ctypes.windll.user32.SendMessageW(hwnd, 0x80, 0, _icon_cache["small"])
                ctypes.windll.user32.SendMessageW(hwnd, 0x80, 1, _icon_cache["large"])
                
                # Remove menu items
                if hMenu := ctypes.windll.user32.GetMenu(hwnd):
                    deleted = 0
                    for i in range(ctypes.windll.user32.GetMenuItemCount(hMenu) - 1, -1, -1):
                        if ctypes.windll.user32.DeleteMenu(hMenu, i, 0x400):
                            deleted += 1
                    if deleted > 0:
                        ctypes.windll.user32.DrawMenuBar(hwnd)
                
                success_count += 1
            except Exception as e:
                logger.error(f"Error customizing window: {str(e)}")
        
        if success_count > 0:
            logger.info(f"Customized {success_count} Flash Player window(s)")
        
    except Exception as e:
        logger.error(f"Error in customize_flash_window: {str(e)}")