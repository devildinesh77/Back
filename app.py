import os
from flask import Flask, request, jsonify
from flask_cors import CORS
import yt_dlp

app = Flask(__name__)
CORS(app)

@app.route('/download', methods=['POST'])
def get_download_link():
    data = request.get_json()
    
    if not data or 'url' not in data:
        return jsonify({'error': 'Missing URL in request body'}), 400
        
    url = data['url']
    
    # Use 'b[ext=mp4]/b' to ensure we get a pre-merged single file with both video and audio.
    ydl_opts = {
        'format': 'b[ext=mp4]/b',
        'noplaylist': True,
        'quiet': True,
        'no_warnings': True,
        'skip_download': True,
        # YouTube blocks standard web requests. Impersonating mobile/TV clients bypasses this.
        'extractor_args': {
            'youtube': {
                'player_client': ['android', 'ios', 'tv', 'web']
            }
        },
        # Use a mobile user-agent to match the client impersonation
        'http_headers': {
            'User-Agent': 'Mozilla/5.0 (Linux; Android 10; SM-G981B) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/80.0.3987.162 Mobile Safari/537.36'
        }
    }
    
    try:
        with yt_dlp.YoutubeDL(ydl_opts) as ydl:
            info = ydl.extract_info(url, download=False)
            
            title = info.get('title', 'Unknown Title')
            download_url = info.get('url')
            thumbnail = info.get('thumbnail')
            
            if not download_url:
                formats = info.get('formats', [])
                # Look for formats with both video and audio
                video_formats = [f for f in formats if f.get('vcodec') != 'none' and f.get('acodec') != 'none' and f.get('url')]
                if video_formats:
                    best_video = sorted(video_formats, key=lambda x: x.get('height') or 0, reverse=True)[0]
                    download_url = best_video.get('url')
                elif formats:
                    # Fallback to any format with a URL if no merged format found
                    download_url = formats[-1].get('url')
                    
            if not download_url:
                return jsonify({'error': 'Could not extract direct download URL. It might be a protected video.'}), 500
                
            return jsonify({
                'title': title,
                'download_url': download_url,
                'thumbnail': thumbnail
            }), 200
            
    except Exception as e:
        return jsonify({'error': f'Extraction failed: {str(e)}'}), 500

@app.route('/health', methods=['GET'])
def health_check():
    return jsonify({'status': 'ok'}), 200

if __name__ == '__main__':
    port = int(os.environ.get('PORT', 5000))
    app.run(host='0.0.0.0', port=port, threaded=True)
