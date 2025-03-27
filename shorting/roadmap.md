# ShortGPT Real Estate Video Generator Roadmap

## Project Overview

ShortGPT now includes real estate video generation capabilities with Google Maps integration. This roadmap details the accelerated development plan leveraging AI and LLMs to automate the entire pipeline efficiently. The goal is to create a specialized tool that allows real estate agents to produce professional, drone-style aerial videos of properties using satellite imagery, user-provided photos, automated narration, and dynamic editing.

**For New Developers**

If you're new to this project, here are some tips for understanding the real estate functionality:

1. Start by examining the `map_imagery.py` and `geo_utils.py` modules to understand the Google Maps integration.
2. Review `ui_tab_realestate.py` to see how the UI is structured and how it interacts with the backend components.
3. Look at `realestate_video_engine.py` to understand the video generation process specific to real estate.
4. Run the test modules (`test_realestate_modules.py` and `test_integration.py`) to see the functionality in action.
5. Check the environment variables required in `.env` file: `GOOGLE_MAPS_API_KEY`, `ELEVENLABS_API_KEY`, and `OPENAI_API_KEY`.

## Current Implementation

The real estate functionality is structured across multiple modules:

```
ShortGPT/
├── gui/
│   └── ui_tab_realestate.py       # Dedicated UI tab for real estate videos
├── shortGPT/
│   ├── modules/
│   │   ├── geo_utils.py           # Location utilities
│   │   └── map_imagery.py         # Maps imagery handling
│   ├── engine/
│   │   └── realestate_video_engine.py  # Real estate video engine
│   └── prompt_templates/
│       └── realestate/
│           └── realestate_prompt_template.yaml
```

### Implementation Strategy

After evaluating our options, we've decided to integrate the real estate video generation feature into the existing `ui_tab_content.py` interface rather than creating a completely separate tab. This integration will add "Real Estate" as a new content type option alongside "Educational", "Tutorial", and "Entertainment".

### Key Features

1. **Multilingual UI & Narration**
   - Full Turkish language support for UI and narration
   - Localized form labels, instructions, and templates
   - Selection of professional Turkish voices via ElevenLabs

2. **Property Location & Mapping**
   - Address input with geocoding support
   - Automatic satellite and street view image retrieval
   - Property boundary drawing (automatic & manual)
   - Google Maps API integration

3. **Media Management**
   - Upload custom property photos and import from gallery
   - Image arrangement tools for optimized video sequencing
   - Support for panoramic and AI-enhanced images

4. **Video Generation**
   - Aerial drone-style transitions & effects
   - Professional real estate showcase templates
   - Dynamic text overlays for property details
   - Custom branding & watermarking
   - Multiple resolution & aspect ratio options

## Technical Implementation

### Phase 1: Core Engine Enhancement (1 Day)

1. **Template System Implementation**
   - Generate high-converting real estate video templates using LLMs
   - Optimize pacing, transitions, and music for different property types

2. **Script Optimization & Automation**
   - Fine-tune property description generation prompts
   - Implement dynamic input fields for script generation

3. **Turkish Language Integration**
   - Extend `voice_module.py` for Turkish TTS support
   - Create Turkish narration templates
   - Configure background music options

### Phase 2: Location & Mapping Features (1 Day)

1. **Google Maps & Property Visualization**
   - Integrate geocoding & mapping in `map_imagery.py`
   - Implement property boundary detection using ML
   - Develop interactive polygon editing for manual adjustments

2. **Media Management & Optimization**
   - Implement image upload, ordering, and enhancement
   - Support AI-powered image processing

### Phase 3: Video Engine Enhancements (1 Day)

1. **Advanced Transitions & Effects**
   - Enhance `realestate_video_engine.py` for drone-style transitions
   - Implement motion graphics for property highlights
   - Enable aspect ratio customization

2. **Performance & Scalability**
   - Optimize high-resolution satellite imagery handling
   - Implement caching mechanisms for faster processing

## API Dependencies

1. **Google Maps API** – Geocoding, satellite imagery, and street view
   - Env variable: `GOOGLE_MAPS_API_KEY`
2. **ElevenLabs API** – AI-driven voice narration
   - Env variable: `ELEVENLABS_API_KEY`
3. **OpenAI API** – Script generation & content automation
   - Env variable: `OPENAI_API_KEY`

## Future Development Roadmap

### Short-Term Improvements (2 Days)

1. **Enhanced Property Boundary Detection**
   - AI-powered automatic boundary detection
   - Interactive polygon editing tools
2. **Expanded Multi-Language Support**
   - Extend UI and narration to German, Arabic, and more
3. **Custom Video Template Library**
   - User-customizable templates
   - Preset-based automation for different property types

### Long-Term Vision

1. **Integration with Real Estate Platforms**
   - Export videos to Zillow, Redfin, MLS, and other platforms
   - API integration with property management systems
2. **AI-Enhanced Image Processing**
   - Automatic room recognition & labeling
   - AI-driven virtual staging capabilities

## Developer Onboarding Guide

1. **Review Core Modules**
   - `map_imagery.py` and `geo_utils.py` for Google Maps integration
   - `ui_tab_realestate.py` for UI and workflow
   - `realestate_video_engine.py` for video generation processes

2. **Setup Environment Variables**
   - Add API keys in `.env` file
   - Run test modules (`test_realestate_modules.py`, `test_integration.py`)

3. **Performance Considerations**
   - Implement caching to optimize API usage
   - Add rate limits to manage API costs
   - Ensure privacy compliance in handling location data

## Timeline for Remaining Work

1. **UI & Feature Refinements** (6 Hours)
2. **Additional Video Templates** (6 Hours)
3. **Multi-Language Expansion** (8 Hours)
4. **Integration Testing** (6 Hours)
5. **Final Documentation & Deployment** (3 Hours)

**Total Estimated Completion Time: 2 Days**

