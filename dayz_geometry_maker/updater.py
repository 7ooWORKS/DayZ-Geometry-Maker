"""
DayZ Geometry Maker - Updater
Handles two separate install modes:

  1. Release install  — checks GitHub Releases API for a tagged release newer
                        than the current version and offers a one-click install.
                        Intended for end users.

  2. Main branch install — downloads the current HEAD of the 'main' branch as a
                           zip directly from GitHub. No version check — always
                           overwrites with whatever is on main right now.
                           Intended for pre-release / testing builds.
"""

import bpy
import urllib.request
import json
import threading
import os
import zipfile
import shutil
import tempfile

# ---------------------------------------------------------------------------
# Constants
# ---------------------------------------------------------------------------

GITHUB_API_LATEST = "https://api.github.com/repos/Phlanka/DayZ-Geometry-Maker/releases/latest"
GITHUB_MAIN_ZIP   = "https://github.com/Phlanka/DayZ-Geometry-Maker/archive/refs/heads/main.zip"
CURRENT_VERSION   = (2, 1, 0)   # keep in sync with bl_info["version"] in __init__.py
ADDON_ID          = "dayz_geometry_maker"
USER_AGENT        = "DayZ-Geometry-Maker-Updater"

# ---------------------------------------------------------------------------
# Release update state  (written from background thread, read on main thread)
# ---------------------------------------------------------------------------

_update_available    = False
_latest_version_str  = ""
_latest_download_url = ""

# ---------------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------------

def _parse_version(tag: str) -> tuple:
    tag = tag.lstrip("vV")
    try:
        return tuple(int(x) for x in tag.split("."))
    except Exception:
        return (0, 0, 0)


def _make_request(url: str) -> urllib.request.Request:
    return urllib.request.Request(url, headers={"User-Agent": USER_AGENT})


def _extract_zip_to_addon(zip_path: str):
    """
    Extract a GitHub source zip into Blender's extensions folder, renaming the
    top-level directory (which GitHub names like 'DayZ-Geometry-Maker-main') to
    the correct ADDON_ID folder name.
    """
    addon_dir  = os.path.dirname(os.path.abspath(__file__))
    parent_dir = os.path.dirname(addon_dir)

    with zipfile.ZipFile(zip_path, 'r') as zf:
        names = zf.namelist()
        top   = names[0].split('/')[0] if names else ""
        zf.extractall(parent_dir)

    extracted = os.path.join(parent_dir, top)
    target    = os.path.join(parent_dir, ADDON_ID)

    if os.path.isdir(extracted) and extracted != target:
        if os.path.isdir(target):
            shutil.rmtree(target)
        shutil.move(extracted, target)

    os.remove(zip_path)


# ---------------------------------------------------------------------------
# Release update check  (background thread + main-thread poll timer)
# ---------------------------------------------------------------------------

def _check_release_thread():
    global _update_available, _latest_version_str, _latest_download_url
    try:
        with urllib.request.urlopen(_make_request(GITHUB_API_LATEST), timeout=8) as resp:
            data = json.loads(resp.read().decode())

        tag    = data.get("tag_name", "")
        remote = _parse_version(tag)
        print("[DGM] Updater: current={} remote={} tag={}".format(CURRENT_VERSION, remote, tag))

        if remote > CURRENT_VERSION:
            _update_available   = True
            _latest_version_str = tag

            # Prefer a .zip release asset, fall back to GitHub's zipball
            for asset in data.get("assets", []):
                if asset.get("name", "").endswith(".zip"):
                    _latest_download_url = asset["browser_download_url"]
                    break
            if not _latest_download_url:
                _latest_download_url = data.get("zipball_url", "")

    except Exception as exc:
        print("[DGM] Updater: release check failed —", exc)


def _poll_for_update():
    """
    Timer callback on the main thread. Polls until the background thread sets
    _update_available, then redraws VIEW_3D so the banner appears.
    Times out after ~30 s (60 × 0.5 s).
    """
    _poll_for_update._count = getattr(_poll_for_update, "_count", 0) + 1

    if _update_available:
        for window in bpy.context.window_manager.windows:
            for area in window.screen.areas:
                if area.type == 'VIEW_3D':
                    area.tag_redraw()
        print("[DGM] Updater: update {} available — panel redrawn.".format(_latest_version_str))
        return None  # stop timer

    if _poll_for_update._count >= 60:
        return None  # timeout — give up

    return 0.5  # check again in 0.5 s


def check_for_update():
    """Kick off a background release-update check. Called on addon register."""
    _poll_for_update._count = 0
    t = threading.Thread(target=_check_release_thread, daemon=True)
    t.start()
    bpy.app.timers.register(_poll_for_update, first_interval=1.0)


# -------------------------------