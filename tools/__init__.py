"""
Tools package for S.Y.N.A.P.S.E. ENGINE.

Contains utility modules and experimental features.
"""

from .tte_animations import (
    TTEAnimator,
    EffectType,
    EffectConfig,
    TTE_AVAILABLE,
    TEXTUAL_AVAILABLE,
)

# Only export widgets if Textual is available
if TEXTUAL_AVAILABLE:
    from .tte_animations import (
        TTEWidget,
        StartupSplash,
        AlertWidget,
        RefreshPanel,
        ThemeTransitionManager,
    )

__all__ = [
    "TTEAnimator",
    "EffectType",
    "EffectConfig",
    "TTE_AVAILABLE",
    "TEXTUAL_AVAILABLE",
]

if TEXTUAL_AVAILABLE:
    __all__.extend(
        [
            "TTEWidget",
            "StartupSplash",
            "AlertWidget",
            "RefreshPanel",
            "ThemeTransitionManager",
        ]
    )
