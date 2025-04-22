import json
import time
from openai import OpenAI
from typing import Dict, Any, List

from app.config import OPENAI_API_KEY, ASSISTANT_ID


class OpenAIService:
    def __init__(self):
        self.client = OpenAI(api_key=OPENAI_API_KEY)
        self.assistant_id = ASSISTANT_ID

    def create_thread(self) -> str:
        """Create a new thread for conversation."""
        thread = self.client.beta.threads.create()
        return thread.id

    def add_message(self, thread_id: str, content: str) -> str:
        """Add a user message to the thread."""
        message = self.client.beta.threads.messages.create(
            thread_id=thread_id,
            role="user",
            content=content
        )
        return message.id

    def run_assistant(self, thread_id: str) -> Dict[str, Any]:
        """Run the assistant on the thread and get a response."""
        # Create a run
        run = self.client.beta.threads.runs.create(
            thread_id=thread_id,
            assistant_id=self.assistant_id
        )
        
        # Poll until the run completes
        while True:
            run_status = self.client.beta.threads.runs.retrieve(
                thread_id=thread_id,
                run_id=run.id
            )
            
            if run_status.status == "completed":
                break
            elif run_status.status in ["failed", "cancelled", "expired"]:
                return {"error": f"Run {run_status.status}: {run_status.last_error}"}
            
            # Wait before polling again
            time.sleep(1)
        
        # Get messages (newest first)
        messages = self.client.beta.threads.messages.list(
            thread_id=thread_id
        )
        
        # Extract the latest assistant message
        for message in messages.data:
            if message.role == "assistant":
                content = message.content[0].text.value
                return {"content": content, "message_id": message.id}
        
        return {"error": "No assistant response found"}

    def get_thread_messages(self, thread_id: str) -> List[Dict[str, Any]]:
        """Get all messages from a thread."""
        messages = self.client.beta.threads.messages.list(
            thread_id=thread_id
        )
        formatted_messages = []
        for message in messages.data:
            message_content = ""
            for content_part in message.content:
                if hasattr(content_part, 'text'):
                    message_content += content_part.text.value
            
            formatted_messages.append({
                "role": message.role,
                "content": message_content,
                "created_at": message.created_at
            })
        
        return formatted_messages