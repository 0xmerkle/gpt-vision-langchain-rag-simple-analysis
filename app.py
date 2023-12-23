import streamlit as st
from pathlib import Path
from deck_analysis import (
    analyze_pitch_deck,
    save_pitchdeck_images,
    add_documents_to_chroma,
    chain as analyst_chain,
)
from streamlit_chat import message

st.title("Pitch Deck Analyzer")

# Initialize session state variables
if "file_processed" not in st.session_state:
    st.session_state.file_processed = False
if "analysis_result" not in st.session_state:
    st.session_state.analysis_result = None

if "chat_history" not in st.session_state:
    st.session_state.chat_history = []

uploaded_file = st.file_uploader("Upload your pitch deck PDF", type=["pdf"])

if uploaded_file is not None and not st.session_state.file_processed:
    progress_bar = st.progress(0)

    image_paths = save_pitchdeck_images(uploaded_file)
    progress_bar.progress(25)

    st.session_state.analysis_result = analyze_pitch_deck(Path(image_paths[0]).parent)
    st.session_state.file_processed = True
    progress_bar.progress(50)

    description_file = st.session_state.analysis_result["file_path"]
    documents_added = add_documents_to_chroma(file_path=description_file)
    st.write(documents_added)
    progress_bar.progress(100)

if st.session_state.file_processed:
    st.header("Pitch Deck Analysis")
    st.write(st.session_state.analysis_result["description"])
    st.write(st.session_state.analysis_result["file_path"])

st.header("Ask me anything about the pitch deck!")
user_input = st.text_input("You:", key="user_query")
if st.button("Enter") and user_input:
    response = analyst_chain.invoke(user_input)
    st.session_state.chat_history.append({"text": response, "is_user": False})

    message(response, is_user=False)
