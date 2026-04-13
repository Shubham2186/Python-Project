"""
helpers.py - Utility functions for the Algorithm Visualizer.

Provides helper functions for generating arrays, color manipulation,
and other shared utilities used across the application.
"""

import random


def generate_random_array(size=50, min_val=10, max_val=500):
    """
    Generate a list of random integers.

    Args:
        size (int): Number of elements in the array.
        min_val (int): Minimum value for each element.
        max_val (int): Maximum value for each element.

    Returns:
        list: A list of random integers.
    """
    return [random.randint(min_val, max_val) for _ in range(size)]


def lerp_color(color_a, color_b, t):
    """
    Linearly interpolate between two RGB colors.

    Args:
        color_a (tuple): Starting color (R, G, B).
        color_b (tuple): Ending color (R, G, B).
        t (float): Interpolation factor (0.0 to 1.0).

    Returns:
        tuple: Interpolated color (R, G, B).
    """
    t = max(0.0, min(1.0, t))  # Clamp t between 0 and 1
    return tuple(int(a + (b - a) * t) for a, b in zip(color_a, color_b))


def get_bar_color(value, max_value):
    """
    Get a gradient color for a bar based on its value.
    Creates a smooth gradient from teal to purple.

    Args:
        value (int): The value of the bar element.
        max_value (int): The maximum value in the array.

    Returns:
        tuple: RGB color tuple.
    """
    if max_value == 0:
        return (0, 200, 200)

    # Ratio of value to max (0.0 to 1.0)
    ratio = value / max_value

    # Gradient from teal (0, 200, 200) to vibrant purple (160, 50, 255)
    color_low = (0, 200, 200)    # Teal
    color_high = (160, 50, 255)  # Purple

    return lerp_color(color_low, color_high, ratio)


# ---------------------------------------------------------------------------
# Color palette used throughout the application
# ---------------------------------------------------------------------------
class Colors:
    """Central color palette for the entire application."""
    # Background and surface colors (dark theme)
    BG_DARK = (18, 18, 28)
    BG_PANEL = (28, 28, 45)
    BG_HOVER = (40, 40, 65)

    # Accent colors
    ACCENT_TEAL = (0, 210, 210)
    ACCENT_PURPLE = (160, 80, 255)
    ACCENT_PINK = (255, 80, 160)
    ACCENT_GREEN = (80, 255, 140)
    ACCENT_ORANGE = (255, 160, 50)

    # Highlight colors for sorting states
    COMPARE = (255, 220, 50)       # Yellow – elements being compared
    SWAP = (255, 80, 80)           # Red – elements being swapped
    SORTED = (80, 255, 140)        # Green – element in final position
    ACTIVE_RANGE = (100, 140, 255) # Blue – merge sort active range
    ARROW = (255, 200, 60)         # Bright gold – sorting arrow indicator
    ARROW_GLOW = (255, 220, 100)   # Lighter gold – arrow glow effect

    # Text colors
    TEXT_PRIMARY = (230, 230, 245)
    TEXT_SECONDARY = (140, 140, 170)
    TEXT_DISABLED = (80, 80, 100)

    # Button colors
    BTN_NORMAL = (45, 45, 75)
    BTN_HOVER = (65, 65, 100)
    BTN_ACTIVE = (0, 180, 180)
    BTN_TEXT = (230, 230, 245)

    # Borders & dividers
    BORDER = (55, 55, 85)
    DIVIDER = (40, 40, 65)


# ---------------------------------------------------------------------------
# Speed configuration
# ---------------------------------------------------------------------------
SPEED_SETTINGS = {
    "Very Slow": {"delay_ms": 300, "label": "Very Slow"},
    "Slow":      {"delay_ms": 120, "label": "Slow"},
    "Medium":    {"delay_ms": 40,  "label": "Medium"},
    "Fast":      {"delay_ms": 8,   "label": "Fast"},
}

# Algorithm metadata shown in the UI
ALGORITHM_INFO = {
    "Bubble Sort": {
        "best":    "O(n)",
        "average": "O(n²)",
        "worst":   "O(n²)",
        "space":   "O(1)",
        "stable":  "Yes",
    },
    "Merge Sort": {
        "best":    "O(n log n)",
        "average": "O(n log n)",
        "worst":   "O(n log n)",
        "space":   "O(n)",
        "stable":  "Yes",
    },
}

# ---------------------------------------------------------------------------
# Complexity comparison data for the recommendation engine
# ---------------------------------------------------------------------------
COMPLEXITY_COMPARISON = {
    "Bubble Sort": {
        "best_n":    1,      # O(n)      – coefficient for n
        "avg_n":     2,      # O(n²)     – exponent
        "worst_n":   2,      # O(n²)
        "space":     0,      # O(1)
        "label_best":    "O(n)",
        "label_avg":     "O(n²)",
        "label_worst":   "O(n²)",
        "label_space":   "O(1)",
    },
    "Merge Sort": {
        "best_n":    1.585,  # O(n log n) ≈ n^1.585 for comparison
        "avg_n":     1.585,
        "worst_n":   1.585,
        "space":     1,      # O(n)
        "label_best":    "O(n log n)",
        "label_avg":     "O(n log n)",
        "label_worst":   "O(n log n)",
        "label_space":   "O(n)",
    },
}


def recommend_algorithm(array_size):
    """
    Suggest the better sorting algorithm based on array size.

    For small arrays (≤ ~30), Bubble Sort can be competitive due to
    low overhead and O(1) space.  For larger arrays, Merge Sort's
    O(n log n) guarantee wins.

    Args:
        array_size (int): Number of elements.

    Returns:
        tuple: (recommended_name, reason_text)
    """
    if array_size <= 20:
        return (
            "Bubble Sort",
            f"n={array_size} is small. Bubble Sort\n"
            f"has low overhead & O(1) space.",
        )
    elif array_size <= 40:
        return (
            "Either",
            f"n={array_size} is moderate. Both are\n"
            f"competitive. Merge scales better.",
        )
    else:
        return (
            "Merge Sort",
            f"n={array_size} is large. O(n log n)\n"
            f"beats Bubble Sort's O(n\u00b2).",
        )
