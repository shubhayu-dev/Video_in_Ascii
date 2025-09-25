🎥 ASCII Player

Play videos, YouTube streams, and webcam feeds directly in your terminal using ASCII characters — with support for color rendering and synchronized audio playback.

🚀 Features

✅ Play local video files, YouTube URLs, or webcam feeds.

✅ Audio playback in sync with video (via FFmpeg).

✅ Color mode with palette optimization.

✅ Customizable width and FPS for performance.

✅ Extra options: inversion, original video preview, and watermark embedding.

✅ Works on Linux, macOS, Windows, and Raspberry Pi.

📦 Installation
1. Install FFmpeg (required for audio)

Linux (Debian/Ubuntu):

sudo apt update && sudo apt install ffmpeg


macOS (Homebrew):

brew install ffmpeg


Windows:
Download binaries from FFmpeg official site
 and add the bin folder to your system PATH.

2. Install Python dependencies

It’s recommended to use a virtual environment:

python3 -m venv venv
source venv/bin/activate   # On Windows: venv\Scripts\activate


Install required packages:

pip install -r requirements.txt

▶️ Usage

Run the player with:

python3 player.py <video_path | youtube_url | webcam_index> [options]

Examples

Play a local video:

python3 player.py sample.mp4 --color


Play a YouTube stream:

python3 player.py "https://youtube.com/..." --width 100 --fps 24


Use your webcam (device index 0):

python3 player.py 0 --color

⚙️ Options
Flag	Description
--width <num>	Set display width in characters (default: 120)
--fps <num>	Set playback framerate (default: 30)
--color	Enable color mode
--inv	Invert brightness mapping (light-on-dark)
--show	Show original video in OpenCV window
--embed <txt>	Overlay a .txt watermark in bottom-right corner
📹 Notes on Audio

If FFmpeg is installed, audio is extracted automatically and played in sync with the ASCII video.

If FFmpeg is missing or the video has no audio, playback defaults to silent mode.

🍓 Running on Raspberry Pi

For best results, use a Raspberry Pi 5.

Install dependencies:

sudo apt install python3-opencv python3-picamera2


Then run as usual:

python3 player.py 0 --color --fps 20

💡 Tips

High-contrast videos with iconic audio work best in ASCII.

Reduce --width or --fps for smoother performance on low-power devices.

📝 License

MIT License – feel free to use and modify.

Do you want me to also add screenshots and a GIF demo section so that your README looks more attractive on GitHub?
