import os
import cv2
import curses
import argparse
import time
import numpy as np
import color
import youtube_utils
import painter # Your painter module
import subprocess
import pygame

# --- Argument Parsing (No changes) ---
parser = argparse.ArgumentParser(description='ASCII Player')
parser.add_argument("--width", type=int, default=120, help="width of the terminal window")
parser.add_argument("--fps", type=int, default=30, help="frames per second to play at")
parser.add_argument("--show", action='store_true', help="show the original video in an opencv window")
parser.add_argument("--inv", action='store_true', help="invert the shades")
parser.add_argument("--color", action='store_true', help="print colors if available (slows things down)")
parser.add_argument("--embed", type=str, default="", help="pass a txt file to embed as watermark")
parser.add_argument("video", type=str, help="path to video or webcam index")
args = parser.parse_args()

video_path_arg = args.video
try:
    video_path_arg = int(video_path_arg)
except ValueError:
    pass

width = args.width
if args.inv:
    painter.invert_chars()

# --- Temporary file for extracted audio ---
TEMP_AUDIO_FILE = "temp_audio_for_ascii_player.mp3"
audio_extracted = False
fps = 0 # Initialize fps to avoid NameError in finally block

try:
    # --- Video Path and Audio Extraction ---
    if isinstance(video_path_arg, str):
        if youtube_utils.is_youtube_url(video_path_arg):
            print("Downloading YouTube video...")
            video = youtube_utils.get_youtube_video_url(video_path_arg)
        elif os.path.isfile(video_path_arg):
            video = video_path_arg
        else:
            print("failed to find video at:", args.video)
            exit()
        
        # --- NEW: Extract audio using FFmpeg ---
        print("Extracting audio... (this may take a moment)")
        command = [
            'ffmpeg', '-i', video, '-q:a', '0', '-map', 'a', TEMP_AUDIO_FILE, '-y'
        ]
        # Use DEVNULL to hide FFmpeg's console output
        result = subprocess.run(command, stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL)
        if result.returncode == 0 and os.path.exists(TEMP_AUDIO_FILE):
            audio_extracted = True
        else:
            print("Warning: Could not extract audio. FFmpeg might not be installed, or the video may have no audio.")
    else:
        video = video_path_arg # For webcam

    # --- Video Capture and Initial Frame Processing ---
    cap = cv2.VideoCapture(video)
    ok, frame = cap.read()
    if not ok:
        print("could not extract frame from video")
        exit()

    ratio = width / frame.shape[1]
    height = int(frame.shape[0] * ratio * 3 / 5)

    # --- Curses and Pygame Setup ---
    curses.initscr()
    curses_color = None
    if args.color and curses.has_colors():
        curses.start_color()
        curses.use_default_colors()
        curses_color = color.CursesColor()
    window = curses.newwin(height, width, 0, 0)

    # --- NEW: Initialize Pygame mixer and play audio if extracted ---
    if audio_extracted:
        pygame.mixer.init()
        pygame.mixer.music.load(TEMP_AUDIO_FILE)
        pygame.mixer.music.play()

    # --- Embedding Setup (No changes) ---
    embedding = ""
    embedding_height = 0
    if args.embed:
        if os.path.isfile(args.embed):
            with open(args.embed, "r", encoding='utf-8') as f:
                embedding = f.read()
            embedding_height = len(embedding.split("\n"))
        else:
            print(f"Warning: Embedding file not found at {args.embed}")

    # --- Main Rendering Loop ---
    frame_count = 0
    frames_per_ms = args.fps / 1000
    start = time.perf_counter_ns() // 1000000

    while True:
        ok, orig_frame = cap.read()
        if not ok:
            break

        frame_resized = cv2.resize(orig_frame, (width, height))
        grayscale_frame = cv2.cvtColor(frame_resized, cv2.COLOR_BGR2GRAY)
        
        if args.show:
            cv2.imshow("frame", orig_frame)
            if cv2.waitKey(1) & 0xFF == ord('q'):
                break

        if args.color and curses_color:
            painter.paint_color_screen(window, grayscale_frame, frame_resized, width, height, curses_color)
        else:
            painter.paint_screen(window, grayscale_frame, width, height)

        if embedding:
            # Note: The original 'paint_embedding' expected bytes. Assuming it's meant to handle strings.
            # If it needs bytes, use embedding.encode('utf-8')
            painter.paint_embedding(window, embedding.encode('utf-8'), embedding_height, width, height)
        
        # FPS Limiter Logic
        elapsed = (time.perf_counter_ns() // 1000000) - start
        supposed_frame_count = frames_per_ms * elapsed
        if frame_count > supposed_frame_count:
            sleep_duration_ms = (frame_count - supposed_frame_count) / frames_per_ms
            time.sleep(sleep_duration_ms / 1000)

        window.refresh()
        frame_count += 1
        
        # Calculate FPS for display
        elapsed_time_seconds = (time.perf_counter_ns() // 1000000 - start) / 1000
        if elapsed_time_seconds > 1:
            fps = frame_count / elapsed_time_seconds

finally:
    # --- Cleanup ---
    cv2.destroyAllWindows()
    curses.endwin()

    # NEW: Quit pygame and remove temporary audio file
    if audio_extracted:
        pygame.mixer.quit()
        if os.path.exists(TEMP_AUDIO_FILE):
            os.remove(TEMP_AUDIO_FILE)

    print(f"Finished. Average playback was around {int(fps)} FPS.")
