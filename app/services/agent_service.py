import openai
from openai import OpenAI
from typing import Dict, Any, List, Optional
import uuid
import json
from datetime import datetime

from app.config import OPENAI_API_KEY, OPENAI_MODEL
from app.models.conversation import Message, MessageRole


class AgentService:
    """Service for interacting with the OpenAI Agent."""
    
    def __init__(self):
        """Initialize the agent service."""
        self.client = OpenAI(api_key=OPENAI_API_KEY)
        self.model = OPENAI_MODEL
        self.system_prompt = """
        You are a helpful voice assistant speaking with a user over the phone.
        
        Guidelines:
        1. Keep your responses concise and conversational - remember this is a phone call.
        2. Speak clearly and use natural language appropriate for voice.
        3. Avoid references to visual elements or sending links.
        4. Always be helpful, friendly, and respectful.
        5. If you don't know something, be honest about it.
        
        The user is speaking to you through a phone call. They can't see you, and you can't see them.
        """
        self.conversation_store = {}  # In-memory store of conversations
        
    def create_conversation(self, call_sid: str, phone_number: str) -> str:
        """
        Create a new conversation.
        
        Args:
            call_sid: Twilio call SID
            phone_number: User's phone number
            
        Returns:
            Conversation ID
        """
        conversation_id = str(uuid.uuid4())
        
        # Initialize with system message
        initial_messages = [
            {
                "role": "system",
                "content": self.system_prompt,
                "timestamp": datetime.now().isoformat()
            }
        ]
        
        self.conversation_store[conversation_id] = {
            "id": conversation_id,
            "call_sid": call_sid,
            "phone_number": phone_number,
            "messages": initial_messages,
            "start_time": datetime.now().isoformat(),
            "end_time": None,
            "context": {}
        }
        
        return conversation_id
        
    def process_user_input(self, conversation_id: str, user_input: str) -> Dict[str, Any]:
        """
        Process user input and get a response from the OpenAI model.
        
        Args:
            conversation_id: Conversation ID
            user_input: User's input text
            
        Returns:
            Dict containing the agent's response
        """
        # Get the conversation
        conversation = self.conversation_store.get(conversation_id)
        if not conversation:
            return {"error": "Conversation not found"}
        
        # Prepare messages for the OpenAI API
        messages = []
        for msg in conversation["messages"]:
            messages.append({
                "role": msg["role"],
                "content": msg["content"]
            })
        
        # Add user message to conversation
        user_message = {
            "role": "user",
            "content": user_input,
            "timestamp": datetime.now().isoformat()
        }
        conversation["messages"].append(user_message)
        
        # Add user message to API request
        messages.append({
            "role": "user", 
            "content": user_input
        })
        
        # Get response from OpenAI
        try:
            response = self.client.chat.completions.create(
                model=self.model,
                messages=messages,
                temperature=0.7
            )
            
            assistant_response = response.choices[0].message.content
            
            # Add assistant message to conversation
            assistant_message = {
                "role": "assistant",
                "content": assistant_response,
                "timestamp": datetime.now().isoformat()
            }
            conversation["messages"].append(assistant_message)
            
            return {
                "conversation_id": conversation_id,
                "response": assistant_response
            }
            
        except Exception as e:
            return {
                "error": f"Failed to get response: {str(e)}"
            }
        
    def get_conversation(self, conversation_id: str) -> Optional[Dict[str, Any]]:
        """
        Get a conversation by ID.
        
        Args:
            conversation_id: Conversation ID
            
        Returns:
            Conversation data or None if not found
        """
        return self.conversation_store.get(conversation_id)
        
    def end_conversation(self, conversation_id: str) -> Dict[str, Any]:
        """
        End a conversation.
        
        Args:
            conversation_id: Conversation ID
            
        Returns:
            Updated conversation data
        """
        conversation = self.conversation_store.get(conversation_id)
        if not conversation:
            return {"error": "Conversation not found"}
        
        conversation["end_time"] = datetime.now().isoformat()
        return conversation
        
    def get_messages_for_transcript(self, conversation_id: str) -> List[Dict[str, Any]]:
        """
        Get messages formatted for transcript.
        
        Args:
            conversation_id: Conversation ID
            
        Returns:
            List of formatted messages
        """
        conversation = self.conversation_store.get(conversation_id)
        if not conversation:
            return []
        
        return conversation["messages"]