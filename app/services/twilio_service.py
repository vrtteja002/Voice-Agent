from twilio.rest import Client
from twilio.twiml.voice_response import VoiceResponse, Gather
import base64
import tempfile
import os

from app.config import TWILIO_ACCOUNT_SID, TWILIO_AUTH_TOKEN, TWILIO_PHONE_NUMBER, BASE_URL


class TwilioService:
    def __init__(self):
        self.client = Client(TWILIO_ACCOUNT_SID, TWILIO_AUTH_TOKEN)
        self.phone_number = TWILIO_PHONE_NUMBER

    def generate_welcome_twiml(self) -> str:
        """Generate TwiML for the welcome message."""
        response = VoiceResponse()
        response.say(
            "Hello! I'm your AI assistant. How can I help you today?",
            voice="Polly.Amy-Neural"
        )
        
        gather = Gather(
            input='speech',
            action=f"{BASE_URL}/api/voice/response",
            method='POST',
            speechTimeout='auto',
            speechModel='phone_call',
            enhanced='true'
        )
        response.append(gather)
        
        # If no input is received, retry
        response.redirect(f"{BASE_URL}/api/voice/welcome")
        
        return str(response)

    def generate_response_twiml(self, ai_response: str) -> str:
        """Generate TwiML with AI response and listen for next input."""
        response = VoiceResponse()
        response.say(ai_response, voice="Polly.Amy-Neural")
        
        gather = Gather(
            input='speech',
            action=f"{BASE_URL}/api/voice/response",
            method='POST',
            speechTimeout='auto',
            speechModel='phone_call',
            enhanced='true'
        )
        response.append(gather)
        
        # If no input is received, end the call
        response.say("I didn't hear anything. Thank you for calling. Goodbye!", voice="Polly.Amy-Neural")
        response.hangup()
        
        return str(response)

    def generate_goodbye_twiml(self) -> str:
        """Generate TwiML for the goodbye message."""
        response = VoiceResponse()
        response.say(
            "Thank you for calling. Goodbye!",
            voice="Polly.Amy-Neural"
        )
        response.hangup()
        
        return str(response)

    def save_recording(self, audio_data: str) -> str:
        """
        Save base64 encoded audio data to a temporary file.
        
        Args:
            audio_data: Base64 encoded audio data
            
        Returns:
            Path to the saved temporary file
        """
        if not audio_data:
            return None
            
        # Remove data URL prefix if present
        if audio_data.startswith('data:audio/'):
            audio_data = audio_data.split(',')[1]
            
        # Decode the base64 data
        decoded_data = base64.b64decode(audio_data)
        
        # Save to a temporary file
        with tempfile.NamedTemporaryFile(delete=False, suffix='.wav') as temp_file:
            temp_file.write(decoded_data)
            return temp_file.name