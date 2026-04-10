# File helpers — uploads, backups, restore, validation

import os
import shutil
from PIL import Image
from datetime import datetime

from backend.config_service import get_active_profile_name

ALLOWED_EXTENSIONS = {"png", "jpg", "jpeg", "bmp"}

_BASE = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
UPLOADS_DIR = os.path.join(_BASE, "uploads")
BACKUPS_DIR = os.path.join(_BASE, "backups")


def _profile_backup_root(profile_name=None):
    active_name = (profile_name or get_active_profile_name() or "default").strip()
    safe_name = "".join(
        ch if ch.isalnum() or ch in ("-", "_") else "_" for ch in active_name
    ).strip("_")
    if not safe_name:
        safe_name = "default"
    return os.path.join(BACKUPS_DIR, safe_name)


def get_profile_backup_root(profile_name=None):
    return _profile_backup_root(profile_name)


def allowed_file(filename):
    return "." in filename and filename.rsplit(".", 1)[1].lower() in ALLOWED_EXTENSIONS


def list_uploaded_files():
    os.makedirs(UPLOADS_DIR, exist_ok=True)
    return [f for f in os.listdir(UPLOADS_DIR) if f != ".gitkeep"]


def save_upload(src_path):
    # Copy file into uploads/, return dest path
    os.makedirs(UPLOADS_DIR, exist_ok=True)
    basename = os.path.basename(src_path)
    dest = os.path.join(UPLOADS_DIR, basename)
    shutil.copy2(src_path, dest)
    return dest


def delete_upload(filename):
    # Deletes chosen file
    path = os.path.join(UPLOADS_DIR, filename)
    if os.path.exists(path):
        os.remove(path)
        return True
    return False


def backup_file(src, source_root, snapshot_id=None, profile_name=None):
    backup_root = _profile_backup_root(profile_name)
    os.makedirs(backup_root, exist_ok=True)
    if snapshot_id is None:
        snapshot_id = datetime.now().strftime("%Y%m%d_%H%M%S")

    rel = os.path.relpath(src, source_root)
    if rel.startswith(".."):
        raise ValueError("src is outside source_root")

    dest = os.path.join(backup_root, snapshot_id, rel)
    os.makedirs(os.path.dirname(dest), exist_ok=True)
    shutil.copy2(src, dest)
    return {
        "snapshot_id": snapshot_id,
        "relative_path": rel,
        "backup_path": dest,
        "profile_name": profile_name or get_active_profile_name() or "",
    }


def copy_to_torcs(upload_path, torcs_root, target_rel, profile_name=None):
    dest = os.path.join(torcs_root, target_rel)
    os.makedirs(os.path.dirname(dest), exist_ok=True)
    shutil.copy2(upload_path, dest)
    return dest


def restore_backup(snapshot_id, torcs_root, relative_path, profile_name=None):
    src = os.path.join(_profile_backup_root(profile_name), snapshot_id, relative_path)
    dest = os.path.join(torcs_root, relative_path)
    os.makedirs(os.path.dirname(dest), exist_ok=True)
    shutil.copy2(src, dest)
    return dest


def validate_image_dimensions(filepath, expected_w, expected_h):
    if filepath is None:
        return False, "No image selected"
    if not os.path.exists(filepath):
        return False, "Image file not found"
    try:
        img = Image.open(filepath)
    except Exception:
        return False, "Image file could not be opened"

    if img.width != expected_w and expected_w is not None:
        return (
            False,
            f"Expected {expected_w}x{expected_h}, got {img.width}x{img.height}",
        )
    if img.height != expected_h and expected_h is not None:
        return (
            False,
            f"Expected {expected_w}x{expected_h}, got {img.width}x{img.height}",
        )
    return True, ""
