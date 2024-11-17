import streamlit as st
import uuid
from datetime import datetime
import json
from io import BytesIO
from elevenlabs import VoiceSettings
from elevenlabs.client import ElevenLabs
import os
from dotenv import load_dotenv
from spotify_handler import SpotifyPodcastHandler

# load env vars and set up ElevenLabs
load_dotenv()
ELEVENLABS_API_KEY = os.getenv("ELEVENLABS_API_KEY")
if not ELEVENLABS_API_KEY:
    raise ValueError("ELEVENLABS_API_KEY environment variable not set")
client = ElevenLabs(api_key=ELEVENLABS_API_KEY)

# Initialize Spotify Handler
if 'spotify_handler' not in st.session_state:
    try:
        st.session_state.spotify_handler = SpotifyPodcastHandler()
    except Exception as e:
        print(f"Error initializing Spotify handler: {str(e)}")
        st.session_state.spotify_handler = None

def text_to_speech_stream(text: str) -> BytesIO:
    """Generate speech from text using ElevenLabs API"""
    response = client.text_to_speech.convert(
        voice_id="pNInz6obpgDQGcFmaJgB",  # Adam voice
        optimize_streaming_latency="0",
        output_format="mp3_22050_32",
        text=text,
        model_id="eleven_multilingual_v2",
        voice_settings=VoiceSettings(
            stability=0.0,
            similarity_boost=1.0,
            style=0.0,
            use_speaker_boost=True,
        ),
    )
    
    audio_stream = BytesIO()
    for chunk in response:
        if chunk:
            audio_stream.write(chunk)
    audio_stream.seek(0)
    return audio_stream

# Initialize session state for storing rehearsals if not exists
if 'rehearsals' not in st.session_state:
    st.session_state.rehearsals = {}

if 'current_screen' not in st.session_state:
    st.session_state.current_screen = 'create'

def generate_id():
    return str(uuid.uuid4())

def create_rehearsal_screen():
    st.title("Create rehearsal")
    
    # Navigation
    if st.button("Go to Playback", type="secondary"):
        st.session_state.current_screen = 'play'
        st.rerun()
    
    # Form for rehearsal creation
    with st.form("rehearsal_form"):
        rehearsal_text = st.text_area(
            "Enter your rehearsal prompt",
            height=200,
            key="rehearsal_input"
        )
        
        # Track whether we're in edit mode
        is_editing = 'enhanced_text' not in st.session_state
        
        if is_editing:
            submit_label = "Design rehearsal"
        else:
            submit_label = "Redesign rehearsal"
        
        col1, col2, col3 = st.columns([1, 2, 1])  # Creates three columns with middle one being larger
        with col2:  # Use the middle column
            design_submitted = st.form_submit_button(
                submit_label,
                type="primary",
                use_container_width=True
            )
        
        # Handle design submission
        if design_submitted and rehearsal_text:
            # Simulate LLM enhancement
            enhanced_text = f"Enhanced: {rehearsal_text}"
            st.session_state.enhanced_text = enhanced_text
            st.rerun()
    
    # Show enhanced text and completion button if we have processed text
    if 'enhanced_text' in st.session_state:
        st.text_area(
            "Enhanced rehearsal",
            value=st.session_state.enhanced_text,
            height=200,
            key="enhanced_output"
        )
        # Add a progress message placeholder
        progress_placeholder = st.empty()
        
        if st.button(
            "Complete and Generate Voiceover",
            type="primary",
            use_container_width=True
        ):
            try:
                progress_placeholder.text("Generating voiceover...")
                
                # Generate audio using ElevenLabs
                audio_stream = text_to_speech_stream(st.session_state.enhanced_text)
                
                # Create new rehearsal object
                rehearsal_id = generate_id()
                
                # Initialize rehearsal object
                rehearsal = {
                    'id': rehearsal_id,
                    'title': st.session_state.enhanced_text.split()[:4],
                    'content': st.session_state.enhanced_text,
                    'created_at': datetime.now().isoformat(),
                    'audio_data': audio_stream.getvalue()
                }

                # Handle Spotify upload if available
                if st.session_state.spotify_handler:
                    try:
                        progress_placeholder.text("Uploading to Spotify...")
                        episode_id = st.session_state.spotify_handler.upload_episode(
                            audio_data=audio_stream.getvalue(),
                            title=" ".join(st.session_state.enhanced_text.split()[:4]),
                            description=st.session_state.enhanced_text
                        )
                        if episode_id:
                            episode_url = st.session_state.spotify_handler.get_episode_url(episode_id)
                            rehearsal['spotify_episode_id'] = episode_id
                            rehearsal['spotify_url'] = episode_url
                            progress_placeholder.success(f"Successfully uploaded to Spotify! Listen here: {episode_url}")
                    except Exception as e:
                        progress_placeholder.error(f"Error uploading to Spotify: {str(e)}")
                
                # Store the rehearsal in session state
                st.session_state.rehearsals[rehearsal_id] = rehearsal
                
                # Clear the session state for next creation
                del st.session_state.enhanced_text
                
                # Update progress and switch screens
                progress_placeholder.text("Rehearsal created successfully!")
                st.session_state.current_screen = 'play'
                st.rerun()

            except Exception as e:
                progress_placeholder.error(f"Error creating rehearsal: {str(e)}")

def play_rehearsal_screen():
    st.title("Play rehearsal")
    
    # Navigation
    if st.button("Create New Rehearsal", type="secondary"):
        st.session_state.current_screen = 'create'
        st.rerun()
    
    if not st.session_state.rehearsals:
        st.warning("No Rehearsals created yet. Create your first Rehearsal!")
        return
    
    # Get list of rehearsals
    rehearsals = list(st.session_state.rehearsals.values())
    
    # Track current rehearsal index
    if 'current_rehearsal_index' not in st.session_state:
        st.session_state.current_rehearsal_index = 0
    
    current_rehearsal = rehearsals[st.session_state.current_rehearsal_index]
    
    # Create columns for navigation and player
    col1, col2, col3 = st.columns([1, 3, 1])
    
    with col1:
        if st.button("⬅️ Previous"):
            st.session_state.current_rehearsal_index = (
                st.session_state.current_rehearsal_index - 1
            ) % len(rehearsals)
            # Reset playing state when changing rehearsal
            st.session_state.is_playing = False
            st.rerun()
    
    with col2:
        # Display current rehearsal
        st.markdown(
            f"<h2 style='text-align: center;'>{' '.join(current_rehearsal['title'])}...</h2>",
            unsafe_allow_html=True
        )
        
        # Center the play controls
        _, play_col, stop_col, _ = st.columns([2, 1, 1, 2])
        
        # Create a placeholder for the audio player and error messages
        audio_placeholder = st.empty()
        message_placeholder = st.empty()
        
        with play_col:
            if 'is_playing' not in st.session_state:
                st.session_state.is_playing = False
            
            if st.button(
                "⏸️ Pause" if st.session_state.is_playing else "▶️ Play",
                use_container_width=True
            ):
                # Check if audio data exists
                if 'audio_data' in current_rehearsal:
                    try:
                        st.session_state.is_playing = not st.session_state.is_playing
                        
                        if st.session_state.is_playing:
                            # Clear any previous error messages
                            message_placeholder.empty()
                            # Display audio player
                            audio_placeholder.audio(
                                current_rehearsal['audio_data'],
                                format='audio/mp3',
                                start_time=0
                            )
                        else:
                            # Clear audio player when paused
                            audio_placeholder.empty()
                            
                    except Exception as e:
                        st.session_state.is_playing = False
                        message_placeholder.error(f"Error playing rehearsal: {str(e)}")
                        audio_placeholder.empty()
                else:
                    message_placeholder.warning("No audio available for this rehearsal")
                    st.session_state.is_playing = False
        
        with stop_col:
            if st.button("⏹️ Stop", use_container_width=True):
                st.session_state.is_playing = False
                audio_placeholder.empty()
                message_placeholder.empty()
    
    with col3:
        if st.button("Next ➡️"):
            st.session_state.current_rehearsal_index = (
                st.session_state.current_rehearsal_index + 1
            ) % len(rehearsals)
            # Reset playing state when changing rehearsal
            st.session_state.is_playing = False
            st.rerun()
    
    # Display rehearsal content
    st.markdown("### Transcript")
    st.write(current_rehearsal['content'])

    # Display Spotify link if available
    if 'spotify_url' in current_rehearsal:
        st.markdown(f"[Listen on Spotify]({current_rehearsal['spotify_url']})")

# Main app logic
def main():
    if st.session_state.current_screen == 'create':
        create_rehearsal_screen()
    else:
        play_rehearsal_screen()

if __name__ == "__main__":
    st.set_page_config(
        page_title="Rehearsals.app",
        page_icon="🧘‍♀️",
        layout="wide"
    )
    main()