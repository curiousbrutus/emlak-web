"""Background task management utilities."""

import time
import threading
import traceback
import gc
import os
import tempfile
import numpy as np
import streamlit as st
import logging
from datetime import datetime
from concurrent.futures import ThreadPoolExecutor, TimeoutError
from PIL import Image

# These imports might be causing circular dependencies - let's fix them
from modules.video.video_generation import generate_video

class BackgroundTaskManager:
    """Manages background tasks and their statuses."""
    
    def __init__(self):
        """Initialize the background task manager"""
        self.tasks = {}
        # Reduce thread pool size to prevent memory issues
        self.executor = ThreadPoolExecutor(max_workers=1)
        self._lock = threading.Lock()
        
    def start_task(self, task_function, task_args=None, task_name="task", timeout=3600):
        """
        Start a background task with timeout
        
        Args:
            task_function: The function to execute in background
            task_args: Arguments to pass to the function
            task_name: Name of the task
            timeout: Timeout for the task in seconds
            
        Returns:
            Task ID
        """
        if task_args is None:
            task_args = ()
            
        # Generate a task ID
        task_id = f"{task_name}_{int(time.time())}"
        
        # Create a task status dictionary
        with self._lock:
            self.tasks[task_id] = {
                "status": "starting",
                "start_time": datetime.now(),
                "progress": 0,
                "result": None,
                "error": None,
                "error_details": None,
                "message": "İşlem başlatılıyor...",
                "timeout": timeout
            }
        
        # Submit task with timeout handling
        future = self.executor.submit(self._run_task, task_function, task_args, task_id)
        
        # Add timeout handling
        def timeout_handler():
            time.sleep(timeout)
            if not future.done():
                with self._lock:
                    if task_id in self.tasks and self.tasks[task_id]["status"] == "running":
                        self.tasks[task_id]["status"] = "failed"
                        self.tasks[task_id]["error"] = "İşlem zaman aşımına uğradı"
                        self.tasks[task_id]["message"] = "Zaman aşımı hatası!"
                future.cancel()
        
        threading.Thread(target=timeout_handler, daemon=True).start()
        return task_id
        
    def _run_task(self, task_function, task_args, task_id):
        """
        Execute the task and update its status
        
        Args:
            task_function: Function to execute
            task_args: Arguments for the function
            task_id: Task ID
        """
        try:
            # Force garbage collection before starting
            gc.collect()
            
            # Update status to running
            with self._lock:
                self.tasks[task_id]["status"] = "running"
                self.tasks[task_id]["message"] = "İşlem çalışıyor..."
            
            # Create a progress callback
            def progress_callback(progress_percentage, message=None):
                with self._lock:
                    if task_id in self.tasks:
                        # Ensure progress is between 0-100
                        self.tasks[task_id]["progress"] = min(100, max(0, progress_percentage * 100))
                        if message:
                            self.tasks[task_id]["message"] = message
                            print(f"Progress update: {message} ({progress_percentage:.1%})")
            
            # Run the task with timeout handling
            max_duration = 1800  # 30 minutes max
            task_args_with_callback = task_args + (progress_callback,)
                
            # Execute task with progress callback
            result = task_function(*task_args_with_callback)
            
            # Task completed successfully
            with self._lock:
                if task_id in self.tasks:
                    self.tasks[task_id]["status"] = "completed"
                    self.tasks[task_id]["result"] = result
                    self.tasks[task_id]["progress"] = 100
                    self.tasks[task_id]["message"] = "İşlem başarıyla tamamlandı."
            
            # Force garbage collection to free memory
            gc.collect()
            
        except Exception as e:
            # Task failed
            error_details = traceback.format_exc()
            print(f"Task {task_id} failed: {str(e)}")
            print(error_details)
            
            with self._lock:
                if task_id in self.tasks:
                    self.tasks[task_id]["status"] = "failed"
                    self.tasks[task_id]["error"] = str(e)
                    self.tasks[task_id]["error_details"] = error_details
                    self.tasks[task_id]["message"] = f"Hata: {str(e)}"
            
            # Force garbage collection on error too
            gc.collect()
    
    def get_task_status(self, task_id):
        """
        Get the current status of a task
        
        Args:
            task_id: The task ID
            
        Returns:
            Task status dictionary or None if task doesn't exist
        """
        with self._lock:
            return self.tasks.get(task_id)
    
    def cancel_task(self, task_id):
        """
        Cancel a running task
        
        Args:
            task_id: The task ID
            
        Returns:
            True if task was canceled, False otherwise
        """
        with self._lock:
            if task_id in self.tasks and self.tasks[task_id]["status"] == "running":
                # We can't actually stop the thread, but we can mark it as canceled
                self.tasks[task_id]["status"] = "canceled"
                return True
        return False
    
    def cleanup_completed_tasks(self, max_age_seconds=3600):
        """
        Remove old completed tasks from memory
        
        Args:
            max_age_seconds: Maximum age of completed tasks to keep
        """
        current_time = datetime.now()
        with self._lock:
            tasks_to_remove = []
            
            for task_id, task_data in self.tasks.items():
                if task_data["status"] in ["completed", "failed", "canceled"]:
                    task_age = current_time - task_data["start_time"]
                    if task_age.total_seconds() > max_age_seconds:
                        tasks_to_remove.append(task_id)
            
            for task_id in tasks_to_remove:
                del self.tasks[task_id]


def generate_video_in_background(images, audio_path, transition_type, fps, quality, callback=None):
    """
    Generate video in a background thread with status updates
    """
    try:
        # Create a proper temporary directory string
        temp_dir = os.path.join(tempfile.gettempdir(), f"emlak_video_{int(time.time())}")
        os.makedirs(temp_dir, exist_ok=True)
        
        # Update status
        if callback:
            callback({"status": "preparing", "progress": 10, "message": "Geçici dosyalar hazırlanıyor..."})
        
        # ...rest of the function implementation...
        
    except Exception as e:
        # Log the error
        logging.error(f"Video generation error: {str(e)}")
        if callback:
            callback({"status": "failed", "error": str(e), "error_details": traceback.format_exc()})
        raise
