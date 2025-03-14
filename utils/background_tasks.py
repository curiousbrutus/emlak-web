"""Background task management utilities."""

import time
import threading
import uuid
import traceback
from collections import defaultdict

# Global task status dictionary
_task_status = {}
_task_lock = threading.Lock()

class BackgroundTaskManager:
    """Manages background tasks and their statuses."""
    
    def start_task(self, func, task_args=None, task_kwargs=None, task_name=None):
        """
        Start a background task.
        
        Args:
            func: Function to run in background
            task_args: Tuple of positional arguments to pass to the function
            task_kwargs: Dictionary of keyword arguments to pass to the function
            task_name: Optional name for the task
            
        Returns:
            task_id: Unique identifier for the task
        """
        task_id = str(uuid.uuid4())
        task_args = task_args or tuple()
        task_kwargs = task_kwargs or {}
        
        # Initialize task status
        with _task_lock:
            _task_status[task_id] = {
                'status': 'starting',
                'progress': 0,
                'result': None,
                'error': None,
                'started_at': time.time(),
                'completed_at': None,
                'name': task_name,
                'message': 'Görev başlatılıyor...'
            }
        
        # Create and start thread
        thread = threading.Thread(
            target=self._run_task,
            args=(task_id, func, task_args, task_kwargs),
            daemon=True
        )
        thread.start()
        
        return task_id
    
    def _run_task(self, task_id, func, args, kwargs):
        """Internal function to run a task and update its status."""
        try:
            # Update status to running
            self.update_task_status(task_id, status='running', progress=5, 
                                   message='Görev çalışıyor...')
            
            # Run the function
            result = func(*args, **kwargs, task_id=task_id)
            
            # Update status to completed
            with _task_lock:
                _task_status[task_id]['status'] = 'completed'
                _task_status[task_id]['result'] = result
                _task_status[task_id]['progress'] = 100
                _task_status[task_id]['completed_at'] = time.time()
                _task_status[task_id]['message'] = 'Görev tamamlandı!'
                
        except Exception as e:
            # Update status to failed
            error_details = traceback.format_exc()
            with _task_lock:
                _task_status[task_id]['status'] = 'failed'
                _task_status[task_id]['error'] = str(e)
                _task_status[task_id]['error_details'] = error_details
                _task_status[task_id]['completed_at'] = time.time()
                _task_status[task_id]['message'] = f'Hata: {str(e)}'
    
    def get_task_status(self, task_id):
        """Get the current status of a task."""
        with _task_lock:
            return _task_status.get(task_id)
    
    def update_task_status(self, task_id, **kwargs):
        """Update the status of a task."""
        with _task_lock:
            if task_id in _task_status:
                for key, value in kwargs.items():
                    _task_status[task_id][key] = value
    
    def cleanup_completed_tasks(self, max_age_seconds=3600):
        """Remove completed tasks older than max_age_seconds."""
        current_time = time.time()
        with _task_lock:
            task_ids = list(_task_status.keys())
            for task_id in task_ids:
                task = _task_status[task_id]
                if task['status'] in ('completed', 'failed'):
                    if task['completed_at'] and (current_time - task['completed_at']) > max_age_seconds:
                        del _task_status[task_id]

def generate_video_in_background(images, audio_path, transition_type, fps, quality, task_id=None):
    """
    Generate video in background thread with progress updates.
    
    Args:
        images: List of images for the video
        audio_path: Path to audio file
        transition_type: Type of transition effect
        fps: Frames per second
        quality: Video quality (normal/high)
        task_id: ID of the background task
        
    Returns:
        Path to the generated video
    """
    task_manager = BackgroundTaskManager()
    
    try:
        # Import here to avoid circular imports
        from modules.video.video_generation import generate_video
        
        # Update task status at key points
        task_manager.update_task_status(
            task_id, 
            status='preparing', 
            progress=10,
            message='Video oluşturma hazırlıkları yapılıyor...'
        )
        
        # Create a wrapper function to update progress
        def progress_callback(stage, percent, message=""):
            task_manager.update_task_status(
                task_id,
                status=stage,
                progress=percent,
                message=message
            )
        
        # Process images
        task_manager.update_task_status(
            task_id, 
            status='processing_images', 
            progress=20,
            message=f'{len(images)} görüntü işleniyor...'
        )
        
        # Generate video
        task_manager.update_task_status(
            task_id, 
            status='generating_video', 
            progress=40,
            message='Video oluşturuluyor, lütfen bekleyin...'
        )
        
        # Actual video generation - the function itself now reports progress
        video_path = generate_video(images, audio_path, transition_type, fps, quality)
        
        # Final update before completion
        task_manager.update_task_status(
            task_id, 
            status='finalizing', 
            progress=95,
            message='Video tamamlanıyor...'
        )
        
        # Wait a moment to ensure UI updates correctly
        time.sleep(1)
        
        return video_path
        
    except Exception as e:
        # Make sure error is properly captured
        task_manager.update_task_status(
            task_id, 
            status='failed', 
            error=str(e),
            error_details=traceback.format_exc()
        )
        raise
