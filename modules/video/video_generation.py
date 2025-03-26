"""Video generation and effects functions.""" 

import os
import tempfile
import cv2
import numpy as np
import streamlit as st
from PIL import Image
import traceback
import gc
from moviepy.editor import ImageSequenceClip, AudioFileClip, VideoFileClip
import time

# Import new modules - ensure they exist
try:
    from modules.video.advanced_stabilization import stabilize_video_sequence
except ImportError:
    # Fallback if module doesn't exist
    def stabilize_video_sequence(frames, smoothing_window=30):
        return frames

# Add to imports
from modules.ai.vertex_services import VertexAIService

def update_progress(progress_callback, percentage, message):
    """Safely update progress with valid percentage"""
    if progress_callback:
        # Ensure percentage is between 0-1
        safe_percentage = max(0.0, min(1.0, percentage))
        progress_callback(safe_percentage, message)
        print(f"Progress: {message} ({safe_percentage:.1%})")

def create_frame_effect(image, n_frames, effect_type="zoom", zoom_in=True, pan_direction="right"):
    """Create effect frames for a single image"""
    # First process image with Vertex AI
    try:
        vertex_service = VertexAIService()
        processed_image = vertex_service.process_image(image)
        img_array = np.array(processed_image)
    except Exception as e:
        print(f"Falling back to local processing: {e}")
        # Fall back to original processing
        if isinstance(image, Image.Image):
            img_array = np.array(image)
        else:
            img_array = image.copy()
    
    # Ensure we're working with color images
    if len(img_array.shape) == 2:  # Grayscale
        img_array = cv2.cvtColor(img_array, cv2.COLOR_GRAY2RGB)
    elif len(img_array.shape) == 3 and img_array.shape[2] == 1:  # Single channel
        img_array = cv2.cvtColor(img_array, cv2.COLOR_GRAY2RGB)
    elif len(img_array.shape) == 3 and img_array.shape[2] == 4:  # RGBA
        img_array = cv2.cvtColor(img_array, cv2.COLOR_RGBA2RGB)
        
    h, w = img_array.shape[:2]
    frames = []
    
    if effect_type == "zoom":
        # Use smooth easing function for zoom
        zoom_range = np.array([1 - np.cos(x * np.pi / 2) for x in np.linspace(0, 1, n_frames)])
        zoom_range = 1.0 + (0.3 if zoom_in else -0.3) * zoom_range
        
        for factor in zoom_range:
            new_h, new_w = int(h / factor), int(w / factor)
            y1, x1 = (h - new_h) // 2, (w - new_w) // 2
            y2, x2 = y1 + new_h, x1 + new_w
            
            if 0 <= y1 < y2 <= h and 0 <= x1 < x2 <= w:
                # Apply Gaussian blur for smoother transitions while preserving color
                cropped = img_array[y1:y2, x1:x2]
                if factor != 1.0:
                    blur_size = int(max(1, min(3, abs(1-factor) * 5)))
                    cropped = cv2.GaussianBlur(cropped, (blur_size*2+1, blur_size*2+1), 0)
                frame = cv2.resize(cropped, (w, h), interpolation=cv2.INTER_LANCZOS4)
                frames.append(frame)
    
    elif effect_type == "pan":
        # Use smooth easing for pan effect
        max_shift = w // 4 if pan_direction in ["right", "left"] else h // 4
        shifts = np.array([1 - np.cos(x * np.pi / 2) for x in np.linspace(0, 1, n_frames)])
        shifts = shifts * max_shift
        
        if pan_direction in ["right", "down"]:
            shifts = shifts[::-1]
            
        for shift in shifts:
            shift = int(shift)
            M = np.float32([[1, 0, -shift], [0, 1, 0]]) if pan_direction in ["right", "left"] else np.float32([[1, 0, 0], [0, 1, -shift]])
            
            # Apply affine transform while preserving colors
            frame = cv2.warpAffine(img_array, M, (w, h), 
                                 flags=cv2.INTER_LANCZOS4,
                                 borderMode=cv2.BORDER_REFLECT)
            frames.append(frame)
    
    # Ensure all frames are in RGB format
    return [cv2.cvtColor(frame, cv2.COLOR_BGR2RGB) if frame.shape[-1] == 3 else frame for frame in frames]

def apply_cinematic_effects(frames, effect_type="cinematic"):
    """
    Apply cinematic color grading and visual effects
    
    Args:
        frames: List of frames
        effect_type: Type of cinematic effect (cinematic, warm, cool, vintage)
        
    Returns:
        List of processed frames
    """
    processed_frames = []
    
    # Define color grading LUTs for different styles
    lut_intensity = 0.7  # Intensity of effect (0-1)
    
    for frame in frames:
        if effect_type == "warm":
            # Warm cinematic look
            frame_lab = cv2.cvtColor(frame, cv2.COLOR_BGR2LAB)
            l, a, b = cv2.split(frame_lab)
            # Boost red/yellow tones
            a = cv2.add(a, 10)
            b = cv2.add(b, 15)
            frame_lab = cv2.merge([l, a, b])
            frame = cv2.cvtColor(frame_lab, cv2.COLOR_LAB2BGR)
            
            # Add slight vignette
            frame = apply_vignette(frame, 0.3)
            
        elif effect_type == "cool":
            # Cool cinematic look
            frame_lab = cv2.cvtColor(frame, cv2.COLOR_BGR2LAB)
            l, a, b = cv2.split(frame_lab)
            # Boost cool tones
            a = cv2.subtract(a, 10)
            b = cv2.subtract(b, 10)
            frame_lab = cv2.merge([l, a, b])
            frame = cv2.cvtColor(frame_lab, cv2.COLOR_LAB2BGR)
            
        elif effect_type == "vintage":
            # Vintage look
            frame = apply_vintage_effect(frame)
            
        else:  # Default cinematic
            # Standard cinematic grade (slight contrast boost, richer shadows)
            frame = apply_cinematic_grade(frame)
            
        processed_frames.append(frame)
        
    return processed_frames

def apply_vignette(image, intensity=0.5):
    """Apply a vignette effect to an image"""
    height, width = image.shape[:2]
    
    # Create a radial gradient mask
    x = np.linspace(-1, 1, width)
    y = np.linspace(-1, 1, height)
    x_grid, y_grid = np.meshgrid(x, y)
    
    # Calculate radial distance from center
    radius = np.sqrt(x_grid**2 + y_grid**2)
    
    # Create vignette mask
    mask = 1 - np.clip(radius - 0.5, 0, 1) * intensity * 1.5
    mask = mask.reshape(height, width, 1)
    
    # Apply mask to image
    vignette = image * mask
    
    return vignette.astype(np.uint8)

def apply_cinematic_grade(image):
    """Apply basic cinematic color grading"""
    # Convert to float for processing
    img_float = image.astype(np.float32) / 255.0
    
    # Lift shadows slightly
    shadows = 0.05
    img_float = img_float * (1 - shadows) + shadows
    
    # Increase contrast with S-curve
    img_float = 0.5 + 1.2 * (img_float - 0.5)
    
    # Boost saturation slightly
    hsv = cv2.cvtColor(np.clip(img_float, 0, 1).astype(np.float32), cv2.COLOR_BGR2HSV)
    h, s, v = cv2.split(hsv)
    s = s * 1.1  # Boost saturation by 10%
    s = np.clip(s, 0, 1)
    hsv = cv2.merge([h, s, v])
    
    # Convert back to BGR
    img_graded = cv2.cvtColor(hsv, cv2.COLOR_HSV2BGR)
    
    # Convert back to uint8
    img_graded = np.clip(img_graded * 255, 0, 255).astype(np.uint8)
    
    return img_graded

def apply_vintage_effect(image):
    """Apply a vintage film effect"""
    # Create sepia tone effect
    sepia = np.array([[0.393, 0.769, 0.189],
                     [0.349, 0.686, 0.168],
                     [0.272, 0.534, 0.131]])
                     
    # Apply sepia transformation
    sepia_img = cv2.transform(image, sepia)
    
    # Add noise to simulate film grain
    noise = np.random.normal(0, 5, image.shape).astype(np.uint8)
    vintage = cv2.add(sepia_img, noise)
    
    # Add slight vignette
    vintage = apply_vignette(vintage, 0.4)
    
    return vintage

def optimize_image_for_video(image, target_width, target_height):
    """
    Optimize an image for video processing to reduce memory usage
    
    Args:
        image: PIL Image
        target_width: Desired width
        target_height: Desired height
        
    Returns:
        Optimized numpy array in BGR format
    """
    try:
        # Convert PIL to numpy if needed
        if isinstance(image, Image.Image):
            # Resize image to target dimensions
            image = image.resize((target_width, target_height), Image.LANCZOS)
            
            # Convert to RGB if in another mode
            if image.mode != 'RGB':
                image = image.convert('RGB')
                
            # Convert to numpy array
            img_array = np.array(image)
            
            # Convert RGB to BGR for OpenCV
            img_array = cv2.cvtColor(img_array, cv2.COLOR_RGB2BGR)
        else:
            # Already numpy array, just resize
            img_array = cv2.resize(image, (target_width, target_height))
            
            # Ensure BGR format
            if len(img_array.shape) == 3 and img_array.shape[2] == 4:
                img_array = cv2.cvtColor(img_array, cv2.COLOR_RGBA2BGR)
            elif len(img_array.shape) == 2:
                img_array = cv2.cvtColor(img_array, cv2.COLOR_GRAY2BGR)
        
        return img_array
    except Exception as e:
        print(f"Image optimization error: {e}")
        traceback.print_exc()
        
        # Fallback: create a blank image with text
        blank = np.ones((target_height, target_width, 3), dtype=np.uint8) * 128
        cv2.putText(blank, "Image Error", (50, target_height//2), 
                  cv2.FONT_HERSHEY_SIMPLEX, 1, (0, 0, 255), 2)
        return blank

def generate_video(images, audio_path, transition_type, fps, quality, temp_dir, final_path, progress_callback=None):
    """Generate video with progress tracking"""
    try:
        # Add debug logging
        print(f"Starting video generation with {len(images)} images")
        print(f"Transition type: {transition_type}")
        
        work_dir = os.path.join(temp_dir, f'video_work_{time.strftime("%Y%m%d-%H%M%S")}')
        os.makedirs(work_dir, exist_ok=True)

        def update_progress(percentage, message):
            if progress_callback:
                progress_callback(percentage, message)
                print(f"Progress: {message} ({percentage:.1%})")

        update_progress(0.01, "Video oluşturma başlatılıyor...")

        # Set video parameters based on quality
        target_size = (1920, 1080) if quality == "high" else (1280, 720)
        bitrate = "4000k" if quality == "high" else "2000k"

        # Process and collect all frames
        all_frames = []
        total_images = len(images)
        
        for i, img in enumerate(images):
            # Process image
            optimized = optimize_image_for_video(img, target_size[0], target_size[1])
            
            # Generate effect frames for this image
            frames = create_frame_effect(
                optimized,
                n_frames=int(fps * 2.5),  # 2.5 seconds per image
                effect_type=transition_type
            )
            
            if frames:
                all_frames.extend(frames)
            
            update_progress(0.4 * (i / total_images), f"Görüntü hazırlanıyor {i+1}/{total_images}...")
            
            if i % 3 == 0:
                optimize_memory_usage()

        # Validate frames
        if not all_frames:
            print("No frames were generated!")  # Debug log
            raise ValueError("No valid frames were generated!")
            
        print(f"Total frames generated: {len(all_frames)}")  # Debug log

        update_progress(0.6, "Video oluşturuluyor...")

        # Create video clip
        clip = ImageSequenceClip(all_frames, fps=fps)
        
        # Add audio if available
        if os.path.exists(audio_path):
            update_progress(0.8, "Ses ekleniyor...")
            audio = AudioFileClip(audio_path)
            clip = clip.set_audio(audio)
        
        # Write final video
        update_progress(0.9, "Video kaydediliyor...")
        clip.write_videofile(
            final_path,
            codec="libx264",
            audio_codec="aac",
            bitrate=bitrate,
            fps=fps,
            threads=2,
            logger=None
        )
        
        # Cleanup
        update_progress(0.95, "Geçici dosyalar temizleniyor...")
        try:
            clip.close()
            if os.path.exists(audio_path):
                audio.close()
            import shutil
            shutil.rmtree(work_dir)
        except:
            pass
        
        update_progress(1.0, "Video oluşturma tamamlandı!")
        return final_path

    except Exception as e:
        print(f"Video generation error: {str(e)}")
        traceback.print_exc()
        if progress_callback:
            progress_callback(0, f"Hata: {str(e)}")
        raise

def generate_video_with_ffmpeg(images, audio_path, fps=30, quality="normal", progress_callback=None):
    """
    Fallback method to generate video using FFmpeg directly via moviepy
    
    Args:
        images: List of PIL images
        audio_path: Path to audio file
        fps: Frames per second
        quality: Video quality (normal/high)
        progress_callback: Callback for progress reporting
        
    Returns:
        Path to generated video
    """
    from moviepy.editor import ImageSequenceClip, AudioFileClip
    import tempfile
    import os
    import numpy as np
    
    # Progress tracking
    progress_text = st.empty()
    progress_bar = st.progress(0.20)  # Start at 20%
    
    def update_progress(percent, message):
        if progress_callback:
            progress_callback(percent, message)
        progress_bar.progress(percent)
        progress_text.text(message)
    
    # Create temp directory
    temp_dir = tempfile.mkdtemp()
    final_path = os.path.join(temp_dir, "final_video.mp4")
    
    # Convert all images to numpy arrays
    if quality == "high":
        target_size = (1920, 1080)
        bitrate = "4000k"
    else:
        target_size = (1280, 720)
        bitrate = "2000k"
    
    # Process images
    update_progress(0.30, "Görüntüler hazırlanıyor... (30%)")
    
    # Process images with better memory management
    frames = []
    for i, img in enumerate(images):
        # Update progress: 30% to 60% for image processing
        current_progress = 0.30 + (0.30 * (i / len(images)))
        remaining_percent = 100 - int(current_progress * 100)
        update_progress(
            current_progress, 
            f"Görüntü hazırlanıyor {i+1}/{len(images)}... (Kalan: %{remaining_percent})"
        )
        
        try:
            if isinstance(img, Image.Image):
                img = img.resize(target_size, Image.LANCZOS)
                img_array = np.array(img.convert('RGB'))
                frames.append(img_array)
            else:
                # Already numpy array
                img_array = cv2.resize(img, target_size)
                if len(img_array.shape) == 2:
                    img_array = cv2.cvtColor(img_array, cv2.COLOR_GRAY2RGB)
                elif img_array.shape[2] == 4:
                    img_array = cv2.cvtColor(img_array, cv2.COLOR_RGBA2RGB)
                frames.append(img_array)
                
            # Force memory cleanup after each image
            if i % 2 == 0:
                optimize_memory_usage()
                
        except Exception as e:
            print(f"Error processing image {i}: {str(e)}")
            # Continue with next image
    
    # Create video clip
    update_progress(0.60, "Video klip hazırlanıyor... (60%)")
    clip = ImageSequenceClip(frames, fps=fps)
    
    # Add audio
    update_progress(0.70, "Ses ekleniyor... (70%)")
    
    # Check audio file existence
    if not os.path.exists(audio_path):
        update_progress(0.70, "Ses dosyası bulunamadı! Sessiz video oluşturuluyor...")
        # Create a silent video
        silent_path = os.path.join(temp_dir, "silent.mp4")
        clip.write_videofile(
            silent_path,
            codec="libx264",
            audio_codec=None,
            bitrate=bitrate,
            fps=fps,
            threads=2,
            logger=None
        )
        return silent_path
    
    audio = AudioFileClip(audio_path)
    clip = clip.set_audio(audio)
    
    # Write video file with explicit parameters
    update_progress(0.80, "Video oluşturuluyor ve kaydediliyor... (80%)")
    
    # Capture potential moviepy errors
    try:
        clip.write_videofile(
            final_path,
            codec="libx264",
            audio_codec="aac",
            bitrate=bitrate,
            fps=fps,
            threads=2,
            logger=None  # Suppress moviepy output
        )
    except Exception as e:
        print(f"MoviePy write error: {str(e)}")
        
        # Try with more conservative settings
        update_progress(0.85, "Alternatif video oluşturma yöntemi deneniyor...")
        try:
            clip.write_videofile(
                final_path,
                codec="libx264",
                audio_codec="aac",
                bitrate="1000k",
                fps=24,
                threads=1,
                logger=None
            )
        except Exception as e2:
            print(f"Second MoviePy write error: {str(e2)}")
            raise
    
    update_progress(1.0, "Tamamlandı! (100%)")
    
    # Clean up
    try:
        clip.close()
        audio.close()
    except:
        pass
    
    return final_path

def optimize_memory_usage():
    """Force garbage collection and free memory"""
    import gc
    import sys
    
    # Force garbage collection
    collected = gc.collect()
    
    # Try to release more memory if on Linux
    if sys.platform.startswith('linux'):
        try:
            # Use malloc_trim to release memory back to OS
            import ctypes
            ctypes.CDLL('libc.so.6').malloc_trim(0)
        except:
            pass
    
    return collected
