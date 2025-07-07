from pytube import YouTube
import os

def test_download():
    # Test URL (a short video)
    url = "https://www.youtube.com/watch?v=dQw4w9WgXcQ"
    
    try:
        print("Testing pytube download...")
        print(f"URL: {url}")
        
        yt = YouTube(url)
        print(f"Title: {yt.title}")
        print(f"Length: {yt.length} seconds")
        
        # Get available streams
        streams = yt.streams.filter(progressive=True)
        print(f"Available progressive streams: {len(streams)}")
        
        if streams:
            stream = streams.get_highest_resolution()
            print(f"Selected stream: {stream}")
            
            # Download to current directory
            current_dir = os.getcwd()
            print(f"Downloading to: {current_dir}")
            
            file_path = stream.download(output_path=current_dir)
            print(f"Download completed: {file_path}")
            print("Test successful!")
        else:
            print("No progressive streams found")
            
    except Exception as e:
        print(f"Error: {str(e)}")

if __name__ == "__main__":
    test_download() 