"""import streamlit as st

st.title("Rehearsals")
st.write(
    "Let's start building! For help and inspiration, head over to [docs.streamlit.io](https://docs.streamlit.io/)."
)

testy = st.chat_input(placeholder="Your message", key=None, max_chars=None, disabled=False, on_submit=None, args=None, kwargs=None)

st.write("testy lives here")
if testy != None:
    testy """

import streamlit as st
import uuid
from datetime import datetime
import json

# Initialize session state for storing meditations if not exists
if 'meditations' not in st.session_state:
    st.session_state.meditations = {}

if 'current_screen' not in st.session_state:
    st.session_state.current_screen = 'create'

def generate_id():
    return str(uuid.uuid4())

def create_meditation_screen():
    st.title("Create Meditation")
    
    # Navigation
    if st.button("Go to Playback", type="secondary"):
        st.session_state.current_screen = 'play'
        st.rerun()
    
    # Form for meditation creation
    with st.form("meditation_form"):
        meditation_text = st.text_area(
            "Enter your meditation ideas",
            height=200,
            key="meditation_input"
        )
        
        # Track whether we're in edit mode
        is_editing = 'enhanced_text' not in st.session_state
        
        if is_editing:
            submit_label = "Design Meditation"
        else:
            submit_label = "Redesign Meditation"
        
        col1, col2 = st.columns([3, 1])
        with col1:
            design_submitted = st.form_submit_button(
                submit_label,
                type="primary",
                use_container_width=True
            )
        
        # Handle design submission
        if design_submitted and meditation_text:
            # Simulate LLM enhancement
            enhanced_text = f"Enhanced: {meditation_text}"
            st.session_state.enhanced_text = enhanced_text
            st.rerun()
    
    # Show enhanced text and completion button if we have processed text
    if 'enhanced_text' in st.session_state:
        st.text_area(
            "Enhanced Meditation",
            value=st.session_state.enhanced_text,
            height=200,
            key="enhanced_output"
        )
        
        if st.button(
            "Complete and Generate Voiceover",
            type="primary",
            use_container_width=True
        ):
            # Create new meditation object
            meditation_id = generate_id()
            meditation = {
                'id': meditation_id,
                'title': st.session_state.enhanced_text.split()[:4],
                'content': st.session_state.enhanced_text,
                'created_at': datetime.now().isoformat(),
                'audio_url': None  # Would be populated by voice generation service
            }
            
            # Store in our dictionary
            st.session_state.meditations[meditation_id] = meditation
            
            # Clear the session state for next creation
            del st.session_state.enhanced_text
            
            # Switch to play screen
            st.session_state.current_screen = 'play'
            st.rerun()

def play_meditation_screen():
    st.title("Play Meditation")
    
    # Navigation
    if st.button("Create New Meditation", type="secondary"):
        st.session_state.current_screen = 'create'
        st.rerun()
    
    if not st.session_state.meditations:
        st.warning("No meditations created yet. Create your first meditation!")
        return
    
    # Get list of meditations
    meditations = list(st.session_state.meditations.values())
    
    # Track current meditation index
    if 'current_meditation_index' not in st.session_state:
        st.session_state.current_meditation_index = 0
    
    current_meditation = meditations[st.session_state.current_meditation_index]
    
    # Create columns for navigation and player
    col1, col2, col3 = st.columns([1, 3, 1])
    
    with col1:
        if st.button("⬅️ Previous"):
            st.session_state.current_meditation_index = (
                st.session_state.current_meditation_index - 1
            ) % len(meditations)
            st.rerun()
    
    with col2:
        # Display current meditation
        st.markdown(
            f"<h2 style='text-align: center;'>{' '.join(current_meditation['title'])}...</h2>",
            unsafe_allow_html=True
        )
        
        # Center the play controls
        _, play_col, stop_col, _ = st.columns([2, 1, 1, 2])
        
        with play_col:
            if 'is_playing' not in st.session_state:
                st.session_state.is_playing = False
            
            if st.button(
                "⏸️ Pause" if st.session_state.is_playing else "▶️ Play",
                use_container_width=True
            ):
                st.session_state.is_playing = not st.session_state.is_playing
        
        with stop_col:
            if st.button("⏹️ Stop", use_container_width=True):
                st.session_state.is_playing = False
    
    with col3:
        if st.button("Next ➡️"):
            st.session_state.current_meditation_index = (
                st.session_state.current_meditation_index + 1
            ) % len(meditations)
            st.rerun()
    
    # Display meditation content
    st.markdown("### Transcript")
    st.write(current_meditation['content'])

# Main app logic
def main():
    if st.session_state.current_screen == 'create':
        create_meditation_screen()
    else:
        play_meditation_screen()

if __name__ == "__main__":
    st.set_page_config(
        page_title="Meditation App",
        page_icon="🧘‍♀️",
        layout="wide"
    )
    main()