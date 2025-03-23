import tkinter as tk
from tkinter import ttk, messagebox
from PIL import Image, ImageTk
import os
from utils import get_resource_path, logger
from game_launcher import open_website, open_flash
from sound_manager import play_sound
from updater import show_update_window
from settings_manager import show_settings_window

def create_button(frame, label, action, color, hover_color):
    """Creates a button with error handling"""
    try:
        def safe_action():
            try:
                action()
            except Exception as e:
                logger.error(f"Error in button action '{label}': {str(e)}")
                messagebox.showerror("Error", f"An error occurred: {str(e)}")
        
        btn = tk.Button(
            frame, text=label, bg=color, fg="white", cursor="hand2",
            font=("Arial", 10), relief="flat", borderwidth=0,
            padx=9, pady=3, command=safe_action,
            activebackground=color, activeforeground="white"
        )
        btn.pack(side=tk.LEFT, padx=10, pady=8)
        
        # Hover effects
        btn.bind("<Enter>", lambda e: btn.config(bg=hover_color))
        btn.bind("<Leave>", lambda e: btn.config(bg=color))
        
        return btn
    except Exception as e:
        logger.error(f"Error creating button '{label}': {str(e)}")
        return None

def create_icon_button(parent, image_path, action, tooltip_text=None):
    """Creates an icon button"""
    try:
        if not os.path.exists(image_path):
            logger.warning(f"Icon image not found: {image_path}")
            return None

        img = Image.open(image_path).resize((24, 24), Image.Resampling.LANCZOS)
        icon = ImageTk.PhotoImage(img)
        
        btn = tk.Button(
            parent, image=icon, bd=0, highlightthickness=0,
            bg="#e5e5e5", activebackground="#d0d0d0", command=action
        )
        btn.image = icon  # Keep a reference

        if tooltip_text:
            # Combine tooltip functions within button definition
            def enter(event):
                try:
                    # First destroy any existing tooltip to prevent duplicates
                    if hasattr(btn, "tooltip") and btn.tooltip:
                        try:
                            btn.tooltip.destroy()
                        except:
                            pass
                    
                    x = btn.winfo_rootx() + 25
                    y = btn.winfo_rooty() + 25
                    
                    tooltip = tk.Toplevel(btn)
                    tooltip.wm_overrideredirect(True)
                    tooltip.wm_geometry(f"+{x}+{y}")
                    
                    tk.Label(tooltip, text=tooltip_text, bg="#ffffe0", relief="solid", borderwidth=1).pack()

                    btn.tooltip = tooltip
                except Exception as e:
                    logger.error(f"Error creating tooltip: {str(e)}")
                
            def leave(event):
                try:
                    if hasattr(btn, "tooltip") and btn.tooltip:
                        btn.tooltip.destroy()
                        btn.tooltip = None
                except Exception as e:
                    logger.error(f"Error destroying tooltip: {str(e)}")
                    
            btn.bind("<Enter>", enter)
            btn.bind("<Leave>", leave)
                
        return btn
    except Exception as e:
        logger.error(f"Error creating icon button: {str(e)}")
        return None

def create_main_ui(root):
    """Creates the main user interface"""
    try:
        logger.info("Creating main UI")
        
        # Load banner - fallback solution in case of error
        try:
            banner_path = get_resource_path("top.png")
            if os.path.exists(banner_path):
                banner_img = ImageTk.PhotoImage(Image.open(banner_path).resize((500, 127), Image.Resampling.LANCZOS))
                banner_label = tk.Label(root, image=banner_img, bg="#e5e5e5")
                banner_label.image = banner_img
            else:
                banner_label = tk.Label(root, text="PTD Launcher", font=("Arial", 24, "bold"), bg="#e5e5e5", height=5)
            banner_label.pack()
        except Exception as e:
            logger.error(f"Error loading banner: {e}")
            tk.Label(root, text="PTD Launcher", font=("Arial", 24, "bold"), bg="#e5e5e5", height=5).pack()

        # Button groups - defined in a single block
        button_groups = [
            # (Button labels, actions, button color, hover color)
            (["PTD 1 PokéCenter", "PTD 2 PokéCenter", "PTD 3 PokéCenter"],
             [lambda: open_website("https://ptd.ooo"), 
              lambda: open_website("https://ptd.ooo/ptd2/"), 
              lambda: open_website("https://ptd.ooo/ptd3/")],
             "#096c09", "#1a7f1d"),

            (["Play PTD 1", "Play PTD 2", "Play PTD 3"],
             [lambda: open_flash("PTD1", "PTD 1"), 
              lambda: open_flash("PTD2", "PTD 2"), 
              lambda: open_flash("PTD3", "PTD 3")],
             "#2a7ab7", "#2d73a9"),

            (["Play PTD 1 Regional Forms", "Play PTD 1 Hacked Version"],
             [lambda: open_flash("PTD1RF", "PTD 1 Regional Forms"), 
              lambda: open_flash("PTD1_Hacked", "PTD 1 Hacked Version")],
             "#2a7ab7", "#2d73a9"),

            (["Play PTD 2 Hacked Version", "Play PTD 3 Hacked Version"],
             [lambda: open_flash("PTD2_Hacked", "PTD 2 Hacked Version"), 
              lambda: open_flash("PTD3_Hacked", "PTD 3 Hacked Version")],
             "#2a7ab7", "#2d73a9")
        ]

        # Style configuration
        ttk.Style().configure("Main.TFrame", background="#e5e5e5")
        main_frame = ttk.Frame(root, style="Main.TFrame")
        main_frame.pack(pady=(14, 0))

        # Create button groups
        for labels, actions, color, hover_color in button_groups:
            frame = ttk.Frame(main_frame, style="Main.TFrame")
            frame.pack()
            for i, label in enumerate(labels):
                create_button(frame, label, actions[i], color, hover_color)
                
        # Top icons frame
        ttk.Style().configure("TopIcons.TFrame", background="#de0505")
        top_icons_frame = ttk.Frame(root, style="TopIcons.TFrame")
        top_icons_frame.place(relx=1.0, y=10, anchor="ne")

        # Create a function to apply background color to images
        def apply_background_to_image(image_path, bg_color="#de0505"):
            img = Image.open(image_path)
            img = img.convert("RGBA")
            
            # Create a new image with the background color
            background = Image.new("RGBA", img.size, bg_color)
            
            # Composite the original image onto the background
            composite = Image.alpha_composite(background, img)
            
            butt_img = ImageTk.PhotoImage(composite)
            
            butt_btn = tk.Label(
                top_icons_frame, 
                image=butt_img, 
                bg="#de0505", 
                cursor="hand2"
            )
            butt_btn.image = butt_img  # Keep a reference to prevent garbage collection
            butt_btn.pack(side=tk.LEFT, padx=5, pady=5)
            butt_btn.bind("<Enter>", lambda e: e.widget.configure(bg="#ff1a1a"))
            butt_btn.bind("<Leave>", lambda e: e.widget.configure(bg="#de0505"))
            
            return butt_btn

        # Update icon
        update_btn = apply_background_to_image(get_resource_path("update.png"))
        update_btn.bind("<Button-1>", lambda e: show_update_window(root))

        # Settings icon
        settings_btn = apply_background_to_image(get_resource_path("settings.png"))
        settings_btn.bind("<Button-1>", lambda e: show_settings_window(root))

        # Graceful exit
        def on_close():
            try:
                logger.info("Application closing")
                play_sound("off.mp3")
                root.after(500, root.destroy)
            except Exception as e:
                logger.error(f"Error during close: {e}")
                root.destroy()
                
        root.protocol("WM_DELETE_WINDOW", on_close)
        logger.info("Main UI created successfully")
    except Exception as e:
        logger.error(f"Error creating main UI: {e}")
        messagebox.showerror("UI Error", f"An error occurred: {e}")