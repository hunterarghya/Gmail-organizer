import os
import yaml
import base64
from typing import Any, Type
from pydantic import BaseModel, Field
from crewai import Agent, Task, Crew, LLM
from crewai.tools import BaseTool
from google.oauth2.credentials import Credentials
from googleapiclient.discovery import build
from google.auth.transport.requests import Request
from email.message import EmailMessage
from backend.core.config import settings
import re


def extract_email(sender: str) -> str:
    match = re.search(r"<(.+?)>", sender)
    if match:
        return match.group(1)
    return sender.strip()

groq_llm = LLM(model="groq/llama-3.3-70b-versatile", temperature=0.0)

class GmailSearchSchema(BaseModel):
    query: str = Field(..., description="Gmail search query.")

class GmailDraftSchema(BaseModel):
    body: str = Field(..., description="Email body.")
    to: str = Field(..., description="Recipient email.")
    subject: str = Field(..., description="Subject line.")

class GmailSearch(BaseTool):
    name: str = "search_gmail"
    description: str = "Search unread emails."
    args_schema: Type[BaseModel] = GmailSearchSchema
    creds_data: dict

    def _run(self, query: str) -> str:
        try:
            
            creds = Credentials.from_authorized_user_info(self.creds_data)
            if creds.expired and creds.refresh_token:
                creds.refresh(Request())
            
            service = build('gmail', 'v1', credentials=creds)
            results = service.users().messages().list(userId='me', q=query, maxResults=10).execute()
            messages = results.get('messages', [])
            
            if not messages: return "No unread emails found."

            
            import json

            emails = []

            for msg in messages:
                m = service.users().messages().get(userId='me', id=msg['id']).execute()
                headers = m.get('payload', {}).get('headers', [])
                
                subject = next((h['value'] for h in headers if h['name'] == 'Subject'), "No Subject")
                
                sender_raw = next((h['value'] for h in headers if h['name'] == 'From'), "Unknown")
                sender = extract_email(sender_raw)

                emails.append({
                    "id": msg["id"],
                    "sender": sender,
                    "subject": subject,
                    "snippet": m.get("snippet")
                })

            return json.dumps(emails)
        except Exception as e:
            raise Exception(f"Gmail Tool Error: {str(e)}")

class GmailDraft(BaseTool):
    name: str = "create_draft"
    description: str = "Create a draft email."
    args_schema: Type[BaseModel] = GmailDraftSchema
    creds_data: dict

    def _run(self, body: str, to: str, subject: str) -> str:
        try:
            creds = Credentials.from_authorized_user_info(self.creds_data)
            if creds.expired and creds.refresh_token:
                creds.refresh(Request())
            service = build('gmail', 'v1', credentials=creds)

            message = EmailMessage()
            message.set_content(body)
            message['To'] = to
            message['From'] = 'me'
            message['Subject'] = subject
            
            raw = base64.urlsafe_b64encode(message.as_bytes()).decode()
            service.users().drafts().create(userId='me', body={'message': {'raw': raw}}).execute()
            return f"SUCCESS: Draft created for {to}"
        except Exception as e:
            raise Exception(f"Draft Error: {str(e)}")

class ZeroInboxCrew:
    def __init__(self, google_token_dict: dict):
        
        self.creds_bundle = {
            "token": google_token_dict.get("access_token"),
            "refresh_token": google_token_dict.get("refresh_token"),
            "token_uri": "https://oauth2.googleapis.com/token",
            "client_id": settings.GOOGLE_CLIENT_ID,
            "client_secret": settings.GOOGLE_CLIENT_SECRET,
            "scopes": google_token_dict.get("scope", "").split()
        }

        print("CREDS_BUNDLE:", self.creds_bundle)
        
        with open('config/agents.yaml', 'r') as f: self.agents_config = yaml.safe_load(f)
        with open('config/tasks.yaml', 'r') as f: self.tasks_config = yaml.safe_load(f)

    def run_workflow(self):
        
        search_tool = GmailSearch(creds_data=self.creds_bundle)
        draft_tool = GmailDraft(creds_data=self.creds_bundle)

        classifier = Agent(config=self.agents_config['classifier'], tools=[search_tool], llm=groq_llm, verbose=True, max_iter=2)
        responder = Agent(config=self.agents_config['responder'], tools=[draft_tool], llm=groq_llm, verbose=True, max_iter=2)

        triage_task = Task(config=self.tasks_config['triage_task'], agent=classifier)
        action_task = Task(config=self.tasks_config['action_task'], agent=responder, context=[triage_task])

        return Crew(agents=[classifier, responder], tasks=[triage_task, action_task], verbose=True).kickoff()