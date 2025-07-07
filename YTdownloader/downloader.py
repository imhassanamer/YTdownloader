import os
from pytube import YouTube

# Prompt user for YouTube URL
url = input("Enter the YouTube video URL: ")

# Prompt user for save directory (default to current directory)
save_path = input(
    "Enter save directory (blank for current dir): "
).strip()
if not save_path:
    save_path = os.getcwd()

try:
    yt = YouTube(url)
    print(f"Title: {yt.title}")
    print("Downloading...")
    stream = yt.streams.get_highest_resolution()
    stream.download(output_path=save_path)
    print(f"Download completed! Video saved to: {save_path}")
except Exception as e:
    print(f"An error occurred: {e}") 