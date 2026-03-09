import cv2
import numpy as np
from deepface import DeepFace
import os
import warnings

warnings.filterwarnings('ignore')

class FaceAnalyzer:
    """
    Face detection and recognition using DeepFace
    DeepFace supports multiple backends: opencv, ssd, mtcnn, dlib, retinaface, mediapipe
    """
    
    def __init__(self, model_name='VGG-Face', detector_backend='retinaface', distance_metric='cosine'):
        """
        Initialize FaceAnalyzer with DeepFace
        
        Args:
            model_name: 'VGG-Face' (default), 'Facenet', 'Facenet512', 'OpenFace', 'DeepFace', 'DeepID', 'ArcFace', 'Dlib'
            detector_backend: 'retinaface' (default), 'opencv', 'mtcnn', 'dlib', 'ssd', 'mediapipe'
            distance_metric: 'cosine' (default), 'euclidean', 'euclidean_l2'
        """
        self.model_name = model_name
        self.detector_backend = detector_backend
        self.distance_metric = distance_metric
        self.models_loaded = False
        
        # Pre-load models for faster processing
        try:
            self._load_models()
        except Exception as e:
            print(f"Warning: Could not pre-load models: {e}")
    
    def _load_models(self):
        """Pre-load DeepFace models"""
        try:
            DeepFace.build_model(self.model_name)
            self.models_loaded = True
        except Exception as e:
            print(f"Error loading DeepFace models: {e}")
    
    def get_face_embedding(self, image_path):
        """
        Extract face embedding from image using DeepFace
        
        Args:
            image_path: Path to image file or numpy array
            
        Returns:
            Dictionary with embedding and face details or None if no face found
        """
        try:
            # Read image if path is provided
            if isinstance(image_path, str):
                if not os.path.exists(image_path):
                    print(f"Image not found: {image_path}")
                    return None
            
            # Extract embedding using DeepFace
            embedding_objs = DeepFace.represent(
                img_path=image_path,
                model_name=self.model_name,
                detector_backend=self.detector_backend,
                enforce_detection=True
            )
            
            if not embedding_objs or len(embedding_objs) == 0:
                return None
            
            # Return the first (largest) face
            face_data = embedding_objs[0]
            
            return {
                'embedding': np.array(face_data['embedding']),
                'facial_area': face_data.get('facial_area', {}),
                'confidence': 1.0  # DeepFace doesn't provide confidence for embedding
            }
        
        except Exception as e:
            print(f"Error getting face embedding from {image_path}: {e}")
            return None
    
    def detect_faces_in_frame(self, frame):
        """
        Detect faces in a frame using DeepFace
        
        Args:
            frame: OpenCV frame (BGR)
            
        Returns:
            List of dictionaries with face detections and embeddings
        """
        try:
            # Convert BGR to RGB for DeepFace
            frame_rgb = cv2.cvtColor(frame, cv2.COLOR_BGR2RGB)
            
            # Detect and extract embeddings
            detections = DeepFace.represent(
                img_path=frame_rgb,
                model_name=self.model_name,
                detector_backend=self.detector_backend,
                enforce_detection=False  # Don't fail if no face detected
            )
            
            return detections if detections else []
        
        except Exception as e:
            print(f"Error detecting faces: {e}")
            return []
    
    def verify_faces(self, frame, reference_embedding, threshold=0.5):
        """
        Verify if faces in frame match reference face
        
        Args:
            frame: OpenCV frame (BGR)
            reference_embedding: Reference face embedding
            threshold: Distance threshold for matching (lower is stricter)
            
        Returns:
            List of matches with confidence scores
        """
        try:
            detections = self.detect_faces_in_frame(frame)
            matches = []
            
            for detection in detections:
                face_embedding = np.array(detection['embedding'])
                
                # Calculate distance
                distance = self._calculate_distance(
                    reference_embedding,
                    face_embedding,
                    self.distance_metric
                )
                
                # Convert distance to confidence (0-1, where 1 is perfect match)
                confidence = 1 - (distance / 2.0)  # Normalize to 0-1 range
                
                # Check if match
                is_match = distance <= threshold
                
                if is_match or confidence > 0.5:  # Include borderline cases
                    matches.append({
                        'embedding': face_embedding,
                        'distance': distance,
                        'confidence': max(0, confidence),
                        'facial_area': detection.get('facial_area', {}),
                        'is_match': is_match
                    })
            
            return matches
        
        except Exception as e:
            print(f"Error verifying faces: {e}")
            return []
    
    def compare_embeddings(self, embedding1, embedding2, threshold=0.5):
        """
        Compare two face embeddings
        
        Args:
            embedding1: First embedding array
            embedding2: Second embedding array
            threshold: Distance threshold
            
        Returns:
            Tuple of (is_match, distance, confidence)
        """
        try:
            distance = self._calculate_distance(
                embedding1,
                embedding2,
                self.distance_metric
            )
            
            confidence = 1 - (distance / 2.0)
            is_match = distance <= threshold
            
            return is_match, distance, max(0, confidence)
        
        except Exception as e:
            print(f"Error comparing embeddings: {e}")
            return False, float('inf'), 0.0
    
    @staticmethod
    def _calculate_distance(embedding1, embedding2, metric='cosine'):
        """
        Calculate distance between two embeddings
        
        Args:
            embedding1: First embedding
            embedding2: Second embedding
            metric: 'cosine', 'euclidean', or 'euclidean_l2'
            
        Returns:
            Distance value
        """
        embedding1 = np.array(embedding1)
        embedding2 = np.array(embedding2)
        
        if metric == 'cosine':
            # Cosine distance
            from scipy.spatial.distance import cosine
            return cosine(embedding1, embedding2)
        
        elif metric == 'euclidean':
            # Euclidean distance
            return np.linalg.norm(embedding1 - embedding2)
        
        elif metric == 'euclidean_l2':
            # L2 normalized euclidean distance
            embedding1 = embedding1 / np.linalg.norm(embedding1)
            embedding2 = embedding2 / np.linalg.norm(embedding2)
            return np.linalg.norm(embedding1 - embedding2)
        
        else:
            return np.linalg.norm(embedding1 - embedding2)
    
    def extract_face_region(self, frame, facial_area):
        """
        Extract face region from frame
        
        Args:
            frame: OpenCV frame
            facial_area: Dictionary with x, y, w, h keys
            
        Returns:
            Cropped face image
        """
        try:
            x = facial_area.get('x', 0)
            y = facial_area.get('y', 0)
            w = facial_area.get('w', 0)
            h = facial_area.get('h', 0)
            
            if w > 0 and h > 0:
                face_img = frame[y:y+h, x:x+w]
                return face_img
        except Exception as e:
            print(f"Error extracting face region: {e}")
        
        return None
    
    def draw_face_detection(self, frame, detections, color=(0, 255, 0), thickness=2):
        """
        Draw face detection boxes on frame
        
        Args:
            frame: OpenCV frame
            detections: List of detection dictionaries
            color: Box color (BGR)
            thickness: Box thickness
            
        Returns:
            Frame with drawn detections
        """
        try:
            frame_copy = frame.copy()
            
            for detection in detections:
                facial_area = detection.get('facial_area', {})
                x = facial_area.get('x', 0)
                y = facial_area.get('y', 0)
                w = facial_area.get('w', 0)
                h = facial_area.get('h', 0)
                
                if w > 0 and h > 0:
                    # Draw rectangle
                    cv2.rectangle(frame_copy, (x, y), (x+w, y+h), color, thickness)
                    
                    # Add confidence text if available
                    confidence = detection.get('confidence', 0)
                    if confidence > 0:
                        text = f"Confidence: {confidence:.2f}"
                        cv2.putText(
                            frame_copy,
                            text,
                            (x, y-10),
                            cv2.FONT_HERSHEY_SIMPLEX,
                            0.5,
                            color,
                            2
                        )
            
            return frame_copy
        
        except Exception as e:
            print(f"Error drawing detections: {e}")
            return frame
