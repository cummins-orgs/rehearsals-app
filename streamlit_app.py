import streamlit as st

st.title("Rehearsals")
st.write(
    "Let's start building! For help and inspiration, head over to [docs.streamlit.io](https://docs.streamlit.io/)."
)

testy = st.chat_input(placeholder="Your message", key=None, max_chars=None, disabled=False, on_submit=None, args=None, kwargs=None)

st.write("testy lives here")
if testy != None:
    testy 