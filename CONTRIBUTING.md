# Contributing to DayZ Geometry Maker

Thanks for your interest in contributing! This guide walks you through setting up a proper development environment so you can write, test, and submit changes cleanly.

---

## Table of Contents

- [Branch Structure](#branch-structure)
- [Development Environment Setup](#development-environment-setup)
- [Making Changes](#making-changes)
- [Submitting a Pull Request](#submitting-a-pull-request)
- [Code Style](#code-style)
- [Versioning](#versioning)

---

## Branch Structure

| Branch | Purpose |
|--------|---------|
| `main` | Stable releases only. Protected — no direct pushes. |
| `dev`  | Active development. All PRs target this branch. |
| `feature/<name>` | Your feature or fix branch, forked off `dev`. |

**Never open a PR directly into `main`.** All contributions go through `dev` first. When `dev` is stable and ready for a release, the maintainer merges it into `main` and tags a release.

---

## Development Environment Setup

> **Important:** Do not develop inside your Blender extensions folder.  
> Instead, clone the repo to a dedicated dev folder and use a **symlink** to let Blender load it live. This way every file save is instantly reflected in Blender — no reinstalling or copying needed.

### 1. Fork & Clone

1. Fork this repository on GitHub
2. Clone your fork somewhere convenient — **not** inside Blender's folders:

```
git clone https://github.com/YOUR_USERNAME/DayZ-Geometry-Maker.git
cd DayZ-Geometry-Maker
```

3. Add the upstream remote so you can pull in future changes:

```
git remote add upstream https://github.com/Phlanka/DayZ-Geometry-Maker.git
```

4. Check out the `dev` branch:

```
git checkout dev
```

### 2. Create the Blender Symlink

The symlink makes Blender treat your cloned repo folder as an installed extension. Pick your platform below, or run the provided script.

#### Windows (run as Administrator)

```bat
scripts\install_dev.bat
```

Or manually (in an elevated Command Prompt):

```bat
mklink /D "%APPDATA%\Blender Foundation\Blender\5.1\extensions\user_default\dayz_geometry_maker" "C:\path\to\your\clone\dayz_geometry_maker"
```

> Replace the path after `dayz_geometry_maker` with the actual path to the `dayz_geometry_maker` subfolder inside your clone.

#### macOS

```bash
bash scripts/install_dev.sh
```

Or manually:

```bash
ln -s "/path/to/your/clone/dayz_geometry_maker" \
  "$HOME/Library/Application Support/Blender/5.1/extensions/user_default/dayz_geometry_maker"
```

#### Linux

```bash
bash scripts/install_dev.sh
```

Or manually:

```bash
ln -s "/path/to/your/clone/dayz_geometry_maker" \
  "$HOME/.config/blender/5.1/extensions/user_default/dayz_geometry_maker"
```

### 3. Enable in Blender

1. Open Blender
2. Go to **Edit → Preferences → Extensions**
3. Find **DayZ Geometry Maker** and make sure it is enabled
4. The DayZ tab will appear in the **3D Viewport N-Panel**

From here, any changes you save to files in your cloned repo are live in Blender — just reload scripts (**Info menu → Reload Scripts**, or `F3` → search "Reload Scripts") or restart Blender for changes that affect registration.

### 4. Keeping Up to Date

Pull upstream changes into your fork regularly:

```
git fetch upstream
git checkout dev
git merge upstream/dev
```

---

## Making Changes

### Create a feature branch

Always branch off `dev`:

```
git checkout dev
git pull upstream dev
git checkout -b feature/my-feature-name
```

Use descriptive branch names:
- `feature/door-rotation-improvements`
- `fix/memory-lod-crash-on-empty-scene`
- `refactor/exporter-cleanup`

### Test your changes

Before submitting, verify:

- [ ] The addon registers without errors in Blender's system console
- [ ] Your change works correctly end-to-end in Blender
- [ ] Existing features you didn't touch still work (basic smoke test)
- [ ] No leftover debug `print()` statements

### Commit style

Write short, present-tense commit messages that describe *what* the change does:

```
Fix shadow volume scaling on low-poly meshes
Add per-point Move button to Memory LOD panel
Refactor exporter to deduplicate vertex normals
```

Keep commits focused — one logical change per commit where possible.

---

## Submitting a Pull Request

1. Push your branch to your fork:

```
git push origin feature/my-feature-name
```

2. Open a Pull Request on GitHub from your branch **into `dev`** (not `main`)
3. Fill in the PR template — describe what changed and how to test it
4. Wait for review — the maintainer may request changes before merging

### PR checklist

- [ ] Targets the `dev` branch
- [ ] Tested in Blender with no console errors
- [ ] CHANGELOG.md updated under `[Unreleased]` if the change is user-facing
- [ ] No unrelated changes included

---

## Code Style

This project follows standard Python conventions with a few specifics:

- **PEP 8** — 4-space indentation, sensible line lengths (~100 chars)
- **Blender operator naming** — follow the existing `DGM_OT_`, `DGM_PT_`, `DGM_MT_` prefix conventions
- **No external dependencies** — the core addon must run with only Blender's bundled Python. Do not add third-party packages.
- **Docstrings on classes** — add a short docstring to any new `bpy.types` class explaining its purpose
- **Keep modules focused** — `geometry.py` for mesh ops, `exporter.py` for P3D writing, `operators.py` for UI/operators, etc. Don't mix concerns.

---

## Versioning

Version numbers follow [Semantic Versioning](https://semver.org/): `MAJOR.MINOR.PATCH`

- `PATCH` — bug fixes, no new features
- `MINOR` — new features, backwards compatible
- `MAJOR` — breaking changes or major rewrites

Versions live in two places and must match on release:
- `__init__.py` → `bl_info["version"]` tuple
- `blender_manifest.toml` → `version` string

Contributors do **not** need to bump versions. The maintainer handles version bumps and tagging as part of the release process.

---

## Questions?

Open an issue on GitHub or reach out via the repository discussions. Thanks for contributing!
