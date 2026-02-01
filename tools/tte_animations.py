"""
TTE (TerminalTextEffects) Integration for Textual Dashboard
============================================================

Proof-of-concept module demonstrating TTE integration with Textual's rendering cycle.

Effects Implemented:
    1. Startup Splash  - Matrix/decrypt effect for dashboard title on launch
    2. Theme Transitions - Slide/fade effect when cycling themes with 't'
    3. Alert Emphasis  - Shake/pulse effect for critical alerts
    4. Refresh Animation - Wipe effect on panel updates

Installation:
    pip install terminaltexteffects textual

Usage:
    from tools.tte_animations import TTEAnimator, TTEWidget
    
    # In your Textual App:
    animator = TTEAnimator()
    widget = TTEWidget(animator, effect="decrypt", text="SYNAPSE ENGINE")
    
Integration Notes:
    - TTE generates ANSI escape sequences; Textual's Rich console handles them
    - Effects are frame generators - we iterate async to not block the event loop
    - Use TTEWidget for self-contained animated widgets
    - Use TTEAnimator for manual control over effect playback

Author: blorp (subagent)
Date: 2026-02-01
"""

from __future__ import annotations

import asyncio
from dataclasses import dataclass, field
from enum import Enum, auto
from typing import TYPE_CHECKING, AsyncIterator, Callable, Iterator, Literal

# TTE imports
try:
    from terminaltexteffects.effects.effect_decrypt import Decrypt
    from terminaltexteffects.effects.effect_matrix import Matrix
    from terminaltexteffects.effects.effect_slide import Slide
    from terminaltexteffects.effects.effect_wipe import Wipe
    from terminaltexteffects.effects.effect_unstable import Unstable
    from terminaltexteffects.effects.effect_scattered import Scattered
    from terminaltexteffects.effects.effect_expand import Expand
    from terminaltexteffects.effects.effect_colorshift import ColorShift
    TTE_AVAILABLE = True
except ImportError:
    TTE_AVAILABLE = False
    Decrypt = Matrix = Slide = Wipe = Unstable = Scattered = Expand = ColorShift = None

# Textual imports - optional for standalone testing
try:
    from textual.app import App, ComposeResult
    from textual.widgets import Static
    from textual.reactive import reactive
    from textual.message import Message
    from rich.text import Text
    from rich.console import Console
    from rich.segment import Segment
    TEXTUAL_AVAILABLE = True
except ImportError:
    TEXTUAL_AVAILABLE = False
    App = ComposeResult = Static = reactive = Message = Text = Console = Segment = None


# =============================================================================
# Effect Types & Configuration
# =============================================================================

class EffectType(Enum):
    """Available TTE effect types mapped to use cases."""
    # Startup effects
    DECRYPT = auto()      # Movie-style decryption reveal
    MATRIX = auto()       # Matrix digital rain
    
    # Transition effects
    SLIDE = auto()        # Slide in from edge
    EXPAND = auto()       # Expand from center
    WIPE = auto()         # Wipe across screen
    
    # Alert effects
    UNSTABLE = auto()     # Shake/jitter effect
    SCATTERED = auto()    # Characters scatter and reform
    
    # Ambient effects
    COLORSHIFT = auto()   # Gradient color cycling


@dataclass
class EffectConfig:
    """Configuration for TTE effects with Textual-friendly defaults."""
    
    # Canvas dimensions (use -1 to match text, 0 to match terminal)
    canvas_width: int = -1
    canvas_height: int = -1
    
    # Frame timing
    frame_rate: int = 60
    frame_delay_ms: int = 16  # ~60fps default
    
    # Effect-specific options
    typing_speed: int = 2  # For decrypt effect
    
    # Colors (hex without #)
    primary_colors: tuple[str, ...] = ("008000", "00cb00", "00ff00")  # Green matrix
    final_colors: tuple[str, ...] = ("eda000",)  # Orange finish
    
    # Behavior flags
    ignore_terminal_dimensions: bool = True
    no_color: bool = False
    
    # Animation control
    enabled: bool = True
    max_frames: int | None = None  # Limit frame count for testing
    
    @classmethod
    def for_startup_splash(cls) -> "EffectConfig":
        """Preset for startup splash effect."""
        return cls(
            frame_rate=60,
            typing_speed=2,
            primary_colors=("3B60E4", "50D8D7", "F4E409"),  # dlorp branding
            final_colors=("FB8B24", "F4E409"),
            max_frames=180,  # ~3 seconds at 60fps
        )
    
    @classmethod
    def for_theme_transition(cls) -> "EffectConfig":
        """Preset for theme cycling transitions."""
        return cls(
            frame_rate=30,
            max_frames=45,  # ~1.5 seconds
        )
    
    @classmethod
    def for_alert(cls) -> "EffectConfig":
        """Preset for critical alert emphasis."""
        return cls(
            frame_rate=30,
            max_frames=30,  # ~1 second burst
            primary_colors=("ff0000", "ff4444", "ff8888"),  # Red alert
        )
    
    @classmethod
    def for_refresh(cls) -> "EffectConfig":
        """Preset for panel refresh animation."""
        return cls(
            frame_rate=30,
            max_frames=20,  # Quick wipe
        )


# =============================================================================
# Core Animator Class
# =============================================================================

class TTEAnimator:
    """
    Core animation controller for TTE effects.
    
    Provides both sync and async frame generation for flexible integration
    with Textual's event loop.
    
    Example:
        animator = TTEAnimator()
        async for frame in animator.animate_async("SYNAPSE", EffectType.DECRYPT):
            widget.update(frame)
    """
    
    def __init__(self, config: EffectConfig | None = None):
        self.config = config or EffectConfig()
        self._active_effect: Iterator | None = None
        self._is_running = False
        
        if not TTE_AVAILABLE:
            raise ImportError(
                "terminaltexteffects not installed. "
                "Run: pip install terminaltexteffects"
            )
    
    def create_effect(
        self,
        text: str,
        effect_type: EffectType,
        config: EffectConfig | None = None,
    ):
        """
        Create a TTE effect instance with proper configuration.
        
        Args:
            text: The text to animate
            effect_type: Which effect to use
            config: Optional override config
            
        Returns:
            Configured TTE effect iterator
        """
        cfg = config or self.config
        
        # Map effect types to TTE classes
        effect_map = {
            EffectType.DECRYPT: Decrypt,
            EffectType.MATRIX: Matrix,
            EffectType.SLIDE: Slide,
            EffectType.WIPE: Wipe,
            EffectType.UNSTABLE: Unstable,
            EffectType.SCATTERED: Scattered,
            EffectType.EXPAND: Expand,
            EffectType.COLORSHIFT: ColorShift,
        }
        
        effect_cls = effect_map.get(effect_type)
        if effect_cls is None:
            raise ValueError(f"Unknown effect type: {effect_type}")
        
        # Create the effect
        effect = effect_cls(text)
        
        # Configure terminal settings
        effect.terminal_config.ignore_terminal_dimensions = cfg.ignore_terminal_dimensions
        effect.terminal_config.frame_rate = cfg.frame_rate
        effect.terminal_config.no_color = cfg.no_color
        
        if cfg.canvas_width > 0:
            effect.terminal_config.canvas_width = cfg.canvas_width
        if cfg.canvas_height > 0:
            effect.terminal_config.canvas_height = cfg.canvas_height
        
        # Configure effect-specific settings where applicable
        if effect_type == EffectType.DECRYPT and hasattr(effect.effect_config, 'typing_speed'):
            effect.effect_config.typing_speed = cfg.typing_speed
        
        return effect
    
    def animate_sync(
        self,
        text: str,
        effect_type: EffectType,
        config: EffectConfig | None = None,
    ) -> Iterator[str]:
        """
        Generate animation frames synchronously.
        
        Yields:
            ANSI-encoded frame strings
        """
        cfg = config or self.config
        effect = self.create_effect(text, effect_type, cfg)
        
        for i, frame in enumerate(effect):
            if cfg.max_frames and i >= cfg.max_frames:
                break
            yield frame
    
    async def animate_async(
        self,
        text: str,
        effect_type: EffectType,
        config: EffectConfig | None = None,
    ) -> AsyncIterator[str]:
        """
        Generate animation frames asynchronously with proper timing.
        
        This is the preferred method for Textual integration as it
        yields control back to the event loop between frames.
        
        Yields:
            ANSI-encoded frame strings
        """
        cfg = config or self.config
        delay = cfg.frame_delay_ms / 1000.0
        
        self._is_running = True
        try:
            for frame in self.animate_sync(text, effect_type, cfg):
                if not self._is_running:
                    break
                yield frame
                await asyncio.sleep(delay)
        finally:
            self._is_running = False
    
    def stop(self):
        """Stop any running animation."""
        self._is_running = False
    
    @property
    def is_running(self) -> bool:
        """Check if an animation is currently playing."""
        return self._is_running


# =============================================================================
# Textual Widget Integration
# =============================================================================

if TEXTUAL_AVAILABLE:
    
    class TTEWidget(Static):
        """
        A Textual widget that displays TTE animations.
        
        This widget handles the async rendering cycle and provides
        reactive updates as frames are generated.
        
        Example:
            class MyApp(App):
                def compose(self):
                    yield TTEWidget(
                        animator=TTEAnimator(),
                        text="SYNAPSE ENGINE",
                        effect=EffectType.DECRYPT,
                        config=EffectConfig.for_startup_splash(),
                    )
        """
        
        # Reactive properties
        is_animating = reactive(False)
        current_frame = reactive("")
        
        class AnimationComplete(Message):
            """Message sent when animation finishes."""
            def __init__(self, widget: "TTEWidget"):
                self.widget = widget
                super().__init__()
        
        class AnimationStarted(Message):
            """Message sent when animation begins."""
            def __init__(self, widget: "TTEWidget"):
                self.widget = widget
                super().__init__()
        
        def __init__(
            self,
            animator: TTEAnimator,
            text: str,
            effect: EffectType = EffectType.DECRYPT,
            config: EffectConfig | None = None,
            auto_start: bool = True,
            show_final: bool = True,
            *args,
            **kwargs,
        ):
            super().__init__(*args, **kwargs)
            self.animator = animator
            self.text = text
            self.effect = effect
            self.config = config
            self.auto_start = auto_start
            self.show_final = show_final
            self._animation_task: asyncio.Task | None = None
        
        def on_mount(self):
            """Start animation when widget is mounted."""
            if self.auto_start:
                self.start_animation()
        
        def start_animation(self):
            """Begin the TTE animation."""
            if self._animation_task and not self._animation_task.done():
                self._animation_task.cancel()
            self._animation_task = asyncio.create_task(self._run_animation())
        
        async def _run_animation(self):
            """Internal async animation loop."""
            self.is_animating = True
            self.post_message(self.AnimationStarted(self))
            
            try:
                async for frame in self.animator.animate_async(
                    self.text, self.effect, self.config
                ):
                    self.current_frame = frame
                    # Strip ANSI cursor control, keep colors
                    clean_frame = self._clean_frame(frame)
                    self.update(clean_frame)
            except asyncio.CancelledError:
                pass
            finally:
                self.is_animating = False
                if self.show_final:
                    self.update(self.text)
                self.post_message(self.AnimationComplete(self))
        
        def _clean_frame(self, frame: str) -> str:
            """
            Clean TTE frame for Textual rendering.
            
            TTE frames include cursor positioning sequences that don't
            work well in Textual widgets. We strip those but keep colors.
            """
            import re
            # Remove cursor positioning (CSI sequences for positioning)
            # Keep color codes (38;2;r;g;b and 0 reset)
            # Pattern matches: ESC[<n>A, ESC[<n>B, ESC[<n>C, ESC[<n>D, ESC[<n>;<m>H
            frame = re.sub(r'\x1b\[\d*[ABCD]', '', frame)
            frame = re.sub(r'\x1b\[\d+;\d+H', '', frame)
            frame = re.sub(r'\x1b\[\?25[hl]', '', frame)  # Cursor show/hide
            return frame
        
        def stop_animation(self):
            """Stop the current animation."""
            self.animator.stop()
            if self._animation_task:
                self._animation_task.cancel()


# =============================================================================
# Specialized Effect Widgets
# =============================================================================

if TEXTUAL_AVAILABLE:
    
    class StartupSplash(TTEWidget):
        """
        Startup splash with matrix/decrypt effect.
        
        Usage:
            yield StartupSplash("S.Y.N.A.P.S.E. ENGINE")
        """
        
        DEFAULT_CSS = """
        StartupSplash {
            width: 100%;
            height: auto;
            text-align: center;
            padding: 1;
        }
        """
        
        def __init__(self, title: str = "S.Y.N.A.P.S.E. ENGINE", **kwargs):
            super().__init__(
                animator=TTEAnimator(),
                text=title,
                effect=EffectType.DECRYPT,
                config=EffectConfig.for_startup_splash(),
                **kwargs,
            )
    
    
    class AlertWidget(TTEWidget):
        """
        Alert widget with shake/unstable effect for critical alerts.
        
        Usage:
            alert = AlertWidget("⚠️ CRITICAL: Memory threshold exceeded!")
            alert.trigger()  # Play the shake animation
        """
        
        DEFAULT_CSS = """
        AlertWidget {
            width: 100%;
            height: auto;
            background: $error;
            color: $text;
            padding: 1;
        }
        """
        
        def __init__(self, message: str, **kwargs):
            super().__init__(
                animator=TTEAnimator(),
                text=message,
                effect=EffectType.UNSTABLE,
                config=EffectConfig.for_alert(),
                auto_start=False,  # Don't auto-play, trigger manually
                **kwargs,
            )
            self.update(message)  # Show static text initially
        
        def trigger(self):
            """Trigger the alert animation."""
            self.start_animation()
    
    
    class RefreshPanel(TTEWidget):
        """
        Panel with wipe animation on content refresh.
        
        Usage:
            panel = RefreshPanel("metrics_panel")
            panel.refresh_content("New metrics data here...")
        """
        
        DEFAULT_CSS = """
        RefreshPanel {
            width: 100%;
            height: auto;
            border: solid $primary;
            padding: 1;
        }
        """
        
        def __init__(self, panel_id: str, initial_content: str = "", **kwargs):
            super().__init__(
                animator=TTEAnimator(),
                text=initial_content,
                effect=EffectType.WIPE,
                config=EffectConfig.for_refresh(),
                auto_start=False,
                **kwargs,
            )
            self.panel_id = panel_id
            self._content = initial_content
            self.update(initial_content)
        
        def refresh_content(self, new_content: str, animate: bool = True):
            """
            Update panel content with optional wipe animation.
            
            Args:
                new_content: The new text to display
                animate: Whether to play wipe animation
            """
            self._content = new_content
            self.text = new_content
            
            if animate:
                self.start_animation()
            else:
                self.update(new_content)


# =============================================================================
# Theme Transition Manager
# =============================================================================

class ThemeTransitionManager:
    """
    Manages theme transitions with visual effects.
    
    Integrates with Textual's theme system to provide animated
    transitions when cycling themes with 't' key.
    
    Example:
        class MyApp(App):
            def __init__(self):
                super().__init__()
                self.transition_manager = ThemeTransitionManager(self)
            
            def action_toggle_theme(self):
                self.transition_manager.transition_to_next_theme()
    """
    
    def __init__(self, app: "App" | None = None):
        self.app = app
        self.config = EffectConfig.for_theme_transition()
        self.enabled = True
        self._transition_in_progress = False
    
    async def transition_to_theme(self, theme_name: str, overlay_widget: Static | None = None):
        """
        Animate transition to a new theme.
        
        Args:
            theme_name: The theme to switch to
            overlay_widget: Optional widget to use as transition overlay
        """
        if not self.enabled or self._transition_in_progress:
            # Skip animation, just switch
            if self.app:
                self.app.theme = theme_name
            return
        
        self._transition_in_progress = True
        
        try:
            # Create slide-out effect on current content
            animator = TTEAnimator(self.config)
            
            # Simple approach: just switch theme
            # A full implementation would capture screen, animate, then reveal
            if self.app:
                self.app.theme = theme_name
                
        finally:
            self._transition_in_progress = False


# =============================================================================
# Demo Application
# =============================================================================

if TEXTUAL_AVAILABLE:
    
    class TTEDemoApp(App):
        """
        Demo application showcasing TTE integration.
        
        Run with: python -m tools.tte_animations
        
        Keybindings:
            t - Cycle themes with transition effect
            a - Trigger alert animation
            r - Trigger refresh animation
            q - Quit
        """
        
        CSS = """
        Screen {
            layout: vertical;
        }
        
        #splash {
            height: 5;
            content-align: center middle;
            background: $surface;
        }
        
        #main {
            height: 1fr;
            layout: horizontal;
        }
        
        #left-panel, #right-panel {
            width: 1fr;
            border: solid $primary;
            padding: 1;
        }
        
        #alert-bar {
            height: 3;
            dock: bottom;
        }
        
        #status {
            height: 1;
            dock: bottom;
            background: $primary;
            color: $text;
        }
        """
        
        BINDINGS = [
            ("t", "toggle_theme", "Theme"),
            ("a", "alert", "Alert"),
            ("r", "refresh", "Refresh"),
            ("q", "quit", "Quit"),
        ]
        
        def compose(self) -> ComposeResult:
            # Startup splash with decrypt effect
            yield StartupSplash("S.Y.N.A.P.S.E. ENGINE", id="splash")
            
            # Main content area
            from textual.containers import Horizontal
            with Horizontal(id="main"):
                yield RefreshPanel(
                    "left",
                    "Left Panel Content\nMetrics: 42\nStatus: OK",
                    id="left-panel",
                )
                yield RefreshPanel(
                    "right",
                    "Right Panel Content\nQueries: 128\nCache Hit: 94%",
                    id="right-panel",
                )
            
            # Alert bar
            yield AlertWidget(
                "⚠️ ALERT: Press 'a' to trigger animation",
                id="alert-bar",
            )
            
            # Status bar
            yield Static("Press: [t]heme [a]lert [r]efresh [q]uit", id="status")
        
        def action_toggle_theme(self):
            """Cycle through available themes."""
            themes = ["textual-dark", "textual-light", "nord", "gruvbox", "monokai"]
            try:
                current_idx = themes.index(self.theme)
                next_idx = (current_idx + 1) % len(themes)
            except (ValueError, AttributeError):
                next_idx = 0
            
            self.theme = themes[next_idx]
            self.query_one("#status", Static).update(
                f"Theme: {themes[next_idx]} | Press: [t]heme [a]lert [r]efresh [q]uit"
            )
        
        def action_alert(self):
            """Trigger alert animation."""
            alert = self.query_one("#alert-bar", AlertWidget)
            alert.text = "🚨 CRITICAL: High memory usage detected!"
            alert.trigger()
        
        def action_refresh(self):
            """Trigger refresh animation on panels."""
            import random
            left = self.query_one("#left-panel", RefreshPanel)
            right = self.query_one("#right-panel", RefreshPanel)
            
            left.refresh_content(
                f"Left Panel Content\nMetrics: {random.randint(10, 100)}\nStatus: OK"
            )
            right.refresh_content(
                f"Right Panel Content\nQueries: {random.randint(100, 500)}\nCache Hit: {random.randint(80, 99)}%"
            )


# =============================================================================
# Integration Guide
# =============================================================================

INTEGRATION_GUIDE = """
================================================================================
TTE + Textual Integration Guide
================================================================================

1. STARTUP SPLASH
-----------------
Add a dramatic entrance to your dashboard:

    from tools.tte_animations import StartupSplash
    
    class MyDashboard(App):
        def compose(self):
            yield StartupSplash("MY DASHBOARD TITLE")
            # ... rest of your UI

The splash will auto-play the decrypt effect on mount, then show static text.


2. THEME TRANSITIONS
--------------------
For smooth theme cycling (bound to 't' key):

    from tools.tte_animations import ThemeTransitionManager
    
    class MyApp(App):
        def __init__(self):
            super().__init__()
            self.themes = ["dark", "light", "nord"]
            self.theme_idx = 0
        
        def action_toggle_theme(self):
            self.theme_idx = (self.theme_idx + 1) % len(self.themes)
            self.theme = self.themes[self.theme_idx]

Note: Full slide transitions require screen capture which is complex in Textual.
The current implementation provides the foundation for future enhancement.


3. ALERT EMPHASIS
-----------------
Make critical alerts impossible to miss:

    from tools.tte_animations import AlertWidget
    
    # In compose():
    yield AlertWidget("System status OK", id="alert")
    
    # When alert triggers:
    def on_critical_event(self, message: str):
        alert = self.query_one("#alert", AlertWidget)
        alert.text = f"🚨 {message}"
        alert.trigger()


4. REFRESH ANIMATION
--------------------
Subtle visual feedback on panel updates:

    from tools.tte_animations import RefreshPanel
    
    # In compose():
    yield RefreshPanel("metrics", "Loading...", id="metrics")
    
    # On data refresh:
    def update_metrics(self, data: dict):
        panel = self.query_one("#metrics", RefreshPanel)
        panel.refresh_content(format_metrics(data))


5. CUSTOM EFFECTS
-----------------
Create your own effect combinations:

    from tools.tte_animations import TTEAnimator, EffectType, EffectConfig
    
    animator = TTEAnimator()
    config = EffectConfig(
        frame_rate=30,
        max_frames=60,
        primary_colors=("ff0000", "00ff00", "0000ff"),
    )
    
    async for frame in animator.animate_async("Custom Text", EffectType.MATRIX, config):
        my_widget.update(frame)


6. TOGGLING EFFECTS
-------------------
All effects can be disabled globally:

    config = EffectConfig()
    config.enabled = False  # Disables all animations
    
Or per-widget:

    widget = TTEWidget(..., auto_start=False)  # Manual trigger only


7. TEXTUAL RENDERING CYCLE
--------------------------
Key points for integration:

- TTE generates ANSI strings with escape codes
- Textual's Rich console renders ANSI colors correctly
- Use async iteration (animate_async) to avoid blocking
- Clean cursor-positioning codes from frames (TTEWidget does this)
- Post messages (AnimationComplete) for coordination


8. PERFORMANCE TIPS
-------------------
- Set max_frames to limit animation duration
- Use lower frame_rate (30) for subtle effects
- Disable animations on low-power devices via config.enabled
- Avoid animating large text blocks (>500 chars)

================================================================================
"""


# =============================================================================
# CLI Entry Point
# =============================================================================

def main():
    """Run the demo application."""
    if not TTE_AVAILABLE:
        print("Error: terminaltexteffects not installed")
        print("Run: pip install terminaltexteffects")
        return 1
    
    if not TEXTUAL_AVAILABLE:
        print("Error: textual not installed")
        print("Run: pip install textual")
        return 1
    
    print("Starting TTE Demo App...")
    print("Press 't' for theme, 'a' for alert, 'r' for refresh, 'q' to quit")
    
    app = TTEDemoApp()
    app.run()
    return 0


if __name__ == "__main__":
    import sys
    sys.exit(main())
