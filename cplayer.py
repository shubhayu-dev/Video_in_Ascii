import os
import cv2
import curses
import argparse
import time
import numpy as np
import color
import youtube_utils
import subprocess
import pygame

# Use pyximport to compile and import the Cython module on the fly
import pyximport
pyximport.install()

# Import the fast, compiled functions from your .pyx file
from painter import paint_screen, paint_color_screen, paint_embedding, invert_chars

# --- Argument Parsing (Corrected) ---
parser = argparse.ArgumentParser(description='ASCII Player')
parser.add_argument("--width", type=int, default=120, help="width of the terminal window")
parser.add_argument("--fps", type=int, default=30, help="frames per second to play at")
parser.add_argument("--show", action='store_true', help="show the original video in an opencv window")
parser.add_argument("--inv", action='store_true', help="invert the shades")
parser.add_argument("--color", action='store_true', help="print colors if available (slows things down)")
parser.add_argument("--embed", type=str, default="", help="pass a txt file to embed as watermark")
parser.add_argument("video", type=str, help="path to video or webcam index")
args = parser.parse_args()

if args.inv:
    invert_chars()

video_path_arg = args.video
try:
    video_path_arg = int(video_path_arg)
except ValueError:
    pass

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
            print(f"Error: Failed to find video at: {args.video}")
            exit()
        
        # --- Extract audio using FFmpeg ---
        print("Extracting audio... (this may take a moment)")
        command = [
            'ffmpeg', '-i', video, '-q:a', '0', '-map', 'a', TEMP_AUDIO_FILE, '-y', '-hide_banner', '-loglevel', 'error'
        ]
        result = subprocess.run(command)
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
        print("Could not extract frame from video.")
        exit()
    
    source_fps = cap.get(cv2.CAP_PROP_FPS)
    if source_fps == 0: # Webcam might report 0, use user-defined fps
        source_fps = args.fps
    
    total_frames = int(cap.get(cv2.CAP_PROP_FRAME_COUNT))

    width = args.width
    ratio = width / frame.shape[1]
    height = int(frame.shape[0] * ratio * (3.0 / 5))

    # --- Curses and Pygame Setup ---
    curses.initscr()
    curses_color = None
    if args.color and curses.has_colors():
        curses.start_color()
        curses.use_default_colors()
        
        # --- Advanced Palette Generation ---
        print("Analyzing video for optimal color palette... (this is a one-time process)")
        
        # Sample pixels from multiple frames across the video for a better palette
        num_palette_frames = 30
        all_sample_pixels = []
        
        # Ensure we don't try to sample more frames than exist
        if total_frames > 1 and isinstance(video, str):
            for i in range(num_palette_frames):
                frame_idx = int(i * (total_frames / num_palette_frames))
                cap.set(cv2.CAP_PROP_POS_FRAMES, frame_idx)
                ret, sample_frame = cap.read()
                if not ret:
                    continue
                
                resized_frame = cv2.resize(sample_frame, (width, height))
                pixels = resized_frame.reshape(-1, 3)
                sample_size = min(len(pixels), 1000) # Sample up to 1000 pixels per frame
                all_sample_pixels.append(pixels[np.random.choice(len(pixels), sample_size, replace=False)])
            
            # Reset video to the beginning
            cap.set(cv2.CAP_PROP_POS_FRAMES, 0)
            
            sample_pixels = np.vstack(all_sample_pixels)
            curses_color = color.CursesColor(sample_pixels)
        else: # Fallback for webcams or single-frame videos
            curses_color = color.CursesColor(cv2.resize(frame, (width, height)))
            
    window = curses.newwin(height, width, 0, 0)

    # --- Initialize Pygame mixer and play audio if extracted ---
    if audio_extracted:
        pygame.mixer.init()
        pygame.mixer.music.load(TEMP_AUDIO_FILE)
        pygame.mixer.music.play()

    # --- Embedding Setup ---
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
    start_time = time.time()
    frame_count = 0
    
    while True:
        # --- Audio-Video Synchronization Logic ---
        if audio_extracted and pygame.mixer.get_init() and pygame.mixer.music.get_busy():
            audio_time = pygame.mixer.music.get_pos() / 1000.0
            target_frame_num = int(audio_time * source_fps)
            current_frame_num = int(cap.get(cv2.CAP_PROP_POS_FRAMES))

            if current_frame_num < target_frame_num:
                cap.set(cv2.CAP_PROP_POS_FRAMES, target_frame_num)
        else:
            target_time = frame_count / args.fps
            elapsed_time = time.time() - start_time
            wait_time = target_time - elapsed_time
            if wait_time > 0:
                time.sleep(wait_time)

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
            paint_color_screen(window, grayscale_frame, frame_resized, width, height, curses_color)
        else:
            paint_screen(window, grayscale_frame, width, height)

        if embedding:
            paint_embedding(window, embedding.encode('utf-8'), embedding_height, width, height)
        
        window.refresh()
        frame_count += 1
        
        elapsed_for_fps = time.time() - start_time
        if elapsed_for_fps > 0:
            fps = frame_count / elapsed_for_fps

finally:
    # --- Cleanup ---
    cv2.destroyAllWindows()
    curses.endwin()

    if 'pygame' in locals() and pygame.mixer.get_init():
        pygame.mixer.quit()
    if audio_extracted and os.path.exists(TEMP_AUDIO_FILE):
        os.remove(TEMP_AUDIO_FILE)

    print(f"Finished. Average playback was around {int(fps)} FPS.")
