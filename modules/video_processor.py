import cv2
import os
import numpy as np
from datetime import timedelta

class VideoProcessor:
    """Handles video processing and frame analysis"""
    
    def __init__(self, progress_callback=None):
        """
        Initialize VideoProcessor
        
        Args:
            progress_callback: Function to call for progress updates
        """
        self.progress_callback = progress_callback
    
    def get_video_info(self, video_path):
        """
        Get video information
        
        Args:
            video_path: Path to video file
            
        Returns:
            Dictionary with video info or None
        """
        try:
            video = cv2.VideoCapture(video_path)
            
            if not video.isOpened():
                return None
            
            info = {
                'fps': video.get(cv2.CAP_PROP_FPS),
                'frame_count': int(video.get(cv2.CAP_PROP_FRAME_COUNT)),
                'width': int(video.get(cv2.CAP_PROP_FRAME_WIDTH)),
                'height': int(video.get(cv2.CAP_PROP_FRAME_HEIGHT)),
                'duration': int(video.get(cv2.CAP_PROP_FRAME_COUNT) / video.get(cv2.CAP_PROP_FPS))
            }
            
            video.release()
            return info
        
        except Exception as e:
            print(f"Error getting video info: {e}")
            return None
    
    def get_video_duration(self, video_path):
        """Get video duration in seconds"""
        info = self.get_video_info(video_path)
        return info['duration'] if info else 0
    
    def seconds_to_timestamp(self, seconds):
        """Convert seconds to HH:MM:SS format"""
        h = seconds // 3600
        m = (seconds % 3600) // 60
        s = seconds % 60
        return f"{int(h):02d}:{int(m):02d}:{int(s):02d}"
    
    def find_matches(self, video_path, reference_embedding, face_analyzer, 
                    distance_threshold=0.5, frame_skip=25):
        """
        Find all frames where reference face appears using DeepFace
        
        Args:
            video_path: Path to video file
            reference_embedding: Reference face embedding from get_face_embedding()
            face_analyzer: FaceAnalyzer instance
            distance_threshold: DeepFace distance threshold (lower = stricter matching)
                              Typical ranges: 0.3-0.7 depending on model and use case
            frame_skip: Process every Nth frame
            
        Returns:
            List of detection dictionaries
        """
        detections = []
        
        try:
            video = cv2.VideoCapture(video_path)
            
            if not video.isOpened():
                raise Exception("Cannot open video file")
            
            fps = video.get(cv2.CAP_PROP_FPS)
            total_frames = int(video.get(cv2.CAP_PROP_FRAME_COUNT))
            frame_count = 0
            processed_frames = 0
            
            if self.progress_callback:
                self.progress_callback(20, "Processing video frames with DeepFace...", frame_count, total_frames)
            
            # Track recent detections to avoid duplicates
            last_detection_frame = -1
            min_frame_gap = max(1, int(fps * 0.5))  # At least 0.5 seconds between detections
            
            while True:
                ret, frame = video.read()
                
                if not ret:
                    break
                
                # Process every Nth frame
                if frame_count % frame_skip == 0:
                    processed_frames += 1
                    
                    try:
                        # Verify faces against reference using DeepFace
                        matches = face_analyzer.verify_faces(
                            frame,
                            reference_embedding,
                            threshold=distance_threshold
                        )
                        
                        # Add detections
                        for match in matches:
                            if match['is_match'] and (frame_count - last_detection_frame) > min_frame_gap:
                                timestamp_seconds = int(frame_count / fps)
                                timestamp_str = self.seconds_to_timestamp(timestamp_seconds)
                                
                                detections.append({
                                    'frame_number': frame_count,
                                    'timestamp': timestamp_str,
                                    'seconds': timestamp_seconds,
                                    'confidence': match['confidence'],
                                    'distance': match['distance']
                                })
                                
                                last_detection_frame = frame_count
                                break  # Only count one detection per frame
                    
                    except Exception as e:
                        print(f"Error processing frame {frame_count}: {e}")
                    
                    # Update progress
                    if self.progress_callback and processed_frames % 10 == 0:
                        progress = 20 + int((frame_count / total_frames) * 75)
                        self.progress_callback(
                            progress,
                            f"Processing frame {frame_count:,}/{total_frames:,}...",
                            frame_count,
                            total_frames
                        )
                
                frame_count += 1
            
            video.release()
            
            if self.progress_callback:
                self.progress_callback(95, "Finalizing results...", frame_count, total_frames)
        
        except Exception as e:
            print(f"Error processing video: {e}")
            if self.progress_callback:
                self.progress_callback(0, f"Error: {str(e)}", 0, 0)
        
        return detections
    
    def find_matches_with_details(self, video_path, reference_embedding, face_analyzer,
                                 distance_threshold=0.5, frame_skip=25, save_detection_frames=False,
                                 output_dir=None):
        """
        Find matches with additional details and optional frame saving
        
        Args:
            video_path: Path to video file
            reference_embedding: Reference face embedding
            face_analyzer: FaceAnalyzer instance
            distance_threshold: Distance threshold
            frame_skip: Process every Nth frame
            save_detection_frames: Save frames with detected faces
            output_dir: Directory to save detection frames
            
        Returns:
            List of detailed detection dictionaries
        """
        detections = []
        
        try:
            video = cv2.VideoCapture(video_path)
            
            if not video.isOpened():
                raise Exception("Cannot open video file")
            
            fps = video.get(cv2.CAP_PROP_FPS)
            total_frames = int(video.get(cv2.CAP_PROP_FRAME_COUNT))
            frame_count = 0
            
            if save_detection_frames and output_dir:
                os.makedirs(output_dir, exist_ok=True)
            
            last_detection_frame = -1
            min_frame_gap = max(1, int(fps * 0.5))
            
            while True:
                ret, frame = video.read()
                
                if not ret:
                    break
                
                if frame_count % frame_skip == 0:
                    try:
                        matches = face_analyzer.verify_faces(
                            frame,
                            reference_embedding,
                            threshold=distance_threshold
                        )
                        
                        for match in matches:
                            if match['is_match'] and (frame_count - last_detection_frame) > min_frame_gap:
                                timestamp_seconds = int(frame_count / fps)
                                timestamp_str = self.seconds_to_timestamp(timestamp_seconds)
                                
                                detection = {
                                    'frame_number': frame_count,
                                    'timestamp': timestamp_str,
                                    'seconds': timestamp_seconds,
                                    'confidence': match['confidence'],
                                    'distance': match['distance'],
                                    'facial_area': match.get('facial_area', {})
                                }
                                
                                # Save detection frame if requested
                                if save_detection_frames and output_dir:
                                    frame_with_box = face_analyzer.draw_face_detection(
                                        frame,
                                        [match]
                                    )
                                    frame_path = os.path.join(
                                        output_dir,
                                        f"detection_{frame_count:06d}_{timestamp_str.replace(':', '-')}.jpg"
                                    )
                                    cv2.imwrite(frame_path, frame_with_box)
                                    detection['frame_image'] = frame_path
                                
                                detections.append(detection)
                                last_detection_frame = frame_count
                                break
                    
                    except Exception as e:
                        print(f"Error processing frame {frame_count}: {e}")
                
                frame_count += 1
            
            video.release()
        
        except Exception as e:
            print(f"Error processing video: {e}")
        
        return detections
