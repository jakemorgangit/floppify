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

![image](https://github.com/user-attachments/assets/ff97600c-7f73-45d3-9f3e-e747a6f16403)


No Disk
![image](https://github.com/user-attachments/assets/96d0027e-8d72-41b2-a1ab-7f9e689da4ab)

With Disk
![image](https://github.com/user-attachments/assets/7b84f136-3383-4f03-9c5e-6c15ba656cd3)




## How It Works
Spotify Developer Setup

https://developer.spotify.com/

You’ll need a Spotify Developer account to create a new app and generate a client ID and secret. This will allow the script to authenticate with Spotify.

Make sure your redirect URL is set to `http://localhost:8888/callback`
![image](https://github.com/user-attachments/assets/3daafb35-1595-4e0c-b860-71d755ec2a72)


## Device Configuration
The script checks your LOCAL_DEVICE_ID on the first run. If it’s not already set, you'll need to select the device where you want Spotify to play (e.g., your computer, speakers, or another connected device).


![image](https://github.com/user-attachments/assets/472a40bb-57f2-4e2a-876f-3d5c9b102667)


## Drive Setup
By default, the script uses drive A: (the traditional floppy drive letter). If you’re using another drive, like a USB floppy emulator or USB drive, simply change the drive letter in the settings.

## Playlist File
Create a file called playlist.txt on the floppy disk.  In this file, paste links to the Spotify playlists or albums you want, one per line. You can have as many playlists as you like on a single floppy, so for instance, you could store an artist’s entire discography on one disk!

![image](https://github.com/user-attachments/assets/06f141eb-6d48-44d5-9d3a-7d355fb2e0cc)


![image](https://github.com/user-attachments/assets/2c4ceb7c-80a9-4c6d-9883-a0497ba6e972)


## Launch the App
With everything set up, insert your floppy, launch the app, and let the retro magic happen!

## Requirements
-Spotify Developer Account
-Floppy Drive (real or emulated)
-Floppy Disks (the more, the merrier!)
-Python 3.x and dependencies (see requirements.txt)

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

Set up your Spotify credentials:

Create a new app on the Spotify Developer Dashboard.
Obtain the CLIENT_ID and CLIENT_SECRET, and configure them in the .env file.

Insert a floppy disk and create a playlist.txt file containing Spotify playlist URLs.

Run the app and enjoy your FLOPPIFY retro playlist loader!

```
python floppify.py
```


![image](https://github.com/user-attachments/assets/b44b0ba5-fdab-4f05-b3ae-0fa62113a4e0)


## Contributing
If you have ideas to enhance floppify, feel free to submit a pull request or open an issue!

## License
This project is licensed under the MIT License.

