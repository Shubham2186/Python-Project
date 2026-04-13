"""
Interactive Algorithm Visualizer
================================
A desktop application (pygame) that animates Bubble Sort and Merge Sort
step by step, with speed control, array-size slider, and color-coded bars.

Run this file to launch the visualizer:

    python main.py

Requirements:
    pip install pygame
"""

from visualizer.renderer import Renderer


def main():
    """Create the renderer and start the application loop."""
    app = Renderer()
    app.run()


if __name__ == "__main__":
    main()
