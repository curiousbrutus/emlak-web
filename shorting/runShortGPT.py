import os
import sys
from pathlib import Path

# Add the project root to the path
project_root = Path(__file__).parent
sys.path.append(str(project_root))

# Import gradio
import gradio as gr

# Import environment loader early
from shortGPT.utils.env_loader import load_environment
load_environment()

# Import tab creators
from gui.ui_tab_content import create_content_tab
from gui.ui_tab_video import create_video_tab
from gui.ui_tab_asset import create_asset_tab
from gui.ui_tab_settings import create_settings_tab
from gui.ui_tab_realestate import create_realestate_tab

def create_ui():
    with gr.Blocks(title="ShortGPT", theme=gr.themes.Soft()) as app:
        # Add tabs to the application 
        with gr.Tabs() as tabs:
            with gr.Tab("Content Creation", id=0):
                create_content_tab()
            with gr.Tab("Video Creation", id=1):
                create_video_tab()
            with gr.Tab("Asset Library", id=2):
                create_asset_tab()
            # Add the real estate tab here
            with gr.Tab("Real Estate Video", id=3):
                create_realestate_tab()
            with gr.Tab("Settings", id=4):
                create_settings_tab()
        
        return app

if __name__ == "__main__":
    # Create the UI
    ui = create_ui()
    
    # Launch the app
    ui.launch(
        server_name="0.0.0.0",
        server_port=31415,
        share=False
    )