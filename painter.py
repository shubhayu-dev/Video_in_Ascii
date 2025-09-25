import curses
from functools import lru_cache

# Note: This script assumes you have a 'color.py' module with a class
# that has a 'get_color' method, as was implied by the original Cython code.

# --- Global variables for ASCII art generation ---

# Characters used to represent different levels of brightness.
# A space ' ' is for the darkest pixels, '@' is for the brightest.
characters = [' ', '.', ',', '-', '~', ':', ';', '=', '!', '*', '#', '$', '@']
# Calculate the brightness range that each character represents.
char_range = int(255 / len(characters))


def invert_chars():
    """
    Inverts the character map, making bright areas dark and dark areas bright.
    """
    global characters
    characters = characters[::-1]


@lru_cache(maxsize=256)
def get_char(val):
    """
    Maps a grayscale value (0-255) to an ASCII character.
    Uses lru_cache for performance, as this function is called for every pixel.

    Args:
        val (int): The grayscale value of a pixel.

    Returns:
        str: The corresponding ASCII character.
    """
    index = min(int(val / char_range), len(characters) - 1)
    return characters[index]


def paint_screen(window, grayscale_frame, width, height):
    """
    Renders a grayscale frame to the curses window using ASCII characters.

    Args:
        window: The curses window object to draw on.
        grayscale_frame (numpy.ndarray): A 2D array of grayscale pixel values.
        width (int): The width of the frame.
        height (int): The height of the frame.
    """
    # Iterate through each pixel of the frame
    for y in range(grayscale_frame.shape[0]):
        for x in range(grayscale_frame.shape[1]):
            try:
                # Get the corresponding character and add it to the window
                char = get_char(grayscale_frame[y, x])
                window.addch(y, x, char)
            except curses.error:
                # Ignore errors that occur when trying to draw outside the window
                pass


def paint_color_screen(window, grayscale_frame, frame, width, height, curses_color):
    """
    Renders a color frame to the curses window, using ASCII characters for
    brightness and curses color pairs for color.

    This function is optimized to draw segments of the same color at once,
    which is much faster than drawing character by character.

    Args:
        window: The curses window object to draw on.
        grayscale_frame (numpy.ndarray): A 2D array of grayscale pixel values.
        frame (numpy.ndarray): A 3D array (height, width, 3) of RGB pixel values.
        width (int): The width of the frame.
        height (int): The height of the frame.
        curses_color: An object with a 'get_color' method that maps an RGB tuple
                      to a curses color pair ID.
    """
    row_width = frame.shape[1]

    for y in range(frame.shape[0]):
        # Precompute the color for each pixel in this row for faster processing.
        row_colors = [curses_color.get_color(tuple(pixel)) for pixel in frame[y]]

        x = 0
        while x < row_width:
            # Find a segment of continuous, same-colored pixels
            current_color = row_colors[x]
            start_x = x
            segment_chars = []
            
            while x < row_width and row_colors[x] == current_color:
                # Collect the ASCII characters for this segment
                segment_chars.append(get_char(grayscale_frame[y, x]))
                x += 1
            
            # Draw the entire segment at once
            try:
                text_segment = "".join(segment_chars)
                window.addstr(y, start_x, text_segment, curses.color_pair(current_color))
            except curses.error:
                # Ignore errors from trying to draw outside the window bounds
                pass

def paint_embedding(window, embed_bytes, height, fullwidth, fullheight):
    """
    Draws a block of text (embedding) onto the window, right-aligned and
    centered vertically based on its content.

    Args:
        window: The curses window object to draw on.
        embed_bytes (bytes): The text to display, as a byte string.
        height (int): The number of lines in the embedding.
        fullwidth (int): The full width of the area to align within.
        fullheight (int): The full height of the area to align within.
    """
    lines = embed_bytes.splitlines()

    for line_idx, line in enumerate(lines):
        if line_idx >= height:
            break
        
        line_length = len(line)
        y = fullheight - height + line_idx
        
        # Iterate over each character in the line
        for char_idx, char_code in enumerate(line):
            try:
                # Calculate position to right-align the text
                x = fullwidth - line_length + char_idx
                if y >= 0 and x >= 0:
                    window.addch(y, x, char_code)
            except curses.error:
                # This can happen if the window is resized, just stop drawing
                return
