"""Tests for backend.track_service."""

from pathlib import Path

from PIL import Image

import backend.track_service as track_service


def _make_torcs_tree(tmp_path):
    root = tmp_path / "torcs"
    (root / "tracks" / "road" / "aalborg").mkdir(parents=True, exist_ok=True)
    (root / "tracks" / "oval" / "e-track").mkdir(parents=True, exist_ok=True)
    return root


def test_list_track_categories_returns_sorted_names(tmp_path):
    root = _make_torcs_tree(tmp_path)

    categories = track_service.list_track_categories(str(root))

    assert categories == ["oval", "road"]


def test_list_tracks_in_category_returns_track_folders(tmp_path):
    root = _make_torcs_tree(tmp_path)

    tracks = track_service.list_tracks_in_category(str(root), "road")

    assert tracks == ["aalborg"]


def test_list_textures_in_track_finds_images_and_paths(tmp_path):
    root = _make_torcs_tree(tmp_path)
    track_dir = root / "tracks" / "road" / "aalborg"
    image_path = track_dir / "advert.png"
    image_path.parent.mkdir(parents=True, exist_ok=True)
    Image.new("RGBA", (64, 32), "red").save(image_path)

    textures = track_service.list_textures_in_track(str(root), "road", "aalborg")

    assert len(textures) == 1
    tex = textures[0]
    assert tex["filename"] == "advert.png"
    assert tex["relative_path"] == "tracks/road/aalborg/advert.png"
    assert tex["full_path"] == str(image_path)
    assert tex["is_accessible"] is True


def test_read_texture_properties_handles_found_and_missing(tmp_path):
    img_path = tmp_path / "icon.png"
    Image.new("RGBA", (50, 20), "blue").save(img_path)

    props = track_service.read_texture_properties(str(img_path))
    missing = track_service.read_texture_properties(str(tmp_path / "missing.png"))

    assert props["width"] == 50
    assert props["height"] == 20
    assert props["format"] == "png"
    assert props["has_alpha"] is True
    assert props["mode"] == "RGBA"
    assert props["error"] is None
    assert missing["error"] == "File not found"


def test_validate_image_compatibility_detects_mismatches(tmp_path):
    source = tmp_path / "source.png"
    target = tmp_path / "target.jpg"
    Image.new("RGB", (100, 50), "white").save(source)
    Image.new("RGB", (50, 50), "black").save(target)

    result = track_service.validate_image_compatibility(str(source), str(target))

    assert result["compatible"] is False
    issue_types = [name for name, _msg in result["issues"]]
    assert "size_mismatch" in issue_types
    assert "format_mismatch" in issue_types


def test_auto_convert_image_matches_target_size_and_mode(tmp_path):
    source = tmp_path / "source.jpg"
    target = tmp_path / "target.png"
    output = tmp_path / "out" / "converted.png"

    Image.new("RGB", (200, 100), "green").save(source)
    Image.new("RGBA", (80, 40), "red").save(target)

    result = track_service.auto_convert_image(str(source), str(target), str(output))

    assert result["success"] is True
    assert Path(result["output_path"]).exists()

    converted_props = track_service.read_texture_properties(str(output))
    assert converted_props["width"] == 80
    assert converted_props["height"] == 40
    assert converted_props["mode"] == "RGBA"
