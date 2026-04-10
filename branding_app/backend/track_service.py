"""Track utilities — discover tracks, read texture properties."""

import os
from PIL import Image


def list_track_categories(torcs_root):
    """Return list of track category folders (road, dirt, oval, ...)."""
    tracks_dir = os.path.join(torcs_root, "tracks")
    if not os.path.isdir(tracks_dir):
        return []

    categories = []
    for item in sorted(os.listdir(tracks_dir)):
        path = os.path.join(tracks_dir, item)
        if os.path.isdir(path) and not item.startswith("."):
            categories.append(item)
    return categories


def list_tracks_in_category(torcs_root, category):
    """Return list of track folders in a category."""
    cat_dir = os.path.join(torcs_root, "tracks", category)
    if not os.path.isdir(cat_dir):
        return []

    tracks = []
    for item in sorted(os.listdir(cat_dir)):
        path = os.path.join(cat_dir, item)
        if os.path.isdir(path) and not item.startswith("."):
            tracks.append(item)
    return tracks


def list_textures_in_track(torcs_root, category, track, keywords=None):
    """List image files in a track folder, optionally filtered by keywords.

    Returns list of dicts with:
    - filename
    - relative_path (relative to torcs_root)
    - full_path
    - is_accessible (True if readable)
    """
    track_dir = os.path.join(torcs_root, "tracks", category, track)
    if not os.path.isdir(track_dir):
        return []

    textures = []
    allowed_ext = {".png", ".jpg", ".jpeg", ".bmp", ".tga"}

    for root, dirs, files in os.walk(track_dir):
        dirs[:] = [d for d in dirs if not d.startswith(".")]  # Skip hidden dirs

        for f in sorted(files):
            if os.path.splitext(f)[1].lower() not in allowed_ext:
                continue

            if keywords:
                if not any(kw.lower() in f.lower() for kw in keywords):
                    continue

            full_path = os.path.join(root, f)
            rel_to_torcs = os.path.relpath(full_path, torcs_root)

            textures.append(
                {
                    "filename": f,
                    "relative_path": rel_to_torcs.replace("\\", "/"),
                    "full_path": full_path,
                    "is_accessible": os.access(full_path, os.R_OK),
                }
            )

    return textures


def read_texture_properties(image_path):
    """Read width, height, format, and alpha properties from an image.

    Returns dict with:
    - width, height
    - format (png, jpg, etc.)
    - has_alpha (boolean)
    - mode (RGB, RGBA, etc.)
    - error (if any)
    """
    try:
        if not os.path.exists(image_path):
            return {"error": "File not found"}

        with Image.open(image_path) as img:
            ext = os.path.splitext(image_path)[1].lower().lstrip(".")

            return {
                "width": img.width,
                "height": img.height,
                "format": ext or "unknown",
                "has_alpha": img.mode in ("RGBA", "PA", "LA"),
                "mode": img.mode,
                "error": None,
            }
    except Exception as e:
        return {"error": str(e)}


def validate_image_compatibility(source_path, target_path):
    """Check if source image can be applied to target.

    Returns dict with:
    - compatible: bool
    - source_props: dict from read_texture_properties(source_path)
    - target_props: dict from read_texture_properties(target_path)
    - issues: list of (issue_type, message) tuples
    """
    source_props = read_texture_properties(source_path)
    target_props = read_texture_properties(target_path)

    issues = []

    if source_props.get("error"):
        issues.append(("error", f"Source error: {source_props['error']}"))
    if target_props.get("error"):
        issues.append(("error", f"Target error: {target_props['error']}"))

    if not issues:  # Only check properties if files are readable
        if source_props["width"] != target_props["width"]:
            issues.append(
                (
                    "size_mismatch",
                    f"Width: {source_props['width']} vs {target_props['width']}",
                )
            )

        if source_props["height"] != target_props["height"]:
            issues.append(
                (
                    "size_mismatch",
                    f"Height: {source_props['height']} vs {target_props['height']}",
                )
            )

        if source_props["format"] != target_props["format"]:
            issues.append(
                (
                    "format_mismatch",
                    f"Format: {source_props['format']} vs {target_props['format']}",
                )
            )

        if source_props["has_alpha"] != target_props["has_alpha"]:
            alpha_issue = "source has" if source_props["has_alpha"] else "source lacks"
            target_alpha = "has" if target_props["has_alpha"] else "lacks"
            issues.append(
                (
                    "alpha_mismatch",
                    f"Alpha channel: {alpha_issue} alpha, target {target_alpha} alpha",
                )
            )

    return {
        "compatible": len(issues) == 0,
        "source_props": source_props,
        "target_props": target_props,
        "issues": issues,
    }


def auto_convert_image(source_path, target_path, output_path):
    """Convert source image to match target properties (size, format, alpha).

    Returns dict with:
    - success: bool
    - output_path: path to converted image
    - error: error message if failed
    """
    try:
        source_img = Image.open(source_path)
        target_props = read_texture_properties(target_path)

        if target_props.get("error"):
            return {
                "success": False,
                "error": f"Cannot read target: {target_props['error']}",
            }

        # Resize to target dimensions
        if source_img.size != (target_props["width"], target_props["height"]):
            source_img = source_img.resize(
                (target_props["width"], target_props["height"]),
                Image.Resampling.LANCZOS,
            )

        # Convert mode (RGB/RGBA) to match target
        target_mode = target_props["mode"]
        if source_img.mode != target_mode:
            if target_mode == "RGBA" and source_img.mode == "RGB":
                source_img = source_img.convert("RGBA")
            elif target_mode == "RGB" and source_img.mode == "RGBA":
                # Remove alpha
                source_img = source_img.convert("RGB")
            elif target_mode in ("RGB", "RGBA"):
                source_img = source_img.convert(target_mode)

        # Save in target format
        target_fmt = target_props["format"].upper()
        if target_fmt == "JPG":
            target_fmt = "JPEG"

        os.makedirs(os.path.dirname(output_path), exist_ok=True)
        source_img.save(output_path, format=target_fmt)

        return {
            "success": True,
            "output_path": output_path,
        }

    except Exception as e:
        return {"success": False, "error": str(e)}
