# Face Finder – AI Face Recognition Web Application

## 📌 Project Overview
Face Finder is a web-based application that allows users to upload images or videos and automatically detect and recognize faces using artificial intelligence.

The system analyzes uploaded media and identifies faces using deep learning. The project uses the DeepFace model for face recognition and OpenCV for image and video processing.

The application is built using Python and Flask for the backend, and HTML, CSS, and JavaScript for the frontend.

---

## 🚀 Features

- Upload images for face recognition
- Upload videos and detect faces frame by frame
- AI-powered face analysis using DeepFace
- Clean and responsive web interface
- Modular backend architecture
- Automatic storage of uploaded files

---

## 🛠️ Technologies Used

### Backend
- Python
- Flask

### AI / Computer Vision
- DeepFace
- OpenCV

### Frontend
- HTML
- CSS
- JavaScript

### Version Control
- Git
- GitHub

---

## 📂 Project Structure
```
Face-Finder/
│
├── modules/
│   ├── face_analyzer.py
│   ├── video_downloader.py
│   └── video_processor.py
│
├── static/
│   ├── css/
│   │   └── styles.css
│   │
│   ├── js/
│   │   └── main.js
│   │
│   └── uploads/
│
├── templates/
│   └── index.html
│
├── app.py
│
└── requirements.txt
```
---

## 📄 Module Explanation

### app.py
Main Flask application file.

Responsibilities:
- Runs the web server
- Handles file uploads
- Connects frontend with backend modules
- Sends uploaded files to face recognition modules
- Displays processed results

---

### face_analyzer.py
Handles face detection and recognition.

Main tasks:
- Detect faces in images
- Analyze faces using the DeepFace model
- Return recognition results

---

### video_processor.py
Processes uploaded videos.

Responsibilities:
- Extract frames from the video
- Perform face detection on each frame
- Analyze faces using AI
- Generate processed results

---

### video_downloader.py
Handles downloading videos from external sources.

Responsibilities:
- Download video files
- Store them in the uploads directory
- Send them for processing

---

## 📁 Static Folder
The static folder contains all frontend resources and uploaded files.

### CSS
`static/css/styles.css`
- Handles UI styling
- Layout design

### JavaScript
`static/js/main.js`
- Handles user interactions
- Upload functionality
- Frontend logic

### Uploads
`static/uploads/`

Stores:
- Uploaded images
- Uploaded videos
- Processed results

---

## 📄 Templates

### index.html

Main webpage of the application.

Contains:
- Upload form
- User interface
- Result display section

Uses Flask templating.

---

## ⚙️ Installation Guide

### 1️⃣ Clone the Repository

```
git clone https://github.com/yourusername/face-finder.git
cd face-finder
```
### 2️⃣ Install Required Libraries
```
pip install -r requirements.txt
```
Required libraries include:
- Flask
- DeepFace
- OpenCV
- NumPy

### 3️⃣ Run the Application
```
python app.py
```
- The server will start at:
http://127.0.0.1:5000
- Open the link in your browser.

---
### 💻 How the System Works

- User uploads an image or video
- File is saved inside static/uploads
- Backend sends the file for analysis
- AI detects and recognizes faces
- Results are returned and displayed on the webpage
---
### 🔮 Future Improvements

- Real-time webcam face recognition
- Face database matching
- Multiple face comparison
- Emotion detection
- Cloud deployment
- Mobile-friendly UI
- CCTV-Based Person Identification
---
##  Conclusion

The Face Finder project demonstrates how artificial intelligence and computer vision can be used to detect and recognize faces from images and videos. By using DeepFace and OpenCV with a Flask-based web application, the system provides an efficient way to analyze uploaded media. With future improvements like real-time recognition and CCTV integration, the system can be expanded into a powerful smart surveillance solution.
