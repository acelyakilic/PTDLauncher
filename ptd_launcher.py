#!/usr/bin/env python3
import os
import sys
import platform
import tkinter as tk
from tkinter import ttk
import webbrowser

# Import our modules
from config import ConfigManager, resource_path
from sound_manager import SoundManager
from download_manager import DownloadManager
from flash_manager import FlashManager
from game_manager import GameManager
from updater import UpdateManager

class PTDLauncher:
    def __init__(self, root):
        self.root = root
        self.root.title("PTD Launcher")
        self.root.geometry("650x400")
        self.root.resizable(False, False)
        
        # Initialize managers
        self.config_manager = ConfigManager()
        self.config_manager.load_config()
        
        self.sound_manager = SoundManager(self.config_manager)
        
        # Initialize download manager
        self.download_manager = DownloadManager(
            self.config_manager,
            status_callback=self.update_status
        )
        
        self.flash_manager = FlashManager(
            self.config_manager,
            download_manager=self.download_manager,
            status_callback=self.update_status
        )
        
        # Initialize managers with circular dependency
        self.game_manager = GameManager(
            self.config_manager,
            self.flash_manager,
            download_manager=self.download_manager,
            status_callback=self.update_status
        )
        
        self.update_manager = UpdateManager(
            self.config_manager,
            self.game_manager,
            download_manager=self.download_manager,
            status_callback=self.update_status
        )
        
        # Set up the circular reference
        self.game_manager.set_update_manager(self.update_manager)
        self.download_manager.set_update_manager(self.update_manager)
        
        # Define common button style
        self.button_style = {
            "font": ("Arial", 11),
            "width": 14,
            "height": 2,
            "borderwidth": 2,
            "relief": tk.RAISED
        }
        
        # Create UI
        self.create_ui()
        
        # Check Flash and games on startup
        self.check_flash_and_games()
    
    def update_status(self, message):
        """Update status message"""
        self.status_var.set(message)
    
    def check_flash_and_games(self):
        """Check Flash Player on startup"""
        # Schedule the flash check after the main loop starts
        self.root.after(100, self._delayed_flash_check)
        
        # Set status to ready
        self.update_status("Ready to play")
    
    def _delayed_flash_check(self):
        """Delayed flash player check to avoid thread issues"""
        flash_path = self.config_manager.get_flash_player_path()
        
        # Only show dialog if Flash Player is not installed
        if not flash_path or not os.path.exists(flash_path):
            result = self.flash_manager.show_dialog(self.root, "Flash Player", "Flash Player is not installed. Do you want to download it now?")
            if result:
                self.flash_manager.download_flash_player(self.root)
    
    def create_ui(self):
        """Create the user interface"""
        # Create each section of the UI
        self._create_header()
        
        # Create a frame for the content
        content_frame = tk.Frame(self.root, bg="#F8F8F8")  # Light background
        content_frame.pack(fill=tk.BOTH, expand=True)
        
        # Create UI components
        self._create_pokecenter_buttons(content_frame)
        self._create_game_buttons(content_frame)
        self._create_special_buttons(content_frame)
        self._create_status_bar()
    
    def _create_header(self):
        """Create the header with logo and buttons"""
        # Create a frame for the header with a more appealing color
        header_frame = tk.Frame(self.root, bg="#4A6EA9", height=150)  # More appealing blue color
        header_frame.pack(fill=tk.X)
        
        # Add the Pokemon Tower Defense logo
        logo_img = tk.PhotoImage(file=resource_path("resources/logo.png"))
        logo_label = tk.Label(header_frame, image=logo_img, bg="#4A6EA9")
        logo_label.image = logo_img  # Keep a reference
        logo_label.pack(side=tk.LEFT, padx=15)
        
        # Add buttons for update and settings
        button_frame = tk.Frame(header_frame, bg="#4A6EA9")
        button_frame.pack(side=tk.RIGHT, padx=10)
        
        settings_img = tk.PhotoImage(file=resource_path("resources/settings.png"))
        settings_btn = tk.Button(button_frame, image=settings_img, bg="#4A6EA9", bd=0,
                                command=self.open_settings)
        settings_btn.image = settings_img  # Keep a reference
        settings_btn.pack(side=tk.RIGHT, padx=5)

        update_img = tk.PhotoImage(file=resource_path("resources/update.png"))
        update_btn = tk.Button(button_frame, image=update_img, bg="#4A6EA9", bd=0, 
                              command=lambda: self.update_manager.check_updates(self.root))
        update_btn.image = update_img  # Keep a reference
        update_btn.pack(side=tk.RIGHT, padx=5)
    
    def _create_pokecenter_buttons(self, parent_frame):
        """Create the PokéCenter buttons"""
        pokecenter_frame = tk.Frame(parent_frame, bg="#F8F8F8")
        pokecenter_frame.pack(pady=20)
        
        pokecenter_buttons_frame = tk.Frame(pokecenter_frame, bg="#F8F8F8")
        pokecenter_buttons_frame.pack()
        
        # Create buttons with teal color
        self._create_button(
            pokecenter_buttons_frame, 
            "PTD 1 PokéCenter", 
            "#5AAA95", "white", 
            lambda: self.open_pokecenter("PTD1")
        ).pack(side=tk.LEFT, padx=5)
        
        self._create_button(
            pokecenter_buttons_frame, 
            "PTD 2 PokéCenter", 
            "#5AAA95", "white", 
            lambda: self.open_pokecenter("PTD2")
        ).pack(side=tk.LEFT, padx=5)
        
        self._create_button(
            pokecenter_buttons_frame, 
            "PTD 3 PokéCenter", 
            "#5AAA95", "white", 
            lambda: self.open_pokecenter("PTD3")
        ).pack(side=tk.LEFT, padx=5)
    
    def _create_game_buttons(self, parent_frame):
        """Create the main game buttons"""
        games_frame = tk.Frame(parent_frame, bg="#F8F8F8")
        games_frame.pack()
        
        games_buttons_frame = tk.Frame(games_frame, bg="#F8F8F8")
        games_buttons_frame.pack()
        
        # Create buttons with blue color
        self._create_button(
            games_buttons_frame, 
            "Play PTD 1", 
            "#4A6EA9", "white", 
            lambda: self.play_game("PTD1")
        ).pack(side=tk.LEFT, padx=5)
        
        self._create_button(
            games_buttons_frame, 
            "Play PTD 2", 
            "#4A6EA9", "white", 
            lambda: self.play_game("PTD2")
        ).pack(side=tk.LEFT, padx=5)
        
        self._create_button(
            games_buttons_frame, 
            "Play PTD 3", 
            "#4A6EA9", "white", 
            lambda: self.play_game("PTD3")
        ).pack(side=tk.LEFT, padx=5)
    
    def _create_special_buttons(self, parent_frame):
        """Create the special/hacked version buttons"""
        special_frame = tk.Frame(parent_frame, bg="#F8F8F8")
        special_frame.pack(pady=20)
        
        hacked_buttons_frame = tk.Frame(special_frame, bg="#F8F8F8")
        hacked_buttons_frame.pack()
        
        # Create buttons with gold color
        self._create_button(
            hacked_buttons_frame, 
            "PTD 1 Hacked", 
            "#E09F3E", "white", 
            lambda: self.play_game("PTD1_Hacked")
        ).pack(side=tk.LEFT, padx=5)
        
        self._create_button(
            hacked_buttons_frame, 
            "PTD 2 Hacked", 
            "#E09F3E", "white", 
            lambda: self.play_game("PTD2_Hacked")
        ).pack(side=tk.LEFT, padx=5)
        
        self._create_button(
            hacked_buttons_frame, 
            "PTD 3 Hacked", 
            "#E09F3E", "white", 
            lambda: self.play_game("PTD3_Hacked")
        ).pack(side=tk.LEFT, padx=5)
    
    def _create_status_bar(self):
        """Create the status bar"""
        self.status_var = tk.StringVar()
        self.status_var.set("Ready")
        status_bar = tk.Label(self.root, textvariable=self.status_var, bd=1, relief=tk.SUNKEN, anchor=tk.W)
        status_bar.pack(side=tk.BOTTOM, fill=tk.X)
    
    def _create_button(self, parent, text, bg_color, fg_color, command):
        """Helper method to create a button with the common style"""
        return tk.Button(
            parent, 
            text=text, 
            bg=bg_color, 
            fg=fg_color, 
            command=command, 
            **self.button_style
        )
    
    def open_pokecenter(self, game):
        """Open the PokéCenter website for the specified game"""
        self.sound_manager.play_sound("opentab")
        
        pokecenter_urls = {
            "PTD1": "https://ptd.ooo/",
            "PTD2": "https://ptd.ooo/ptd2/",
            "PTD3": "https://ptd.ooo/ptd3/"
        }
        
        if game in pokecenter_urls:
            try:
                # Try to open the browser
                webbrowser.open(pokecenter_urls[game])
                self.update_status(f"Opened {game} PokéCenter")
            except Exception as e:
                # If there's an error, show a dialog with the URL
                error_msg = f"Failed to open browser: {str(e)}\n\nPlease manually visit:\n{pokecenter_urls[game]}"
                self.flash_manager.show_dialog(self.root, "Browser Error", error_msg, dialog_type="warning")
                
                # Create a dialog with a copyable URL
                self._show_url_dialog(game, pokecenter_urls[game])
    
    def _show_url_dialog(self, game, url):
        """Show a dialog with a copyable URL"""
        dialog = tk.Toplevel(self.root)
        dialog.title(f"{game} PokéCenter URL")
        dialog.geometry("500x150")
        dialog.resizable(False, False)
        
        # Center the dialog
        self.flash_manager.center_window(dialog, self.root)
        
        # Create the content
        frame = tk.Frame(dialog, padx=20, pady=20)
        frame.pack(fill=tk.BOTH, expand=True)
        
        tk.Label(frame, text="Please copy this URL and paste it into your browser:", font=("Arial", 11)).pack(pady=(0, 10))
        
        # URL entry for copying
        url_var = tk.StringVar(value=url)
        url_entry = tk.Entry(frame, textvariable=url_var, width=50, font=("Arial", 10))
        url_entry.pack(fill=tk.X, pady=5)
        url_entry.select_range(0, tk.END)
        
        # Copy button
        def copy_url():
            dialog.clipboard_clear()
            dialog.clipboard_append(url)
            copy_btn.config(text="Copied!")
            dialog.after(500, lambda: copy_btn.config(text="Copy URL"))
        
        copy_btn = tk.Button(frame, text="Copy URL", command=copy_url, bg="#4A6EA9", fg="white", font=("Arial", 11))
        copy_btn.pack(pady=10)
        
        # Focus the entry for easy copying
        url_entry.focus_set()
    
    def play_game(self, game):
        """Play the specified game"""
        self.sound_manager.play_sound("on")
        
        # Use the game manager to play the game
        result = self.game_manager.play_game(game, parent=self.root)
    
    def open_settings(self):
        """Open settings dialog"""
        self.sound_manager.play_sound("opentab")
        
        settings_window = tk.Toplevel(self.root)
        settings_window.title("Settings")
        settings_window.geometry("400x300")
        settings_window.resizable(False, False)
        
        # Center the window on the parent window
        self._center_window(settings_window)
        
        # Create the settings UI
        self._create_settings_ui(settings_window)
    
    def _create_settings_ui(self, settings_window):
        """Create the settings UI components"""
        # Create main settings frame with a better color scheme
        main_frame = tk.Frame(settings_window, bg="#F8F8F8", padx=15, pady=15)
        main_frame.pack(fill=tk.BOTH, expand=True)
        
        # Add sound settings
        sound_var = self._create_sound_settings(main_frame)
        
        # Add separator
        ttk.Separator(main_frame, orient='horizontal').pack(fill=tk.X, pady=10)
        
        # Add Flash Player settings
        path_var = self._create_flash_player_settings(main_frame)
        
        # Add Flash Player download button
        download_btn = self._create_flash_download_button(main_frame)
        
        # Update button state initially
        if self.flash_manager.is_download_in_progress():
            download_btn.config(state=tk.DISABLED)
            
        # Schedule periodic updates of the button state
        self._schedule_button_update(settings_window, download_btn)
        
        # Add Save and Cancel buttons
        self._create_settings_action_buttons(settings_window, sound_var, path_var)
    
    def _create_sound_settings(self, parent_frame):
        """Create the sound settings section"""
        sound_frame = tk.Frame(parent_frame, bg="#F8F8F8", pady=5)
        sound_frame.pack(fill=tk.X)
        
        tk.Label(sound_frame, text="Sound Effects:", font=("Arial", 11), bg="#F8F8F8").pack(side=tk.LEFT)
        sound_var = tk.BooleanVar(value=self.sound_manager.enabled)
        sound_check = tk.Checkbutton(sound_frame, variable=sound_var, bg="#F8F8F8")
        sound_check.pack(side=tk.LEFT, padx=10)
        
        return sound_var
    
    def _create_flash_player_settings(self, parent_frame):
        """Create the Flash Player settings section"""
        flash_frame = tk.Frame(parent_frame, bg="#F8F8F8", pady=5)
        flash_frame.pack(fill=tk.X)
        
        tk.Label(flash_frame, text="Flash Player Path:", font=("Arial", 11), bg="#F8F8F8").pack(side=tk.LEFT)
        
        # Get Flash Player path from ConfigManager
        default_path = self.config_manager.get_flash_player_path() or ""
        
        path_var = tk.StringVar(value=default_path)
        
        path_entry_frame = tk.Frame(parent_frame, bg="#F8F8F8", pady=5)
        path_entry_frame.pack(fill=tk.X)
        
        path_entry = tk.Entry(path_entry_frame, textvariable=path_var, width=40, font=("Arial", 10))
        path_entry.pack(side=tk.LEFT)
        
        browse_btn = tk.Button(path_entry_frame, text="Browse", 
                             command=lambda: self._browse_flash_player(path_var),
                             bg="#4A6EA9", fg="white", font=("Arial", 10))
        browse_btn.pack(side=tk.LEFT, padx=5)
        
        return path_var
    
    def _create_flash_download_button(self, parent_frame):
        """Create the Flash Player download button"""
        download_frame = tk.Frame(parent_frame, bg="#F8F8F8", pady=10)
        download_frame.pack(fill=tk.X)
        
        download_btn = tk.Button(download_frame, text="Download Flash Player", 
                               command=lambda: self._download_flash_player(download_btn),
                               bg="#4A6EA9", fg="white", font=("Arial", 11))
        download_btn.pack()
        
        return download_btn
    
    def _create_settings_action_buttons(self, settings_window, sound_var, path_var):
        """Create the Save and Cancel buttons for settings"""
        btn_frame = tk.Frame(settings_window, bg="#F8F8F8")
        btn_frame.pack(fill=tk.X, padx=15, pady=15)
        
        cancel_btn = tk.Button(btn_frame, text="Cancel", 
                             command=settings_window.destroy,
                             bg="#6B7A8F", fg="white", font=("Arial", 11), width=10)
        cancel_btn.pack(side=tk.RIGHT, padx=5)
        
        save_btn = tk.Button(btn_frame, text="Save", 
                           command=lambda: self._save_settings(sound_var, path_var, settings_window),
                           bg="#4A6EA9", fg="white", font=("Arial", 11), width=10)
        save_btn.pack(side=tk.RIGHT, padx=5)
    
    def _center_window(self, window):
        """Center a window on its parent"""
        # Use the BaseManager's center_window method
        self.flash_manager.center_window(window, self.root)
    
    def _browse_flash_player(self, path_var):
        """Browse for Flash Player executable"""
        from tkinter import filedialog
        
        # Get the parent window (settings window)
        parent_window = self.root.focus_get().winfo_toplevel()
        
        system = platform.system()
        if system == "Windows":
            filetypes = [("Executable files", "*.exe")]
            initialdir = os.path.dirname(path_var.get()) if os.path.exists(path_var.get()) else self.config_manager.get_flash_dir()
        elif system == "Darwin":  # macOS
            filetypes = [("Application", "*.app")]
            initialdir = os.path.dirname(path_var.get()) if os.path.exists(path_var.get()) else self.config_manager.get_flash_dir()
        elif system == "Linux":
            filetypes = [("All files", "*")]
            initialdir = os.path.dirname(path_var.get()) if os.path.exists(path_var.get()) else self.config_manager.get_flash_dir()
        else:
            filetypes = [("All files", "*")]
            initialdir = os.path.expanduser("~")
        
        # Make sure the parent window stays on top
        parent_window.attributes('-topmost', True)
        
        # Open the file dialog
        filename = filedialog.askopenfilename(
            title="Select Flash Player",
            initialdir=initialdir,
            filetypes=filetypes,
            parent=parent_window  # Explicitly set the parent window
        )
        
        # Restore normal window behavior
        parent_window.attributes('-topmost', False)
        
        # Bring the parent window back to the front
        parent_window.lift()
        parent_window.focus_force()
        
        # Set the selected path if a file was chosen
        if filename:
            path_var.set(filename)
    
    def _download_flash_player(self, download_btn):
        """Download Flash Player and update button state"""
        # Get the settings window
        settings_window = download_btn.winfo_toplevel()
        
        # Only proceed if download is not already in progress
        if not self.flash_manager.is_download_in_progress():
            # Disable the button immediately
            download_btn.config(state=tk.DISABLED)
            
            # Start the download
            self.flash_manager.download_flash_player()
    
    def _update_download_button_state(self, button):
        """Update the download button state based on download status"""
        if self.flash_manager.is_download_in_progress():
            button.config(state=tk.DISABLED)
        else:
            button.config(state=tk.NORMAL)
    
    def _schedule_button_update(self, window, button, interval=500):
        """Schedule periodic updates of the button state"""
        # Update the button state
        self._update_download_button_state(button)
        
        # Schedule the next update if the window still exists
        if window.winfo_exists():
            window.after(interval, lambda: self._schedule_button_update(window, button, interval))
    
    def _save_settings(self, sound_var, path_var, window):
        """Save settings"""
        # Update sound manager
        self.sound_manager.set_enabled(sound_var.get())
        
        # Create settings object
        settings = {
            "sound_enabled": sound_var.get()
        }
        
        # Save Flash Player path if changed
        if path_var.get() and path_var.get() != self.config_manager.get_flash_player_path():
            # Validate the path exists
            if not os.path.exists(path_var.get()):
                self.flash_manager.show_dialog(window, "Error", 
                                             f"Flash Player path does not exist: {path_var.get()}", 
                                             dialog_type="error")
                return
                
            # Get the flash directory based on OS
            flash_dir = self.config_manager.get_flash_dir()
            
            # Create the directory if it doesn't exist
            os.makedirs(flash_dir, exist_ok=True)
            
            # Get the filename from the path
            filename = os.path.basename(path_var.get())
            
            # Copy the file to the flash directory if it's not already there
            if os.path.dirname(path_var.get()) != flash_dir:
                try:
                    import shutil
                    dest_path = os.path.join(flash_dir, filename)
                    
                    # Check if source and destination are the same file
                    if os.path.normpath(path_var.get()) == os.path.normpath(dest_path):
                        # Files are the same, no need to copy
                        pass
                    else:
                        # Copy the file
                        shutil.copy2(path_var.get(), dest_path)
                        
                        # Update the path to point to the copied file
                        path_var.set(dest_path)
                except Exception as e:
                    self.flash_manager.show_dialog(window, "Error", 
                                                 f"Failed to copy Flash Player: {str(e)}", 
                                                 dialog_type="error")
                    return
            
            # Update the version information
            system = platform.system()
            if system == "Windows":
                self.config_manager.config["flash_player"]["windows"]["filename"] = filename
            elif system == "Darwin":  # macOS
                self.config_manager.config["flash_player"]["macos"]["filename"] = filename
            elif system == "Linux":
                self.config_manager.config["flash_player"]["linux"]["filename"] = filename
            
            # Save the version information
            self.config_manager.version["flash_player"] = "custom"
            self.config_manager.save_version_info()
            
            # Add Flash Player path to settings
            settings["flash_player_path"] = path_var.get()
            
            self.update_status(f"Flash Player path updated: {path_var.get()}")
        
        # Save settings to settings.json
        self.config_manager.save_settings(settings)
        
        # Reload settings from file to update the in-memory settings
        self.config_manager.settings = self.config_manager.load_settings()
        
        # Play sound and close window
        self.sound_manager.play_sound("closetab")
        window.destroy()

def main():
    root = tk.Tk()
    app = PTDLauncher(root)
    root.mainloop()

if __name__ == "__main__":
    main()
