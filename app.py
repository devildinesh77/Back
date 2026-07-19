import os
from flask import Flask, request, jsonify
from flask_cors import CORS
import yt_dlp

app = Flask(__name__)
# Enable CORS for all routes so the frontend can securely communicate with this API
CORS(app)

@app.route('/download', methods=['POST'])
def get_download_link():
    data = request.get_json()
    
    if not data or 'url' not in data:
        return jsonify({'error': 'Missing URL in request body'}), 400
        
    url = data['url']
    
    req_format = data.get('format', 'mp4')
    
    # Configure yt-dlp to extract metadata only, without downloading the video
    if req_format == 'mp3':
        ydl_opts = {
            'format': 'bestaudio/best',
            'noplaylist': True,
            'quiet': True,
        }
        ext = 'mp3'
    else:
        ydl_opts = {
            'format': 'best',
            'noplaylist': True,
            'quiet': True,
        }
        ext = 'mp4'
    
    try:
        with yt_dlp.YoutubeDL(ydl_opts) as ydl:
            # download=False enforces the zero-server-download policy
            info = ydl.extract_info(url, download=False)
            
            # Extract necessary metadata
            title = info.get('title', 'Unknown Title')
            download_url = info.get('url', None)
            thumbnail = info.get('thumbnail', None)
            
            if not download_url:
                return jsonify({'error': 'Could not extract direct download URL'}), 500
                
            response = jsonify({
                'title': title,
                'download_url': download_url,
                'thumbnail': thumbnail
            })
            # Content-Disposition forces the browser to download the file
            safe_title = "".join([c for c in title if c.isalpha() or c.isdigit() or c==' ']).rstrip()
            if not safe_title:
                safe_title = "download"
            response.headers['Content-Disposition'] = f'attachment; filename="{safe_title}.{ext}"'
            
            return response, 200
            
    except Exception as e:
        return jsonify({'error': f'Extraction failed: {str(e)}'}), 500

@app.route('/health', methods=['GET'])
def health_check():
    return jsonify({'status': 'ok'}), 200

if __name__ == '__main__':
    # Dynamically bind to the PORT environment variable, defaulting to 5000
    port = int(os.environ.get('PORT', 5000))
    app.run(host='0.0.0.0', port=port)
