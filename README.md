#  Floppify
Retro Floppy Disk Spotify Playlist Loader
![image](https://github.com/user-attachments/assets/f3f39165-b441-4082-a689-d17864cc7be2)


## Introduction
Growing up in the '90s, I have vivid memories of 3.5" floppy disks. They were the go-to storage format of the time, though far too small to store actual music files (only 1.44MB per disk!). Back then, we relied on cassette tapes and later CDs for our music—though I can't even recall the last time I used a CD.

As a fan of retro tech, I recently felt nostalgic and decided to build a "sleeper" PC. For those unfamiliar, a sleeper PC is a powerful, modern machine hidden inside the case of an old, unassuming PC from the late '90s or early 2000s. Of course, I included a floppy drive in the build for authenticity—but, unsurprisingly, it's not very practical.
https://github.com/jakemorgangit/timemachine/


Then came a flash of inspiration: why not repurpose those old floppy disks? What if I could load Spotify playlists from these disks? This would give me a tactile, retro way of interacting with music, bringing back the joy of tangible media. And so, floppify was born.

## What is Floppify?
Floppify is a project that lets you use floppy disks to load Spotify playlists. It’s a fun, retro-tech way to interact with modern streaming services by using an old-fashioned medium.

(Part of joy of this project is finding and printing your own labels / disk art!)

![image](https://github.com/user-attachments/assets/0318217a-2354-486d-9027-045e9891104c)



# In a nutshell...

Run the script.  
It will authenticate against your Spotify credentials (a browser window will load where you'll need to authorise the app).
From there, you'll be given a list of the devices you use with your spotify account - make a note of the ID of the device you want to use and pump that into the `.env` file.  
Now you've chosen a preferred device, run the script again.  
A GUI will launch and the main loop will poll for the insertion of a disk.  
These disks must contain a `playlist.txt` file which contains link(s) to a spotify playlist/album.  
If this disk has never been loaded (or read by the program before) a uniq ID will be generated and stored in the root of the floppy disk under a file called `unique_id.txt`.  
This ID is stored internally and used to ensure that the main loop doesn't pick up a new playlist everytime it polls for a new disk (which is every 5 seconds) - this fixed one fo the first bugs!  
On detection of an inserted disk, the program will stream the playlist from spotify (or, if there a multiple playlist links, it will pick one at random).  
If a disk is ejected, the music will stop the next time the main loop loops (within 5 seconds) and the console and GUI will be updated to say that nothing is available.  
Put in another disk and process repeats.  It's all pretty simple :) 


# The GUI

No Disk

![image](https://github.com/user-attachments/assets/96d0027e-8d72-41b2-a1ab-7f9e689da4ab)

With Disk

![image](https://github.com/user-attachments/assets/7b84f136-3383-4f03-9c5e-6c15ba656cd3)

I should mention that the gui isn't actually required, the entire thing can run silently, but I thought `why not` !


## How It Works
Spotify Developer Setup

https://developer.spotify.com/

You’ll need a Spotify Developer account to create a new app and generate a client ID and secret. This will allow the script to authenticate with Spotify.


Make sure your redirect URL is set to `http://localhost:8888/callback`
![image](https://github.com/user-attachments/assets/3daafb35-1595-4e0c-b860-71d755ec2a72)


## Device Configuration
The script checks your LOCAL_DEVICE_ID on the first run. If it’s not already set, you'll need to select the device where you want Spotify to play (e.g., your computer, speakers, or another connected device).


![image](https://github.com/user-attachments/assets/472a40bb-57f2-4e2a-876f-3d5c9b102667)

![image](https://github.com/user-attachments/assets/376c8959-1ca7-44b4-afbd-fb50ad2bd73a)



## Drive Setup
By default, the script uses drive A: (the traditional floppy drive letter). If you’re using another drive, like a USB floppy emulator or USB drive, simply change the drive letter in the `.env file.


![image](https://github.com/user-attachments/assets/285c18f8-8690-4ae2-ba43-ed5b459559c9)

## Playlist File
Create a file called playlist.txt on the floppy disk.  In this file, paste links to the Spotify playlists or albums you want, one per line. You can have as many playlists as you like on a single floppy, so for instance, you could store an artist’s entire discography on one disk!

![image](https://github.com/user-attachments/assets/06f141eb-6d48-44d5-9d3a-7d355fb2e0cc)





## Launch the App
With everything set up, insert your floppy, launch the app, and let the retro magic happen!

## Requirements
- Spotify Developer Account
- Floppy Drive (real or emulated/USB stick also works)
- Floppy Disks (the more, the merrier!)
- Python 3.x and dependencies (see requirements.txt)

## How to use

Clone the repository:

```
git clone https://github.com/jakemorgangit/floppify.git
cd floppify
```

Install dependencies:

```
pip install -r requirements.txt
```

Font
This project uses the LED Dot-Matrix font available at DaFont:
https://www.dafont.com/led-dot-matrix.font

You'll need to download the TTF file and install it - alternatively, use a different font (courier for example should work out of the box) :) 

-----
Then...

Set up your Spotify credentials.  
Create a new app on the Spotify Developer Dashboard.  
Obtain the CLIENT_ID and CLIENT_SECRET, and configure them in the .env file.  

![image](https://github.com/user-attachments/assets/a8930042-304d-42af-b994-c2e5705816dd)

Insert a floppy disk and create a playlist.txt file containing Spotify playlist URLs.  
Run the app and enjoy your FLOPPIFY retro playlist loader!

```
python floppify.py
```


![image](https://github.com/user-attachments/assets/b44b0ba5-fdab-4f05-b3ae-0fa62113a4e0)


## Contributing
If you have ideas to enhance floppify, feel free to submit a pull request or open an issue!




