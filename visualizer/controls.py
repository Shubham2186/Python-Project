"""
controls.py - UI control components for the Algorithm Visualizer.

Provides reusable Button and Panel classes rendered with pygame,
along with layout constants used by the main renderer.
"""

import pygame

from utils.helpers import Colors


# ---------------------------------------------------------------------------
# Layout constants
# ---------------------------------------------------------------------------
SIDEBAR_WIDTH = 260          # Width of the left control panel
TOP_BAR_HEIGHT = 60          # Height of the top status bar
PADDING = 16                 # General padding
BUTTON_HEIGHT = 40           # Height of standard buttons
BUTTON_SPACING = 10          # Vertical gap between buttons
CORNER_RADIUS = 8            # Rounded-corner radius


class Button:
    """
    A clickable button with hover/active states, rounded corners,
    and an optional custom icon drawn with pygame primitives.

    Args:
        x (int): X position.
        y (int): Y position.
        w (int): Width.
        h (int): Height.
        text (str): Button label.
        font (pygame.font.Font): Font used to render the label.
        active (bool): Whether the button is in the "selected" state.
        icon_fn (callable|None): Optional function(surface, x, y, size, color)
            that draws a custom icon.  Receives the surface, top-left x/y of
            the icon area, the icon size (square), and the current text color.
    """

    def __init__(self, x, y, w, h, text, font, active=False, icon_fn=None):
        self.rect = pygame.Rect(x, y, w, h)
        self.text = text
        self.font = font
        self.active = active
        self.hovered = False
        self.icon_fn = icon_fn

    def draw(self, surface):
        """Draw the button onto *surface*."""
        # Choose background color based on state
        if self.active:
            bg = Colors.BTN_ACTIVE
            text_color = Colors.BG_DARK
        elif self.hovered:
            bg = Colors.BTN_HOVER
            text_color = Colors.BTN_TEXT
        else:
            bg = Colors.BTN_NORMAL
            text_color = Colors.BTN_TEXT

        # Draw rounded rectangle
        pygame.draw.rect(surface, bg, self.rect, border_radius=CORNER_RADIUS)

        # Draw subtle border
        border_color = Colors.ACCENT_TEAL if self.active else Colors.BORDER
        pygame.draw.rect(surface, border_color, self.rect, width=1,
                         border_radius=CORNER_RADIUS)

        # Render text
        text_surf = self.font.render(self.text, True, text_color)

        if self.icon_fn:
            # Layout: [  icon  gap  text  ]  centered as a group
            icon_size = 16
            gap = 8
            total_w = icon_size + gap + text_surf.get_width()
            start_x = self.rect.x + (self.rect.width - total_w) // 2
            icon_y = self.rect.centery - icon_size // 2

            self.icon_fn(surface, start_x, icon_y, icon_size, text_color)

            text_x = start_x + icon_size + gap
            text_y = self.rect.centery - text_surf.get_height() // 2
            surface.blit(text_surf, (text_x, text_y))
        else:
            # No icon — center text as before
            text_rect = text_surf.get_rect(center=self.rect.center)
            surface.blit(text_surf, text_rect)

    def handle_event(self, event):
        """
        Process a pygame event and return True if the button was clicked.

        Also updates the hover state.

        Args:
            event (pygame.event.Event): The event to process.

        Returns:
            bool: True if clicked, False otherwise.
        """
        if event.type == pygame.MOUSEMOTION:
            self.hovered = self.rect.collidepoint(event.pos)

        if event.type == pygame.MOUSEBUTTONDOWN and event.button == 1:
            if self.rect.collidepoint(event.pos):
                return True

        return False


# ---------------------------------------------------------------------------
# Icon drawing functions  (used as icon_fn callbacks for buttons)
# ---------------------------------------------------------------------------

def icon_speed_bars(num_bars):
    """
    Return an icon_fn that draws *num_bars* rising bars (1-4).
    Gives a visual speed-meter effect:  ▁  ▁▂  ▁▂▃  ▁▂▃▄
    """
    def _draw(surface, x, y, size, color):
        bar_w = max(2, size // 5)
        gap = 1
        total_w = num_bars * bar_w + (num_bars - 1) * gap
        start_x = x + (size - total_w) // 2

        for i in range(num_bars):
            # Bar height increases with index
            frac = (i + 1) / 4
            bar_h = max(3, int(size * frac))
            bx = start_x + i * (bar_w + gap)
            by = y + size - bar_h
            pygame.draw.rect(surface, color,
                             pygame.Rect(bx, by, bar_w, bar_h),
                             border_radius=1)
    return _draw


def icon_play(surface, x, y, size, color):
    """Draw a right-pointing play triangle."""
    margin = size // 5
    points = [
        (x + margin, y + margin),
        (x + size - margin, y + size // 2),
        (x + margin, y + size - margin),
    ]
    pygame.draw.polygon(surface, color, points)


def icon_stop_reset(surface, x, y, size, color):
    """Draw a stop square (⏹)."""
    margin = size // 4
    rect = pygame.Rect(x + margin, y + margin,
                       size - 2 * margin, size - 2 * margin)
    pygame.draw.rect(surface, color, rect, border_radius=2)


def icon_shuffle(surface, x, y, size, color):
    """Draw two crossing arrows to indicate shuffle / new array."""
    m = size // 5
    # Two diagonal lines crossing
    pygame.draw.line(surface, color,
                     (x + m, y + m), (x + size - m, y + size - m), 2)
    pygame.draw.line(surface, color,
                     (x + m, y + size - m), (x + size - m, y + m), 2)
    # Arrow heads on the ends
    ah = max(3, size // 4)
    # Top-right arrow head
    pygame.draw.line(surface, color,
                     (x + size - m, y + m), (x + size - m - ah, y + m), 2)
    pygame.draw.line(surface, color,
                     (x + size - m, y + m), (x + size - m, y + m + ah), 2)
    # Bottom-right arrow head
    pygame.draw.line(surface, color,
                     (x + size - m, y + size - m),
                     (x + size - m - ah, y + size - m), 2)
    pygame.draw.line(surface, color,
                     (x + size - m, y + size - m),
                     (x + size - m, y + size - m - ah), 2)


class Panel:
    """
    A simple rectangular panel with a dark background and optional title.

    Args:
        x (int): X position.
        y (int): Y position.
        w (int): Width.
        h (int): Height.
    """

    def __init__(self, x, y, w, h):
        self.rect = pygame.Rect(x, y, w, h)

    def draw(self, surface):
        """Draw the panel background and border."""
        pygame.draw.rect(surface, Colors.BG_PANEL, self.rect,
                         border_radius=CORNER_RADIUS)
        pygame.draw.rect(surface, Colors.BORDER, self.rect, width=1,
                         border_radius=CORNER_RADIUS)


class Slider:
    """
    A horizontal slider for choosing array size.

    Args:
        x (int): X position.
        y (int): Y position.
        w (int): Width.
        h (int): Height of the track.
        min_val (int): Minimum value.
        max_val (int): Maximum value.
        initial (int): Starting value.
        font (pygame.font.Font): Font for the value label.
    """

    def __init__(self, x, y, w, h, min_val, max_val, initial, font):
        self.rect = pygame.Rect(x, y, w, h)
        self.min_val = min_val
        self.max_val = max_val
        self.value = initial
        self.font = font
        self.dragging = False

        # Knob radius (compact size)
        self.knob_radius = max(6, h - 2)

    @property
    def _knob_x(self):
        """Calculate the knob's X position from the current value."""
        ratio = (self.value - self.min_val) / max(1, self.max_val - self.min_val)
        return int(self.rect.x + ratio * self.rect.width)

    def draw(self, surface):
        """Render the slider track, filled portion, and knob."""
        cy = self.rect.centery

        # Track background
        track_rect = pygame.Rect(self.rect.x, cy - 3, self.rect.width, 6)
        pygame.draw.rect(surface, Colors.BORDER, track_rect, border_radius=3)

        # Filled portion
        knob_x = self._knob_x
        fill_rect = pygame.Rect(self.rect.x, cy - 3, knob_x - self.rect.x, 6)
        pygame.draw.rect(surface, Colors.ACCENT_TEAL, fill_rect, border_radius=3)

        # Knob
        pygame.draw.circle(surface, Colors.ACCENT_TEAL, (knob_x, cy),
                           self.knob_radius)
        pygame.draw.circle(surface, Colors.BG_DARK, (knob_x, cy),
                           self.knob_radius - 3)

        # Value label
        label = self.font.render(str(self.value), True, Colors.TEXT_PRIMARY)
        surface.blit(label, (self.rect.right + 10, cy - label.get_height() // 2))

    def handle_event(self, event):
        """
        Handle mouse events for dragging the slider knob.

        Returns:
            bool: True if the value changed.
        """
        if event.type == pygame.MOUSEBUTTONDOWN and event.button == 1:
            # Check if click is near the knob or on the track
            expanded = self.rect.inflate(0, 20)
            if expanded.collidepoint(event.pos):
                self.dragging = True
                return self._update_value(event.pos[0])

        elif event.type == pygame.MOUSEBUTTONUP:
            self.dragging = False

        elif event.type == pygame.MOUSEMOTION and self.dragging:
            return self._update_value(event.pos[0])

        return False

    def _update_value(self, mouse_x):
        """Update the slider value from a mouse X position."""
        ratio = (mouse_x - self.rect.x) / max(1, self.rect.width)
        ratio = max(0.0, min(1.0, ratio))
        new_val = int(self.min_val + ratio * (self.max_val - self.min_val))

        if new_val != self.value:
            self.value = new_val
            return True
        return False
