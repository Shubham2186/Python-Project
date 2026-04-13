"""
renderer.py - Main rendering engine for the Algorithm Visualizer.

Handles the pygame display loop, draws bars, sidebar controls,
status bar, and drives the sorting animation via generators.

The sidebar is split into two zones:
  1. **Scrollable area** – algorithm buttons, speed buttons, array-size
     slider, and action buttons.  Scrolls with the mouse wheel when the
     content is taller than the available space.
  2. **Fixed info panel** – algorithm complexity info pinned to the
     bottom of the sidebar (never scrolls).
"""

import math
import pygame
import sys
import time

from utils.helpers import (
    Colors, generate_random_array, get_bar_color, lerp_color,
    SPEED_SETTINGS, ALGORITHM_INFO, COMPLEXITY_COMPARISON,
    recommend_algorithm,
)
from visualizer.controls import (
    Button, Panel, Slider,
    SIDEBAR_WIDTH, TOP_BAR_HEIGHT, PADDING, BUTTON_HEIGHT, BUTTON_SPACING,
    CORNER_RADIUS,
    icon_speed_bars, icon_play, icon_stop_reset, icon_shuffle,
)
from algorithms.bubble_sort import bubble_sort
from algorithms.merge_sort import merge_sort


# ---------------------------------------------------------------------------
# Constants
# ---------------------------------------------------------------------------
MIN_WINDOW_W = 960
MIN_WINDOW_H = 640
DEFAULT_ARRAY_SIZE = 50
BAR_GAP = 2              # Pixels between bars
BAR_BOTTOM_MARGIN = 40   # Leave room for the legend
INFO_PANEL_HEIGHT = 250  # Fixed height for comparison + recommendation panel
SCROLL_SPEED = 25        # Pixels per mouse-wheel notch
ARROW_SIZE = 12          # Size of the sorting-indicator arrow
GLOW_PULSE_SPEED = 6.0   # Speed of the bar glow pulse (Hz)


class Renderer:
    """
    The core visualizer class.

    Manages the pygame window, control sidebar, status bar,
    bar rendering, and the animation loop.
    """

    def __init__(self):
        pygame.init()

        # Window setup
        info = pygame.display.Info()
        self.width = max(MIN_WINDOW_W, int(info.current_w * 0.75))
        self.height = max(MIN_WINDOW_H, int(info.current_h * 0.7))
        self.screen = pygame.display.set_mode(
            (self.width, self.height), pygame.RESIZABLE
        )
        pygame.display.set_caption("Interactive Algorithm Visualizer")

        # Fonts
        self.font_title = pygame.font.SysFont("Segoe UI", 22, bold=True)
        self.font_heading = pygame.font.SysFont("Segoe UI", 16, bold=True)
        self.font_body = pygame.font.SysFont("Segoe UI", 14)
        self.font_small = pygame.font.SysFont("Segoe UI", 12)
        self.font_big = pygame.font.SysFont("Segoe UI", 28, bold=True)

        # Clock for frame-rate limiting
        self.clock = pygame.time.Clock()

        # State
        self.algorithm = "Bubble Sort"
        self.speed = "Medium"
        self.array_size = DEFAULT_ARRAY_SIZE
        self.array = generate_random_array(self.array_size)
        self.sorting = False
        self.finished = False
        self.generator = None
        self.current_state = None
        self.step_count = 0
        self.start_time = 0.0
        self.elapsed_snapshot = 0.0  # frozen elapsed time when sorting finishes

        # Last step timestamp (for speed control)
        self._last_step_time = 0.0

        # Animation state
        self._anim_tick = 0          # incremented every frame for pulse effects
        self._bar_offsets = {}       # index -> (dy, frame_count) for bounce anim
        self._prev_swap_set = set()  # track previous swap to trigger bounces

        # Sidebar scroll offset (pixels; 0 = top, positive = scrolled down)
        self._scroll_offset = 0

        # Build UI controls (buttons, slider)
        self._build_controls()

    # ------------------------------------------------------------------
    # UI construction
    # ------------------------------------------------------------------
    def _build_controls(self):
        """
        Create all sidebar buttons and the array-size slider.

        Positions are calculated relative to y=0 (top of the scrollable
        content area).  During drawing they are shifted by -scroll_offset
        and clipped to the visible scroll region.
        """
        x = PADDING
        btn_w = SIDEBAR_WIDTH - 2 * PADDING

        # ----- positions are relative to the scroll content origin -----
        y = PADDING  # start from top of scroll content

        # Section: ALGORITHM
        self._algo_label_y = y
        y += 22

        self.btn_bubble = Button(
            x, y, btn_w, BUTTON_HEIGHT, "Bubble Sort",
            self.font_body, active=(self.algorithm == "Bubble Sort"),
        )
        y += BUTTON_HEIGHT + BUTTON_SPACING

        self.btn_merge = Button(
            x, y, btn_w, BUTTON_HEIGHT, "Merge Sort",
            self.font_body, active=(self.algorithm == "Merge Sort"),
        )
        y += BUTTON_HEIGHT + 28

        # Section: SPEED
        self._speed_label_y = y
        y += 22

        self.btn_very_slow = Button(
            x, y, btn_w, BUTTON_HEIGHT, "Very Slow",
            self.font_body, active=(self.speed == "Very Slow"),
            icon_fn=icon_speed_bars(1),
        )
        y += BUTTON_HEIGHT + BUTTON_SPACING

        self.btn_slow = Button(
            x, y, btn_w, BUTTON_HEIGHT, "Slow",
            self.font_body, active=(self.speed == "Slow"),
            icon_fn=icon_speed_bars(2),
        )
        y += BUTTON_HEIGHT + BUTTON_SPACING

        self.btn_medium = Button(
            x, y, btn_w, BUTTON_HEIGHT, "Medium",
            self.font_body, active=(self.speed == "Medium"),
            icon_fn=icon_speed_bars(3),
        )
        y += BUTTON_HEIGHT + BUTTON_SPACING

        self.btn_fast = Button(
            x, y, btn_w, BUTTON_HEIGHT, "Fast",
            self.font_body, active=(self.speed == "Fast"),
            icon_fn=icon_speed_bars(4),
        )
        y += BUTTON_HEIGHT + 28

        # Section: ARRAY SIZE
        self._slider_label_y = y
        y += 25

        self.slider_size = Slider(
            x, y, btn_w - 50, 14,
            min_val=10, max_val=150,
            initial=self.array_size,
            font=self.font_body,
        )
        y += 45

        # Section: ACTIONS
        self.btn_generate = Button(
            x, y, btn_w, BUTTON_HEIGHT, "New Array",
            self.font_body, icon_fn=icon_shuffle,
        )
        y += BUTTON_HEIGHT + BUTTON_SPACING

        self.btn_start = Button(
            x, y, btn_w, BUTTON_HEIGHT + 4, "Start Sorting",
            self.font_heading, icon_fn=icon_play,
        )
        y += BUTTON_HEIGHT + BUTTON_SPACING + 4

        self.btn_restart = Button(
            x, y, btn_w, BUTTON_HEIGHT, "Reset",
            self.font_body, icon_fn=icon_stop_reset,
        )
        y += BUTTON_HEIGHT + PADDING

        # Total height of all scrollable content
        self._scroll_content_height = y

        # Gather all buttons for event processing
        self.all_buttons = [
            self.btn_bubble, self.btn_merge,
            self.btn_very_slow, self.btn_slow, self.btn_medium, self.btn_fast,
            self.btn_generate, self.btn_start, self.btn_restart,
        ]

    # ------------------------------------------------------------------
    # Scroll helpers
    # ------------------------------------------------------------------
    @property
    def _scroll_view_height(self):
        """Visible height available for the scrollable control area."""
        return self.height - TOP_BAR_HEIGHT - INFO_PANEL_HEIGHT

    @property
    def _max_scroll(self):
        """Maximum scroll offset (0 when content fits without scrolling)."""
        return max(0, self._scroll_content_height - self._scroll_view_height)

    def _clamp_scroll(self):
        """Keep scroll offset within valid bounds."""
        self._scroll_offset = max(0, min(self._scroll_offset, self._max_scroll))

    def _scroll_to_screen_y(self, content_y):
        """Convert a content-space Y to screen-space Y."""
        return TOP_BAR_HEIGHT + content_y - self._scroll_offset

    # ------------------------------------------------------------------
    # Event handling
    # ------------------------------------------------------------------
    def _handle_events(self):
        """Process all pygame events for one frame."""
        for event in pygame.event.get():
            if event.type == pygame.QUIT:
                pygame.quit()
                sys.exit()

            if event.type == pygame.VIDEORESIZE:
                self.width, self.height = event.w, event.h
                self.screen = pygame.display.set_mode(
                    (self.width, self.height), pygame.RESIZABLE
                )
                self._clamp_scroll()

            # --- Mouse wheel scrolling (only when pointer inside sidebar) ---
            if event.type == pygame.MOUSEWHEEL:
                mx, my = pygame.mouse.get_pos()
                if mx < SIDEBAR_WIDTH and my > TOP_BAR_HEIGHT:
                    self._scroll_offset -= event.y * SCROLL_SPEED
                    self._clamp_scroll()

            # --- Slider interaction ---
            if not self.sorting:
                # Translate mouse pos into scroll-content space for slider
                adjusted_event = self._adjust_event_for_scroll(event)
                if self.slider_size.handle_event(adjusted_event):
                    self.array_size = self.slider_size.value
                    self.array = generate_random_array(self.array_size)
                    self.finished = False

            # --- Button clicks ---
            for btn in self.all_buttons:
                adjusted_event = self._adjust_event_for_scroll(event)
                if btn.handle_event(adjusted_event):
                    self._on_button_click(btn)

    def _adjust_event_for_scroll(self, event):
        """
        Return a shallow copy of a mouse event with its Y position
        translated from screen-space into scroll-content-space.

        Non-mouse events are returned unchanged.
        """
        if event.type in (pygame.MOUSEBUTTONDOWN, pygame.MOUSEBUTTONUP,
                          pygame.MOUSEMOTION):
            # Only adjust if inside the sidebar scroll area
            mx, my = event.pos
            if mx < SIDEBAR_WIDTH and my >= TOP_BAR_HEIGHT:
                adjusted_y = my - TOP_BAR_HEIGHT + self._scroll_offset
                # Create a new event with adjusted pos
                new_event = pygame.event.Event(event.type, {
                    **{k: getattr(event, k) for k in event.__dict__
                       if k != 'pos'},
                    'pos': (mx, adjusted_y),
                })
                return new_event
        return event

    def _on_button_click(self, btn):
        """Dispatch logic when a button is pressed."""

        # --- Algorithm selection (only when not sorting) ---
        if not self.sorting:
            if btn is self.btn_bubble:
                self.algorithm = "Bubble Sort"
                self.btn_bubble.active = True
                self.btn_merge.active = False
            elif btn is self.btn_merge:
                self.algorithm = "Merge Sort"
                self.btn_bubble.active = False
                self.btn_merge.active = True

        # --- Speed selection (always available) ---
        if btn is self.btn_very_slow:
            self.speed = "Very Slow"
        elif btn is self.btn_slow:
            self.speed = "Slow"
        elif btn is self.btn_medium:
            self.speed = "Medium"
        elif btn is self.btn_fast:
            self.speed = "Fast"

        # Update speed button highlights
        self.btn_very_slow.active = (self.speed == "Very Slow")
        self.btn_slow.active = (self.speed == "Slow")
        self.btn_medium.active = (self.speed == "Medium")
        self.btn_fast.active = (self.speed == "Fast")

        # --- Generate new array ---
        if btn is self.btn_generate and not self.sorting:
            self.array = generate_random_array(self.array_size)
            self.current_state = None
            self.finished = False
            self.step_count = 0

        # --- Start sorting ---
        if btn is self.btn_start and not self.sorting and not self.finished:
            self._start_sorting()

        # --- Restart ---
        if btn is self.btn_restart:
            self.sorting = False
            self.finished = False
            self.generator = None
            self.current_state = None
            self.step_count = 0
            self.array = generate_random_array(self.array_size)

    def _start_sorting(self):
        """Initialize the generator for the selected algorithm."""
        self.sorting = True
        self.finished = False
        self.step_count = 0
        self.start_time = time.time()
        self.elapsed_snapshot = 0.0
        self._last_step_time = 0.0

        if self.algorithm == "Bubble Sort":
            self.generator = bubble_sort(self.array)
        else:
            self.generator = merge_sort(self.array)

    # ------------------------------------------------------------------
    # Animation stepping
    # ------------------------------------------------------------------
    def _advance_sort(self):
        """Advance the sort generator by one step (respecting speed delay)."""
        if not self.sorting or self.generator is None:
            return

        now = time.time() * 1000  # milliseconds
        delay = SPEED_SETTINGS[self.speed]["delay_ms"]

        if now - self._last_step_time < delay:
            return  # Not time for the next step yet

        try:
            self.current_state = next(self.generator)
            self.step_count += 1
            self._last_step_time = now
        except StopIteration:
            # Sorting done – mark all as sorted
            self.sorting = False
            self.finished = True
            self.elapsed_snapshot = time.time() - self.start_time
            self.generator = None
            if self.current_state:
                self.current_state["sorted"] = set(range(len(self.array)))
                self.current_state["compare"] = None
                self.current_state["swap"] = None

    # ------------------------------------------------------------------
    # Drawing
    # ------------------------------------------------------------------
    def _draw(self):
        """Render a single frame: background, bars, sidebar, status bar."""
        self._anim_tick += 1
        self.screen.fill(Colors.BG_DARK)

        self._draw_sidebar()
        self._draw_top_bar()
        self._draw_bars()

        pygame.display.flip()

    # -- Sidebar --
    def _draw_sidebar(self):
        """
        Draw the left control panel with a scrollable controls area
        and a fixed complexity-info panel at the bottom.
        """
        # Full sidebar background
        pygame.draw.rect(self.screen, Colors.BG_PANEL,
                         pygame.Rect(0, 0, SIDEBAR_WIDTH, self.height))
        pygame.draw.line(self.screen, Colors.BORDER,
                         (SIDEBAR_WIDTH - 1, 0),
                         (SIDEBAR_WIDTH - 1, self.height))

        # ---- Title (fixed, always visible above the scroll area) ----
        title = self.font_title.render("Algorithm Visualizer", True,
                                       Colors.ACCENT_TEAL)
        self.screen.blit(title, (PADDING, PADDING + 4))

        # ---- Scrollable controls area ----
        scroll_top = TOP_BAR_HEIGHT      # screen Y where scroll area begins
        scroll_h = self._scroll_view_height  # visible height

        if scroll_h > 0:
            # Create an off-screen surface for the scrollable content
            scroll_surface = pygame.Surface(
                (SIDEBAR_WIDTH, self._scroll_content_height), pygame.SRCALPHA
            )
            scroll_surface.fill((0, 0, 0, 0))  # transparent

            # Draw section labels onto scroll surface
            algo_label = self.font_heading.render("ALGORITHM", True,
                                                   Colors.TEXT_SECONDARY)
            scroll_surface.blit(algo_label, (PADDING, self._algo_label_y))

            speed_label = self.font_heading.render("SPEED", True,
                                                    Colors.TEXT_SECONDARY)
            scroll_surface.blit(speed_label, (PADDING, self._speed_label_y))

            size_label = self.font_heading.render("ARRAY SIZE", True,
                                                   Colors.TEXT_SECONDARY)
            scroll_surface.blit(size_label, (PADDING, self._slider_label_y))

            # Draw buttons onto scroll surface
            for btn in self.all_buttons:
                btn.draw(scroll_surface)

            # Draw slider onto scroll surface
            self.slider_size.draw(scroll_surface)

            # Blit the visible portion of the scroll surface onto screen
            src_rect = pygame.Rect(0, self._scroll_offset,
                                   SIDEBAR_WIDTH, scroll_h)
            self.screen.blit(scroll_surface, (0, scroll_top), src_rect)

            # ---- Scroll indicator (thin bar on right edge) ----
            if self._max_scroll > 0:
                self._draw_scrollbar(scroll_top, scroll_h)

        # ---- Fixed comparison panel at bottom (not scrollable) ----
        self._draw_comparison_panel()

    def _draw_scrollbar(self, scroll_top, scroll_h):
        """Draw a thin scrollbar indicator on the right side of the sidebar."""
        bar_x = SIDEBAR_WIDTH - 5
        bar_w = 3

        # Track
        pygame.draw.rect(self.screen, Colors.BORDER,
                         pygame.Rect(bar_x, scroll_top, bar_w, scroll_h),
                         border_radius=2)

        # Thumb
        if self._scroll_content_height > 0:
            thumb_ratio = scroll_h / self._scroll_content_height
            thumb_h = max(20, int(scroll_h * thumb_ratio))
            thumb_y = scroll_top + int(
                (self._scroll_offset / self._max_scroll) *
                (scroll_h - thumb_h)
            ) if self._max_scroll > 0 else scroll_top

            pygame.draw.rect(self.screen, Colors.ACCENT_TEAL,
                             pygame.Rect(bar_x, thumb_y, bar_w, thumb_h),
                             border_radius=2)

    def _draw_comparison_panel(self):
        """
        Draw a complexity comparison table for Bubble Sort vs Merge Sort
        plus a smart recommendation based on current array size.
        All rendering is clipped to the panel bounds.
        """
        box_y = self.height - INFO_PANEL_HEIGHT
        box_w = SIDEBAR_WIDTH
        box_bottom = self.height  # absolute bottom edge

        # Background
        pygame.draw.rect(self.screen, Colors.BG_PANEL,
                         pygame.Rect(0, box_y, box_w, INFO_PANEL_HEIGHT))
        # Top divider
        pygame.draw.line(self.screen, Colors.BORDER,
                         (0, box_y), (box_w, box_y))

        # Inner card
        card_margin = 6
        card = Panel(card_margin, box_y + card_margin,
                     box_w - 2 * card_margin,
                     INFO_PANEL_HEIGHT - 2 * card_margin)
        card.draw(self.screen)

        # --- Clip all subsequent drawing to the panel area ---
        prev_clip = self.screen.get_clip()
        self.screen.set_clip(pygame.Rect(0, box_y, box_w, INFO_PANEL_HEIGHT))

        y = box_y + card_margin + 8
        max_text_w = box_w - 2 * PADDING - 8  # max pixel width for text

        # ----- Section: Complexity Comparison Table -----
        header = self.font_heading.render("COMPLEXITY COMPARISON", True,
                                          Colors.ACCENT_TEAL)
        self.screen.blit(header, (PADDING, y))
        y += 22

        # Column headers
        col_left = PADDING + 55   # "Bubble" column
        col_right = PADDING + 145  # "Merge" column

        bh = self.font_small.render("Bubble", True, Colors.ACCENT_PURPLE)
        mh = self.font_small.render("Merge", True, Colors.ACCENT_TEAL)
        self.screen.blit(bh, (col_left, y))
        self.screen.blit(mh, (col_right, y))
        y += 16

        # Separator line
        pygame.draw.line(self.screen, Colors.BORDER,
                         (PADDING, y), (box_w - PADDING, y))
        y += 4

        # Rows
        bubble_info = COMPLEXITY_COMPARISON["Bubble Sort"]
        merge_info = COMPLEXITY_COMPARISON["Merge Sort"]

        rows = [
            ("Best",  bubble_info["label_best"],  merge_info["label_best"]),
            ("Avg",   bubble_info["label_avg"],   merge_info["label_avg"]),
            ("Worst", bubble_info["label_worst"], merge_info["label_worst"]),
            ("Space", bubble_info["label_space"], merge_info["label_space"]),
        ]

        for label, bval, mval in rows:
            if y >= box_bottom - 4:
                break
            lbl = self.font_small.render(f"  {label}", True,
                                          Colors.TEXT_SECONDARY)
            b_better = self._is_better(bval, mval)
            m_better = self._is_better(mval, bval)

            bc = Colors.ACCENT_GREEN if b_better else Colors.TEXT_PRIMARY
            mc = Colors.ACCENT_GREEN if m_better else Colors.TEXT_PRIMARY

            bv = self.font_small.render(bval, True, bc)
            mv = self.font_small.render(mval, True, mc)

            self.screen.blit(lbl, (PADDING, y))
            self.screen.blit(bv, (col_left, y))
            self.screen.blit(mv, (col_right, y))
            y += 16

        y += 6

        # ----- Section: Recommendation -----
        if y < box_bottom - 20:
            pygame.draw.line(self.screen, Colors.BORDER,
                             (PADDING, y), (box_w - PADDING, y))
            y += 6

            rec_header = self.font_heading.render("RECOMMENDATION", True,
                                                   Colors.ACCENT_ORANGE)
            self.screen.blit(rec_header, (PADDING, y))
            y += 20

            recommended, reason = recommend_algorithm(self.array_size)

            # Recommendation badge
            if recommended == "Bubble Sort":
                badge_color = Colors.ACCENT_PURPLE
            elif recommended == "Merge Sort":
                badge_color = Colors.ACCENT_TEAL
            else:
                badge_color = Colors.ACCENT_ORANGE

            # Pulsing badge
            pulse = 0.7 + 0.3 * math.sin(self._anim_tick * 0.05)
            badge_c = tuple(max(0, min(255, int(c * pulse)))
                            for c in badge_color)

            badge_text = self.font_body.render(f" \u25b6 {recommended} ", True,
                                                Colors.BG_DARK)
            badge_rect = badge_text.get_rect()
            badge_rect.x = PADDING + 4
            badge_rect.y = y
            bg_rect = badge_rect.inflate(8, 4)
            pygame.draw.rect(self.screen, badge_c, bg_rect, border_radius=4)
            self.screen.blit(badge_text, badge_rect)
            y += 24

            # Reason text (multi-line, truncated to fit)
            for line in reason.split("\n"):
                if y >= box_bottom - 6:
                    break
                text = line.strip()
                line_surf = self.font_small.render(text, True,
                                                   Colors.TEXT_SECONDARY)
                # Truncate if wider than available space
                if line_surf.get_width() > max_text_w:
                    while (line_surf.get_width() > max_text_w
                           and len(text) > 3):
                        text = text[:-4] + "..."
                        line_surf = self.font_small.render(
                            text, True, Colors.TEXT_SECONDARY)
                self.screen.blit(line_surf, (PADDING + 4, y))
                y += 14

        # --- Restore previous clip ---
        self.screen.set_clip(prev_clip)

    @staticmethod
    def _is_better(val_a, val_b):
        """
        Rough heuristic: return True if val_a is strictly better
        (lower complexity) than val_b based on the label strings.
        """
        order = ["O(1)", "O(n)", "O(n log n)", "O(n²)", "O(n³)"]
        try:
            return order.index(val_a) < order.index(val_b)
        except ValueError:
            return False

    # -- Top bar --
    def _draw_top_bar(self):
        """Draw the status bar across the top of the visualization area."""
        bar_rect = pygame.Rect(SIDEBAR_WIDTH, 0,
                               self.width - SIDEBAR_WIDTH, TOP_BAR_HEIGHT)
        pygame.draw.rect(self.screen, Colors.BG_PANEL, bar_rect)
        pygame.draw.line(self.screen, Colors.BORDER,
                         (SIDEBAR_WIDTH, TOP_BAR_HEIGHT),
                         (self.width, TOP_BAR_HEIGHT))

        x = SIDEBAR_WIDTH + PADDING
        cy = TOP_BAR_HEIGHT // 2

        # Status indicator
        if self.sorting:
            status_text = "SORTING..."
            status_color = Colors.ACCENT_ORANGE
        elif self.finished:
            status_text = "COMPLETE ✓"
            status_color = Colors.ACCENT_GREEN
        else:
            status_text = "READY"
            status_color = Colors.ACCENT_TEAL

        # Pulsing dot
        dot_radius = 6
        pygame.draw.circle(self.screen, status_color, (x + dot_radius, cy),
                           dot_radius)
        x += dot_radius * 2 + 10

        status = self.font_heading.render(status_text, True, status_color)
        self.screen.blit(status, (x, cy - status.get_height() // 2))
        x += status.get_width() + 30

        # Step counter
        step_txt = self.font_body.render(
            f"Steps: {self.step_count}", True, Colors.TEXT_SECONDARY
        )
        self.screen.blit(step_txt, (x, cy - step_txt.get_height() // 2))
        x += step_txt.get_width() + 30

        # Elapsed time
        if self.sorting:
            elapsed = time.time() - self.start_time
        elif self.finished:
            elapsed = self.elapsed_snapshot
        else:
            elapsed = None

        if elapsed is not None:
            time_txt = self.font_body.render(
                f"Time: {elapsed:.2f}s", True, Colors.TEXT_SECONDARY
            )
            self.screen.blit(time_txt,
                             (x, cy - time_txt.get_height() // 2))

        # Array size
        size_txt = self.font_body.render(
            f"n = {len(self.array)}", True, Colors.TEXT_SECONDARY
        )
        self.screen.blit(
            size_txt,
            (self.width - size_txt.get_width() - PADDING,
             cy - size_txt.get_height() // 2),
        )

    # -- Bars --
    def _draw_bars(self):
        """
        Draw the array as vertical bars in the main visualization area.

        Bars are color-coded:
          - Default: gradient from teal to purple based on value
          - Yellow: currently compared
          - Red: currently being swapped / written
          - Green: in final sorted position
          - Blue outline: active merge range

        Active bars get a downward arrow indicator and a glow effect.
        Swapped bars get a bounce animation.
        """
        vis_x = SIDEBAR_WIDTH + PADDING
        vis_y = TOP_BAR_HEIGHT + PADDING
        vis_w = self.width - SIDEBAR_WIDTH - 2 * PADDING
        vis_h = self.height - TOP_BAR_HEIGHT - 2 * PADDING - BAR_BOTTOM_MARGIN

        n = len(self.array)
        if n == 0:
            return

        max_val = max(self.array) or 1

        # Calculate bar width
        total_gap = BAR_GAP * (n - 1)
        bar_w = max(1, (vis_w - total_gap) / n)

        # Determine highlight sets from current state
        compare_set = set()
        swap_set = set()
        sorted_set = set()
        active_range = None

        if self.current_state:
            cmp = self.current_state.get("compare")
            if cmp:
                compare_set = set(cmp) if isinstance(cmp, tuple) else {cmp}

            swp = self.current_state.get("swap")
            if swp is not None:
                swap_set = {swp} if isinstance(swp, int) else set(swp)

            sorted_set = self.current_state.get("sorted", set())
            active_range = self.current_state.get("active_range")

        elif self.finished:
            sorted_set = set(range(n))

        # --- Trigger bounce animation on new swaps ---
        new_swaps = swap_set - self._prev_swap_set
        for idx in new_swaps:
            self._bar_offsets[idx] = 8  # start bounce at 8px upward
        self._prev_swap_set = set(swap_set)

        # --- Update bounce offsets ---
        finished_bounces = []
        for idx in list(self._bar_offsets):
            self._bar_offsets[idx] *= 0.75  # decay
            if abs(self._bar_offsets[idx]) < 0.5:
                finished_bounces.append(idx)
        for idx in finished_bounces:
            del self._bar_offsets[idx]

        # --- Glow pulse factor ---
        glow_t = (math.sin(self._anim_tick * 0.12) + 1) / 2  # 0..1

        for i, val in enumerate(self.array):
            # Bar geometry
            bx = vis_x + i * (bar_w + BAR_GAP)
            bar_h = max(2, (val / max_val) * vis_h)
            by = vis_y + vis_h - bar_h

            # Apply bounce offset
            bounce_dy = self._bar_offsets.get(i, 0)
            by -= bounce_dy

            # Choose color
            is_active = False
            if i in swap_set:
                color = Colors.SWAP
                is_active = True
            elif i in compare_set:
                color = Colors.COMPARE
                is_active = True
            elif i in sorted_set:
                color = Colors.SORTED
            else:
                color = get_bar_color(val, max_val)

            # Draw glow behind active bars
            if is_active and self.sorting:
                glow_alpha = int(60 + 40 * glow_t)
                glow_expand = int(3 + 2 * glow_t)
                glow_surf = pygame.Surface(
                    (max(1, int(bar_w)) + glow_expand * 2,
                     int(bar_h) + glow_expand * 2),
                    pygame.SRCALPHA,
                )
                glow_color = (*Colors.ARROW_GLOW, glow_alpha)
                glow_surf.fill(glow_color)
                self.screen.blit(
                    glow_surf,
                    (int(bx) - glow_expand, int(by) - glow_expand),
                )

            # Draw the bar
            bar_rect = pygame.Rect(int(bx), int(by), max(1, int(bar_w)),
                                   int(bar_h))
            pygame.draw.rect(self.screen, color, bar_rect,
                             border_radius=min(3, int(bar_w // 2)))

            # Active range outline (merge sort)
            if active_range and active_range[0] <= i <= active_range[1]:
                pygame.draw.rect(self.screen, Colors.ACTIVE_RANGE, bar_rect,
                                 width=1, border_radius=min(3, int(bar_w // 2)))

            # --- Draw arrow above active bars ---
            if is_active and self.sorting:
                self._draw_sorting_arrow(
                    int(bx) + max(1, int(bar_w)) // 2,
                    int(by) - 4,
                    glow_t,
                )

        # Draw legend at bottom
        self._draw_legend(vis_x, self.height - BAR_BOTTOM_MARGIN + 5)

    def _draw_sorting_arrow(self, cx, tip_y, pulse_t):
        """
        Draw a small downward-pointing arrow above a bar being sorted.

        Args:
            cx (int): Center X of the arrow.
            tip_y (int): Y position of the arrow tip (just above the bar).
            pulse_t (float): 0..1 pulse phase for subtle bobbing.
        """
        bob = int(2 * math.sin(self._anim_tick * 0.15))  # subtle bobbing
        tip_y += bob

        half = ARROW_SIZE // 2
        top_y = tip_y - ARROW_SIZE

        # Arrow body (triangle pointing down)
        points = [
            (cx, tip_y),                  # tip
            (cx - half - 1, top_y),       # top-left
            (cx + half + 1, top_y),       # top-right
        ]

        # Glow outline
        glow_alpha = int(100 + 80 * pulse_t)
        glow_surf = pygame.Surface((ARROW_SIZE + 8, ARROW_SIZE + 8),
                                    pygame.SRCALPHA)
        glow_points = [
            (ARROW_SIZE // 2 + 4, ARROW_SIZE + 4),
            (2, 2),
            (ARROW_SIZE + 6, 2),
        ]
        pygame.draw.polygon(glow_surf, (*Colors.ARROW_GLOW, glow_alpha),
                            glow_points)
        self.screen.blit(glow_surf,
                         (cx - ARROW_SIZE // 2 - 4, top_y - 4))

        # Solid arrow
        pygame.draw.polygon(self.screen, Colors.ARROW, points)
        # Thin border
        pygame.draw.polygon(self.screen, Colors.BG_DARK, points, width=1)

    def _draw_legend(self, x, y):
        """Draw a compact color legend beneath the bars."""
        items = [
            (Colors.COMPARE, "Comparing"),
            (Colors.SWAP, "Swap / Write"),
            (Colors.SORTED, "Sorted"),
        ]
        if self.algorithm == "Merge Sort":
            items.append((Colors.ACTIVE_RANGE, "Active Range"))

        for color, label in items:
            pygame.draw.rect(self.screen, color,
                             pygame.Rect(x, y, 14, 14), border_radius=3)
            txt = self.font_small.render(label, True, Colors.TEXT_SECONDARY)
            self.screen.blit(txt, (x + 20, y))
            x += txt.get_width() + 40

    # ------------------------------------------------------------------
    # Main loop
    # ------------------------------------------------------------------
    def run(self):
        """Start the main application loop."""
        while True:
            self._handle_events()
            self._advance_sort()
            self._draw()
            self.clock.tick(120)  # cap at 120 FPS for smooth rendering
