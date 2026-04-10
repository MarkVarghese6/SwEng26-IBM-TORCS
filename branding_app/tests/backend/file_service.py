"""Tests for backend.file_service."""

from pathlib import Path

from PIL import Image

import backend.file_service as file_service


def _set_service_dirs(tmp_path, monkeypatch):
    uploads_dir = tmp_path / "uploads"
    backups_dir = tmp_path / "backups"
    monkeypatch.setattr(file_service, "UPLOADS_DIR", str(uploads_dir))
    monkeypatch.setattr(file_service, "BACKUPS_DIR", str(backups_dir))
    return uploads_dir, backups_dir


def test_allowed_file_accepts_supported_extensions():
    assert file_service.allowed_file("image.png")
    assert file_service.allowed_file("image.JPG")
    assert not file_service.allowed_file("readme.txt")
    assert not file_service.allowed_file("no_extension")


def test_list_uploaded_files_ignores_gitkeep(tmp_path, monkeypatch):
    uploads_dir, _ = _set_service_dirs(tmp_path, monkeypatch)
    uploads_dir.mkdir(parents=True, exist_ok=True)
    (uploads_dir / ".gitkeep").write_text("")
    (uploads_dir / "car.png").write_text("x")

    assert file_service.list_uploaded_files() == ["car.png"]


def test_save_upload_and_delete_upload(tmp_path, monkeypatch):
    uploads_dir, _ = _set_service_dirs(tmp_path, monkeypatch)
    src = tmp_path / "source.png"
    src.write_text("payload")

    saved_path = Path(file_service.save_upload(str(src)))
    assert saved_path == uploads_dir / "source.png"
    assert saved_path.exists()

    assert file_service.delete_upload("source.png") is True
    assert not saved_path.exists()
    assert file_service.delete_upload("source.png") is False


def test_backup_file_copies_and_records_relative_path(tmp_path, monkeypatch):
    _, backups_dir = _set_service_dirs(tmp_path, monkeypatch)
    source_root = tmp_path / "torcs"
    src = source_root / "data" / "img" / "splash.png"
    src.parent.mkdir(parents=True, exist_ok=True)
    src.write_text("img")
    monkeypatch.setattr(file_service, "get_active_profile_name", lambda: "baseline")

    result = file_service.backup_file(
        str(src), str(source_root), snapshot_id="20260327_000000"
    )

    assert result["snapshot_id"] == "20260327_000000"
    assert result["relative_path"] == str(Path("data") / "img" / "splash.png")
    assert result["profile_name"] == "baseline"
    assert Path(result["backup_path"]).exists()
    assert Path(result["backup_path"]).read_text() == "img"
    assert Path(result["backup_path"]).is_relative_to(backups_dir / "baseline")


def test_backup_file_rejects_source_outside_root(tmp_path, monkeypatch):
    _set_service_dirs(tmp_path, monkeypatch)
    source_root = tmp_path / "torcs"
    src = tmp_path / "outside.png"
    src.write_text("x")

    try:
        file_service.backup_file(str(src), str(source_root), snapshot_id="snap")
        assert False, "Expected ValueError for source outside root"
    except ValueError as exc:
        assert "outside source_root" in str(exc)


def test_copy_to_torcs_copies_file(tmp_path):
    upload = tmp_path / "upload.png"
    upload.write_text("abc")
    torcs_root = tmp_path / "torcs"

    dest = Path(
        file_service.copy_to_torcs(str(upload), str(torcs_root), "cars/car.png")
    )
    assert dest.exists()
    assert dest.read_text() == "abc"


def test_restore_backup_restores_file(tmp_path, monkeypatch):
    _, backups_dir = _set_service_dirs(tmp_path, monkeypatch)
    snapshot_id = "snap"
    relative_path = "data/img/loading.png"
    monkeypatch.setattr(file_service, "get_active_profile_name", lambda: "baseline")
    src = backups_dir / "baseline" / snapshot_id / relative_path
    src.parent.mkdir(parents=True, exist_ok=True)
    src.write_text("restored")

    torcs_root = tmp_path / "torcs"
    dest = Path(
        file_service.restore_backup(snapshot_id, str(torcs_root), relative_path)
    )
    assert dest.exists()
    assert dest.read_text() == "restored"


def test_get_profile_backup_root_uses_safe_profile_name(tmp_path, monkeypatch):
    _, backups_dir = _set_service_dirs(tmp_path, monkeypatch)
    monkeypatch.setattr(file_service, "get_active_profile_name", lambda: "Team A/One")

    assert Path(file_service.get_profile_backup_root()) == backups_dir / "Team_A_One"


def test_validate_image_dimensions_cases(tmp_path):
    ok_img = tmp_path / "ok.png"
    bad_img = tmp_path / "bad.png"
    Image.new("RGB", (128, 64), "red").save(ok_img)
    Image.new("RGB", (64, 64), "blue").save(bad_img)

    assert file_service.validate_image_dimensions(None, 128, 64) == (
        False,
        "No image selected",
    )
    assert file_service.validate_image_dimensions(
        str(tmp_path / "missing.png"), 1, 1
    ) == (
        False,
        "Image file not found",
    )
    assert file_service.validate_image_dimensions(str(ok_img), 128, 64) == (True, "")
    assert file_service.validate_image_dimensions(str(bad_img), 128, 64) == (
        False,
        "Expected 128x64, got 64x64",
    )
    assert file_service.validate_image_dimensions(str(ok_img), None, None) == (True, "")
