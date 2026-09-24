# =============================================================================
# Configuration template
#
# Copy this file to config.py and edit it with your own URLs and settings:
#
#     cp config.example.py config.py
#
# config.py is gitignored so your URLs and settings stay local.
# =============================================================================

# =============================================================================
# YouTube Download Settings
# =============================================================================

# YouTube URLs to download
# Supports:
#   - Single video URLs: "https://www.youtube.com/watch?v=VIDEO_ID"
#   - Playlist URLs: "https://www.youtube.com/playlist?list=PLAYLIST_ID"
#   - Mix of both
#
# yt-dlp automatically handles playlists (downloads all videos in playlist)
# NOTE: Always end each URL with a trailing comma. Adjacent strings without a
# comma are silently concatenated by Python into one broken URL.
YOUTUBE_URLS = [
    # "https://www.youtube.com/playlist?list=PLxxxxxxxx",
    # "https://www.youtube.com/watch?v=EXAMPLE1",
]

# Guard against the missing-comma footgun above: a concatenated entry would
# contain two "http" substrings.
for _url in YOUTUBE_URLS:
    if _url.count("http") > 1:
        raise ValueError(
            f"YOUTUBE_URLS entry looks like two URLs merged (missing comma?): {_url[:100]}"
        )

# Directory to save downloaded videos
DOWNLOAD_DIR = "./downloads"

# Browser to read YouTube cookies from (yt-dlp --cookies-from-browser).
# Required as of 2026: YouTube gates streaming formats behind PO tokens, so
# unauthenticated downloads fail with "HTTP Error 403: Forbidden".
# Options: "brave", "chrome", "chromium", "edge", "vivaldi", "opera", "firefox",
# "safari" (Safari's cookie file is SIP-protected on macOS and usually fails).
# Set to None to download without cookies.
COOKIES_FROM_BROWSER = None

# Download full video or audio only
# True = audio only (smaller files, faster download)
# False = full video file (default)
AUDIO_ONLY = True

# =============================================================================
# Transcription Settings
# =============================================================================

# Output format for transcriptions
# Options: "txt", "vtt", "srt", "json", "tsv"
OUTPUT_FORMAT = "txt"

# Language for transcription
# Set to None for auto-detection (default)
# Or specify language code: "en", "ja", "es", "fr", etc.
LANGUAGE = None

# =============================================================================
# Post-Processing Settings
# =============================================================================

# Delete downloaded files after successful transcription
# True = delete after transcription
# False = keep files (default)
DELETE_AFTER_TRANSCRIPTION = False
