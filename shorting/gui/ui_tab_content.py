import gradio as gr
from shortGPT.modules.map_imagery import get_coordinates_from_address
from PIL import Image
from shortGPT.config.languages import EDGE_TTS_VOICENAME_MAPPING
from shortGPT.audio.voice_module import VoiceModule
from shortGPT.audio.edge_voice_module import EdgeVoiceModule
from shortGPT.audio.eleven_voice_module import ElevenVoiceModule
from shortGPT.engine.realestate_video_engine import RealEstateVideoEngine
import requests
from shortGPT.editing_framework.editing_engine import EditingEngine, EditingStep

import os
import tempfile

def update_real_estate_images(files):
    file_paths = [file.name for file in files]
    return file_paths

def create_content_tab( ):
    """Create the content creation tab interface"""
    with gr.Column():
        gr.Markdown("## Content Creation")
        gr.Markdown("Create short-form video content with AI")

        def update_real_estate_visibility(content_type):
            if content_type == "Real Estate":
                return gr.update(visible=True)
            else:
                return gr.update(visible=False)

        def real_estate_fetch_location_data(address):
            if not address:
                return "Please enter an address", gr.update(visible=False)
            
            try:
                lat, lng, formatted_address = get_coordinates_from_address(address)
                
                if not lat or not lng:
                    return "Unable to find this location. Please enter a valid address.", gr.update(visible=False)
                
                map_html = f"""
                <div style="text-align: center;">
                    <iframe width="100%" height="300" frameborder="0" scrolling="no" marginheight="0" marginwidth="0"
                    src="https://maps.google.com/maps?q={lat},{lng}&z=15&output=embed"></iframe>
                </div>
                """
                
                return f"📍 Found: {formatted_address}", gr.update(value=map_html, visible=True)
                
            except Exception as e:
                return f"Error: {str(e)}", gr.update(visible=False)

        def real_estate_generate_video(property_data, script, template, voice_provider, language, images):
            
            try:
                 # Fetch satellite image
                address = property_data.get("address")
                if not address:
                    raise ValueError("Property address is missing.")

                lat, lng, _ = get_coordinates_from_address(address)
                if not lat or not lng:
                    raise ValueError("Could not get coordinates for the address.")

                # Construct static map URL
                api_key = ""  # Replace with your API key if necessary
                map_url = f"https://maps.googleapis.com/maps/api/staticmap?center={lat},{lng}&zoom=17&size=600x300&maptype=satellite&key={api_key}"

                # Download and save satellite image
                response = requests.get(map_url, stream=True)
                response.raise_for_status()  # Raise an exception for bad status codes

                with tempfile.NamedTemporaryFile(delete=False, suffix=".jpg") as temp_file:
                    for chunk in response.iter_content(chunk_size=8192):
                        temp_file.write(chunk)
                    satellite_image_path = temp_file.name

                property_data["satellite_image"] = satellite_image_path


                if images:
                    property_data["user_images"] = images

                satellite_image_path = property_data["satellite_image"]

                # Get image size, default to 600x300 if there is an error
                try:
                    with Image.open(satellite_image_path) as img:
                        img_width, img_height = img.size
                except Exception:
                    img_width, img_height = 600, 300

                # Initialize editing engine
                editing_engine = EditingEngine()

                # --- First Subclip (0-2.5 seconds) ---
                first_subclip_params = {
                    "url": satellite_image_path,
                    "set_time_start": 0,
                    "set_time_end": 2.5,
                    "auto_resize_image": {
                        "maxWidth": int(img_width * 1.1),
                        "maxHeight": int(img_height * 1.1),
                    },
                }

                editing_engine.addEditingStep(
                    editingStep=EditingStep.SHOW_IMAGE,
                    args=first_subclip_params,
                )

                # --- Second Subclip (2.5-5 seconds) ---
                second_subclip_params = {
                    "url": satellite_image_path,
                    "set_time_start": 2.5,
                    "set_time_end": 5,
                    "auto_resize_image": {
                        "maxWidth": int(img_width),
                        "maxHeight": int(img_height),
                    },
                }
                editing_engine.addEditingStep(
                    editingStep=EditingStep.SHOW_IMAGE,
                    args=second_subclip_params,
                )

                # Render the video
                with tempfile.NamedTemporaryFile(
                    delete=False, suffix=".mp4"
                ) as temp_output_file:
                    try:
                        editing_engine.renderVideo(temp_output_file.name)
                    except Exception as e:
                        raise Exception(
                            f"Error during video rendering: {str(e)}"
                        ) from e
                    video_path = temp_output_file.name

                #remove the temp file
                os.unlink(satellite_image_path)

                return "Video generated successfully!", video_path

            except Exception as e:
                return f"Error during video generation: {str(e)}", None

        


        # Add your content creation UI components here
        with gr.Group():
            gr.Markdown("### Content Type")
            content_type = gr.Radio(
                ["Educational", "Entertainment", "Tutorial"], 
                label="Select content type",
                value="Educational",
                interactive=True
            )
        
        with gr.Group():
            gr.Markdown("### Topic")
            topic_input = gr.Textbox(
                label="Enter your topic",
                placeholder="E.g., The history of quantum physics"
            )
            generate_button = gr.Button("Generate Content")

        
        # Placeholder for future functionality
        with gr.Group():
            output_text = gr.Textbox(
                label="Generated Content",
                placeholder="Content will appear here...",
                lines=10
            )
            
        content_type.change(
            fn=update_real_estate_visibility,
            inputs=[content_type],
            outputs=[real_estate_section]
        )

        with gr.Group(visible=False) as real_estate_section:
            gr.Markdown("### 📍 Property Location")
            real_estate_address_input = gr.Textbox(
                label="Property Address",
                placeholder="Enter full property address (e.g., 123 Main St, Anytown, USA)",
            )
            real_estate_get_location_button = gr.Button("Get Location Data")
            real_estate_location_status = gr.Markdown("")
            real_estate_map_view = gr.HTML("", visible=False)

            real_estate_get_location_button.click(

                    fn=real_estate_fetch_location_data,
                    inputs=[real_estate_address_input],
                    outputs=[real_estate_location_status, real_estate_map_view]
                )
            
            with gr.Group(visible=False) as real_estate_property_form:
                    gr.Markdown("### 🏠 Property Details")
                    with gr.Row():
                        real_estate_property_type = gr.Dropdown(
                            choices=["Apartment", "House", "Villa", "Land", "Office", "Retail"], 
                            label="Property Type"
                        )
                        real_estate_rooms = gr.Number(label="Bedrooms", precision=0, minimum=0)
                    with gr.Row():
                        real_estate_bathrooms = gr.Number(label="Bathrooms", precision=0, minimum=0)
                        real_estate_area = gr.Number(label="Area (sq. meters)", precision=0, minimum=1)
                    with gr.Row():
                        real_estate_price = gr.Number(label="Price", precision=0, minimum=0)
                        real_estate_year_built = gr.Number(label="Year Built", precision=0, minimum=1900)
                    
                    real_estate_special_features = gr.Textbox(
                        label="Special Features",
                        placeholder="Sea view, swimming pool, garden, security, etc.",
                        lines=2
                    )
                    real_estate_image_upload = gr.File(
                            label="Property Images",
                            file_types=["image"],
                            file_count="multiple",
                        )
                    real_estate_template_select = gr.Radio(
                        choices=["luxury_residence", "commercial_property", "standard"],
                        label="Video Template",
                        value="standard",
                    )
                    real_estate_generate_script_button = gr.Button("Generate Script", variant="primary")
                    real_estate_images = gr.State([]) #initiate it

                # Script and voice section
            with gr.Group(visible=False) as real_estate_script_form:
                gr.Markdown("### 📝 Property Script")
                real_estate_script_output = gr.Textbox(label="Generated Script", lines=5)
                real_estate_edit_script = gr.Checkbox(label="Edit Script", value=False)
                real_estate_script_edit = gr.Textbox(label="Edit Script", lines=5, visible=False)


                real_estate_image_upload.change(
                    fn=update_real_estate_images,
                    inputs=[real_estate_image_upload],
                    outputs=[real_estate_images]


                gr.Markdown("### 🎤 Voice Selection")
                with gr.Row():
                    real_estate_voice_provider = gr.Radio(
                        choices=["EdgeTTS", "ElevenLabs"],
                        label="Voice Provider",
                        value="EdgeTTS"
                    )
                    real_estate_language_selector = gr.Dropdown(
                        choices=["English", "Spanish", "French", "German", "Turkish"],
                        label="Language",
                        value="English"
                    )
                
                real_estate_voice_options = gr.Dropdown(label="Voice", choices=[])

            with gr.Group(visible=False) as real_estate_video_form:
                gr.Markdown("### 🎬 Generate Video")
                real_estate_generate_video_button = gr.Button("Create Real Estate Video", variant="primary")
                real_estate_video_status = gr.Markdown(value="")
                real_estate_video_output = gr.Video()

                 real_estate_generate_video_button.click(
                     fn=real_estate_generate_video,
                     inputs=[
                         gr.State(   format_property_data(real_estate_address_input.value, real_estate_property_type.value, real_estate_rooms.value, real_estate_bathrooms.value, real_estate_area.value, real_estate_price.value, real_estate_year_built.value, real_estate_special_features.value)


                         ),
                         real_estate_script_output,
                         real_estate_template_select,
                         real_estate_voice_provider,
                         real_estate_language_selector,
                         real_estate_images
                     ],
                     outputs=[real_estate_video_status, real_estate_video_output]
                 )
                
            
                def format_property_data(address, property_type, rooms, bathrooms, area, price, year_built, special_features):
                    return {"address": address,"property_type": property_type,"rooms": rooms,"bathrooms": bathrooms,"area": area,"price": price,"year_built": year_built,"special_features": special_features}
                    fn=format_property_data,
                    inputs=[real_estate_address_input, real_estate_property_type, real_estate_rooms, real_estate_bathrooms, real_estate_area, real_estate_price, real_estate_year_built, real_estate_special_features],
                    outputs=[]  # No outputs, you're just formatting the data
                )
            
            real_estate_script_output.change(
                fn=lambda x: gr.update(visible=True),
                inputs=[real_estate_script_output],
                outputs=[real_estate_video_form]
            )

            real_estate_edit_script.change(
                fn=lambda x, y: (gr.update(visible=x), y if not x else y),
                inputs=[real_estate_edit_script, real_estate_script_output],
                outputs=[real_estate_script_edit, real_estate_script_edit]
            )

            real_estate_address_input.change(
                fn=lambda x: gr.update(visible=True),
                inputs=[real_estate_address_input],
                outputs=[real_estate_property_form]
            )


        generate_button.click(
            lambda x, y: f"This is a placeholder for generated content about '{y}' in '{x}' style.",
            inputs=[content_type, topic_input],
            outputs=[output_text]
        )
    return gr.update()