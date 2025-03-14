"""Video generation and effects functions."""

import os
import tempfile
import cv2
import numpy as np
import streamlit as st
from PIL import Image
from moviepy.editor import ImageSequenceClip, AudioFileClip, VideoFileClip

def create_frame_effect(image, n_frames, effect_type="zoom", zoom_in=True, pan_direction="right"):
    """Create effect frames for a single image"""
    img_array = np.array(image)
    h, w = img_array.shape[:2]
    frames = []
    
    if effect_type == "zoom":
        zoom_range = np.linspace(1.0, 1.3 if zoom_in else 1.0, n_frames)
        start_zoom = 1.0 if zoom_in else 1.3
        for factor in zoom_range:
            new_h, new_w = int(h / factor), int(w / factor)
            y1, x1 = (h - new_h) // 2, (w - new_w) // 2
            y2, x2 = y1 + new_h, x1 + new_w
            if 0 <= y1 < y2 <= h and 0 <= x1 < x2 <= w:
                cropped = img_array[y1:y2, x1:x2]
                frame = cv2.resize(cropped, (w, h))
                frames.append(frame)
    
    elif effect_type == "pan":
        max_shift = w // 4 if pan_direction in ["right", "left"] else h // 4
        shifts = np.linspace(0, max_shift, n_frames)
        if pan_direction in ["right", "down"]:
            shifts = shifts[::-1]
            
        for shift in shifts:
            shift = int(shift)
            if pan_direction in ["right", "left"]:
                M = np.float32([[1, 0, -shift], [0, 1, 0]])
            else:
                M = np.float32([[1, 0, 0], [0, 1, -shift]])
            frame = cv2.warpAffine(img_array, M, (w, h))
            frames.append(frame)
    
    return frames

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

def generate_video(images, audio_path, transition_type, fps=30, quality="normal"):
    """Generate video with effects and audio"""
    try:
        # Set video resolution based on quality
        if quality == "high":
            target_width, target_height = 1920, 1080
            bitrate = "4000k"
        else:
            target_width, target_height = 1280, 720
            bitrate = "2000k"
            
        # Progress tracking
        progress_text = st.empty()
        progress_bar = st.progress(0)
        
        # Create temp directory for output
        temp_dir = tempfile.mkdtemp()
        video_path = os.path.join(temp_dir, "temp_video.mp4")
        
        # Get audio duration
        progress_text.text("Ses dosyası hazırlanıyor... (10%)")
        audio = AudioFileClip(audio_path)
        duration = audio.duration
        
        # Calculate frames per image
        n_images = min(len(images), 8)  # Limit to 8 images
        frames_per_image = int((duration * fps) / n_images)
        
        progress_text.text("Video codec kontrolü yapılıyor... (15%)")
        progress_bar.progress(0.15)
        
        # Check available codecs and choose a supported one
        test_codecs = ['mp4v', 'avc1', 'XVID', 'H264']
        working_codec = None
        
        for codec in test_codecs:
            try:
                # Test if codec works
                fourcc = cv2.VideoWriter_fourcc(*codec)
                test_path = os.path.join(temp_dir, f"test_{codec}.mp4")
                test_writer = cv2.VideoWriter(test_path, fourcc, fps, (100, 100))
                
                if test_writer.isOpened():
                    test_writer.release()
                    working_codec = codec
                    print(f"Using codec: {working_codec}")
                    break
            except Exception as e:
                print(f"Codec {codec} not supported: {str(e)}")
                continue
                
        if not working_codec:
            print("No supported video codec found. Falling back to FFmpeg directly.")
            progress_text.text("Alternatif video oluşturma yöntemi kullanılıyor... (20%)")
            progress_bar.progress(0.20)
            return generate_video_with_ffmpeg(images, audio_path, fps, quality)
        
        # Prepare video writer with detected codec
        fourcc = cv2.VideoWriter_fourcc(*working_codec)
        out = cv2.VideoWriter(video_path, fourcc, fps, (target_width, target_height))
        
        progress_text.text("Video oluşturmaya hazırlanıyor... (20%)")
        progress_bar.progress(0.20)
        
        # Process each image
        for idx, image in enumerate(images[:n_images]):
            # Calculate overall progress: 20% start + up to 60% for image processing
            overall_progress = 0.20 + (0.60 * (idx / n_images))
            progress_text.text(f"Görüntü işleniyor {idx+1}/{n_images}... ({int(overall_progress*100)}%)")
            progress_bar.progress(overall_progress)
            
            # Convert and resize image using the optimization function
            img_array = optimize_image_for_video(image, target_width, target_height)
            
            # Create effect frames
            if transition_type == "Yakınlaşma":
                frames = create_frame_effect(img_array, frames_per_image, "zoom", zoom_in=(idx % 2 == 0))
            elif transition_type == "Kaydırma":
                pan_directions = ["right", "left", "up", "down"]
                frames = create_frame_effect(img_array, frames_per_image, "pan", 
                                          pan_direction=pan_directions[idx % len(pan_directions)])
            else:  # Combined effect
                half_frames = frames_per_image // 2
                zoom_frames = create_frame_effect(img_array, half_frames, "zoom", zoom_in=(idx % 2 == 0))
                pan_frames = create_frame_effect(img_array, frames_per_image - half_frames, "pan", 
                                              pan_direction=["right", "left"][idx % 2])
                frames = zoom_frames + pan_frames
            
            # Write frames
            for frame in frames:
                out.write(frame)
        
        out.release()
        progress_text.text("Ses ekleniyor... (80%)")
        progress_bar.progress(0.80)
        
        # Add audio
        video = VideoFileClip(video_path)
        final_clip = video.set_audio(audio)
        
        # Save final video
        progress_text.text("Video dosyası kaydediliyor... (90%)")
        progress_bar.progress(0.90)
        final_path = os.path.join(temp_dir, "final_video.mp4")
        final_clip.write_videofile(
            final_path,
            codec="libx264",
            audio_codec="aac",
            bitrate=bitrate,
            fps=fps,
            threads=2,
            logger=None  # Suppress moviepy output
        )
        
        # Cleanup
        video.close()
        audio.close()
        final_clip.close()
        
        progress_text.text("Tamamlandı! (100%)")
        progress_bar.progress(1.0)
        
        return final_path
        
    except Exception as e:
        print(f"Standard video generation failed: {str(e)}. Trying fallback method...")
        try:
            return generate_video_with_ffmpeg(images, audio_path, fps, quality)
        except Exception as fallback_error:
            print(f"Fallback video generation also failed: {str(fallback_error)}")
            raise

def generate_video_with_ffmpeg(images, audio_path, fps=30, quality="normal"):
    """
    Fallback method to generate video using FFmpeg directly via moviepy
    
    Args:
        images: List of PIL images
        audio_path: Path to audio file
        fps: Frames per second
        quality: Video quality (normal/high)
        
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
    progress_text.text("Görüntüler hazırlanıyor... (30%)")
    progress_bar.progress(0.30)
    
    frames = []
    for i, img in enumerate(images):
        # Update progress: 30% to 60% for image processing
        current_progress = 0.30 + (0.30 * (i / len(images)))
        progress_bar.progress(current_progress)
        progress_text.text(f"Görüntü hazırlanıyor {i+1}/{len(images)}... ({int(current_progress*100)}%)")
        
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
    
    # Create video clip
    progress_text.text("Video klip hazırlanıyor... (60%)")
    progress_bar.progress(0.60)
    clip = ImageSequenceClip(frames, fps=fps)
    
    # Add audio
    progress_text.text("Ses ekleniyor... (70%)")
    progress_bar.progress(0.70)
    audio = AudioFileClip(audio_path)
    clip = clip.set_audio(audio)
    
    # Write video file with explicit parameters
    progress_text.text("Video oluşturuluyor ve kaydediliyor... (80%)")
    progress_bar.progress(0.80)
    clip.write_videofile(
        final_path,
        codec="libx264",
        audio_codec="aac",
        bitrate=bitrate,
        fps=fps,
        threads=2,
        logger=None  # Suppress moviepy output
    )
    
    progress_text.text("Tamamlandı! (100%)")
    progress_bar.progress(1.0)
    
    # Clean up
    clip.close()
    audio.close()
    
    return final_path
