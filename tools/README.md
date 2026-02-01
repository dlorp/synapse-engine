# Tools - S.Y.N.A.P.S.E. ENGINE

Utility modules and experimental features for the dashboard.

## TTE Animations (`tte_animations.py`)

Terminal Text Effects integration for Textual dashboard. Provides animated visual effects for:

- **Startup splash** — Matrix/decrypt effect for dashboard title on launch
- **Theme transitions** — Slide/fade effect when cycling themes with 't'
- **Alert emphasis** — Shake/pulse effect for critical alerts
- **Refresh animation** — Subtle wipe effect on panel updates

### Installation

```bash
pip install -r tools/requirements.txt
```

Or install individually:
```bash
pip install terminaltexteffects textual
```

### Quick Start

```python
from tools.tte_animations import StartupSplash, AlertWidget, RefreshPanel

class MyDashboard(App):
    def compose(self):
        # Dramatic startup with decrypt effect
        yield StartupSplash("S.Y.N.A.P.S.E. ENGINE")
        
        # Panels with refresh animations
        yield RefreshPanel("metrics", "Loading...")
        
        # Alert bar with shake effect
        yield AlertWidget("System OK")
```

### Demo

Run the interactive demo:

```bash
python -m tools.tte_animations
```

**Keybindings:**
- `t` — Cycle themes with transition
- `a` — Trigger alert animation
- `r` — Trigger refresh animation
- `q` — Quit

### Available Effects

| Effect Type | Use Case | Description |
|-------------|----------|-------------|
| `DECRYPT` | Startup | Movie-style decryption reveal |
| `MATRIX` | Startup | Matrix digital rain |
| `SLIDE` | Transitions | Slide in from edge |
| `WIPE` | Refresh | Wipe across content |
| `UNSTABLE` | Alerts | Shake/jitter effect |
| `SCATTERED` | Alerts | Characters scatter and reform |
| `EXPAND` | Transitions | Expand from center |
| `COLORSHIFT` | Ambient | Gradient color cycling |

### Configuration

```python
from tools.tte_animations import EffectConfig

# Use presets
config = EffectConfig.for_startup_splash()
config = EffectConfig.for_alert()
config = EffectConfig.for_refresh()

# Or customize
config = EffectConfig(
    frame_rate=30,
    max_frames=60,
    primary_colors=("3B60E4", "50D8D7"),  # dlorp branding
    enabled=True,  # Set False to disable all animations
)
```

### Textual Integration Notes

1. **Async rendering** — Use `animate_async()` to avoid blocking the event loop
2. **Frame cleaning** — TTEWidget strips cursor positioning codes automatically
3. **Messages** — `AnimationComplete` and `AnimationStarted` messages for coordination
4. **Toggling** — Set `config.enabled = False` for low-power mode

### Architecture

```
TTEAnimator
    ├── create_effect()     → Configure TTE effect
    ├── animate_sync()      → Generator for frames
    └── animate_async()     → AsyncGenerator with timing

TTEWidget (Textual Static)
    ├── start_animation()   → Begin async playback
    ├── stop_animation()    → Cancel playback
    └── _clean_frame()      → Strip cursor codes

Specialized Widgets
    ├── StartupSplash       → Auto-play decrypt on mount
    ├── AlertWidget         → Manual trigger for alerts
    └── RefreshPanel        → Animate on content change
```

### Performance Tips

- Set `max_frames` to limit animation duration
- Use `frame_rate=30` for subtle effects (vs 60 for dramatic)
- Avoid animating large text blocks (>500 chars)
- Disable animations on low-power devices via `config.enabled`

### Credits

- [TerminalTextEffects](https://github.com/ChrisBuilds/terminaltexteffects) by ChrisBuilds
- [Textual](https://github.com/Textualize/textual) by Textualize
