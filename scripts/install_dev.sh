#!/usr/bin/env bash
# DayZ Geometry Maker - macOS / Linux Developer Setup
# Creates a symlink from Blender's extensions folder to this repo.
#
# Usage:
#   bash scripts/install_dev.sh
#
# Run from anywhere inside the cloned repository.

set -euo pipefail

echo "============================================================"
echo " DayZ Geometry Maker - Developer Symlink Setup (Mac/Linux)"
echo "============================================================"
echo

# --- Locate the repo's addon subfolder ---
# This script lives in <repo_root>/scripts/
SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
REPO_ROOT="$(cd "$SCRIPT_DIR/.." && pwd)"
ADDON_SRC="$REPO_ROOT/dayz_geometry_maker"

if [[ ! -f "$ADDON_SRC/__init__.py" ]]; then
    echo "ERROR: Could not find the addon folder at:"
    echo "  $ADDON_SRC"
    echo "Make sure you are running this script from inside the cloned repository."
    exit 1
fi

echo "Addon source folder:"
echo "  $ADDON_SRC"
echo

# --- Detect platform and Blender extensions path ---
OS="$(uname -s)"
BLENDER_EXT=""
BLENDER_VER=""

find_blender_ext() {
    local base="$1"
    for ver in 5.1 5.0 4.4 4.3 4.2; do
        local candidate="$base/$ver/extensions/user_default"
        if [[ -d "$candidate" ]]; then
            BLENDER_EXT="$candidate"
            BLENDER_VER="$ver"
            return 0
        fi
    done
    return 1
}

case "$OS" in
    Darwin)
        find_blender_ext "$HOME/Library/Application Support/Blender" || true
        ;;
    Linux)
        find_blender_ext "$HOME/.config/blender" || true
        ;;
    *)
        echo "WARNING: Unrecognised OS '$OS'. Will prompt for path."
        ;;
esac

if [[ -z "$BLENDER_EXT" ]]; then
    echo "Could not auto-detect your Blender extensions folder."
    echo "Please enter the full path to your Blender extensions/user_default folder."
    echo
    if [[ "$OS" == "Darwin" ]]; then
        echo "  Example: $HOME/Library/Application Support/Blender/5.1/extensions/user_default"
    else
        echo "  Example: $HOME/.config/blender/5.1/extensions/user_default"
    fi
    echo
    read -rp "Path: " BLENDER_EXT
    if [[ ! -d "$BLENDER_EXT" ]]; then
        echo "ERROR: Path does not exist. Aborting."
        exit 1
    fi
fi

echo "Detected Blender $BLENDER_VER extensions folder:"
echo "  $BLENDER_EXT"
echo

LINK_TARGET="$BLENDER_EXT/dayz_geometry_maker"

# --- Check if something already exists at the link target ---
if [[ -e "$LINK_TARGET" || -L "$LINK_TARGET" ]]; then
    echo "WARNING: Something already exists at:"
    echo "  $LINK_TARGET"
    echo
    read -rp "Remove it and create a fresh symlink? [y/N]: " OVERWRITE
    if [[ "${OVERWRITE,,}" == "y" ]]; then
        rm -rf "$LINK_TARGET"
    else
        echo "Aborted. No changes made."
        exit 0
    fi
fi

# --- Create the symlink ---
ln -s "$ADDON_SRC" "$LINK_TARGET"

echo
echo "SUCCESS! Symlink created:"
echo "  $LINK_TARGET"
echo "  -> $ADDON_SRC"
echo
echo "Next steps:"
echo "  1. Open Blender"
echo "  2. Go to Edit > Preferences > Extensions"
echo "  3. Enable 'DayZ Geometry Maker' if not already enabled"
echo "  4. The DayZ tab will appear in the 3D Viewport N-Panel"
echo
echo "Any file you save in your repo is instantly live in Blender."
echo "Use F3 > 'Reload Scripts' to pick up changes without restarting."
echo
