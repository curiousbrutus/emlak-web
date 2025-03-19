"""Advanced video stabilization techniques for smoother real estate videos."""

import cv2
import numpy as np
import streamlit as st

def stabilize_video_sequence(frames, smoothing_window=30):
    """
    Apply advanced stabilization to a sequence of frames
    
    Args:
        frames: List of frames to stabilize
        smoothing_window: Smoothing window size for trajectory
    
    Returns:
        List of stabilized frames
    """
    n_frames = len(frames)
    if n_frames < 3:
        return frames  # Not enough frames to stabilize
        
    # Get frame dimensions
    h, w = frames[0].shape[:2]
    
    # Pre-allocate trajectory and smoothed trajectory arrays
    trajectory = np.zeros((n_frames-1, 3), np.float32)  # dx, dy, da (angle)
    
    # Track feature points across frames
    prev_gray = cv2.cvtColor(frames[0], cv2.COLOR_BGR2GRAY)
    prev_pts = cv2.goodFeaturesToTrack(prev_gray, maxCorners=200, qualityLevel=0.01, minDistance=30, blockSize=3)
    
    if prev_pts is None or len(prev_pts) < 10:
        return frames  # Not enough feature points
        
    # Progress indicator
    progress_placeholder = st.empty()
    
    # Calculate frame-to-frame transformations
    for i in range(1, n_frames):
        curr_gray = cv2.cvtColor(frames[i], cv2.COLOR_BGR2GRAY)
        
        # Update progress
        if i % 5 == 0:
            progress_placeholder.text(f"Stabilizing frames: {i}/{n_frames}")
            
        # Calculate optical flow
        curr_pts, status, _ = cv2.calcOpticalFlowPyrLK(prev_gray, curr_gray, prev_pts, None)
        
        # Filter only valid points
        idx = np.where(status == 1)[0]
        if len(idx) < 10:  # Not enough matching points
            prev_gray = curr_gray.copy()
            prev_pts = cv2.goodFeaturesToTrack(prev_gray, maxCorners=200, qualityLevel=0.01, minDistance=30, blockSize=3)
            continue
            
        prev_pts_valid = prev_pts[idx].reshape(-1, 2)
        curr_pts_valid = curr_pts[idx].reshape(-1, 2)
        
        # Estimate rigid transformation
        m = cv2.estimateAffinePartial2D(prev_pts_valid, curr_pts_valid)[0]
        
        if m is None:  # Transformation estimation failed
            trajectory[i-1] = trajectory[i-2] if i > 1 else np.zeros(3)
        else:
            # Extract translation and rotation
            dx = m[0, 2]
            dy = m[1, 2]
            da = np.arctan2(m[1, 0], m[0, 0])
            trajectory[i-1] = [dx, dy, da]
        
        # Update for next iteration
        prev_gray = curr_gray.copy()
        prev_pts = curr_pts_valid.reshape(-1, 1, 2)
    
    # Smooth trajectory
    smoothed_trajectory = smooth_trajectory(trajectory, smoothing_window)
    
    # Calculate difference
    difference = smoothed_trajectory - trajectory
    
    # Apply transformation
    stabilized_frames = []
    stabilized_frames.append(frames[0])  # First frame remains unchanged
    
    for i in range(1, n_frames):
        # Get transformation matrix
        dx, dy, da = difference[i-1]
        
        # Create transformation matrix
        m = np.zeros((2, 3), np.float32)
        m[0, 0] = np.cos(da)
        m[0, 1] = -np.sin(da)
        m[1, 0] = np.sin(da)
        m[1, 1] = np.cos(da)
        m[0, 2] = dx
        m[1, 2] = dy
        
        # Apply transformation
        frame_stabilized = cv2.warpAffine(frames[i], m, (w, h), borderMode=cv2.BORDER_REFLECT)
        stabilized_frames.append(frame_stabilized)
        
        # Update progress
        if i % 5 == 0:
            progress_placeholder.text(f"Applying stabilization: {i}/{n_frames}")
    
    progress_placeholder.empty()
    return stabilized_frames

def smooth_trajectory(trajectory, window_size):
    """
    Smooth trajectory using moving average
    
    Args:
        trajectory: Array of trajectory vectors
        window_size: Window size for smoothing
    
    Returns:
        Smoothed trajectory array
    """
    smoothed = np.copy(trajectory)
    
    # Handle edge cases for small trajectories
    if len(trajectory) <= window_size:
        return smoothed
        
    # Apply moving average
    for i in range(len(trajectory)):
        start = max(0, i - window_size // 2)
        end = min(len(trajectory), i + window_size // 2 + 1)
        
        # Calculate average in window
        smoothed[i] = np.mean(trajectory[start:end], axis=0)
    
    return smoothed
