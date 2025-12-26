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
YOUTUBE_URLS = [
    # Example: Single playlist (yt-dlp downloads all videos automatically)
    # "https://www.youtube.com/playlist?list=PLxxxxxxxx",
    "https://www.youtube.com/playlist?list=PLUZoVeBe_mXiBwoy--zP9RyPnLjyeKJCe"

    # Example: Individual videos
    # "https://www.youtube.com/watch?v=EXAMPLE1",
    # "https://www.youtube.com/watch?v=EXAMPLE2",
]

# Directory to save downloaded videos
DOWNLOAD_DIR = "./downloads"

# Download full video or audio only
# True = audio only (smaller files, faster download)
# False = full video file (default)
AUDIO_ONLY = False

# =============================================================================
# Transcription Settings
# =============================================================================

# Output format for transcriptions
# Options: "txt", "vtt", "srt", "json", "tsv"
OUTPUT_FORMAT = "vtt"

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
