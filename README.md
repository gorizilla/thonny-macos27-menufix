# Thonny: fix for dialogs freezing from the macOS menu bar (macOS 27)

> **Unofficial workaround – not affiliated with the Thonny project.**
> For [Thonny](https://thonny.org) ([GitHub](https://github.com/thonny/thonny)),
> until an official release contains the fix.

On **macOS 27**, Thonny freezes completely (0 % CPU, only Force Quit helps) when a
dialog is opened by **clicking the macOS menu bar**, e.g.

- *Tools → Manage packages…*
- *Thonny → Settings…* / *About Thonny*

Dialogs opened via keyboard shortcut (e.g. ⌘O) work fine.

This repository contains a tiny **Thonny plug-in** that works around the problem
without modifying the Thonny app itself (no `sudo`, settings are kept).

## Cause

The macOS 27 menu bar calls Thonny's command from inside a system callback
(`MenuBarClientCore` → `triggerActionForItemID`). If that command opens a modal
dialog, Tk starts a nested event loop and waits for the dialog – while macOS still
waits for the menu callback to finish. Both wait for each other: **deadlock**.

The plug-in runs every menu-bar command **1 ms later** (`after(1, …)`), i.e.
outside of the menu callback. This is the same approach as the proposed upstream
fix [thonny/thonny#3937](https://github.com/thonny/thonny/pull/3937)
by [@K-cermak](https://github.com/K-cermak) – credit for the approach goes there
(related issues: [#3934](https://github.com/thonny/thonny/issues/3934),
[#3938](https://github.com/thonny/thonny/issues/3938)).

## Tested with

- macOS 27.0.1 (26A434), Apple Silicon
- Thonny 5.0.0 (arm64 bundle), Python 3.14.3, Tk 8.6.17

## Install

1. Download this repository (*Code → Download ZIP*) and unzip it.
2. Copy the folder `thonnycontrib/menufix_macos27` to

   ```
   ~/Library/Thonny/plugins/lib/python/site-packages/thonnycontrib/menufix_macos27
   ```

   Create the folders if they don't exist. In Finder, press ⇧⌘G and paste
   `~/Library/Thonny` to get there quickly.

   Or in Terminal, from inside the unzipped folder:

   ```bash
   mkdir -p ~/Library/Thonny/plugins/lib/python/site-packages/thonnycontrib
   cp -R thonnycontrib/menufix_macos27 ~/Library/Thonny/plugins/lib/python/site-packages/thonnycontrib/
   ```

3. Restart Thonny.

**Check:** `~/Library/Thonny/frontend.log` should contain a line like

```
menufix_macos27: 77 menu entries deferred, preferences=True, about=True
```

## Uninstall

Delete the folder `menufix_macos27` shown above and restart Thonny.
Once an official Thonny release contains the fix (the upstream PR is targeted at
5.0.1), the plug-in is no longer needed – it does no harm if left installed.

## What it does / doesn't do

- Only active on macOS; only affects clicks in the menu bar. Keyboard shortcuts are unchanged.
- Patches all entries of the menu bar once at start-up, plus *Settings…* and *About Thonny*.
- Sub-menus that Thonny rebuilds on the fly (e.g. recent files) are not patched;
  they don't open modal dialogs.

## License

Open source under the MIT License – see [LICENSE](LICENSE).
Contributions and bug reports are welcome.
