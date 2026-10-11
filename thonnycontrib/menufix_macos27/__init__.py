# -*- coding: utf-8 -*-
"""
Thonny plug-in: workaround for dialogs freezing when opened from the
macOS menu bar (macOS 27 "Golden Gate").

Problem
-------
On macOS 27 the menu bar invokes Thonny's commands from inside a macOS
callback (MenuBarClientCore -> triggerActionForItemID). If the command opens a
modal dialog (Tools -> Manage packages, Preferences, About ...), Tk enters a
nested event loop (wait_window) while macOS is still waiting for the menu
callback to return -> deadlock, Thonny freezes at 0 % CPU.

Fix
---
Run menu-bar commands 1 ms later, i.e. outside of the menu callback.
Same approach as https://github.com/thonny/thonny/pull/3937

Remove: delete this folder (menufix_macos27).
"""

import sys
import logging

logger = logging.getLogger(__name__)

DELAY_MS = 1
_MARK = "menufix27"
_OWN = set()  # Tcl commands registered by this plug-in


def _deferred(widget, tcl_command):
    def call(*_):
        widget.after(DELAY_MS, lambda: widget.tk.eval(tcl_command))
    return call


def _patch_menu(wb, menu, seen):
    if str(menu) in seen:
        return 0
    seen.add(str(menu))
    count = 0
    last = menu.index("end")
    if last is None:
        return 0
    for i in range(last + 1):
        try:
            kind = menu.type(i)
        except Exception:
            continue
        if kind == "cascade":
            name = str(menu.entrycget(i, "menu"))
            if name:
                try:
                    count += _patch_menu(wb, wb.nametowidget(name), seen)
                except Exception:
                    pass
        elif kind in ("command", "checkbutton", "radiobutton"):
            cmd = str(menu.entrycget(i, "command")).strip()
            if not cmd or cmd in _OWN:
                continue
            new = menu.register(_deferred(menu, cmd))
            _OWN.add(new)
            menu.entryconfigure(i, command=new)
            count += 1
    return count


def _patch_mac_command(wb, name):
    try:
        if not wb.tk.call("info", "commands", name):
            return False
        original = name + "_" + _MARK + "_orig"
        if wb.tk.call("info", "commands", original):
            return False  # already patched
        wb.tk.call("rename", name, original)
        wb.createcommand(name, lambda *_: wb.after(DELAY_MS, lambda: wb.tk.call(original)))
        return True
    except Exception:
        logger.exception("menufix: could not patch %s", name)
        return False


def _apply(event=None):
    from thonny import get_workbench
    wb = get_workbench()
    try:
        menubar = wb.nametowidget(wb["menu"]) if wb["menu"] else None
    except Exception:
        menubar = None
    count = _patch_menu(wb, menubar, set()) if menubar is not None else 0
    prefs = _patch_mac_command(wb, "::tk::mac::ShowPreferences")
    about = _patch_mac_command(wb, "tkAboutDialog")
    logger.info("menufix_macos27: %d menu entries deferred, preferences=%s, about=%s",
                count, prefs, about)


def load_plugin():
    if sys.platform != "darwin":
        return
    from thonny import get_workbench
    get_workbench().bind("WorkbenchReady", _apply, True)
