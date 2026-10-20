"""Annunci vocali tramite il lettore di schermo in uso (NVDA, JAWS, VoiceOver...).

Se nessun lettore di schermo è attivo, o le librerie non sono disponibili, non fa nulla.
"""

from __future__ import annotations

import sys

_outputs = None


def _windows_outputs():
    global _outputs
    if _outputs is None:
        _outputs = []
        try:
            from accessible_output2.outputs.auto import Auto  # type: ignore

            # Solo i veri lettori di schermo: la sintesi SAPI parlerebbe anche a chi non la usa.
            _outputs = [o for o in Auto().outputs if not type(o).__name__.lower().startswith("sapi")]
        except Exception:
            _outputs = []
    return _outputs


def speak(text: str):
    try:
        if sys.platform == "win32":
            for output in _windows_outputs():
                try:
                    if output.is_active():
                        output.speak(text, interrupt=False)
                        return
                except Exception:
                    continue
        elif sys.platform == "darwin":
            import AppKit  # type: ignore  (pyobjc)

            app = AppKit.NSApplication.sharedApplication()
            window = app.keyWindow() or app.mainWindow()
            if window is None:
                return
            AppKit.NSAccessibilityPostNotificationWithUserInfo(
                window,
                AppKit.NSAccessibilityAnnouncementRequestedNotification,
                {
                    AppKit.NSAccessibilityAnnouncementKey: text,
                    AppKit.NSAccessibilityPriorityKey: AppKit.NSAccessibilityPriorityHigh,
                },
            )
    except Exception:
        pass
