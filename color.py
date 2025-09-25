import curses
import numpy as np
from functools import lru_cache
from scipy.spatial import KDTree
from sklearn.cluster import KMeans

class CursesColor:
    def __init__(self, sample_pixels_or_frame, start_color_idx=16):
        """
        Generates an optimized color palette by combining dominant colors from the video
        (found via K-Means) with a set of guaranteed base colors for vibrancy.
        It then uses a KD-Tree for rapid nearest-color lookups.
        """
        if not curses.has_colors() or not curses.can_change_color():
            raise RuntimeError("Terminal does not support custom colors.")

        self.start_color_idx = start_color_idx
        # Use a safe number of colors, leaving room for standard ones. Max is often 256.
        self.num_custom_colors = min(curses.COLORS - self.start_color_idx, 240)
        if self.num_custom_colors < 16: # Need at least 16 for base colors + some custom
            raise RuntimeError(f"Not enough available color slots in the terminal. Found only {curses.COLORS}.")

        # --- Define a set of guaranteed base colors for vibrancy (in BGR format) ---
        base_colors_bgr = np.array([
            [0, 0, 0],       # Black
            [255, 255, 255], # White
            [0, 0, 255],     # Red
            [0, 255, 0],     # Green
            [255, 0, 0],     # Blue
            [0, 255, 255],   # Yellow
            [255, 0, 255],   # Magenta
            [255, 255, 0],   # Cyan
            [128, 128, 128], # Gray
            [0, 0, 128],     # Maroon
            [0, 128, 0],     # Dark Green
            [128, 0, 0],     # Navy
        ], dtype=np.uint8)

        # --- Palette Generation using K-Means ---
        if sample_pixels_or_frame.ndim == 3:
             pixels = sample_pixels_or_frame.reshape(-1, 3)
        else:
             pixels = sample_pixels_or_frame

        unique_pixels = np.unique(pixels, axis=0)
        
        # Calculate how many colors we can dedicate to K-Means after reserving space for base colors
        num_kmeans_colors = self.num_custom_colors - len(base_colors_bgr)
        n_clusters = min(num_kmeans_colors, len(unique_pixels))

        if n_clusters > 0:
            # Fit KMeans to find the dominant colors
            kmeans = KMeans(n_clusters=n_clusters, random_state=0, n_init='auto').fit(unique_pixels)
            kmeans_palette = kmeans.cluster_centers_.astype(int)
            # Combine dominant colors with base colors
            final_palette_bgr = np.vstack([kmeans_palette, base_colors_bgr])
        else:
            # If not enough room for K-Means, just use the base colors
            final_palette_bgr = base_colors_bgr

        # Ensure no duplicate colors in the final palette
        final_palette_bgr = np.unique(final_palette_bgr, axis=0)

        # --- Initialize Curses Colors and Build KD-Tree ---
        self.palette = []
        palette_for_kdtree = []

        current_color_idx = self.start_color_idx
        current_pair_id = self.start_color_idx 

        for b, g, r in final_palette_bgr:
            if current_color_idx >= curses.COLORS or current_pair_id >= curses.COLOR_PAIRS:
                break # Stop if we exceed terminal limits

            curses_r = (r * 1000) // 255
            curses_g = (g * 1000) // 255
            curses_b = (b * 1000) // 255
            
            curses.init_color(current_color_idx, curses_r, curses_g, curses_b)
            curses.init_pair(current_pair_id, current_color_idx, -1) 
            
            self.palette.append({
                "pair_id": current_pair_id
            })
            palette_for_kdtree.append((r, g, b)) # Use RGB for KD-Tree
            
            current_color_idx += 1
            current_pair_id += 1

        self.kdtree = KDTree(palette_for_kdtree)
        print(f"Hybrid color palette created with {len(self.palette)} colors.")

    @lru_cache(maxsize=16384) # Increased cache size for more diverse videos
    def get_color(self, bgr: tuple) -> int:
        """
        Given a BGR color tuple (0-255), finds the closest color in the
        pre-computed palette using the KD-Tree and returns its curses pair ID.
        """
        b, g, r = bgr
        target_rgb = (r, g, b) # KD-Tree was built with RGB

        distance, index = self.kdtree.query(target_rgb)
        
        # Ensure the index is within the bounds of the created palette
        if index < len(self.palette):
            return self.palette[index]["pair_id"]
        return 1 # Default to a basic color pair if something goes wrong
