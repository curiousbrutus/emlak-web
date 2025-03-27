"""Utility to check system dependencies for video generation."""

import subprocess
import shutil
import platform
import os
import streamlit as st

def check_ffmpeg():
    """Check if FFmpeg is installed and working."""
    try:
        ffmpeg_path = shutil.which('ffmpeg')
        if ffmpeg_path:
            result = subprocess.run(['ffmpeg', '-version'], 
                                  stdout=subprocess.PIPE, 
                                  stderr=subprocess.PIPE,
                                  text=True)
            return True, ffmpeg_path, result.stdout.split('\n')[0]
        else:
            return False, None, "FFmpeg not found in PATH"
    except Exception as e:
        return False, None, str(e)

def check_opencv():
    """Check OpenCV version and capabilities."""
    import cv2
    version = cv2.__version__
    
    # Check if OpenCV was built with video support
    has_video = "Video I/O" in cv2.getBuildInformation()
    
    # Check available video codecs
    codecs = []
    for codec in ['XVID', 'MJPG', 'X264', 'AVC1', 'H264']:
        try:
            if cv2.VideoWriter_fourcc(*codec) != -1:
                codecs.append(codec)
        except:
            pass
    
    return version, has_video, codecs

def check_system_resources():
    """Check system resources."""
    try:
        import psutil
        
        # Memory info
        memory = psutil.virtual_memory()
        free_memory_gb = memory.available / (1024**3)
        
        # CPU info
        cpu_count = os.cpu_count()
        cpu_usage = psutil.cpu_percent(interval=1)
        
        # Disk info
        disk = psutil.disk_usage('/')
        free_disk_gb = disk.free / (1024**3)
        
        return {
            "free_memory_gb": free_memory_gb,
            "cpu_count": cpu_count,
            "cpu_usage": cpu_usage,
            "free_disk_gb": free_disk_gb
        }
    except ImportError:
        return {
            "error": "psutil module not installed",
            "cpu_count": os.cpu_count()
        }

def run_dependency_checks():
    """Run all dependency checks and return results."""
    results = {}
    
    # System info
    results["system"] = {
        "platform": platform.system(),
        "platform_version": platform.version(),
        "python_version": platform.python_version()
    }
    
    # FFmpeg
    ffmpeg_ok, ffmpeg_path, ffmpeg_version = check_ffmpeg()
    results["ffmpeg"] = {
        "available": ffmpeg_ok,
        "path": ffmpeg_path,
        "version": ffmpeg_version
    }
    
    # OpenCV
    try:
        cv_version, has_video, codecs = check_opencv()
        results["opencv"] = {
            "version": cv_version,
            "has_video": has_video,
            "available_codecs": codecs
        }
    except Exception as e:
        results["opencv"] = {
            "error": str(e)
        }
    
    # System resources
    results["resources"] = check_system_resources()
    
    return results

def display_system_info():
    """Display system information in Streamlit."""
    with st.expander("🖥️ Sistem Bilgileri"):
        try:
            results = run_dependency_checks()
            
            col1, col2 = st.columns(2)
            
            with col1:
                st.subheader("Sistem")
                st.write(f"**Platform:** {results['system']['platform']} {results['system']['platform_version']}")
                st.write(f"**Python:** {results['system']['python_version']}")
                
                if 'resources' in results and 'error' not in results['resources']:
                    st.subheader("Kaynaklar")
                    if "free_memory_gb" in results['resources']:
                        st.write(f"**Boş Bellek:** {results['resources']['free_memory_gb']:.1f} GB")
                    st.write(f"**CPU Çekirdek:** {results['resources']['cpu_count']}")
                    if "cpu_usage" in results['resources']:
                        st.write(f"**CPU Kullanımı:** {results['resources']['cpu_usage']}%")
                    if "free_disk_gb" in results['resources']:
                        st.write(f"**Boş Disk:** {results['resources']['free_disk_gb']:.1f} GB")
            
            with col2:
                st.subheader("FFmpeg")
                if results['ffmpeg']['available']:
                    st.success("✅ FFmpeg kurulu")
                    st.write(f"**Versiyon:** {results['ffmpeg']['version']}")
                else:
                    st.error("❌ FFmpeg kurulu değil")
                    st.write("FFmpeg video oluşturma için gereklidir.")
                
                st.subheader("OpenCV")
                if 'error' not in results['opencv']:
                    st.write(f"**Versiyon:** {results['opencv']['version']}")
                    if results['opencv']['has_video']:
                        st.success("✅ Video desteği mevcut")
                    else:
                        st.warning("⚠️ OpenCV video desteği sınırlı")
                    
                    st.write(f"**Kodekler:** {', '.join(results['opencv']['available_codecs'])}")
                else:
                    st.error(f"❌ OpenCV hatası: {results['opencv']['error']}")
        
        except Exception as e:
            st.error(f"Sistem bilgileri alınamadı: {str(e)}")
            
        st.info("Video oluşturma işlemi sırasında sorun yaşıyorsanız, FFmpeg ve OpenCV'nin düzgün kurulduğundan emin olun.")

# Add this to your app setup or settings page
if __name__ == "__main__":
    display_system_info()
