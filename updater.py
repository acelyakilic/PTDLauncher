import tkinter as tk
from tkinter import ttk, messagebox
import threading
import requests
import json
import re
import time
import os
from utils import get_resource_path, get_file_path, logger
from version_manager import load_versions, save_versions

def load_config():
    try:
        config_path = get_resource_path("config.json")
        if os.path.exists(config_path):
            with open(config_path, 'r') as f:
                return json.load(f)
        else:
            logger.warning(f"Config file not found: {config_path}, using defaults")
    except Exception as e:
        logger.error(f"Error loading config: {str(e)}")
    
    # Default configuration
    return {
        "flash_player": {
            "fallback_version": "32.0.0.465",
            "primary_url": "https://www.flash.cn/cdm/latest/flashplayer_sa.exe",
            "fallback_url": "https://fpdownload.macromedia.com/pub/flashplayer/updaters/32/flashplayer_32_sa.exe"
        },
        "game_urls": {
            "PTD1": "https://ptd.onl/ptd1-latest.swf",
            "PTD1RF": "https://ptd.onl/ptd1rf-latest.swf",
            "PTD1_Hacked": "https://ptd.onl/ptd1-hacked-latest.swf",
            "PTD2": "https://ptd.onl/ptd2-latest.swf",
            "PTD2_Hacked": "https://ptd.onl/ptd2-hacked-latest.swf",
            "PTD3": "https://ptd.onl/ptd3-latest.swf",
            "PTD3_Hacked": "https://ptd.onl/ptd3-hacked-latest.swf"
        }
    }

CONFIG = load_config()
FLASH_FALLBACK_VERSION = CONFIG["flash_player"]["fallback_version"]
FLASH_PRIMARY_URL = CONFIG["flash_player"]["primary_url"]
FLASH_FALLBACK_URL = CONFIG["flash_player"]["fallback_url"]
GAME_URLS = CONFIG["game_urls"]

def download_file(url, destination, progress_label=None, progress_bar=None, progress_start=0, progress_end=100, timeout=30, retries=3):
    os.makedirs(os.path.dirname(destination), exist_ok=True)
    
    for attempt in range(retries):
        try:
            if attempt > 0:
                logger.info(f"Retry attempt {attempt}/{retries-1} for {url}")
                if progress_label:
                    progress_label.config(text=f"Retrying download... ({attempt}/{retries-1})")
                    progress_bar and progress_bar.update()
            
            session = requests.Session()
            response = session.get(url, stream=True, timeout=timeout)
            response.raise_for_status()
            
            total_size = int(response.headers.get('content-length', 0))
            chunk_size = 16384
            
            with open(destination, 'wb') as f:
                downloaded = 0
                update_threshold = max(1, total_size // 100) if total_size > 0 else chunk_size
                last_update = 0
                
                for chunk in response.iter_content(chunk_size=chunk_size):
                    if chunk:
                        f.write(chunk)
                        downloaded += len(chunk)
                        
                        if total_size > 0 and progress_bar and progress_label and \
                           (downloaded - last_update > update_threshold or downloaded == total_size):
                            percent = downloaded / total_size
                            progress_bar["value"] = progress_start + (progress_end - progress_start) * percent
                            progress_label.config(text=f"Downloading... {int(percent * 100)}%")
                            progress_bar.update()
                            last_update = downloaded
            
            logger.info(f"Successfully downloaded {url} to {destination}")
            return True
            
        except requests.RequestException as e:
            logger.warning(f"Download attempt {attempt+1}/{retries} failed for {url}: {str(e)}")
            
            error_msg = "Download error"
            if isinstance(e, requests.ConnectionError):
                error_msg = "Connection error - check internet"
            elif isinstance(e, requests.Timeout):
                error_msg = "Download timed out"
            elif isinstance(e, requests.HTTPError):
                if e.response.status_code >= 500:
                    error_msg = f"Server error ({e.response.status_code})"
                elif e.response.status_code == 404:
                    error_msg = "File not found"
            
            if progress_label:
                progress_label.config(text=error_msg)
                progress_bar and progress_bar.update()
            
            if attempt == retries - 1:
                logger.error(f"Failed to download {url} after {retries} attempts")
                raise
            
            time.sleep(1 * (2 ** attempt))  # Exponential backoff

def check_flash_player_updates(versions, progress_label, progress_bar, update_window):
    try:
        logger.info("Checking Flash Player updates")
        progress_label.config(text="Checking Flash Player updates...")
        progress_bar["value"] = 10
        update_window.update()
        
        if versions["flash_player"] == "custom":
            logger.info("Using custom Flash Player, skipping update")
            progress_label.config(text="Using custom Flash Player...")
            progress_bar["value"] = 30
            update_window.update()
            return True
        
        latest_flash_version = FLASH_FALLBACK_VERSION
        try:
            for retry in range(3):
                try:
                    response = requests.get("https://api.flash.cn/config/flashVersion/", timeout=5)
                    if response.status_code == 200:
                        match = re.search(r"_flash_install_packages_\((.*)\);", response.text)
                        if match:
                            flash_data = json.loads(match.group(1))
                            latest_flash_version = flash_data.get("activex", {}).get("version", FLASH_FALLBACK_VERSION)
                            logger.info(f"Latest Flash Player version: {latest_flash_version}")
                            break
                    else:
                        logger.warning(f"Flash version API returned status code {response.status_code}")
                except Exception as e:
                    if retry == 2:
                        raise
                    logger.warning(f"Retry {retry+1}/3 for Flash version check: {str(e)}")
                    time.sleep(1 * (2 ** retry))
        except Exception as e:
            logger.warning(f"Error getting Flash Player version, using fallback {FLASH_FALLBACK_VERSION}: {str(e)}")

        flash_player_path = get_file_path("flashplayer_sa.exe")
        
        
        if latest_flash_version != versions["flash_player"] or not os.path.exists(flash_player_path):
            logger.info(f"Downloading Flash Player version {latest_flash_version}")
            progress_label.config(text="Downloading Flash Player...")
            progress_bar["value"] = 20
            update_window.update()
            
            download_success = False
            try:
                download_success = download_file(FLASH_PRIMARY_URL, flash_player_path, progress_label, progress_bar, 20, 30)
            except Exception as e:
                logger.warning(f"Primary Flash Player download failed: {str(e)}")
                
            if not download_success:
                try:
                    download_success = download_file(FLASH_FALLBACK_URL, flash_player_path, progress_label, progress_bar, 20, 30)
                except Exception as e:
                    logger.error(f"Fallback Flash Player download failed: {str(e)}")
                    progress_label.config(text="Flash Player download failed")
                    update_window.update()
                    time.sleep(2)
                    return False
            
            if download_success:
                versions["flash_player"] = latest_flash_version
                progress_label.config(text="Flash Player updated successfully")
                progress_bar["value"] = 30
                update_window.update()
                time.sleep(0.5)  # Brief pause to show success message
                return True
            return False
        else:
            logger.info("Flash Player is up to date")
            return True
    except Exception as e:
        logger.error(f"Error in Flash Player update: {str(e)}")
        progress_label.config(text=f"Flash Player update error")
        update_window.update()
        time.sleep(2)
        return False

def check_game_updates(versions, progress_label, progress_bar, update_window):
    try:
        logger.info("Checking game updates")
        total_games = len(GAME_URLS)
        success_count = 0
        
        for i, (game_key, url) in enumerate(GAME_URLS.items()):
            progress_percent = 30 + (i * 70 // total_games)
            progress_label.config(text=f"Checking {game_key} updates...")
            progress_bar["value"] = progress_percent
            update_window.update()
            
            try:
                response = None
                for retry in range(3):
                    try:
                        response = requests.head(url, timeout=5)
                        response.raise_for_status()
                        break
                    except requests.RequestException as e:
                        if retry == 2:
                            raise
                        logger.warning(f"Retry {retry+1}/3 for HEAD request to {url}")
                        time.sleep(1 * (2 ** retry))
                
                if 'content-disposition' in response.headers:
                    filename = response.headers['content-disposition'].split('filename=')[1].strip('"')
                else:
                    filename = url.split('/')[-1]
                
                if '-v' in filename:
                    version = filename.split('-v')[1].split('.swf')[0]
                else:
                    version = str(int(time.time()))
                
                logger.info(f"{game_key} latest version: {version}")
                
                current_version = versions["games"].get(game_key, "")
                current_file = get_file_path(f"{game_key}-v{current_version}.swf")
                new_file = get_file_path(f"{game_key}-v{version}.swf")
                
                if version != current_version or not os.path.exists(current_file):
                    logger.info(f"Updating {game_key} from {current_version} to {version}")
                    progress_label.config(text=f"Downloading {game_key}...")
                    update_window.update()
                    
                    game_progress_start = progress_percent
                    game_progress_end = progress_percent + (70 // total_games)
                    
                    try:
                        download_success = download_file(
                            url, new_file, progress_label, progress_bar,
                            game_progress_start, game_progress_end, timeout=30, retries=3
                        )
                        
                        if download_success:
                            if os.path.exists(current_file) and current_file != new_file:
                                try:
                                    os.remove(current_file)
                                except Exception as e:
                                    logger.warning(f"Could not delete old version {current_file}")
                            
                            versions["games"][game_key] = version
                            success_count += 1
                        else:
                            logger.error(f"Failed to download {game_key}")
                            progress_label.config(text=f"{game_key} download failed")
                    except Exception as e:
                        logger.error(f"Failed to download {game_key}: {str(e)}")
                        progress_label.config(text=f"{game_key} download failed")
                else:
                    logger.info(f"{game_key} is up to date")
                    success_count += 1
            
            except Exception as e:
                logger.error(f"Error checking {game_key} updates: {str(e)}")
                progress_label.config(text=f"{game_key} update check failed")
            
            update_window.update()
        
        return success_count > 0
    except Exception as e:
        logger.error(f"Error in game updates: {str(e)}")
        progress_label.config(text="Game update error")
        update_window.update()
        time.sleep(2)
        return False

def check_updates(update_window, progress_label, progress_bar):
    try:
        logger.info("Starting update check")
        versions = load_versions()
        
        flash_updated = check_flash_player_updates(versions, progress_label, progress_bar, update_window)
        games_updated = check_game_updates(versions, progress_label, progress_bar, update_window)
        
        if flash_updated or games_updated:
            updates_successful = save_versions(versions)
            logger.info("Updates completed and versions saved" if updates_successful else "Updates completed but failed to save versions")
        else:
            updates_successful = False
        
        progress_label.config(text="Updates completed!" if updates_successful else "Updates completed with errors")
        progress_bar["value"] = 100
        update_window.update()
        time.sleep(1)
    except Exception as e:
        logger.error(f"Update process error: {str(e)}")
        progress_label.config(text="Update error")
        update_window.update()
        time.sleep(2)
    finally:
        try:
            update_window.destroy()
        except:
            pass

def show_update_window(root):
    try:
        logger.info("Opening update window")
        update_window = tk.Toplevel()
        update_window.title("PTD Launcher Updates")
        
        try:
            icon_path = get_resource_path("favicon.ico")
            if os.path.exists(icon_path):
                update_window.iconbitmap(icon_path)
        except Exception as e:
            logger.warning("Could not set update window icon")
            
        update_window.geometry("400x150")
        update_window.resizable(False, False)
        
        # Center window
        screen_width = update_window.winfo_screenwidth()
        screen_height = update_window.winfo_screenheight()
        position_top = int((screen_height - 150) / 2)
        position_right = int((screen_width - 400) / 2)
        update_window.geometry(f'400x150+{position_right}+{position_top}')
        
        progress_frame = ttk.Frame(update_window, padding=20)
        progress_frame.pack(fill=tk.BOTH, expand=True)
        
        ttk.Label(progress_frame, text="PTD Launcher Update", font=("Arial", 14, "bold")).pack(pady=(0, 10))
        
        progress_label = ttk.Label(progress_frame, text="Checking for updates...")
        progress_label.pack(pady=(0, 5))
        
        progress_bar = ttk.Progressbar(progress_frame, orient=tk.HORIZONTAL, length=350, mode='determinate')
        progress_bar.pack(pady=(0, 10))
        
        update_thread = threading.Thread(target=check_updates, args=(update_window, progress_label, progress_bar))
        update_thread.daemon = True
        update_thread.start()
        
        update_window.transient(root)
        update_window.grab_set()
        
        update_window.protocol("WM_DELETE_WINDOW", update_window.destroy)
        
        root.wait_window(update_window)
    except Exception as e:
        logger.error(f"Error showing update window: {str(e)}")
        messagebox.showerror("Update Error", f"An error occurred while checking for updates: {str(e)}")
