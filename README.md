# Smart Park AI - Parking Lot Analysis System

A Django application that uses OpenAI Vision API to analyze parking lot CCTV footage in real-time and identify available parking spaces.

## Features

- Real-time video analysis of parking lots
- Continuous monitoring with frame-by-frame analysis
- OpenAI Vision API integration for accurate space detection
- Live updates of available spaces and recommended spots
- Visual feedback with analyzed frames
- Support for both video file upload and direct path input

## Prerequisites

- Python 3.8+
- OpenAI API key
- OpenCV
- Django
- Django Channels

## Installation

1. Clone the repository:
```bash
git clone [repository-url]
cd parkingScanner
```

2. Install required packages:
```bash
pip install django channels daphne opencv-python openai python-dotenv
```

3. Create a `.env` file in the project root and add your OpenAI API key:
```
OPENAI_API_KEY=your_api_key_here
```

## Running the Application

1. Start the server:
```bash
daphne -b 0.0.0.0 -p 8000 parkingScanner.asgi:application
```

2. Open a web browser and navigate to:
```
http://localhost:8000
```

## Usage

1. On the homepage, you have two options:
   - Upload a video file directly
   - Provide a path to an existing video file

2. After submitting, you'll be taken to the analysis page where you can see:
   - Live video frames being analyzed
   - Number of available parking spaces
   - Recommended parking spots
   - Frame information and FPS
   - Last update timestamp

3. The system will continuously analyze the video, looping back to the start when it reaches the end.

## Configuration

- Frame analysis interval can be adjusted in `scanner/consumers.py` by modifying the `frame_count % 240` value
- Video processing delay can be adjusted by modifying the `asyncio.sleep(0.1)` value

## Technical Details

- Uses Django Channels for WebSocket communication
- OpenAI Vision API for parking space detection
- OpenCV for video frame processing
- Asynchronous processing for smooth performance
- Base64 encoding for frame transmission
- Temporary file handling for frame analysis

## Note

Make sure your OpenAI API key has access to the Vision API and sufficient credits for continuous analysis.
