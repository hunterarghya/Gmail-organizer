import os
import yaml
from typing import Any, Type
from dotenv import load_dotenv
from pydantic import BaseModel, Field
from crewai import Agent, Task, Crew, LLM
from crewai.tools import BaseTool
from langchain_community.agent_toolkits import GmailToolkit

load_dotenv()

groq_llm = LLM(
    model="groq/llama-3.3-70b-versatile", 
    temperature=0.0
    )


class GmailSearchSchema(BaseModel):
    query: str = Field(..., description="The Gmail search query (e.g., 'is:unread').")

class GmailDraftSchema(BaseModel):
    body: str = Field(..., description="Content of the email.")
    to: str = Field(..., description="Recipient email address.")
    subject: str = Field(..., description="Subject line.")


class GmailSearch(BaseTool):
    name: str = "search_gmail"
    description: str = "Search Gmail for unread emails and return snippets."
    args_schema: Type[BaseModel] = GmailSearchSchema
    api_resource: Any

    def _run(self, query: str) -> str:
        results = self.api_resource.users().messages().list(userId='me', q=query, maxResults=5).execute()
        messages = results.get('messages', [])
        output = []
        for msg in messages:
            m = self.api_resource.users().messages().get(userId='me', id=msg['id']).execute()
            # Extracting "From" address to solve the "example@example.com" issue
            headers = m.get('payload', {}).get('headers', [])
            sender = next((h['value'] for h in headers if h['name'] == 'From'), "Unknown")
            snippet = m.get('snippet')
            output.append(f"ID: {msg['id']} | From: {sender} | Snippet: {snippet}")
        return "\n".join(output) if output else "No emails found."

class GmailDraft(BaseTool):
    name: str = "create_draft"
    description: str = "Create a draft email. REQUIRES 'to', 'subject', and 'body'."
    args_schema: Type[BaseModel] = GmailDraftSchema
    api_resource: Any

    def _run(self, body: str, to: str, subject: str) -> str:
        from email.message import EmailMessage
        import base64
        message = EmailMessage()
        message.set_content(body)
        message['To'] = to
        message['From'] = 'me'
        message['Subject'] = subject
        encoded_message = base64.urlsafe_b64encode(message.as_bytes()).decode()
        create_message = {'message': {'raw': encoded_message}}
        draft = self.api_resource.users().drafts().create(userId='me', body=create_message).execute()
        return f"Draft created successfully. Draft ID: {draft['id']}"


class ZeroInboxCrew:
    def __init__(self):
        # Load YAML configs
        with open('config/agents.yaml', 'r') as f:
            self.agents_config = yaml.safe_load(f)
        with open('config/tasks.yaml', 'r') as f:
            self.tasks_config = yaml.safe_load(f)

        # Setup Gmail
        toolkit = GmailToolkit()
        self.api_resource = toolkit.api_resource
        self.search_tool = GmailSearch(api_resource=self.api_resource)
        self.send_tool = GmailDraft(api_resource=self.api_resource)

    def run(self):
        # Define Agents using YAML
        classifier = Agent(
            config=self.agents_config['classifier'],
            tools=[self.search_tool],
            llm=groq_llm,
            verbose=True,
            allow_delegation=False
        )

        responder = Agent(
            config=self.agents_config['responder'],
            tools=[self.send_tool],
            llm=groq_llm,
            verbose=True,
            allow_delegation=False
        )

        # Define Tasks using YAML
        triage_task = Task(
            config=self.tasks_config['triage_task'],
            agent=classifier
        )

        action_task = Task(
            config=self.tasks_config['action_task'],
            agent=responder,
            context=[triage_task] # Passes results of triage to responder
        )

        return Crew(
            agents=[classifier, responder], 
            tasks=[triage_task, action_task], 
            verbose=True
        ).kickoff()

if __name__ == "__main__":
    ZeroInboxCrew().run()