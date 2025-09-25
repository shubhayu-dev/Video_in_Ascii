ASCII Player
This player plays videos, YouTube streams, and webcam feeds directly in your terminal using ASCII characters, with support for both color and synchronized audio playback.

A great example is a video with iconic sound and high-contrast visuals. You can use a local video file, a YouTube URL, or your webcam index directly in the command line.

YouTube Explanations
General Process of Converting Videos to ASCII

Porting to Raspberry Pi

Install Dependencies
1. FFmpeg (Required for Audio)
This project uses FFmpeg to automatically extract audio from video files. You must install it on your system for audio to work.

Linux (Debian/Ubuntu): sudo apt update && sudo apt install ffmpeg

macOS (using Homebrew): brew install ffmpeg

Windows: Download binaries from the official FFmpeg website and add the bin folder to your system's PATH.

2. Python Libraries
It's recommended to use a virtual environment.

python3 -m venv venv
source venv/bin/activate  # On Windows: venv\Scripts\activate

Then, install the required packages from requirements.txt:

pip3 install -r requirements.txt

Usage
After installing the dependencies, run the player with the player.py script:

python3 player.py <path_to_video or youtube_url or webcam_index>

Note on Audio: If FFmpeg is installed correctly, the player will automatically handle the audio. It extracts the audio to a temporary file, plays it in sync with the video, and deletes the file when finished. If FFmpeg is not found or the video has no audio, it will play silently.

Options
Flag

Description

--width <num>

Sets the display width in characters (default: 120).

--fps <num>

Sets the target playback framerate (default: 30).

--color

Enables color mode using a palette optimized for the video.

--inv

Inverts the brightness mapping (light-on-dark).

--show

Displays the original video in a separate OpenCV window.

--embed <path>

Overlays a .txt file as a watermark on the bottom right.

Webcam Usage
To use your webcam, provide its device index (usually 0):

python3 player.py 0 --color

Running on a Raspberry Pi
For best results, run on a Raspberry Pi 5.

Install Dependencies
Install the Picamera2 and OpenCV dependencies via apt:

sudo apt install python3-opencv python3-picamera2
