"""Tests for backend.branding_service."""

import backend.branding_service as branding_service


def test_iter_profile_assets_discovers_nested_assets():
    profile = {
        "banners": {
            "splash": {
                "target_path": "data/img/splash.png",
                "file": "splash.png",
                "width": 1024,
                "height": 512,
            }
        },
        "livery": {
            "texture_file": "car.png",
            "target_path": "cars/car1/car.png",
        },
    }

    assets = branding_service.iter_profile_assets(profile)

    assert assets == [
        {
            "label": "banners.splash",
            "target_path": "data/img/splash.png",
            "source_file": "splash.png",
            "width": 1024,
            "height": 512,
        },
        {
            "label": "livery",
            "target_path": "cars/car1/car.png",
            "source_file": "car.png",
            "width": None,
            "height": None,
        },
    ]


def test_resolve_source_file_prefers_explicit_path(tmp_path):
    uploads_dir = tmp_path / "uploads"
    uploads_dir.mkdir(parents=True, exist_ok=True)

    explicit = tmp_path / "explicit.png"
    explicit.write_text("x")

    asset = {
        "target_path": "data/img/splash.png",
        "source_file": str(explicit),
    }

    resolved = branding_service.resolve_source_file(asset, str(uploads_dir))
    assert resolved == str(explicit)


def test_resolve_source_file_falls_back_to_upload_basename(tmp_path):
    uploads_dir = tmp_path / "uploads"
    uploads_dir.mkdir(parents=True, exist_ok=True)
    fallback = uploads_dir / "splash.png"
    fallback.write_text("x")

    asset = {
        "target_path": "data/img/splash.png",
        "source_file": "not-an-existing-file.png",
    }

    resolved = branding_service.resolve_source_file(asset, str(uploads_dir))
    assert resolved == str(fallback)


def test_build_apply_plan_splits_plan_and_unresolved(tmp_path):
    uploads_dir = tmp_path / "uploads"
    uploads_dir.mkdir(parents=True, exist_ok=True)
    (uploads_dir / "splash.png").write_text("x")

    profile = {
        "banners": {
            "splash": {
                "target_path": "data/img/splash.png",
                "file": "missing-explicit.png",
                "width": 100,
                "height": 50,
            },
            "loading": {
                "target_path": "data/img/loading.png",
                "file": "missing.png",
            },
        }
    }

    plan, unresolved = branding_service.build_apply_plan(profile, str(uploads_dir))

    assert len(plan) == 1
    assert plan[0]["label"] == "banners.splash"
    assert plan[0]["source_path"] == str(uploads_dir / "splash.png")
    assert plan[0]["target_path"] == "data/img/splash.png"
    assert plan[0]["width"] == 100
    assert plan[0]["height"] == 50

    assert unresolved == [
        {
            "label": "banners.loading",
            "target_path": "data/img/loading.png",
            "source_file": "missing.png",
            "width": None,
            "height": None,
        }
    ]


def test_build_apply_plan_applies_predicate(tmp_path):
    uploads_dir = tmp_path / "uploads"
    uploads_dir.mkdir(parents=True, exist_ok=True)
    (uploads_dir / "icon.png").write_text("x")

    profile = {
        "tracks": {
            "tracks/road/a/icon.png": {
                "target_path": "tracks/road/a/icon.png",
                "file": "icon.png",
            }
        },
        "banners": {
            "splash": {
                "target_path": "data/img/splash.png",
                "file": "icon.png",
            }
        },
    }

    plan, unresolved = branding_service.build_apply_plan(
        profile,
        str(uploads_dir),
        predicate=lambda a: a["target_path"].startswith("tracks/"),
    )

    assert len(plan) == 1
    assert plan[0]["label"] == "tracks.tracks/road/a/icon.png"
    assert unresolved == []
