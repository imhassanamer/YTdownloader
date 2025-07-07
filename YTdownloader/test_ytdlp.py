import yt_dlp
import os


def test_download():
    # Test URL (a short video)
    url = "https://www.youtube.com/watch?v=dQw4w9WgXcQ"
    
    try:
        print("Testing yt-dlp download...")
        print(f"URL: {url}")
        
        # Configure yt-dlp options
        ydl_opts = {
            'outtmpl': '%(title)s.%(ext)s',
            'format': 'best[ext=mp4]/best',
            'noplaylist': True,
        }
        
        # Test download
        with yt_dlp.YoutubeDL(ydl_opts) as ydl:
            # Get video info first
            info = ydl.extract_info(url, download=False)
            video_title = info.get('title', 'Unknown')
            print(f"Video title: {video_title}")
            print(f"Video duration: {info.get('duration', 'Unknown')} seconds")
            
            # Download the video
            print("Starting download...")
            ydl.download([url])
        
        print("Test successful!")
        
    except Exception as e:
        print(f"Error: {str(e)}")


if __name__ == "__main__":
    test_download() 