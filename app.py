import os
import streamlit as st
import tempfile
import time
import ollama
import speech_recognition as sr
from pydub import AudioSegment
from dotenv import load_dotenv

# Load environment variables
load_dotenv()

# Initialize Ollama
try:
    # Check if Ollama is running
    ollama.list()
except:
    st.error("Ollama is not running. Please start Ollama service first.")
    st.stop()

# Set page config
st.set_page_config(
    page_title="Meeting Notes & Action Items Extractor",
    page_icon="🎙️",
    layout="wide"
)

def transcribe_audio(audio_file_path):
    """Transcribe audio using SpeechRecognition and Ollama"""
    try:
        # Convert audio to WAV if needed
        audio = AudioSegment.from_file(audio_file_path)
        wav_path = os.path.splitext(audio_file_path)[0] + ".wav"
        audio.export(wav_path, format="wav")
        
        # Initialize recognizer
        r = sr.Recognizer()
        
        # Open the WAV file
        with sr.AudioFile(wav_path) as source:
            # Listen for the data (load audio to memory)
            audio_data = r.record(source)
            
            # Recognize (convert from speech to text)
            text = r.recognize_google(audio_data)  # Using Google's free API for initial transcription
            
        # Clean up temporary WAV file
        if os.path.exists(wav_path):
            os.remove(wav_path)
            
        return text
    except Exception as e:
        st.error(f"Error during audio transcription: {str(e)}")
        return None

def extract_meeting_notes(transcript):
    """Use Ollama with llama3 to extract structured notes and action items"""
    try:
        prompt = f"""Extract key points, decisions, and action items from this meeting transcript. 
        Format the response with clear sections for 'Key Points', 'Decisions', and 'Action Items'. 
        For action items, include assignees and deadlines if mentioned.
        
        Transcript:
        {transcript}"""
        
        # Use Ollama to generate the response
        response = ollama.chat(model='tinyllama', messages=[
            {
                'role': 'user',
                'content': prompt,
            },
        ])
        
        return response['message']['content']
    except Exception as e:
        st.error(f"Error generating meeting notes: {str(e)}")
        return None

def main():
    st.title("🎙️ Meeting Notes & Action Items Extractor")
    st.write("Upload your meeting audio file and get structured notes with action items.")
    
    # File uploader
    uploaded_file = st.file_uploader("Upload Meeting Audio", type=["mp3", "wav", "m4a"])
    
    if uploaded_file is not None:
        with st.spinner("Processing your audio file..."):
            # Save uploaded file to a temporary file
            with tempfile.NamedTemporaryFile(delete=False, suffix=os.path.splitext(uploaded_file.name)[1]) as tmp_file:
                tmp_file.write(uploaded_file.getvalue())
                tmp_file_path = tmp_file.name
            
            try:
                # Transcribe audio
                st.info("Transcribing audio...")
                transcript = transcribe_audio(tmp_file_path)
                
                if transcript:
                    with st.expander("View Transcript"):
                        st.write(transcript)
                    
                    # Extract meeting notes
                    st.info("Generating meeting notes...")
                    meeting_notes = extract_meeting_notes(transcript)
                    
                    if meeting_notes:
                        st.success("Meeting Notes & Action Items")
                        st.markdown("---")
                        st.markdown(meeting_notes)
                        
                        # Add download button
                        st.download_button(
                            label="Download Notes",
                            data=meeting_notes,
                            file_name=f"meeting_notes_{int(time.time())}.md",
                            mime="text/markdown"
                        )
            finally:
                # Clean up the temporary file
                if os.path.exists(tmp_file_path):
                    os.unlink(tmp_file_path)

if __name__ == "__main__":
    main()
