from typing import Type
from crewai.tools import BaseTool
from pydantic import BaseModel, Field

from .gmail_utility import authenticate_gmail, create_draft, create_message

class GmailToolInput(BaseModel):
    """Input schema for GmailTool"""

    body: str = Field(..., description="The body of the email to send")


class GmailTool(BaseTool):
    name: str = "GmailTool"
    description: str = (
        "GmailTool will be used to create message and draft an email."
    )

    args_schema: Type[BaseModel] = GmailToolInput

    def _run(self, body: str) -> str:
        try:
            service = authenticate_gmail()

            sender = "kushalagrawal3011@gmail.com"
            to = "kushalagr04@gmail.com"
            subject = "Meeting Minutes"
            message_text = body

            message = create_message(sender=sender, to=to, subject=subject, message_text=message_text)
            draft = create_draft(service=service, user_id="me",message_body=message)

            return f"Email sent succesfully! Draft id: {draft['id']}"
        
        except Exception as e:
            return f"Error sending email: {e}"