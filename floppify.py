import os
import time
import threading
import tkinter as tk
from tkinter import messagebox
from PIL import Image, ImageTk
import spotipy
from spotipy.oauth2 import SpotifyOAuth
import requests
from io import BytesIO
import random
import tkinter.font as tkFont
import uuid  # For generating unique IDs
import queue  # For thread-safe message passing
from dotenv import load_dotenv  # To load environment variables

# Load environment variables from .env file
load_dotenv()

# Retrieve environment variables
CLIENT_ID = os.getenv('CLIENT_ID')
CLIENT_SECRET = os.getenv('CLIENT_SECRET')
REDIRECT_URI = os.getenv('REDIRECT_URI')
LOCAL_DEVICE_ID = os.getenv('LOCAL_DEVICE_ID')
DRIVE_LETTER = os.getenv('DRIVE_LETTER', 'F')  # Default to 'F' if not set

# ----------------------------
# Initialize Log Queue
# ----------------------------
log_queue = queue.Queue()

def log_message(message):
    """
    Logs a message by printing it to the console and enqueueing it for the GUI.
    """
    print(message)  # Print to console
    log_queue.put(message)  # Enqueue for GUI

# ----------------------------
# Spotify Authentication Setup
# ----------------------------

# Validate that necessary environment variables are set
if not all([CLIENT_ID, CLIENT_SECRET, REDIRECT_URI, LOCAL_DEVICE_ID]):
    missing = [var for var, val in [('CLIENT_ID', CLIENT_ID), 
                                   ('CLIENT_SECRET', CLIENT_SECRET),
                                   ('REDIRECT_URI', REDIRECT_URI),
                                   ('LOCAL_DEVICE_ID', LOCAL_DEVICE_ID)] if not val]
    log_message(f"Missing environment variables: {', '.join(missing)}")
    raise EnvironmentError(f"Please set the missing environment variables in the .env file: {', '.join(missing)}")

# Set up Spotify authentication
sp_oauth = SpotifyOAuth(
    client_id=CLIENT_ID,
    client_secret=CLIENT_SECRET,
    redirect_uri=REDIRECT_URI,
    scope='user-modify-playback-state user-read-playback-state user-read-currently-playing',
    open_browser=True,
    show_dialog=True  # Force login screen
)

sp = spotipy.Spotify(auth_manager=sp_oauth)

# ----------------------------
# Spotify Control Functions
# ----------------------------

# Function to authenticate with Spotify
def authenticate_spotify():
    token_info = sp_oauth.get_cached_token()
    if not token_info:
        auth_url = sp_oauth.get_authorize_url()
        log_message(f"Please navigate here: {auth_url}")
        import webbrowser
        webbrowser.open(auth_url, new=1)
        # Wait for user to authorize and get the response
        while True:
            try:
                token_info = sp_oauth.get_access_token(as_dict=False)
                break
            except:
                time.sleep(1)
    else:
        sp_oauth.validate_token(token_info)

# Function to list available devices
def list_devices():
    devices = sp.devices()
    log_message("Available devices:")
    for device in devices['devices']:
        log_message(f"Name: {device['name']}, ID: {device['id']}, Type: {device['type']}")

# Function to check if the local device is available
def is_device_available(device_id):
    devices = sp.devices()
    for device in devices['devices']:
        if device['id'] == device_id:
            return True
    return False

# Function to check if the floppy disk is inserted
def is_floppy_disk_inserted(drive_letter):
    filepath = f'{drive_letter}:\\playlist.txt'
    return os.path.exists(filepath)

# Function to read the Spotify URIs or URLs from the floppy disk and select one at random
def get_spotify_uri_from_floppy(drive_letter):
    filepath = f'{drive_letter}:\\playlist.txt'
    try:
        with open(filepath, 'r') as f:
            lines = f.readlines()
            lines = [line.strip() for line in lines if line.strip()]
            if lines:
                uri_or_url = random.choice(lines)  # Select one at random
                return uri_or_url
            else:
                return None
    except FileNotFoundError:
        return None

# Function to parse Spotify URI or URL
def parse_spotify_uri(uri_or_url):
    if uri_or_url.startswith('spotify:'):
        return uri_or_url
    elif 'open.spotify.com' in uri_or_url:
        parts = uri_or_url.strip().split('/')
        if len(parts) >= 5:
            uri_type = parts[3]
            uri_id = parts[4].split('?')[0]
            return f'spotify:{uri_type}:{uri_id}'
    return None

# Function to get the Spotify item's name
def get_spotify_item_name(uri):
    try:
        uri_parts = uri.split(':')
        if len(uri_parts) < 3:
            return None
        uri_type = uri_parts[1]
        uri_id = uri_parts[2]
        if uri_type == 'playlist':
            playlist = sp.playlist(uri_id)
            return f"Playlist: {playlist['name']}"
        elif uri_type == 'album':
            album = sp.album(uri_id)
            return f"Album: {album['name']}"
        elif uri_type == 'track':
            track = sp.track(uri_id)
            return f"Track: {track['name']}"
        elif uri_type == 'artist':
            artist = sp.artist(uri_id)
            return f"Artist: {artist['name']}"
        else:
            return None
    except Exception as e:
        log_message(f"Error getting item name: {e}")
        return None

# Function to play the Spotify URI on the local device
def play_spotify_uri(uri):
    try:
        device_id = LOCAL_DEVICE_ID

        if not is_device_available(device_id):
            messagebox.showerror("Device Error", "Local device not available. Please open Spotify on your computer.")
            return

        # Transfer playback to the local device
        sp.transfer_playback(device_id=device_id, force_play=True)

        if 'track' in uri:
            sp.start_playback(device_id=device_id, uris=[uri])
        else:
            sp.start_playback(device_id=device_id, context_uri=uri)
        log_message(f"Started playback for URI: {uri}")
    except spotipy.exceptions.SpotifyException as e:
        log_message(f"Error starting playback: {e}")
        messagebox.showerror("Playback Error", str(e))

# Function to stop Spotify playback
def stop_playback():
    try:
        log_message("Stopping playback...")
        sp.pause_playback(device_id=LOCAL_DEVICE_ID)
        log_message("Playback stopped.")
    except spotipy.exceptions.SpotifyException as e:
        log_message(f"Error stopping playback: {e}")
        messagebox.showerror("Playback Error", str(e))

# Function to toggle play/pause
def toggle_play_pause():
    try:
        playback = sp.current_playback()
        if playback and playback['is_playing']:
            sp.pause_playback(device_id=LOCAL_DEVICE_ID)
            log_message("Paused playback.")
        else:
            sp.start_playback(device_id=LOCAL_DEVICE_ID)
            log_message("Resumed playback.")
    except spotipy.exceptions.SpotifyException as e:
        log_message(f"Error toggling playback: {e}")
        messagebox.showerror("Playback Error", str(e))

# Function to toggle shuffle
def toggle_shuffle():
    try:
        playback = sp.current_playback()
        if playback and 'shuffle_state' in playback:
            new_shuffle = not playback['shuffle_state']
            sp.shuffle(new_shuffle, device_id=LOCAL_DEVICE_ID)
            state = "enabled" if new_shuffle else "disabled"
            log_message(f"Shuffle {state}.")
    except spotipy.exceptions.SpotifyException as e:
        log_message(f"Error toggling shuffle: {e}")
        messagebox.showerror("Shuffle Error", str(e))

# Function to toggle loop (repeat)
def toggle_loop():
    try:
        playback = sp.current_playback()
        if playback and 'repeat_state' in playback:
            current_state = playback['repeat_state']
            new_state = "off"
            if current_state == "off":
                new_state = "context"  # Loop the playlist
            elif current_state == "context":
                new_state = "track"    # Loop the current track
            elif current_state == "track":
                new_state = "off"       # Disable looping

            sp.repeat(new_state, device_id=LOCAL_DEVICE_ID)
            log_message(f"Loop set to {new_state}.")
    except spotipy.exceptions.SpotifyException as e:
        log_message(f"Error toggling loop: {e}")
        messagebox.showerror("Loop Error", str(e))

# ----------------------------
# Helper Functions for Unique ID
# ----------------------------

def generate_unique_id():
    return str(uuid.uuid4())

def write_unique_id(drive_letter, unique_id):
    unique_id_path = f'{drive_letter}:\\unique_id.txt'
    try:
        with open(unique_id_path, 'w') as f:
            f.write(unique_id)
        log_message(f"Unique ID written to {unique_id_path}: {unique_id}")
    except Exception as e:
        log_message(f"Error writing unique ID: {e}")

def read_unique_id(drive_letter):
    unique_id_path = f'{drive_letter}:\\unique_id.txt'
    try:
        with open(unique_id_path, 'r') as f:
            unique_id = f.read().strip()
            log_message(f"Unique ID read from {unique_id_path}: {unique_id}")
            return unique_id
    except FileNotFoundError:
        return None
    except Exception as e:
        log_message(f"Error reading unique ID: {e}")
        return None

def unique_id_exists(drive_letter):
    unique_id_path = f'{drive_letter}:\\unique_id.txt'
    return os.path.exists(unique_id_path)

# ----------------------------
# Marquee Class for Scrolling Text
# ----------------------------

class Marquee(tk.Label):
    def __init__(self, parent, text, font, width, fg, bg, delay=150):
        super().__init__(parent, font=font, fg=fg, bg=bg, width=width, anchor='w')
        self.original_text = text
        self.text = text
        self.delay = delay  # milliseconds
        self.after_id = None
        self.scroll_active = False
        self.font_obj = tkFont.Font(font=self['font'])
        self.bind('<Configure>', self.check_scroll)

    def set_text(self, text):
        self.original_text = text
        self.check_scroll()

    def check_scroll(self, event=None):
        # Measure text width
        text_width = self.font_obj.measure(self.original_text)
        label_width = self.winfo_width()
        if text_width > label_width:
            if not self.scroll_active:
                self.scroll_active = True
                self.text = self.original_text + '   '  # Add spaces for smooth scrolling
                self.current_index = 0
                self.after_id = self.after(self.delay, self.scroll_text)
        else:
            if self.scroll_active:
                self.scroll_active = False
                if self.after_id:
                    self.after_cancel(self.after_id)
                    self.after_id = None
            self.configure(text=self.original_text)

    def scroll_text(self):
        if self.scroll_active:
            self.text = self.text[1:] + self.text[0]
            self.configure(text=self.text)
            self.after_id = self.after(self.delay, self.scroll_text)

# ----------------------------
# Gradient Background Canvas (Horizontal Gradient)
# ----------------------------

class GradientCanvas(tk.Canvas):
    def __init__(self, parent, width, height, color1, color2, color3, **kwargs):
        super().__init__(parent, width=width, height=height, highlightthickness=0, **kwargs)
        self.width = width
        self.height = height
        self.color1 = color1
        self.color2 = color2
        self.color3 = color3
        self.create_gradient()

    def create_gradient(self):
        """Creates a three-phase horizontal gradient."""
        limit = self.width
        for i in range(limit):
            # Calculate intermediate color between color1 and color2
            r1, g1, b1 = self.hex_to_rgb(self.color1)
            r2, g2, b2 = self.hex_to_rgb(self.color2)
            r = int(r1 + (r2 - r1) * i / (limit / 2))
            g = int(g1 + (g2 - g1) * i / (limit / 2))
            b = int(b1 + (b2 - b1) * i / (limit / 2))
            if i > limit / 2:
                # Calculate intermediate color between color2 and color3
                ratio = (i - limit / 2) / (limit / 2)
                r = int(r2 + (self.hex_to_rgb(self.color3)[0] - r2) * ratio)
                g = int(g2 + (self.hex_to_rgb(self.color3)[1] - g2) * ratio)
                b = int(b2 + (self.hex_to_rgb(self.color3)[2] - b2) * ratio)
            color = f'#{r:02x}{g:02x}{b:02x}'
            self.create_line(i, 0, i, self.height, fill=color)

    @staticmethod
    def hex_to_rgb(hex_color):
        """Converts hex color to RGB tuple."""
        hex_color = hex_color.lstrip('#')
        return tuple(int(hex_color[i:i+2], 16) for i in (0, 2 ,4))

# ----------------------------
# Custom Title Bar
# ----------------------------

class CustomTitleBar(tk.Frame):
    def __init__(self, master, *args, **kwargs):
        super().__init__(master, bg='#008000')  #  green
        self.master = master
        self.init_widgets()
        self.bind_events()

    def init_widgets(self):
        # Floppify Logo
        try:
            logo_image = Image.open("./images/floppify_logo.png").convert("RGBA")
            logo_image = logo_image.resize((30, 30), Image.Resampling.LANCZOS)
            self.logo_photo = ImageTk.PhotoImage(logo_image)
            self.logo_label = tk.Label(self, image=self.logo_photo, bg='#008000')
            self.logo_label.pack(side='left', padx=5)
        except FileNotFoundError:
            self.logo_label = tk.Label(self, text="Floppify", bg='#008000', fg='white', font=('Arial', 12, 'bold'))
            self.logo_label.pack(side='left', padx=5)

        # Window Title
        self.title_label = tk.Label(self, text="FLOPPIFY", bg='#008000', fg='white', font=('LED Dot-Matrix', 12))
        self.title_label.pack(side='left', padx=5)

        # Spacer
        self.spacer = tk.Label(self, bg='#008000')
        self.spacer.pack(side='left', expand=True, fill='x')

        # Minimize and Close Buttons
        try:
            minimize_image = Image.open("./images/minimize.png").convert("RGBA")
            minimize_image = minimize_image.resize((20, 20), Image.Resampling.LANCZOS)
            self.minimize_photo = ImageTk.PhotoImage(minimize_image)
            self.minimize_button = tk.Button(self, image=self.minimize_photo, bg='#008000', bd=0, activebackground='#006400', command=self.minimize_window)
            self.minimize_button.pack(side='right', padx=2)

            close_image = Image.open("./images/close.png").convert("RGBA")
            close_image = close_image.resize((20, 20), Image.Resampling.LANCZOS)
            self.close_photo = ImageTk.PhotoImage(close_image)
            self.close_button = tk.Button(self, image=self.close_photo, bg='#008000', bd=0, activebackground='#006400', command=self.master.destroy)
            self.close_button.pack(side='right', padx=2)
        except FileNotFoundError:
            self.minimize_button = tk.Button(self, text="_", bg='#008000', fg='white', bd=0, command=self.minimize_window)
            self.minimize_button.pack(side='right', padx=2)
            self.close_button = tk.Button(self, text="X", bg='#008000', fg='white', bd=0, command=self.master.destroy)
            self.close_button.pack(side='right', padx=2)

    def bind_events(self):
        self.bind("<ButtonPress-1>", self.start_move)
        self.bind("<ButtonRelease-1>", self.stop_move)
        self.bind("<B1-Motion>", self.on_move)

        self.logo_label.bind("<ButtonPress-1>", self.start_move)
        self.logo_label.bind("<ButtonRelease-1>", self.stop_move)
        self.logo_label.bind("<B1-Motion>", self.on_move)

        self.title_label.bind("<ButtonPress-1>", self.start_move)
        self.title_label.bind("<ButtonRelease-1>", self.stop_move)
        self.title_label.bind("<B1-Motion>", self.on_move)

    def minimize_window(self):
        self.master.iconify()

    def start_move(self, event):
        self.x = event.x
        self.y = event.y

    def stop_move(self, event):
        self.x = None
        self.y = None

    def on_move(self, event):
        deltax = event.x - self.x
        deltay = event.y - self.y
        x = self.master.winfo_x() + deltax
        y = self.master.winfo_y() + deltay
        self.master.geometry(f"+{x}+{y}")

# ----------------------------
#  Floppify Player GUI
# ----------------------------

class FloppifyPlayer:
    def __init__(self, master):
        self.master = master
        # Set window size to 800x450 and prevent resizing
        self.master.geometry("550x450")
        self.master.resizable(True, True)
        self.master.overrideredirect(True)  # Remove default window decorations

        # Initialize Gradient Background
        self.gradient = GradientCanvas(master, width=550, height=450, color1='#191925', color2='#31314f', color3='#1c1c2c')
        self.gradient.place(x=0, y=0)

        # Initialize Custom Title Bar
        self.title_bar = CustomTitleBar(master)
        self.title_bar.place(x=0, y=0, width=550, height=40)

        # Define font styles
        try:
            label_font = ('LED Dot-Matrix', 10)  # Ensure this font is installed
            text_font = ('LED Dot-Matrix', 16)
        except:
            # Fallback to default font if custom font not available
            label_font = ('Courier', 10)
            text_font = ('Courier', 16)

        # ------------------------
        # Layout Frames with Reverse Bevel
        # ------------------------
        bevel_options = {'relief': 'sunken', 'bd': 2, 'bg': '#1f1f2e'}  # Dark grey background

        self.right_frame = tk.Frame(master, **bevel_options)
        self.right_frame.place(x=230, y=60, width=300, height=200)

        self.buttons_frame = tk.Frame(master, **bevel_options)
        self.buttons_frame.place(x=20, y=270, width=510, height=60)

        self.log_frame = tk.Frame(master, **bevel_options)
        self.log_frame.place(x=20, y=350, width=510, height=80)

        # ------------------------
        # Left Section: Floppy Disk with Album Cover (Placed Directly on Gradient)
        # ------------------------
        try:
            floppy_image = Image.open("./images/floppy_disk.png").convert("RGBA")
            floppy_image = floppy_image.resize((200, 200), Image.Resampling.LANCZOS)
            self.floppy_photo = ImageTk.PhotoImage(floppy_image)
            # Place floppy_label directly on the gradient canvas with dark grey background
            self.floppy_label = tk.Label(master, image=self.floppy_photo,  **bevel_options)
            self.floppy_label.image = self.floppy_photo  # Prevent garbage collection
            # Position the floppy_label at (120, 160)
            self.gradient.create_window(120, 160, window=self.floppy_label)
        except FileNotFoundError:
            # If the image is not found, display a placeholder text directly on the gradient
            self.floppy_label = tk.Label(master, text="Floppy Disk", fg='#FFFFFF', bg='#1f1f2e', font=('Arial', 12))
            self.gradient.create_window(120, 160, window=self.floppy_label)

        # Placeholder for Album Cover (Placed Directly on Gradient) - COVER LOCATION
        self.album_cover_photo = None
        self.album_cover_label = tk.Label(master, bg='#1f1f2e')
        self.album_cover_label.image = None  # Initialize to prevent errors
        self.gradient.create_window(120, 120, window=self.album_cover_label)  # Adjust coordinates as needed

        # ----------------------------
        # Right Frame: Track, Artist, Album Information
        # ----------------------------
        # Track Information
        track_frame = tk.Frame(self.right_frame, bg='#1f1f2e')
        track_frame.pack(anchor='nw', pady=(10,5), fill='x')

        track_static = tk.Label(track_frame, text='TRK:', font=label_font, fg='#00FF00', bg='#1f1f2e')
        track_static.pack(side='left', padx=5)

        self.track_marquee = Marquee(track_frame, text='', font=text_font, width=25, fg='#00FF00', bg='#1f1f2e')
        self.track_marquee.pack(side='left', padx=5)

        # Artist Information
        artist_frame = tk.Frame(self.right_frame, bg='#1f1f2e')
        artist_frame.pack(anchor='nw', pady=5, fill='x')

        artist_static = tk.Label(artist_frame, text='ART:', font=label_font, fg='#00FF00', bg='#1f1f2e')
        artist_static.pack(side='left', padx=5)

        self.artist_marquee = Marquee(artist_frame, text='', font=text_font, width=25, fg='#00FF00', bg='#1f1f2e')
        self.artist_marquee.pack(side='left', padx=5)

        # Album Information
        album_frame = tk.Frame(self.right_frame, bg='#1f1f2e')
        album_frame.pack(anchor='nw', pady=5, fill='x')

        album_static = tk.Label(album_frame, text='ALB:', font=label_font, fg='#00FF00', bg='#1f1f2e')
        album_static.pack(side='left', padx=5)

        self.album_marquee = Marquee(album_frame, text='', font=text_font, width=25, fg='#00FF00', bg='#1f1f2e')
        self.album_marquee.pack(side='left', padx=5)

        # ------------------------
        # Additional Information: kbps and kHz
        # ------------------------
        info_frame = tk.Frame(self.right_frame, bg='#1f1f2e')
        info_frame.pack(anchor='nw', pady=5, fill='x')

        kbps_label = tk.Label(info_frame, text='KBPS:', font=label_font, fg='#00FF00', bg='#1f1f2e')
        kbps_label.pack(side='left', padx=5)

        self.kbps_var = tk.StringVar(value="190")
        self.kbps_display = tk.Label(info_frame, textvariable=self.kbps_var, font=text_font, fg='#00FF00', bg='#1f1f2e')
        self.kbps_display.pack(side='left', padx=5)

        khz_label = tk.Label(info_frame, text='KHZ:', font=label_font, fg='#00FF00', bg='#1f1f2e')
        khz_label.pack(side='left', padx=15)

        self.khz_var = tk.StringVar(value="44")
        self.khz_display = tk.Label(info_frame, textvariable=self.khz_var, font=text_font, fg='#00FF00', bg='#1f1f2e')
        self.khz_display.pack(side='left', padx=5)

        # ----------------------------
        # Volume Control: 11 Segments with Gradient and Buttons
        # ----------------------------
        volume_frame = tk.Frame(self.right_frame, bg='#1f1f2e')
        volume_frame.pack(pady=(10, 0), fill='x')

        # Volume Down Button
        try:
            volume_down_image = Image.open("./images/volume_down.png").convert("RGBA")
            volume_down_image = volume_down_image.resize((30, 30), Image.Resampling.LANCZOS)
            self.volume_down_photo = ImageTk.PhotoImage(volume_down_image)
            self.volume_down_button = tk.Button(volume_frame, image=self.volume_down_photo, bg='#1f1f2e', bd=0, activebackground='#696969', command=self.decrease_volume)
            self.volume_down_button.pack(side='left', padx=5)
        except FileNotFoundError:
            self.volume_down_button = tk.Button(volume_frame, text="↓", bg='#1f1f2e', fg='#00FF00', bd=0, font=('Arial', 12), command=self.decrease_volume)
            self.volume_down_button.pack(side='left', padx=5)

        # Volume Segments
        self.volume_segments = []
        segment_width = 20
        segment_height = 20
        spacing = 2
        for i in range(11):
            frame = tk.Frame(volume_frame, width=segment_width, height=segment_height, bg='grey', relief='raised', bd=1)
            frame.pack(side='left', padx=1)
            self.volume_segments.append(frame)

        # Volume Up Button
        try:
            volume_up_image = Image.open("./images/volume_up.png").convert("RGBA")
            volume_up_image = volume_up_image.resize((30, 30), Image.Resampling.LANCZOS)
            self.volume_up_photo = ImageTk.PhotoImage(volume_up_image)
            self.volume_up_button = tk.Button(volume_frame, image=self.volume_up_photo, bg='#1f1f2e', bd=0, activebackground='#696969', command=self.increase_volume)
            self.volume_up_button.pack(side='left', padx=5)
        except FileNotFoundError:
            self.volume_up_button = tk.Button(volume_frame, text="↑", bg='#1f1f2e', fg='#00FF00', bd=0, font=('Arial', 12), command=self.increase_volume)
            self.volume_up_button.pack(side='left', padx=5)

        # Initialize current volume
        self.current_volume = 50  # Default volume
        self.update_volume_segments(self.current_volume)

        # ----------------------------
        # Buttons Frame: Shuffle, Loop, Previous, Play/Pause, Next
        # ----------------------------
        # Load button images
        try:

            self.prev_img = ImageTk.PhotoImage(Image.open("./images/previous.png").resize((50, 40), Image.Resampling.LANCZOS))
            self.play_img = ImageTk.PhotoImage(Image.open("./images/play.png").resize((50, 40), Image.Resampling.LANCZOS))
            self.pause_img = ImageTk.PhotoImage(Image.open("images/pause.png").resize((50, 40), Image.Resampling.LANCZOS))
            self.next_img = ImageTk.PhotoImage(Image.open("./images/next.png").resize((50, 40), Image.Resampling.LANCZOS))
            self.shuffle_img = ImageTk.PhotoImage(Image.open("./images/shuffle.png").resize((120, 30), Image.Resampling.LANCZOS))
            self.loop_img = ImageTk.PhotoImage(Image.open("./images/loop.png").resize((60, 30), Image.Resampling.LANCZOS))
        except FileNotFoundError as e:
            messagebox.showerror("Image Error", f"Button image not found: {e}")
            return



        # Previous Button
        self.prev_button = tk.Button(
            self.buttons_frame, image=self.prev_img, bg='#1f1f2e', bd=0, activebackground='#696969',
            command=lambda: sp.previous_track(device_id=LOCAL_DEVICE_ID)
        )
        self.prev_button.pack(side='left', padx=1)

        # Play/Pause Button
        self.play_pause_button = tk.Button(
            self.buttons_frame, image=self.play_img, bg='#1f1f2e', bd=0, activebackground='#696969',
            command=self.on_play_pause
        )
        self.play_pause_button.pack(side='left', padx=1)

        # Next Button
        self.next_button = tk.Button(
            self.buttons_frame, image=self.next_img, bg='#1f1f2e', bd=0, activebackground='#696969',
            command=lambda: sp.next_track(device_id=LOCAL_DEVICE_ID)
        )
        self.next_button.pack(side='left', padx=1)


                # Shuffle Button
        self.shuffle_button = tk.Button(
            self.buttons_frame, image=self.shuffle_img, bg='#1f1f2e', bd=0, activebackground='#696969',
            command=self.toggle_shuffle
        )
        self.shuffle_button.pack(side='left', padx=30)

        # Loop Button
        self.loop_button = tk.Button(
            self.buttons_frame, image=self.loop_img, bg='#1f1f2e', bd=0, activebackground='#696969',
            command=self.toggle_loop
        )
        self.loop_button.pack(side='left', padx=1)

        # ----------------------------
        # Log Frame: Console/Message Log
        # ----------------------------
        # Create a Text widget for logs (read-only)
        self.log_text = tk.Text(self.log_frame, height=5, width=95, bg='#00FF00', fg='#000000', state='disabled', bd=0, wrap='word', font=('LED Dot-Matrix', 12))
        self.log_text.pack()

        # Initialize log history
        self.log_history = []

        # Start the GUI update loop
        self.update_gui()

    # ----------------------------
    # Playback Control Methods
    # ----------------------------

    def on_play_pause(self):
        toggle_play_pause()
        self.update_play_pause_button()

    def update_play_pause_button(self):
        playback = sp.current_playback()
        if playback and playback['is_playing']:
            self.play_pause_button.config(image=self.pause_img)
            self.is_playing = True
        else:
            self.play_pause_button.config(image=self.play_img)
            self.is_playing = False

    def toggle_shuffle(self):
        toggle_shuffle()

    def toggle_loop(self):
        toggle_loop()

    # ----------------------------
    # Volume Control Methods
    # ----------------------------

    def increase_volume(self):
        if self.current_volume < 100:
            self.current_volume += 10
            if self.current_volume > 100:
                self.current_volume = 100
            self.set_volume(self.current_volume)

    def decrease_volume(self):
        if self.current_volume > 0:
            self.current_volume -= 10
            if self.current_volume < 0:
                self.current_volume = 0
            self.set_volume(self.current_volume)

    def set_volume(self, volume):
        """Sets the volume both in Spotify and updates the GUI segments."""
        try:
            sp.volume(volume, device_id=LOCAL_DEVICE_ID)
            log_message(f"Volume set to {volume}%")
            self.update_volume_segments(volume)
            self.current_volume = volume
        except spotipy.exceptions.SpotifyException as e:
            log_message(f"Error setting volume: {e}")
            messagebox.showerror("Volume Error", str(e))

    def update_volume_segments(self, volume):
        """Updates the visual representation of volume segments."""
        segments_to_fill = volume // 10
        for i in range(11):
            if i <= segments_to_fill:
                # Apply gradient color
                color = self.get_gradient_color(i)
                self.volume_segments[i].config(bg=color)
            else:
                self.volume_segments[i].config(bg='grey')

    def get_gradient_color(self, segment):
        """Returns a color based on the segment index for gradient effect."""
        if segment <= 3:
            return '#006400'  # Dark green
        elif 4 <= segment <= 6:
            return '#00FF00'  # Light green
        elif 7 <= segment <= 8:
            return '#FFFF00'  # Yellow
        elif 9 <= segment <= 10:
            return '#FFA500'  # Orange
        else:
            return '#FF0000'  # Red

    # ----------------------------
    # GUI Update Loop
    # ----------------------------

    def update_gui(self):
        try:
            # Process any messages in the log_queue
            while not log_queue.empty():
                message = log_queue.get_nowait()
                # Avoid printing duplicate consecutive messages
                if not self.log_history or self.log_history[-1] != message:
                    self.log_history.append(message)
                    if len(self.log_history) > 10:
                        self.log_history.pop(0)
                    # Update the log_text widget
                    self.log_text.config(state='normal')
                    self.log_text.delete(1.0, tk.END)
                    self.log_text.insert(tk.END, '\n'.join(self.log_history))
                    self.log_text.config(state='disabled')

            playback = sp.current_playback()
            if playback:
                is_playing = playback['is_playing']
                track = playback['item']
                if is_playing and track:
                    track_name = track['name']
                    artist_name = ', '.join([artist['name'] for artist in track['artists']])
                    album_name = track['album']['name']
                    album_cover_url = track['album']['images'][0]['url']

                    # Update Marquee texts
                    self.track_marquee.set_text(f'{track_name}')
                    self.artist_marquee.set_text(f'{artist_name}')
                    self.album_marquee.set_text(f'{album_name}')

                    # Update Album Cover  -- COVER SIZE
                    response = requests.get(album_cover_url)
                    img_data = response.content
                    img = Image.open(BytesIO(img_data)).convert("RGBA")
                    img = img.resize((110, 95), Image.Resampling.LANCZOS)
                    album_cover = ImageTk.PhotoImage(img)

                    # Overlay Album Cover on Gradient Canvas
                    # Remove previous album cover if exists
                    if self.album_cover_photo:
                        self.album_cover_label.config(image='')
                        self.album_cover_label.image = None
                    self.album_cover_photo = album_cover
                    self.album_cover_label.config(image=self.album_cover_photo)
                    self.album_cover_label.image = self.album_cover_photo  # Prevent garbage collection

                    # Update Play/Pause Button Icon
                    self.play_pause_button.config(image=self.pause_img)
                    self.is_playing = True

                    # Update kbps and kHz (Set to fixed values as per user instruction)
                    self.kbps_var.set("192")
                    self.khz_var.set("44")

                    # Update Volume Segments and enforce app's volume control
                    if 'device' in playback and playback['device']:
                        current_volume = playback['device']['volume_percent']
                        if self.current_volume != current_volume:
                            log_message(f"Spotify volume changed externally to {current_volume}%, resetting to {self.current_volume}%")
                            self.set_volume(self.current_volume)
                else:
                    # Update Marquee texts to default
                    self.track_marquee.set_text('Not available')
                    self.artist_marquee.set_text('Not available')
                    self.album_marquee.set_text('Not available')
                    
                    # Remove Album Cover
                    if self.album_cover_photo:
                        self.album_cover_label.config(image='')
                        self.album_cover_label.image = None

                    # Update Play/Pause Button Icon
                    self.play_pause_button.config(image=self.play_img)
                    self.is_playing = False

                    # Update kbps and kHz
                    self.kbps_var.set("N/A")
                    self.khz_var.set("N/A")

                    # Update Volume Segments and enforce app's volume control
                    if self.current_volume != 0:
                        log_message(f"Spotify volume changed externally to {self.current_volume}%, resetting to 0%")
                        self.set_volume(0)
            else:
                # No playback information available
                self.track_marquee.set_text('Not available')
                self.artist_marquee.set_text('Not available')
                self.album_marquee.set_text('Not available')
                
                # Remove Album Cover
                if self.album_cover_photo:
                    self.album_cover_label.config(image='')
                    self.album_cover_label.image = None

                # Update Play/Pause Button Icon
                self.play_pause_button.config(image=self.play_img)
                self.is_playing = False

                # Update kbps and kHz
                self.kbps_var.set("N/A")
                self.khz_var.set("N/A")

                # Update Volume Segments and enforce app's volume control
                if self.current_volume != 0:
                    log_message(f"Spotify volume changed externally to {self.current_volume}%, resetting to 0%")
                    self.set_volume(0)

            # Update Volume Segments (already handled above)
        except Exception as e:
            log_message(f"Error in update_gui: {e}")
        # Schedule the next update
        self.master.after(1000, self.update_gui)  # Updated to 1 second for smoother updates

# ----------------------------
# Main Loop to Monitor the Floppy Disk
# ----------------------------

def main():
    current_unique_id = None  # Tracks the current session's unique ID
    disk_inserted = False
    drive_letter = DRIVE_LETTER  # Loaded from .env

    while True:
        inserted = is_floppy_disk_inserted(drive_letter)
        log_message(f"Disk Inserted: {inserted}")

        if inserted and not disk_inserted:
            # Disk was inserted
            log_message("Disk inserted")
            unique_id = read_unique_id(drive_letter)
            if not unique_id:
                # If unique_id.txt does not exist, generate and write it
                unique_id = generate_unique_id()
                write_unique_id(drive_letter, unique_id)
                log_message(f"Generated new unique ID for disk: {unique_id}")

            if unique_id != current_unique_id:
                # Play a new playlist
                uri_or_url = get_spotify_uri_from_floppy(drive_letter)
                if uri_or_url:
                    uri = parse_spotify_uri(uri_or_url)
                    if uri:
                        item_name = get_spotify_item_name(uri)
                        if item_name:
                            log_message(f"Playing {item_name} ({uri})")
                        else:
                            log_message(f"Playing URI: {uri}")
                        play_spotify_uri(uri)
                        current_unique_id = unique_id
                        log_message(f"Internal unique ID set to: {current_unique_id}")
        elif not inserted and disk_inserted:
            # Disk was removed
            log_message("Disk removed")
            stop_playback()
            current_unique_id = None  # Clear the unique ID
            log_message("Internal unique ID cleared.")
        elif inserted and disk_inserted:
            # Disk is still inserted
            # Optional: Check if the unique_id.txt has changed unexpectedly
            pass  # No action needed as unique_id is already set

        disk_inserted = inserted
        time.sleep(5)  # Adjust polling interval as needed

# ----------------------------
# Entry Point
# ----------------------------

if __name__ == '__main__':
    log_message("Starting authentication...")
    # Perform authentication
    authenticate_spotify()

    log_message("Authentication complete. Listing devices...")
    # List available devices
    list_devices()

    # Ensure that LOCAL_DEVICE_ID is correctly set
    if not is_device_available(LOCAL_DEVICE_ID):
        log_message("Local device ID is not available. Please ensure your device is active in Spotify.")
        exit(1)

    log_message("Starting floppy disk monitoring thread...")
    # Start the floppy disk monitoring in a separate thread
    monitoring_thread = threading.Thread(target=main)
    monitoring_thread.daemon = True
    monitoring_thread.start()

    log_message("Initializing GUI...")
    # Start the GUI
    root = tk.Tk()
    app = FloppifyPlayer(root)
    log_message("GUI initialized. Running main loop.")
    root.mainloop()
