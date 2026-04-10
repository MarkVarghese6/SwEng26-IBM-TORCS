"""Helpers for profile-driven branding operations."""

import os


def iter_profile_assets(profile):
    """Yield branding assets from a profile.

    An asset is any dict containing a ``target_path`` key. Source can be given by
    ``file`` or ``texture_file``.
    """

    assets = []

    def _walk(node, path_parts):
        if isinstance(node, dict):
            if "target_path" in node:
                label = ".".join(path_parts) if path_parts else "asset"
                assets.append(
                    {
                        "label": label,
                        "target_path": str(node.get("target_path", "")).strip(),
                        "source_file": node.get("file") or node.get("texture_file"),
                        "width": node.get("width"),
                        "height": node.get("height"),
                    }
                )

            for key, value in node.items():
                _walk(value, path_parts + [str(key)])
        elif isinstance(node, list):
            for i, value in enumerate(node):
                _walk(value, path_parts + [str(i)])

    _walk(profile, [])

    # Keep deterministic order and ignore malformed entries.
    return [a for a in assets if a["target_path"]]


def resolve_source_file(asset, uploads_dir):
    """Resolve source path from profile asset entry.

    Priority:
    1) explicit source file in profile
    2) uploaded file matching basename of target_path
    """

    explicit = asset.get("source_file")
    if explicit:
        explicit = str(explicit)
        if os.path.exists(explicit):
            return explicit

    fallback = os.path.join(uploads_dir, os.path.basename(asset["target_path"]))
    if os.path.exists(fallback):
        return fallback
    return None


def build_apply_plan(profile, uploads_dir, predicate=None):
    """Build list of copy operations from a profile.

    Returns tuple ``(plan, unresolved)`` where plan entries include source/target.
    """

    assets = iter_profile_assets(profile)
    if predicate is not None:
        assets = [a for a in assets if predicate(a)]

    plan = []
    unresolved = []
    for asset in assets:
        source_path = resolve_source_file(asset, uploads_dir)
        if source_path:
            plan.append({**asset, "source_path": source_path})
        else:
            unresolved.append(asset)
    return plan, unresolved
