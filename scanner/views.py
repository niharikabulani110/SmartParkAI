from django.shortcuts import render, redirect
from django.views.decorators.http import require_http_methods
from django.core.files.storage import default_storage
from django.conf import settings
import os

@require_http_methods(["GET", "POST"])
def upload_video(request):
    """Handle video upload or video path input"""
    if request.method == "POST":
        video_path = None
        
        if 'video' in request.FILES:
            # Handle file upload
            video = request.FILES['video']
            video_path = default_storage.save(
                'parking_video.mp4',
                video
            )
            video_path = os.path.join(settings.MEDIA_ROOT, video_path)
        elif 'video_path' in request.POST:
            # Handle direct path input
            video_path = request.POST['video_path']
            if not os.path.exists(video_path):
                return render(request, 'scanner/upload.html', 
                            {'error': 'Video file not found at specified path'})
        
        if video_path:
            return redirect('analyze', video_path=video_path)
        
        return render(request, 'scanner/upload.html', 
                     {'error': 'Please provide a video file or path'})
    
    return render(request, 'scanner/upload.html')

@require_http_methods(["GET"])
def analyze_video(request, video_path):
    """Render the analysis page"""
    if not os.path.exists(video_path):
        return redirect('upload')
    
    return render(request, 'scanner/analysis.html', {
        'video_path': video_path
    })
