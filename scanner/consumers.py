import json
import asyncio
import cv2
import base64
import os
import tempfile
from channels.generic.websocket import AsyncWebsocketConsumer
from channels.layers import get_channel_layer
from asgiref.sync import sync_to_async
from openai import OpenAI
from dotenv import load_dotenv

# Load environment variables
load_dotenv()

# Initialize OpenAI client
client = OpenAI(api_key=os.getenv('OPENAI_API_KEY'))

class ParkingAnalysisConsumer(AsyncWebsocketConsumer):
    async def connect(self):
        # Accept the WebSocket connection
        await self.accept()
        # Store the video processing task
        self.video_task = None
        
    async def disconnect(self, close_code):
        # Cancel the video processing if it's running
        if self.video_task:
            self.video_task.cancel()
            try:
                await self.video_task
            except asyncio.CancelledError:
                pass

    async def receive(self, text_data):
        data = json.loads(text_data)
        if data['type'] == 'start_analysis':
            video_path = data['video_path']
            # Start the video processing in a background task
            self.video_task = asyncio.create_task(self.process_video(video_path))

    @sync_to_async
    def analyze_frame(self, frame_path):
        """Analyze a single frame using OpenAI Vision API"""
        try:
            with open(frame_path, "rb") as image_file:
                image_base64 = base64.b64encode(image_file.read()).decode('utf-8')
                
                response = client.chat.completions.create(
                    model="gpt-4o-mini",
                    messages=[
                        {
                            "role": "system",
                            "content": "Analyze parking lot images and identify available spaces."
                        },
                        {
                            "role": "user",
                            "content": [
                                {
                                    "type": "text",
                                    "text": "Analyze this parking lot image and respond in this exact format:\n1. Available spaces: [number]\n2. Recommended spots:\n- [spot description]\n- [spot description]\n..."
                                },
                                {
                                    "type": "image_url",
                                    "image_url": {
                                        "url": f"data:image/jpeg;base64,{image_base64}"
                                    }
                                }
                            ]
                        }
                    ],
                    max_tokens=300
                )
                return response.choices[0].message.content
        except Exception as e:
            print(f"Error analyzing frame: {str(e)}")
            return None

    async def process_video(self, video_path):
        """Process video frames continuously"""
        cap = cv2.VideoCapture(video_path)
        frame_count = 0
        fps = int(cap.get(cv2.CAP_PROP_FPS))
        
        while True:  # Continuous loop
            try:
                ret, frame = cap.read()
                if not ret:
                    # If we reach the end of the video, start over
                    cap.set(cv2.CAP_PROP_POS_FRAMES, 0)
                    frame_count = 0  # Reset frame counter
                    print("Reached end of video, restarting...")  # Debug log
                    continue
                
                # Analyze every 240th frame (every 8 seconds at 30fps)
                if frame_count % 240 == 0:
                    print(f"Processing frame {frame_count}")  # Debug log
                    # Save frame temporarily
                    frame_path = os.path.join(tempfile.gettempdir(), 'current_frame.jpg')
                    cv2.imwrite(frame_path, frame)
                    
                    # Analyze frame
                    analysis = await self.analyze_frame(frame_path)
                    
                    if analysis:
                        try:
                            print(f"Received analysis: {analysis}")  # Debug log
                            
                            # Parse the structured response
                            lines = [line.strip() for line in analysis.split('\n') if line.strip()]
                            available_spaces = 0
                            recommended_spots = []
                            
                            try:
                                # Find the available spaces number
                                for line in lines:
                                    if 'Available spaces:' in line:
                                        number_str = ''.join(filter(str.isdigit, line))
                                        if number_str:
                                            available_spaces = int(number_str)
                                        else:
                                            print(f"No number found in line: {line}")
                                        break
                                
                                # Collect recommended spots
                                collecting_spots = False
                                for line in lines:
                                    if 'Recommended spots:' in line:
                                        collecting_spots = True
                                        continue
                                    if collecting_spots and line.startswith('-'):
                                        spot = line[1:].strip()  # Remove the dash and whitespace
                                        if spot:
                                            recommended_spots.append(spot)
                            
                            except Exception as e:
                                print(f"Error during parsing: {str(e)}")
                                print(f"Line being processed: {line}")
                            
                            # Convert the current frame to base64 for display
                            _, buffer = cv2.imencode('.jpg', frame)
                            frame_base64 = base64.b64encode(buffer).decode('utf-8')
                            
                            # Send results to the client
                            await self.send(json.dumps({
                                'type': 'analysis_update',
                                'available_spaces': available_spaces,
                                'recommended_spots': recommended_spots,
                                'timestamp': str(asyncio.get_event_loop().time()),
                                'frame': frame_base64,
                                'frame_count': frame_count,
                                'fps': fps
                            }))
                        except Exception as e:
                            print(f"Error parsing analysis: {str(e)}")
                    
                    # Clean up temporary file
                    if os.path.exists(frame_path):
                        os.remove(frame_path)
                
                frame_count += 1
                
                # Add a small delay to prevent overwhelming the system
                await asyncio.sleep(0.1)  # Reduced delay for more responsive updates
                
            except Exception as e:
                print(f"Error in video processing: {str(e)}")
                await asyncio.sleep(5)  # Wait before retrying
                continue
        
        cap.release()
