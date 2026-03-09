from flask import Flask, render_template, request, jsonify, Response, url_for
import os
import json
import time
from datetime import timedelta
from werkzeug.utils import secure_filename
from modules.video_processor import VideoProcessor
from modules.face_analyzer import FaceAnalyzer
from modules.video_downloader import download_youtube_video

app = Flask(__name__)

# Configuration
UPLOAD_FOLDER = os.path.join(os.path.dirname(__file__), "static", "uploads")
ALLOWED_VIDEO_EXTENSIONS = {'mp4', 'avi', 'mov', 'mkv', 'flv', 'wmv'}
ALLOWED_IMAGE_EXTENSIONS = {'jpg', 'jpeg', 'png', 'bmp', 'gif'}
MAX_FILE_SIZE = 500 * 1024 * 1024  # 500MB

os.makedirs(UPLOAD_FOLDER, exist_ok=True)
app.config['UPLOAD_FOLDER'] = UPLOAD_FOLDER
app.config['MAX_CONTENT_LENGTH'] = MAX_FILE_SIZE

# Global progress tracking
progress_data = {
    "percent": 0,
    "status": "Starting...",
    "frame_count": 0,
    "total_frames": 0
}

def allowed_file(filename, allowed_extensions):
    """Check if file extension is allowed"""
    return '.' in filename and filename.rsplit('.', 1)[1].lower() in allowed_extensions

@app.route("/")
def index():
    """Render main page"""
    return render_template("index.html")

@app.route("/api/progress")
def progress():
    """Server-sent events for real-time progress"""
    def generate():
        last_percent = -1
        while True:
            if progress_data["percent"] != last_percent:
                last_percent = progress_data["percent"]
                yield f"data: {json.dumps(progress_data)}\n\n"
            
            if progress_data["percent"] >= 100:
                time.sleep(1)
                break
            time.sleep(0.3)
    
    return Response(generate(), mimetype='text/event-stream')

@app.route("/api/validate", methods=["POST"])
def validate_files():
    """Validate uploaded files before processing"""
    try:
        if 'reference' not in request.files:
            return jsonify({"success": False, "error": "Reference image is required"}), 400
        
        ref_file = request.files['reference']
        if not allowed_file(ref_file.filename, ALLOWED_IMAGE_EXTENSIONS):
            return jsonify({"success": False, "error": "Invalid reference image format"}), 400
        
        # Check video source
        youtube_url = request.form.get("youtube_url", "").strip()
        video_file = request.files.get("video")
        
        if not youtube_url and (not video_file or video_file.filename == ''):
            return jsonify({"success": False, "error": "Video source is required"}), 400
        
        if video_file and not allowed_file(video_file.filename, ALLOWED_VIDEO_EXTENSIONS):
            return jsonify({"success": False, "error": "Invalid video format"}), 400
        
        return jsonify({"success": True}), 200
    
    except Exception as e:
        return jsonify({"success": False, "error": str(e)}), 500

@app.route("/api/process", methods=["POST"])
def process():
    """Process video and find face matches using DeepFace"""
    global progress_data
    progress_data = {"percent": 0, "status": "Initializing...", "frame_count": 0, "total_frames": 0}
    
    try:
        # Save reference image
        if 'reference' not in request.files:
            return jsonify({"success": False, "error": "Reference image missing"}), 400
        
        ref_file = request.files['reference']
        ref_filename = secure_filename(f"ref_{int(time.time())}_{ref_file.filename}")
        ref_path = os.path.join(UPLOAD_FOLDER, ref_filename)
        ref_file.save(ref_path)
        
        # Get video source
        youtube_url = request.form.get("youtube_url", "").strip()
        video_file = request.files.get("video")
        
        video_path = ""
        video_filename = ""
        
        if youtube_url:
            progress_data = {"percent": 5, "status": "Downloading YouTube video...", "frame_count": 0, "total_frames": 0}
            try:
                video_path = download_youtube_video(youtube_url, UPLOAD_FOLDER)
                video_filename = os.path.basename(video_path)
            except Exception as e:
                return jsonify({"success": False, "error": f"YouTube download failed: {str(e)}"}), 400
        
        elif video_file:
            video_filename = secure_filename(f"video_{int(time.time())}_{video_file.filename}")
            video_path = os.path.join(UPLOAD_FOLDER, video_filename)
            video_file.save(video_path)
        
        if not video_path or not os.path.exists(video_path):
            return jsonify({"success": False, "error": "Failed to save video"}), 400
        
        # Initialize DeepFace analyzer
        progress_data = {"percent": 10, "status": "Loading DeepFace models...", "frame_count": 0, "total_frames": 0}
        face_analyzer = FaceAnalyzer(
            model_name='VGG-Face',      # Fast and accurate
            detector_backend='retinaface',  # Best for video frames
            distance_metric='cosine'
        )
        
        video_processor = VideoProcessor(progress_callback=update_progress)
        
        # Extract reference face embedding
        progress_data = {"percent": 15, "status": "Analyzing reference image with DeepFace...", "frame_count": 0, "total_frames": 0}
        reference_data = face_analyzer.get_face_embedding(ref_path)
        
        if reference_data is None:
            return jsonify({"success": False, "error": "No face found in reference image. Please use a clear image with a visible face."}), 400
        
        reference_embedding = reference_data['embedding']
        
        # Get sensitivity level
        sensitivity = request.form.get('sensitivity', 'balanced')
        threshold_map = {
            'strict': 0.3,
            'balanced': 0.5,
            'sensitive': 0.7
        }
        threshold = threshold_map.get(sensitivity, 0.5)
        
        # Process video
        progress_data = {"percent": 20, "status": "Processing video frames with DeepFace...", "frame_count": 0, "total_frames": 0}
        detections = video_processor.find_matches(
            video_path,
            reference_embedding,
            face_analyzer,
            distance_threshold=threshold,
            frame_skip=25
        )
        
        # Format results
        formatted_results = []
        for detection in detections:
            formatted_results.append({
                "time": detection['timestamp'],
                "seconds": detection['seconds'],
                "confidence": round(detection['confidence'], 2),
                "frame": detection['frame_number']
            })
        
        progress_data = {"percent": 100, "status": "Complete!", "frame_count": 0, "total_frames": 0}
        
        return jsonify({
            "success": True,
            "video_url": url_for('static', filename=f'uploads/{video_filename}'),
            "results": formatted_results,
            "total_detections": len(formatted_results),
            "video_duration": video_processor.get_video_duration(video_path)
        }), 200
    
    except Exception as e:
        import traceback
        error_trace = traceback.format_exc()
        print(f"Error in process route: {error_trace}")
        progress_data = {"percent": 0, "status": f"Error: {str(e)}", "frame_count": 0, "total_frames": 0}
        return jsonify({"success": False, "error": str(e)}), 500

def update_progress(percent, status, frame_count=0, total_frames=0):
    """Update global progress"""
    global progress_data
    progress_data = {
        "percent": min(percent, 99),
        "status": status,
        "frame_count": frame_count,
        "total_frames": total_frames
    }

@app.route("/api/health", methods=["GET"])
def health():
    """Health check endpoint"""
    return jsonify({"status": "healthy"}), 200

@app.errorhandler(413)
def request_entity_too_large(error):
    """Handle file too large"""
    return jsonify({"success": False, "error": "File too large. Maximum size is 500MB"}), 413

@app.errorhandler(500)
def internal_error(error):
    """Handle internal server errors"""
    return jsonify({"success": False, "error": "Internal server error"}), 500

if __name__ == "__main__":
    app.run(debug=False, host="0.0.0.0", port=5000)
