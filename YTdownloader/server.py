from flask import Flask, render_template, request, jsonify, send_file, Response
import yt_dlp
import os
from flask_cors import CORS
import tempfile
import shutil
import json
import time


app = Flask(__name__)
CORS(app)

# Global variable to store download progress
download_progress = {}


class ProgressHook:
    def __init__(self, download_id):
        self.download_id = download_id
        
    def __call__(self, d):
        if d['status'] == 'downloading':
            progress = {
                'status': 'downloading',
                'downloaded_bytes': d.get('downloaded_bytes', 0),
                'total_bytes': d.get('total_bytes', 0),
                'speed': d.get('speed', 0),
                'eta': d.get('eta', 0),
                'percentage': 0
            }
            
            if progress['total_bytes']:
                progress['percentage'] = round((progress['downloaded_bytes'] / progress['total_bytes']) * 100, 1)
            
            download_progress[self.download_id] = progress
            print(f"Download {self.download_id}: {progress['percentage']}% - {progress['speed']} bytes/s")
            
        elif d['status'] == 'finished':
            download_progress[self.download_id] = {
                'status': 'finished',
                'filename': d.get('filename', ''),
                'percentage': 100
            }
            print(f"Download {self.download_id}: Finished!")


@app.route('/')
def index():
    return render_template('index.html')


@app.route('/get-formats', methods=['POST'])
def get_formats():
    """Get available video formats for a YouTube URL"""
    try:
        data = request.get_json()
        if not data:
            return jsonify({'status': 'error', 'message': 'No data received'}), 400
        
        url = data.get('url')
        if not url:
            return jsonify({'status': 'error', 'message': 'URL is required'}), 400
        
        print(f"Getting formats for: {url}")
        
        # Configure yt-dlp options
        ydl_opts = {
            'noplaylist': True,
        }
        
        # Get video info and formats
        with yt_dlp.YoutubeDL(ydl_opts) as ydl:
            info = ydl.extract_info(url, download=False)
            video_title = info.get('title', 'Unknown')
            video_duration = info.get('duration', 0)
            
            # Get available formats
            formats = info.get('formats', [])
            
            # Filter and organize formats
            video_formats = []
            audio_formats = []
            
            for fmt in formats:
                format_info = {
                    'format_id': fmt.get('format_id', ''),
                    'ext': fmt.get('ext', ''),
                    'filesize': fmt.get('filesize', 0),
                    'height': fmt.get('height', 0),
                    'width': fmt.get('width', 0),
                    'fps': fmt.get('fps', 0),
                    'vcodec': fmt.get('vcodec', ''),
                    'acodec': fmt.get('acodec', ''),
                    'format_note': fmt.get('format_note', ''),
                }
                
                # Calculate file size in MB
                if format_info['filesize']:
                    format_info['filesize_mb'] = round(format_info['filesize'] / (1024 * 1024), 1)
                else:
                    format_info['filesize_mb'] = 'Unknown'
                
                # Categorize formats
                if format_info['vcodec'] != 'none' and format_info['acodec'] != 'none':
                    # Video with audio
                    video_formats.append(format_info)
                elif format_info['vcodec'] != 'none':
                    # Video only
                    video_formats.append(format_info)
                elif format_info['acodec'] != 'none':
                    # Audio only
                    audio_formats.append(format_info)
            
            # Sort video formats by quality (height)
            video_formats.sort(key=lambda x: x['height'] or 0, reverse=True)
            
            return jsonify({
                'status': 'success',
                'video_title': video_title,
                'duration': video_duration,
                'video_formats': video_formats,
                'audio_formats': audio_formats
            })
            
    except Exception as e:
        print(f"Error getting formats: {str(e)}")
        return jsonify({'status': 'error', 'message': f'Failed to get formats: {str(e)}'}), 400


@app.route('/progress/<download_id>')
def progress_stream(download_id):
    """Stream download progress using Server-Sent Events"""
    def generate():
        while True:
            if download_id in download_progress:
                progress = download_progress[download_id]
                yield f"data: {json.dumps(progress)}\n\n"
                
                if progress['status'] == 'finished':
                    # Clean up progress data after a delay
                    time.sleep(2)
                    if download_id in download_progress:
                        del download_progress[download_id]
                    break
            else:
                yield f"data: {json.dumps({'status': 'waiting'})}\n\n"
            
            time.sleep(0.5)
    
    return Response(generate(), mimetype='text/event-stream')


@app.route('/download', methods=['POST'])
def download():
    try:
        data = request.get_json()
        if not data:
            return jsonify({'status': 'error', 'message': 'No data received'}), 400
        
        url = data.get('url')
        format_id = data.get('format_id', 'best')
        
        if not url:
            return jsonify({'status': 'error', 'message': 'URL is required'}), 400
        
        # Generate unique download ID
        download_id = f"download_{int(time.time())}"
        download_progress[download_id] = {'status': 'starting'}
        
        print(f"Starting download {download_id} for: {url} with format: {format_id}")
        
        # Return download ID immediately so frontend can start tracking
        return jsonify({
            'status': 'success',
            'download_id': download_id,
            'message': 'Download started'
        })
        
    except Exception as e:
        print(f"Error during download: {str(e)}")
        return jsonify({'status': 'error', 'message': f'Download failed: {str(e)}'}), 400


@app.route('/download-file/<download_id>', methods=['POST'])
def download_file(download_id):
    """Actually perform the download after progress tracking is set up"""
    try:
        data = request.get_json()
        if not data:
            return jsonify({'status': 'error', 'message': 'No data received'}), 400
        
        url = data.get('url')
        format_id = data.get('format_id', 'best')
        
        if not url:
            return jsonify({'status': 'error', 'message': 'URL is required'}), 400
        
        print(f"Performing download {download_id} for: {url} with format: {format_id}")
        
        # Create a temporary directory for the download
        temp_dir = tempfile.mkdtemp()
        
        try:
            # Configure yt-dlp options with progress hook
            ydl_opts = {
                'outtmpl': os.path.join(temp_dir, '%(title)s.%(ext)s'),
                'format': format_id,
                'noplaylist': True,
                'progress_hooks': [ProgressHook(download_id)],
            }
            
            # Download the video
            with yt_dlp.YoutubeDL(ydl_opts) as ydl:
                # Get video info first
                info = ydl.extract_info(url, download=False)
                video_title = info.get('title', 'Unknown')
                print(f"Video title: {video_title}")
                
                # Download the video
                print("Starting download...")
                ydl.download([url])
            
            # Find the downloaded file
            files = os.listdir(temp_dir)
            if not files:
                return jsonify({'status': 'error', 'message': 'No file downloaded'}), 400
            
            video_file = os.path.join(temp_dir, files[0])
            print(f"Download completed: {video_file}")
            
            # Copy to a permanent location
            downloads_dir = os.path.expanduser("~/Downloads")
            if not os.path.exists(downloads_dir):
                downloads_dir = os.getcwd()
            
            permanent_file = os.path.join(downloads_dir, files[0])
            shutil.copy2(video_file, permanent_file)
            print(f"File saved to: {permanent_file}")
            
            # Update progress to finished
            download_progress[download_id] = {
                'status': 'finished',
                'filename': files[0],
                'percentage': 100
            }
            
            # Send file to browser for download
            return send_file(
                permanent_file,
                as_attachment=True,
                download_name=files[0],
                mimetype='video/mp4'
            )
            
        finally:
            # Clean up temporary directory
            try:
                shutil.rmtree(temp_dir)
            except Exception:
                pass
        
    except Exception as e:
        print(f"Error during download: {str(e)}")
        if download_id in download_progress:
            download_progress[download_id] = {
                'status': 'error',
                'message': str(e)
            }
        return jsonify({'status': 'error', 'message': f'Download failed: {str(e)}'}), 400


if __name__ == "__main__":
    import os
    port = int(os.environ.get("PORT", 5000))
    app.run(host="0.0.0.0", port=port) 