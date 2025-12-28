#!/usr/bin/env python3
"""
YouTube video downloader using yt-dlp.
Supports single videos and playlists.
"""

import os
import yt_dlp
from config import YOUTUBE_URLS, DOWNLOAD_DIR, AUDIO_ONLY


def get_ydl_opts(output_dir: str, audio_only: bool) -> dict:
    """Get yt-dlp options based on configuration."""
    opts = {
        "outtmpl": os.path.join(output_dir, "%(title)s [%(id)s].%(ext)s"),
        "ignoreerrors": True,  # Continue on download errors
        "no_warnings": False,
        "quiet": False,
    }

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


def download_videos(urls: list = None, output_dir: str = None, audio_only: bool = None) -> list:
    """
    Download videos from YouTube URLs.

    Args:
        urls: List of YouTube URLs (videos or playlists). Defaults to config.YOUTUBE_URLS
        output_dir: Output directory. Defaults to config.DOWNLOAD_DIR
        audio_only: Download audio only. Defaults to config.AUDIO_ONLY

    Returns:
        List of downloaded file paths
    """
    urls = urls if urls is not None else YOUTUBE_URLS
    output_dir = output_dir if output_dir is not None else DOWNLOAD_DIR
    audio_only = audio_only if audio_only is not None else AUDIO_ONLY

    if not urls:
        print("No URLs specified in config.py")
        return []

    # Create output directory if it doesn't exist
    os.makedirs(output_dir, exist_ok=True)

    # Track downloaded files
    downloaded_files = []

    def progress_hook(d):
        if d["status"] == "finished":
            filepath = d.get("filename")
            if filepath:
                downloaded_files.append(filepath)

    opts = get_ydl_opts(output_dir, audio_only)
    opts["progress_hooks"] = [progress_hook]

    print(f"Download directory: {os.path.abspath(output_dir)}")
    print(f"Audio only: {audio_only}")
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

    media_extensions = {
        ".mp4", ".mkv", ".webm", ".avi", ".mov",  # Video
        ".mp3", ".m4a", ".wav", ".flac", ".ogg", ".aac", ".wma"  # Audio
    }

    files = []
    for filename in os.listdir(output_dir):
        ext = os.path.splitext(filename)[1].lower()
        if ext in media_extensions:
            files.append(os.path.join(output_dir, filename))

    return sorted(files)


if __name__ == "__main__":
    # Run as standalone script
    downloaded = download_videos()
    if downloaded:
        print("\nDownloaded files:")
        for f in downloaded:
            print(f"  - {f}")
