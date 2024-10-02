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
# Retro-Style Spotify Player GUI
# ----------------------------

class RetroSpotifyPlayer:
    def __init__(self, master):
        self.master = master
        master.title("Floppify Player")
        master.geometry("320x700")  # Adjusted width and height for better layout
        master.configure(bg='black')

        # Define font styles
        label_font = ('LED Dot-Matrix', 8)
        text_font = ('LED Dot-Matrix', 26)

        # ------------------------
        # Track Information Frame
        # ------------------------
        track_frame = tk.Frame(master, bg='black')
        track_frame.pack(pady=2)

        # Static Label
        track_static = tk.Label(track_frame, text='TRK:', font=label_font,  fg='black', bg='cyan')
        track_static.pack(side='left')

        # Dynamic Marquee Label
        self.track_marquee = Marquee(track_frame, text='', font=text_font, width=40, fg='lime', bg='black')
        self.track_marquee.pack(side='left', padx=5)

        # -------------------------
        # Artist Information Frame
        # -------------------------
        artist_frame = tk.Frame(master, bg='black')
        artist_frame.pack(pady=2)

        # Static Label
        artist_static = tk.Label(artist_frame, text='ART:', font=label_font, fg='black', bg='cyan')
        artist_static.pack(side='left')

        # Dynamic Marquee Label
        self.artist_marquee = Marquee(artist_frame, text='', font=text_font, width=40, fg='lime', bg='black')
        self.artist_marquee.pack(side='left', padx=5)

        # -------------------------
        # Album Information Frame
        # -------------------------
        album_frame = tk.Frame(master, bg='black')
        album_frame.pack(pady=2)

        # Static Label
        album_static = tk.Label(album_frame, text='ALB:', font=label_font, fg='black', bg='cyan')
        album_static.pack(side='left')

        # Dynamic Marquee Label
        self.album_marquee = Marquee(album_frame, text='', font=text_font, width=40, fg='lime', bg='black')
        self.album_marquee.pack(side='left', padx=5)

        # ------------------------
        # Album Cover Display with Floppy Disk Overlay
        # ------------------------
        # Load Floppy Disk Image
        try:
            floppy_image = Image.open("floppy_disk.png").convert("RGBA")  # Ensure PNG with transparency
        except FileNotFoundError:
            messagebox.showerror("Image Error", "floppy_disk.png not found in the script directory.")
            return

        floppy_image = floppy_image.resize((300, 300), Image.Resampling.LANCZOS)  # Adjust size as needed

        # Create a Canvas to overlay images
        self.canvas = tk.Canvas(master, width=300, height=300, bg='black', highlightthickness=0)
        self.canvas.pack(pady=10)

        # Convert Floppy Disk Image to Tkinter PhotoImage
        self.floppy_photo = ImageTk.PhotoImage(floppy_image)
        self.canvas.create_image(150, 150, image=self.floppy_photo)  # Centered

        # Placeholder for Album Cover
        self.album_cover_photo = None
        self.album_cover_id = None

        # ----------------------------
        # Playback Control Buttons
        # ----------------------------
        # Create a frame for the playback buttons
        button_frame = tk.Frame(master, bg='black')
        button_frame.pack(pady=10)

        # Previous Button
        self.prev_button = tk.Button(
            button_frame, text='⏮', font=('Courier', 20),
            command=lambda: sp.previous_track(device_id=LOCAL_DEVICE_ID)
        )
        self.prev_button.pack(side='left', padx=10)

        # Play/Pause Button
        self.play_pause_button = tk.Button(
            button_frame, text='▶', font=('Courier', 20),
            command=self.on_play_pause
        )
        self.play_pause_button.pack(side='left', padx=10)

        # Next Button
        self.next_button = tk.Button(
            button_frame, text='⏭', font=('Courier', 20),
            command=lambda: sp.next_track(device_id=LOCAL_DEVICE_ID)
        )
        self.next_button.pack(side='left', padx=10)

        # ----------------------------
        # Volume Control Buttons
        # ----------------------------
        # Create a frame for the volume controls
        volume_frame = tk.Frame(master, bg='black')
        volume_frame.pack(pady=10)

        # Volume Down Button
        self.vol_down_button = tk.Button(
            volume_frame, text='-', font=('Courier', 20),
            command=self.decrease_volume
        )
        self.vol_down_button.pack(side='left', padx=5)

        # Volume Up Button
        self.vol_up_button = tk.Button(
            volume_frame, text='+', font=('Courier', 20),
            command=self.increase_volume
        )
        self.vol_up_button.pack(side='left', padx=5)

        # ----------------------------
        # Volume Bar Visualization
        # ----------------------------
        # Create the volume bar
        self.volume_bar_frame = tk.Frame(master, bg='black')
        self.volume_bar_frame.pack(pady=10)

        # Create 11 segments for the volume bar
        self.volume_segments = []
        for i in range(11):
            segment = tk.Label(
                self.volume_bar_frame,
                text=' ',
                bg='grey',
                width=2,
                height=1,
                bd=1,
                relief='sunken'
            )
            segment.pack(side='left', padx=1)
            self.volume_segments.append(segment)

        # ----------------------------
        # Log Display Frame
        # ----------------------------
        log_frame = tk.Frame(master, bg='black')
        log_frame.pack(pady=10)

        # Create a Text widget for logs (read-only)
        self.log_text = tk.Text(log_frame, height=6, width=40, bg='lime', fg='black', state='disabled', bd=0, wrap='word', font=('LED Dot-Matrix', 12))
        self.log_text.pack()

        # Initialize the volume bar
        self.update_volume_bar()

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
            self.play_pause_button.config(text='⏸')  # Pause icon
        else:
            self.play_pause_button.config(text='▶')  # Play icon

    # ----------------------------
    # Volume Control Methods
    # ----------------------------

    def increase_volume(self):
        # Get current volume
        playback = sp.current_playback()
        if playback and 'device' in playback and playback['device']:
            current_volume = playback['device']['volume_percent']
        else:
            current_volume = 50  # Default to 50 if unable to get current volume

        # Increase volume by one step
        step = int(100 / 11)  # Approximately 9%
        new_volume = min(current_volume + step, 100)
        try:
            sp.volume(int(new_volume), device_id=LOCAL_DEVICE_ID)
            self.update_volume_bar()
            log_message(f"Increased volume to {new_volume}%")
        except spotipy.exceptions.SpotifyException as e:
            log_message(f"Error increasing volume: {e}")
            messagebox.showerror("Volume Error", str(e))

    def decrease_volume(self):
        # Get current volume
        playback = sp.current_playback()
        if playback and 'device' in playback and playback['device']:
            current_volume = playback['device']['volume_percent']
        else:
            current_volume = 50  # Default to 50 if unable to get current volume

        # Decrease volume by one step
        step = int(100 / 11)  # Approximately 9%
        new_volume = max(current_volume - step, 0)
        try:
            sp.volume(int(new_volume), device_id=LOCAL_DEVICE_ID)
            self.update_volume_bar()
            log_message(f"Decreased volume to {new_volume}%")
        except spotipy.exceptions.SpotifyException as e:
            log_message(f"Error decreasing volume: {e}")
            messagebox.showerror("Volume Error", str(e))

    def update_volume_bar(self):
        # Get current volume
        playback = sp.current_playback()
        if playback and 'device' in playback and playback['device']:
            current_volume = playback['device']['volume_percent']
        else:
            current_volume = 0  # Assume 0 if unable to get current volume

        # Map volume percentage to levels (0 to 11)
        level = int(current_volume * 11 / 100)
        if level > 11:
            level = 11

        # Update segments
        for i in range(11):
            if i < level:
                # Set color based on level
                if i < 5:
                    color = 'green'
                elif i < 8:
                    color = 'yellow'
                else:
                    color = 'red'
                self.volume_segments[i].config(bg=color)
            else:
                self.volume_segments[i].config(bg='grey')

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
                    if len(self.log_history) > 2:
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

                    # Update Album Cover
                    response = requests.get(album_cover_url)
                    img_data = response.content
                    img = Image.open(BytesIO(img_data)).convert("RGBA")
                    img = img.resize((170, 142), Image.Resampling.LANCZOS)
                    album_cover = ImageTk.PhotoImage(img)

                    # Overlay Album Cover on Floppy Disk
                    # Remove previous album cover if exists
                    if self.album_cover_id:
                        self.canvas.delete(self.album_cover_id)
                    self.album_cover_photo = album_cover
                    # Position the album cover at the center of the floppy disk
                    self.album_cover_id = self.canvas.create_image(150, 205, image=self.album_cover_photo)

                    # Update Play/Pause Button Icon
                    self.play_pause_button.config(text='⏸')  # Pause icon
                else:
                    # Update Marquee texts to default
                    self.track_marquee.set_text('Not available')
                    self.artist_marquee.set_text('Not available')
                    self.album_marquee.set_text('Not available')
                    
                    # Remove Album Cover
                    if self.album_cover_id:
                        self.canvas.delete(self.album_cover_id)
                        self.album_cover_id = None
                        self.album_cover_photo = None

                    # Update Play/Pause Button Icon
                    self.play_pause_button.config(text='▶')  # Play icon
            else:
                # No playback information available
                self.track_marquee.set_text('Not available')
                self.artist_marquee.set_text('Not available')
                self.album_marquee.set_text('Not available')
                
                # Remove Album Cover
                if self.album_cover_id:
                    self.canvas.delete(self.album_cover_id)
                    self.album_cover_id = None
                    self.album_cover_photo = None

                # Update Play/Pause Button Icon
                self.play_pause_button.config(text='▶')  # Play icon

            # Update Volume Bar
            self.update_volume_bar()
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
            else:
                log_message("Playlist already played for this disk insertion. Skipping.")

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
    app = RetroSpotifyPlayer(root)
    log_message("GUI initialized. Running main loop.")
    root.mainloop()
