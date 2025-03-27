import gradio as gr
import os

def create_settings_tab():
    """Create the settings tab interface"""
    with gr.Column():
        gr.Markdown("## Settings")
        gr.Markdown("Configure ShortGPT settings and API keys")
        
        # API Keys Section
        with gr.Group():
            gr.Markdown("### API Keys")
            
            # OpenAI API Key
            openai_api_key = gr.Textbox(
                label="OpenAI API Key",
                placeholder="sk-...",
                type="password",
                value=os.environ.get("OPENAI_API_KEY", "")
            )
            
            # ElevenLabs API Key
            elevenlabs_api_key = gr.Textbox(
                label="ElevenLabs API Key",
                placeholder="your-elevenlabs-api-key",
                type="password",
                value=os.environ.get("ELEVENLABS_API_KEY", "")
            )
            
            # Google Maps API Key
            google_maps_api_key = gr.Textbox(
                label="Google Maps API Key",
                placeholder="your-google-maps-api-key",
                type="password",
                value=os.environ.get("GOOGLE_MAPS_API_KEY", "")
            )
            
            # Gemini API Key
            gemini_api_key = gr.Textbox(
                label="Gemini API Key",
                placeholder="your-gemini-api-key",
                type="password",
                value=os.environ.get("GEMINI_API_KEY", "")
            )
            
            save_api_keys_button = gr.Button("Save API Keys")
        
        # Application Settings
        with gr.Group():
            gr.Markdown("### Application Settings")
            
            cache_enabled = gr.Checkbox(
                label="Enable Cache",
                value=True
            )
            
            debug_mode = gr.Checkbox(
                label="Debug Mode",
                value=False
            )
            
            output_dir = gr.Textbox(
                label="Output Directory",
                placeholder="/path/to/output",
                value="./outputs"
            )
            
            save_settings_button = gr.Button("Save Settings")
        
        # Placeholder for save function
        save_api_keys_button.click(
            lambda: gr.update(value="API keys saved!"),
            outputs=[gr.Textbox(label="Status", visible=False)]
        )
        
        save_settings_button.click(
            lambda: gr.update(value="Settings saved!"),
            outputs=[gr.Textbox(label="Status", visible=False)]
        )
    
    return gr.update()
