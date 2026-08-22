#!/usr/bin/env python3
"""
Video registry: one project-wide record of what has been downloaded and
transcribed, so re-runs never re-download work that is already done.

Why this exists
---------------
yt-dlp's --download-archive was previously written inside the output
directory, so every ``--dir`` got its own archive and none of them could see
the others. Running the same playlist into a new directory re-downloaded
everything.

Two layers solve that:

1. Registry (``.registry.json`` at the project root) -- durable state keyed by
   YouTube video ID. Survives directory renames and media cleanup.
2. Filesystem scan -- ``outtmpl`` is ``%(title)s [%(id)s].%(ext)s``, so every
   media file *and* every transcript already carries its video ID. The registry
   can therefore always be rebuilt from disk; deleting it loses nothing except
   history for files that are themselves gone.

Both feed a single generated archive at the project root, which is what yt-dlp
actually reads.

CLI:
    python registry.py rebuild          # rescan disk, merge, save
    python registry.py list [--pending] # show tracked videos
    python registry.py stats            # counts
    python registry.py forget ID [ID..] # drop entries so they download again
"""

import json
import os
import re
import sys
from datetime import datetime

from common import MEDIA_EXTENSIONS, OUTPUT_FORMATS

PROJECT_ROOT = os.path.dirname(os.path.abspath(__file__))
REGISTRY_PATH = os.path.join(PROJECT_ROOT, ".registry.json")
ARCHIVE_PATH = os.path.join(PROJECT_ROOT, ".download-archive.txt")
ARCHIVE_BASENAME = ".download-archive.txt"

REGISTRY_VERSION = 1

# YouTube IDs are exactly 11 chars of [0-9A-Za-z_-], written as "[ID]" by
# outtmpl. Anchored to the end of the stem so a title containing brackets
# cannot win over the real ID.
VIDEO_ID_RE = re.compile(r"\[([0-9A-Za-z_-]{11})\]$")

TRANSCRIPT_EXTENSIONS = {f".{fmt}" for fmt in OUTPUT_FORMATS}

# Directories never worth walking.
SKIP_DIRS = {".git", "__pycache__", ".venv", "node_modules", ".pytest_cache", ".claude"}


def extract_video_id(filename: str) -> str:
    """Return the YouTube ID embedded in a filename, or None."""
    stem = os.path.splitext(os.path.basename(filename))[0]
    match = VIDEO_ID_RE.search(stem)
    return match.group(1) if match else None


def extract_title(filename: str) -> str:
    """Return the title portion of a '<title> [<id>]' filename."""
    stem = os.path.splitext(os.path.basename(filename))[0]
    return VIDEO_ID_RE.sub("", stem).strip()


def _mtime_iso(path: str) -> str:
    try:
        return datetime.fromtimestamp(os.path.getmtime(path)).isoformat(timespec="seconds")
    except OSError:
        return _now()


def _now() -> str:
    return datetime.now().isoformat(timespec="seconds")


def load_registry() -> dict:
    """Load the registry, returning an empty one if absent or unreadable."""
    if not os.path.exists(REGISTRY_PATH):
        return {"version": REGISTRY_VERSION, "videos": {}}

    try:
        with open(REGISTRY_PATH, encoding="utf-8") as f:
            data = json.load(f)
    except (json.JSONDecodeError, OSError) as e:
        print(f"Registry unreadable ({e}); rebuilding from disk.", file=sys.stderr)
        return {"version": REGISTRY_VERSION, "videos": {}}

    data.setdefault("version", REGISTRY_VERSION)
    data.setdefault("videos", {})
    return data


def save_registry(registry: dict) -> None:
    registry["updated_at"] = _now()
    tmp = f"{REGISTRY_PATH}.tmp"
    with open(tmp, "w", encoding="utf-8") as f:
        json.dump(registry, f, indent=2, ensure_ascii=False, sort_keys=True)
    os.replace(tmp, REGISTRY_PATH)


def scan_filesystem(root: str = PROJECT_ROOT) -> dict:
    """
    Walk the project for files whose name carries a video ID.

    Returns:
        {video_id: {"title", "dir", "media", "transcript",
                    "downloaded_at", "transcribed_at"}}
        Keys are only present when the corresponding file was actually found.
    """
    found = {}

    for dirpath, dirnames, filenames in os.walk(root):
        dirnames[:] = [d for d in dirnames if d not in SKIP_DIRS]

        for filename in filenames:
            video_id = extract_video_id(filename)
            if not video_id:
                continue

            ext = os.path.splitext(filename)[1].lower()
            is_media = ext in MEDIA_EXTENSIONS
            is_transcript = ext in TRANSCRIPT_EXTENSIONS
            if not (is_media or is_transcript):
                continue

            full_path = os.path.join(dirpath, filename)
            rel_path = os.path.relpath(full_path, root)
            entry = found.setdefault(video_id, {})
            entry["title"] = extract_title(filename)
            entry["dir"] = os.path.relpath(dirpath, root)

            if is_media:
                entry["media"] = rel_path
                entry["downloaded_at"] = _mtime_iso(full_path)
            else:
                entry["transcript"] = rel_path
                entry["transcribed_at"] = _mtime_iso(full_path)

    return found


def _legacy_archive_ids(root: str = PROJECT_ROOT) -> dict:
    """
    Collect IDs from per-directory .download-archive.txt files left by the old
    layout. The root archive is excluded: that one is generated from this
    registry, so reading it back would make every entry permanently sticky.
    """
    ids = {}

    for dirpath, dirnames, filenames in os.walk(root):
        dirnames[:] = [d for d in dirnames if d not in SKIP_DIRS]

        if ARCHIVE_BASENAME not in filenames:
            continue

        path = os.path.join(dirpath, ARCHIVE_BASENAME)
        if os.path.abspath(path) == os.path.abspath(ARCHIVE_PATH):
            continue

        try:
            with open(path, encoding="utf-8") as f:
                lines = f.read().splitlines()
        except OSError:
            continue

        for line in lines:
            parts = line.split()
            if len(parts) == 2 and parts[0] == "youtube":
                ids[parts[1]] = os.path.relpath(path, root)

    return ids


def rebuild(root: str = PROJECT_ROOT, save: bool = True, quiet: bool = False) -> dict:
    """
    Merge stored registry + filesystem scan + legacy per-directory archives.

    Merge rules:
      - ``media`` is recomputed every time. Media is transient (cleanup deletes
        it after transcription), so a stale path must not keep a failed video
        marked as already-downloaded forever.
      - ``transcript`` / ``transcribed_at`` are sticky. A transcript the user
        moved or archived elsewhere still means the work is done.
      - Legacy archive IDs are recorded as ``legacy`` and treated as done, which
        errs toward never re-downloading. ``forget`` overrides that.
    """
    registry = load_registry()
    videos = registry["videos"]
    scanned = scan_filesystem(root)
    legacy = _legacy_archive_ids(root)

    for video_id, scan_entry in scanned.items():
        entry = videos.setdefault(video_id, {})
        entry["title"] = scan_entry.get("title", entry.get("title", ""))
        entry["dir"] = scan_entry.get("dir", entry.get("dir", ""))

        if "media" in scan_entry:
            entry["media"] = scan_entry["media"]
            entry.setdefault("downloaded_at", scan_entry["downloaded_at"])
        else:
            entry.pop("media", None)

        if "transcript" in scan_entry:
            entry["transcript"] = scan_entry["transcript"]
            entry.setdefault("transcribed_at", scan_entry["transcribed_at"])

    # Entries known only from the registry: drop media paths that no longer exist.
    for video_id, entry in videos.items():
        if video_id in scanned:
            continue
        media = entry.get("media")
        if media and not os.path.exists(os.path.join(root, media)):
            entry.pop("media", None)

    new_legacy = 0
    for video_id, source in legacy.items():
        entry = videos.setdefault(video_id, {})
        if not entry.get("legacy"):
            new_legacy += 1
        entry["legacy"] = source
        entry.setdefault("downloaded_at", "unknown (legacy archive)")

    if save:
        save_registry(registry)

    if not quiet:
        done = sum(1 for e in videos.values() if not needs_download(e))
        print(f"Registry: {len(videos)} video(s) tracked, {done} already done"
              + (f", {new_legacy} imported from legacy archives" if new_legacy else ""))

    return registry


def needs_download(entry: dict) -> bool:
    """
    True when a video still has to be fetched.

    A bare ``downloaded_at`` is deliberately not enough: if the media is gone
    and no transcript exists, the transcription failed and the file was cleaned
    up, so the video must come back.
    """
    if entry.get("transcript") or entry.get("transcribed_at"):
        return False
    if entry.get("media"):
        return False
    if entry.get("legacy"):
        return False
    return True


def done_ids(registry: dict) -> set:
    """IDs that must not be downloaded again."""
    return {
        video_id
        for video_id, entry in registry["videos"].items()
        if not needs_download(entry)
    }


def pending_ids(registry: dict) -> set:
    """IDs that are tracked but still need downloading."""
    return set(registry["videos"]) - done_ids(registry)


def write_archive(registry: dict, path: str = None) -> str:
    """
    Generate the yt-dlp --download-archive file from the registry.

    Rewritten from scratch on every run: the registry is the source of truth,
    and yt-dlp's own appends are folded back in by the post-run rebuild.

    ``path`` resolves at call time rather than as a default argument value, so
    tests can retarget the module at a throwaway tree.
    """
    path = path or ARCHIVE_PATH
    ids = sorted(done_ids(registry))
    with open(path, "w", encoding="utf-8") as f:
        for video_id in ids:
            f.write(f"youtube {video_id}\n")
    return path


def record_downloads(paths: list, root: str = PROJECT_ROOT, save: bool = True) -> dict:
    """Record freshly downloaded files (paths come from yt-dlp's hook)."""
    registry = load_registry()
    videos = registry["videos"]

    for path in paths:
        video_id = extract_video_id(path)
        if not video_id:
            continue
        entry = videos.setdefault(video_id, {})
        entry["title"] = extract_title(path)
        entry["dir"] = os.path.relpath(os.path.dirname(os.path.abspath(path)), root)
        entry["media"] = os.path.relpath(os.path.abspath(path), root)
        entry["downloaded_at"] = _now()

    if save:
        save_registry(registry)

    return registry


def forget(video_ids, save: bool = True) -> int:
    """Drop entries so the videos are downloaded again. Returns count removed."""
    registry = load_registry()
    removed = 0

    for video_id in video_ids:
        if registry["videos"].pop(video_id, None) is not None:
            removed += 1
        else:
            print(f"Not in registry: {video_id}", file=sys.stderr)

    if save and removed:
        save_registry(registry)
        write_archive(registry)

    return removed


def prepare_archive(redownload=None, root: str = PROJECT_ROOT, quiet: bool = False) -> str:
    """
    Full pre-download step: rebuild from disk, honour --redownload, and write
    the archive yt-dlp will read. Returns the archive path.
    """
    registry = rebuild(root=root, save=False, quiet=quiet)

    for video_id in (redownload or []):
        if registry["videos"].pop(video_id, None) is not None:
            print(f"Forcing re-download: {video_id}")
        else:
            print(f"--redownload: {video_id} not in registry (nothing to clear)")

    save_registry(registry)
    return write_archive(registry)


def _cmd_list(args) -> int:
    registry = load_registry()
    pending = pending_ids(registry)

    for video_id in sorted(registry["videos"], key=lambda i: registry["videos"][i].get("title", "")):
        entry = registry["videos"][video_id]
        is_pending = video_id in pending
        if args.pending and not is_pending:
            continue
        state = "PENDING" if is_pending else ("transcribed" if entry.get("transcript") else "downloaded")
        print(f"{video_id}  {state:<12}  {entry.get('title', '')[:70]}")

    return 0


def _cmd_stats(args) -> int:
    registry = load_registry()
    videos = registry["videos"]
    transcribed = sum(1 for e in videos.values() if e.get("transcript") or e.get("transcribed_at"))
    media_on_disk = sum(1 for e in videos.values() if e.get("media"))
    legacy = sum(1 for e in videos.values() if e.get("legacy"))

    print(f"Tracked videos:    {len(videos)}")
    print(f"Transcribed:       {transcribed}")
    print(f"Media on disk:     {media_on_disk}")
    print(f"From old archives: {legacy}")
    print(f"Pending download:  {len(pending_ids(registry))}")
    print(f"Registry:          {REGISTRY_PATH}")
    print(f"Archive:           {ARCHIVE_PATH}")
    return 0


def main() -> int:
    import argparse

    parser = argparse.ArgumentParser(description="Inspect and maintain the video registry")
    sub = parser.add_subparsers(dest="command")

    sub.add_parser("rebuild", help="Rescan the project and merge into the registry")

    list_parser = sub.add_parser("list", help="List tracked videos")
    list_parser.add_argument("--pending", action="store_true", help="Only videos still needing download")

    sub.add_parser("stats", help="Show registry counts")

    forget_parser = sub.add_parser("forget", help="Drop entries so they download again")
    forget_parser.add_argument("video_ids", nargs="+", metavar="ID")

    args = parser.parse_args()

    if args.command == "rebuild":
        registry = rebuild()
        write_archive(registry)
        return 0
    if args.command == "list":
        return _cmd_list(args)
    if args.command == "stats":
        return _cmd_stats(args)
    if args.command == "forget":
        removed = forget(args.video_ids)
        print(f"Removed {removed} entr{'y' if removed == 1 else 'ies'}")
        return 0

    parser.print_help()
    return 1


if __name__ == "__main__":
    sys.exit(main())
