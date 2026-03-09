import os
import time
import re
import subprocess
from pathlib import Path

def download_youtube_video(url, output_path="static/uploads"):
    """
    Download YouTube video using multiple methods with fallbacks
    
    Args:
        url: YouTube URL
        output_path: Directory to save video
        
    Returns:
        Path to downloaded video file
        
    Raises:
        Exception: If all download methods fail
    """
    
    # Validate and clean URL
    url = url.strip()
    if not url:
        raise Exception("YouTube URL is empty")
    
    # Extract video ID from various YouTube URL formats
    video_id = extract_youtube_video_id(url)
    if not video_id:
        raise Exception("Invalid YouTube URL format. Use: https://www.youtube.com/watch?v=VIDEO_ID")
    
    if not os.path.exists(output_path):
        os.makedirs(output_path, exist_ok=True)
    
    print(f"Attempting to download YouTube video: {video_id}")
    
    # Try Method 1: yt-dlp with proxy and headers (Recommended)
    try:
        return _download_with_ytdlp_advanced(url, video_id, output_path)
    except Exception as e:
        print(f"yt-dlp advanced method failed: {e}")
    
    # Try Method 2: yt-dlp standard
    try:
        return _download_with_ytdlp(url, video_id, output_path)
    except Exception as e:
        print(f"yt-dlp method failed: {e}")
    
    # Try Method 3: pytube with oauth disabled
    try:
        return _download_with_pytube(url, video_id, output_path)
    except Exception as e:
        print(f"PyTube method failed: {e}")
    
    # Try Method 4: youtube-dl
    try:
        return _download_with_youtubedl(url, video_id, output_path)
    except Exception as e:
        print(f"youtube-dl method failed: {e}")
    
    # Try Method 5: ffmpeg direct download
    try:
        return _download_with_ffmpeg(url, video_id, output_path)
    except Exception as e:
        print(f"ffmpeg method failed: {e}")
    
    # All methods failed
    raise Exception(
        "YouTube download failed. Possible solutions:\n"
        "1. Try a different YouTube video\n"
        "2. Use a VPN (YouTube may be blocking your region)\n"
        "3. Install ffmpeg: https://ffmpeg.org/download.html\n"
        "4. Use video file upload instead (recommended)\n"
        "5. Check your internet connection"
    )


def extract_youtube_video_id(url):
    """
    Extract video ID from various YouTube URL formats
    """
    url = url.strip()
    
    patterns = [
        r'(?:youtube\.com\/watch\?v=|youtu\.be\/)([^&\n?#]+)',
        r'(?:youtube\.com\/)?.*?v=([^&\n?#]+)',
        r'youtu\.be\/([^&\n?#]+)',
        r'youtube\.com\/embed\/([^&\n?#]+)',
    ]
    
    for pattern in patterns:
        match = re.search(pattern, url)
        if match:
            video_id = match.group(1)
            if video_id and len(video_id) == 11:
                return video_id
    
    return None


def _download_with_ytdlp_advanced(url, video_id, output_path):
    """Download using yt-dlp with advanced settings and proxies"""
    try:
        import yt_dlp
    except ImportError:
        raise Exception("yt-dlp not installed")
    
    timestamp = int(time.time())
    output_template = os.path.join(output_path, f"youtube_{timestamp}_{video_id}_%(title).30s.%(ext)s")
    
    # Advanced yt-dlp options
    ydl_opts = {
        'format': 'best[ext=mp4]/best[height<=720]/best',
        'outtmpl': output_template,
        'quiet': False,
        'no_warnings': False,
        'socket_timeout': 30,
        'http_headers': {
            'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36',
            'Accept-Language': 'en-US,en;q=0.9',
            'Accept-Encoding': 'gzip, deflate',
            'DNT': '1',
            'Connection': 'keep-alive',
            'Upgrade-Insecure-Requests': '1'
        },
        'extractor_args': {
            'youtube': {
                'lang': ['en']
            }
        },
        'skip_unavailable_fragments': True,
        'fragment_retries': 10,
        'retries': 10,
        'quiet': True,
        'no_warnings': True,
        'postprocessors': [{
            'key': 'FFmpegVideoConvertor',
            'prefixes': ['best', '18'],
            'format': 'mp4',
        }],
    }
    
    try:
        with yt_dlp.YoutubeDL(ydl_opts) as ydl:
            print(f"[yt-dlp] Downloading video {video_id}...")
            info = ydl.extract_info(url, download=True)
            output_file = ydl.prepare_filename(info)
            
            if os.path.exists(output_file) and os.path.getsize(output_file) > 0:
                print(f"[yt-dlp] Successfully downloaded: {output_file}")
                return output_file
            else:
                raise Exception("Downloaded file is empty or doesn't exist")
    
    except Exception as e:
        raise Exception(f"yt-dlp advanced: {str(e)}")


def _download_with_ytdlp(url, video_id, output_path):
    """Download using yt-dlp standard method"""
    try:
        import yt_dlp
    except ImportError:
        raise Exception("yt-dlp not installed")
    
    timestamp = int(time.time())
    output_template = os.path.join(output_path, f"youtube_{timestamp}_{video_id}_%(title).30s.%(ext)s")
    
    ydl_opts = {
        'format': 'best[ext=mp4]/best[height<=480]',
        'outtmpl': output_template,
        'quiet': True,
        'no_warnings': True,
    }
    
    try:
        with yt_dlp.YoutubeDL(ydl_opts) as ydl:
            print(f"[yt-dlp standard] Downloading video {video_id}...")
            info = ydl.extract_info(url, download=True)
            output_file = ydl.prepare_filename(info)
            
            if os.path.exists(output_file) and os.path.getsize(output_file) > 0:
                print(f"[yt-dlp] Successfully downloaded: {output_file}")
                return output_file
            else:
                raise Exception("Downloaded file is empty")
    
    except Exception as e:
        raise Exception(f"yt-dlp standard: {str(e)}")


def _download_with_pytube(url, video_id, output_path):
    """Download using pytube with custom settings"""
    try:
        from pytube import YouTube
        from pytube.exceptions import PytubeError
    except ImportError:
        raise Exception("pytube not installed")
    
    try:
        print(f"[pytube] Downloading video {video_id}...")
        
        # Disable oauth and use simpler method
        yt = YouTube(
            url,
            use_oauth=False,
            allow_oauth_cache=False,
            on_progress_callback=None,
            on_complete_callback=None
        )
        
        # Try to get the best mp4 stream
        stream = yt.streams.filter(
            progressive=True,
            file_extension='mp4'
        ).order_by('resolution').desc().first()
        
        if not stream:
            # Try non-progressive streams
            stream = yt.streams.filter(
                file_extension='mp4'
            ).order_by('resolution').desc().first()
        
        if not stream:
            raise Exception("No suitable video stream found")
        
        timestamp = int(time.time())
        filename = f"youtube_{timestamp}_{video_id}_{sanitize_filename(yt.title[:30])}.mp4"
        
        output_file = stream.download(output_path=output_path, filename=filename)
        
        if os.path.exists(output_file) and os.path.getsize(output_file) > 0:
            print(f"[pytube] Successfully downloaded: {output_file}")
            return output_file
        else:
            raise Exception("Downloaded file is empty or doesn't exist")
    
    except Exception as e:
        raise Exception(f"pytube: {str(e)}")


def _download_with_youtubedl(url, video_id, output_path):
    """Download using youtube-dl"""
    try:
        import youtube_dl
    except ImportError:
        raise Exception("youtube-dl not installed")
    
    timestamp = int(time.time())
    output_template = os.path.join(output_path, f"youtube_{timestamp}_{video_id}_%(title).30s.%(ext)s")
    
    ydl_opts = {
        'format': 'best[ext=mp4]/best',
        'outtmpl': output_template,
        'quiet': True,
        'no_warnings': True,
    }
    
    try:
        with youtube_dl.YoutubeDL(ydl_opts) as ydl:
            print(f"[youtube-dl] Downloading video {video_id}...")
            info = ydl.extract_info(url, download=True)
            output_file = ydl.prepare_filename(info)
            
            if os.path.exists(output_file) and os.path.getsize(output_file) > 0:
                print(f"[youtube-dl] Successfully downloaded: {output_file}")
                return output_file
            else:
                raise Exception("Downloaded file is empty")
    
    except Exception as e:
        raise Exception(f"youtube-dl: {str(e)}")


def _download_with_ffmpeg(url, video_id, output_path):
    """
    Download using ffmpeg directly
    Requires ffmpeg to be installed: https://ffmpeg.org/download.html
    """
    
    # Check if ffmpeg is installed
    try:
        subprocess.run(['ffmpeg', '-version'], capture_output=True, check=True)
    except (subprocess.CalledProcessError, FileNotFoundError):
        raise Exception("ffmpeg not installed. Install from: https://ffmpeg.org/download.html")
    
    timestamp = int(time.time())
    output_file = os.path.join(output_path, f"youtube_{timestamp}_{video_id}.mp4")
    
    try:
        print(f"[ffmpeg] Downloading video {video_id}...")
        
        cmd = [
            'ffmpeg',
            '-i', url,
            '-c:v', 'libx264',
            '-preset', 'fast',
            '-c:a', 'aac',
            '-b:a', '128k',
            '-y',  # Overwrite without asking
            output_file
        ]
        
        result = subprocess.run(
            cmd,
            capture_output=True,
            text=True,
            timeout=300  # 5 minutes timeout
        )
        
        if result.returncode == 0 and os.path.exists(output_file) and os.path.getsize(output_file) > 0:
            print(f"[ffmpeg] Successfully downloaded: {output_file}")
            return output_file
        else:
            raise Exception(f"ffmpeg error: {result.stderr}")
    
    except subprocess.TimeoutExpired:
        raise Exception("Download timeout - video too large")
    except Exception as e:
        raise Exception(f"ffmpeg: {str(e)}")


def sanitize_filename(filename):
    """Remove special characters from filename"""
    # Remove invalid filename characters
    invalid_chars = r'[<>:"/\\|?*\n\r\t]'
    filename = re.sub(invalid_chars, '', filename)
    # Remove leading/trailing spaces and dots
    filename = filename.strip('. ')
    return filename if filename else "video"
