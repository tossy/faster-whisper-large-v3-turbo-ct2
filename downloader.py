#!/usr/bin/env python3
"""
YouTube video downloader using yt-dlp.
Supports single videos and playlists.
"""

import os
import sys
import yt_dlp
import registry
from common import MEDIA_EXTENSIONS

try:
    from config import YOUTUBE_URLS, DOWNLOAD_DIR, AUDIO_ONLY
    try:
        from config import COOKIES_FROM_BROWSER
    except ImportError:  # older config.py without the setting
        COOKIES_FROM_BROWSER = None
except ImportError:
    print(
        "config.py not found. Copy the template first:\n"
        "    cp config.example.py config.py",
        file=sys.stderr,
    )
    sys.exit(1)


def get_ydl_opts(output_dir: str, audio_only: bool, cookies_from_browser: str = None,
                 download_archive: str = None) -> dict:
    """Get yt-dlp options based on configuration."""
    # The archive lives at the project root, not inside output_dir: a
    # per-directory archive cannot see what other directories already hold,
    # so switching --dir used to re-download everything.
    archive_path = download_archive or registry.ARCHIVE_PATH

    opts = {
        "outtmpl": os.path.join(output_dir, "%(title)s [%(id)s].%(ext)s"),
        "ignoreerrors": True,  # Continue on download errors
        "no_warnings": False,
        "quiet": False,
        # Skip videos already downloaded or transcribed in previous runs
        "download_archive": archive_path,
        # Enable remote components for JavaScript challenge solving
        # This fixes the issue where the first video in a playlist gets audio-only
        "remote_components": {"ejs:github"},
    }

    # YouTube gates streaming formats behind PO tokens; an authenticated
    # cookie jar is what makes the media URLs resolve instead of 403.
    if cookies_from_browser:
        opts["cookiesfrombrowser"] = (cookies_from_browser,)

    if audio_only:
        opts.update({
            "format": "bestaudio/best",
            "postprocessors": [{
                "key": "FFmpegExtractAudio",
                "preferredcodec": "m4a",
                "preferredquality": "192",
            }],
        })
    else:
        opts.update({
            "format": "bestvideo[ext=mp4]+bestaudio[ext=m4a]/best[ext=mp4]/best",
            "merge_output_format": "mp4",
        })

    return opts


def download_videos(urls: list = None, output_dir: str = None, audio_only: bool = None,
                    cookies_from_browser: str = None, download_archive: str = None) -> list:
    """
    Download videos from YouTube URLs.

    Args:
        urls: List of YouTube URLs (videos or playlists). Defaults to config.YOUTUBE_URLS
        output_dir: Output directory. Defaults to config.DOWNLOAD_DIR
        audio_only: Download audio only. Defaults to config.AUDIO_ONLY
        cookies_from_browser: Browser to pull YouTube cookies from
                              (e.g. 'brave'). Defaults to config.COOKIES_FROM_BROWSER
        download_archive: yt-dlp archive of already-fetched video IDs.
                          Defaults to the project-wide registry.ARCHIVE_PATH

    Returns:
        List of downloaded file paths
    """
    urls = urls if urls is not None else YOUTUBE_URLS
    output_dir = output_dir if output_dir is not None else DOWNLOAD_DIR
    audio_only = audio_only if audio_only is not None else AUDIO_ONLY
    cookies_from_browser = (
        cookies_from_browser if cookies_from_browser is not None else COOKIES_FROM_BROWSER
    )

    if not urls:
        print("No URLs specified in config.py")
        return []

    # Create output directory if it doesn't exist
    os.makedirs(output_dir, exist_ok=True)

    # Track downloaded files
    downloaded_files = []

    def postprocessor_hook(d):
        """Called after post-processing (including merge) is complete."""
        if d["status"] == "finished":
            # Get the final filepath after all post-processing
            filepath = d.get("info_dict", {}).get("filepath")
            if filepath and filepath not in downloaded_files:
                downloaded_files.append(filepath)

    opts = get_ydl_opts(output_dir, audio_only, cookies_from_browser, download_archive)
    opts["postprocessor_hooks"] = [postprocessor_hook]

    print(f"Download directory: {os.path.abspath(output_dir)}")
    print(f"Audio only: {audio_only}")
    print(f"Cookies from browser: {cookies_from_browser or 'none'}")
    print(f"Download archive: {opts['download_archive']}")
    print(f"URLs to process: {len(urls)}")
    print("-" * 50)

    with yt_dlp.YoutubeDL(opts) as ydl:
        for i, url in enumerate(urls, 1):
            print(f"\n[{i}/{len(urls)}] Processing: {url}")
            try:
                ydl.download([url])
            except Exception as e:
                print(f"Error downloading {url}: {e}")

    print("-" * 50)
    print(f"Download complete. Files downloaded: {len(downloaded_files)}")

    return downloaded_files


def get_downloaded_files(output_dir: str = None) -> list:
    """
    Get list of media files in the download directory.

    Args:
        output_dir: Directory to scan. Defaults to config.DOWNLOAD_DIR

    Returns:
        List of file paths
    """
    output_dir = output_dir if output_dir is not None else DOWNLOAD_DIR

    if not os.path.isdir(output_dir):
        return []

    return sorted(
        os.path.join(output_dir, filename)
        for filename in os.listdir(output_dir)
        if os.path.splitext(filename)[1].lower() in MEDIA_EXTENSIONS
    )


if __name__ == "__main__":
    # Run as standalone script
    registry.prepare_archive()
    downloaded = download_videos()
    if downloaded:
        registry.record_downloads(downloaded)
        print("\nDownloaded files:")
        for f in downloaded:
            print(f"  - {f}")
