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
import os

from crews.meeting_minutes_crew.meeting_minutes_crew import MeetingMinutesCrew
from crews.gmailcrew.gmailcrew import Gmailcrew


load_dotenv()
GEMINI_API_KEY = os.getenv("GEMINI_API_KEY")

model = whisper.load_model("base")

# client = genai.Client(api_key="GEMINI_API_KEY")

class MeetingMinutesState(BaseModel):
    transcript: str = ""
    meeting_minutes: str = ""


class MeetingMinutesFlow(Flow[MeetingMinutesState]):

    @start()
    def transcribe_meeting(self):
        print("Generating Transcription")

        SCRIPT_DIR = Path(__file__).parent
        audio_path = str(SCRIPT_DIR / "EarningsCall.wav")

        audio = AudioSegment.from_file(audio_path, format="wav")

        chunk_length_ms = 60000
        chunks = make_chunks(audio, chunk_length_ms)


        full_transcription = ""
        for i, chunk in enumerate(chunks):

            print(f"Transcribing chunks {i+1}/{len(chunks)}")
            chunk_path = f"{SCRIPT_DIR}/chunk_{i}.wav"
            chunk.export(chunk_path, format="wav")
            
            transcription = model.transcribe(chunk_path)

            full_transcription += transcription["text"] + " "
            os.remove(chunk_path)
        
        self.state.transcript = full_transcription
        print(f"Transcription {self.state.transcript}")


  
    @listen(transcribe_meeting)
    def generate_meeting_minutes(self):
        print("Generating Meeting Minutes")
        crew = MeetingMinutesCrew()
        inputs = {
            "transcript": self.state.transcript,
            "date_today": date.today().strftime("%B %d %Y"),
            "company_name": "RootAgent",
            "organizer_name": "Kushal",
            "location": "Google Meet"
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

        crew = Gmailcrew()

        inputs = {
            "body": self.state.meeting_minutes
        }

        draft_crew = crew.crew().kickoff(inputs)
        print(f"Draft crew: {draft_crew}")


def kickoff():
    meeting_minutes_flow = MeetingMinutesFlow()
    meeting_minutes_flow.plot()
    meeting_minutes_flow.kickoff()


if __name__ == "__main__":
    kickoff()
