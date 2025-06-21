#!/usr/bin/env python
from pydantic import BaseModel
from crewai.flow import Flow, listen, start
from dotenv import load_dotenv
import google.generativeai as genai
from pydub import AudioSegment
from pydub.utils import make_chunks
from pathlib import Path
import whisper
from datetime import date
import datetime
import os
import re

import streamlit as st

from crews.meeting_minutes_crew.meeting_minutes_crew import MeetingMinutesCrew
from crews.gmailcrew.gmailcrew import Gmailcrew

def is_valid_mail(email):
    return re.match(r"[^@]+@[^@]+\.[^@]+", email)


load_dotenv()
GEMINI_API_KEY = os.getenv("GEMINI_API_KEY")

model = whisper.load_model("base")


class MeetingMinutesState(BaseModel):
    transcript: str = ""
    meeting_minutes: str = ""


class MeetingMinutesFlow(Flow[MeetingMinutesState]):
    def __init__(self, organizer_name, company_name, today_date,  meeting_platform, sender_mail, subject, to_mails):
        super().__init__()
        self.organizer_name = organizer_name
        self.company_name = company_name
        self.today_date = today_date
        self.meeting_platform = meeting_platform
        self.sender_mail = sender_mail
        self.subject = subject
        self.to_mails = to_mails


    @start()
    def transcribe_meeting(self):
        print("Generating Transcription")
        SCRIPT_DIR = Path(__file__).parent
        audio_path = str(SCRIPT_DIR / uploaded_file.name)
        audio = AudioSegment.from_file(audio_path, format="wav")

        chunk_length_ms = 60000
        chunks = make_chunks(audio, chunk_length_ms)


        full_transcription = ""
        for i, chunk in enumerate(chunks):

            print(f"Transcribing chunks {i+1}/{len(chunks)}")
            # placeholder.markdown(f"<h3 style='font-size:22px;'>Transcribing chunks {i+1}/{len(chunks)}</h3>", unsafe_allow_html=True)
            chunk_path = f"{SCRIPT_DIR}/chunk_{i}.wav"
            chunk.export(chunk_path, format="wav")
            
            transcription = model.transcribe(chunk_path)

            full_transcription += transcription["text"] + " "
            os.remove(chunk_path)
        
        self.state.transcript = full_transcription
        os.remove(audio_path)
        print(f"Transcription {self.state.transcript}")


  
    @listen(transcribe_meeting)
    def generate_meeting_minutes(self):
        print("Generating Meeting Minutes")
        # placeholder.markdown("<h3 style='font-size:22px;'>Generating Meeting Minutes...</h3>", unsafe_allow_html=True)
        crew = MeetingMinutesCrew()
        inputs = {
            "transcript": self.state.transcript,
            "date_today": self.today_date,
            "company_name": self.company_name,
            "organizer_name": self.organizer_name,
            "location": self.meeting_platform
        }
        meeting_minutes = crew.crew().kickoff(inputs)
        print(type(meeting_minutes))
        if hasattr(meeting_minutes, "result"):
            self.state.meeting_minutes = meeting_minutes.result
        else:
            self.state.meeting_minutes = str(meeting_minutes)
        print(self.state.meeting_minutes)
        print(type(self.state.meeting_minutes))


    @listen(generate_meeting_minutes)
    # @start()
    def create_draft_meeting_minutes(self):
        print("Creating draft Meeting Minutes")
        # placeholder.markdown("<h3 style='font-size:22px;'>Creating draft Meeting Minutes</h3>", unsafe_allow_html=True)

        crew = Gmailcrew()

        inputs = {
            "body": self.state.meeting_minutes,
            "sender": self.sender_mail,
            "subject": self.subject,
            "to": self.to_mails
        }

        draft_crew = crew.crew().kickoff(inputs)
        print(f"Draft crew: {draft_crew}")
        # placeholder.markdown("")
        return self.state.meeting_minutes
    

# def kickoff():
#     meeting_minutes_flow = MeetingMinutesFlow()
#     meeting_minutes_flow.plot()
#     meeting_minutes_flow.kickoff()


# if __name__ == "__main__":
#     kickoff()

st.markdown("""
    <style>
        .st-emotion-cache-zy6yx3 {
            padding-top: 1rem;
        }
    </style>
""", unsafe_allow_html=True)

st.title('Crew AI Meeting Minutes')
st.divider()

st.set_page_config(layout="wide")


col1, col2 = st.columns([1,2])

with col1:
    uploaded_file = st.file_uploader("Upload an audio file", type=["mp3", "wav", "ogg"])

    with st.form("my_form"):
        organizer_name = st.text_input("Enter name")
        company_name = st.text_input("Enter company name")
        today_date = st.date_input("Enter meeting date", datetime.date.today())
        meeting_platform = st.text_input("Enter meeting platform")
        sender_mail = st.text_input("Enter senders mail")
        subject = st.text_input("Enter Subject")
        to_mail_options = st.multiselect(
            "Enter receivers mail",
            key="to_emails",
            accept_new_options=True,
            options=[]
        )
        submit = st.form_submit_button('Generate minutes')


with col2:
    st.header("Minutes Minutes:")
    # placeholder = st.empty()


def submit_form():
    if not(organizer_name and company_name and sender_mail):
        st.warning("Please enter all details")
        return
    else:
        if not is_valid_mail(sender_mail):
            st.warning("Please enter a vlaid email")
            return
    
    with col2:
        # placeholder.markdown("<h3 style='font-size:22px;'>Saving audio...</h3>", unsafe_allow_html=True)
        with st.spinner("Generating mail draft..."):
            meeting_minutes_flow = MeetingMinutesFlow(
                organizer_name,
                company_name,
                today_date.strftime("%B %d %Y"),
                meeting_platform,
                sender_mail,
                subject,
                ",".join(to_mail_options)
            )
            mail_draft = meeting_minutes_flow.kickoff()
        st.markdown(f'''{mail_draft.replace("```markdown", "").replace("```","")}''')

def save_auido():   
    SCRIPT_DIR = Path(__file__).parent
    with open(os.path.join(SCRIPT_DIR, uploaded_file.name), "wb") as f:
        f.write(uploaded_file.getbuffer())
    st.write(f"Saved file: {uploaded_file.name}")


# if uploaded_file is not None:
#     save_auido()
#     submit_form()


if submit:
    if uploaded_file is not None:
        save_auido()
        submit_form()
    else:
        st.warning('Upload a file')
            

