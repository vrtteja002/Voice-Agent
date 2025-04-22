from fastapi import APIRouter, Request, HTTPException, Depends, Form
from fastapi.responses import Response, JSONResponse
import uuid
from datetime import datetime
import json

from app.services.agent_service import AgentService
from app.services.twilio_service import TwilioService
from app.services.storage_service import StorageService

router = APIRouter(prefix="/api/voice", tags=["voice"])

# Store active conversations
active_conversations = {}


def get_agent_service():
    return AgentService()


def get_twilio_service():
    return TwilioService()


def get_storage_service():
    return StorageService()


@router.post("/incoming")
async def incoming_call(
    request: Request,
    agent_service: AgentService = Depends(get_agent_service),
    twilio_service: TwilioService = Depends(get_twilio_service)
):
    """Handle incoming Twilio voice calls."""
    form_data = await request.form()
    call_sid = form_data.get("CallSid")
    phone_number = form_data.get("From")
    
    # Create a new conversation
    conversation_id = agent_service.create_conversation(
        call_sid=call_sid,
        phone_number=phone_number
    )
    
    # Store the conversation ID
    active_conversations[call_sid] = conversation_id
    
    # Return welcome TwiML
    welcome_twiml = twilio_service.generate_welcome_twiml()
    return Response(content=welcome_twiml, media_type="application/xml")


@router.post("/welcome")
async def welcome(
    twilio_service: TwilioService = Depends(get_twilio_service)
):
    """Return welcome message TwiML."""
    welcome_twiml = twilio_service.generate_welcome_twiml()
    return Response(content=welcome_twiml, media_type="application/xml")


@router.post("/response")
async def process_response(
    request: Request,
    agent_service: AgentService = Depends(get_agent_service),
    twilio_service: TwilioService = Depends(get_twilio_service)
):
    """Process user speech and respond with AI."""
    form_data = await request.form()
    call_sid = form_data.get("CallSid")
    user_input = form_data.get("SpeechResult")
    
    # Check if the conversation exists
    if call_sid not in active_conversations:
        # If not, create a new conversation
        conversation_id = agent_service.create_conversation(
            call_sid=call_sid,
            phone_number=form_data.get("From")
        )
        active_conversations[call_sid] = conversation_id
    else:
        conversation_id = active_conversations[call_sid]
    
    # Process the user input
    result = agent_service.process_user_input(
        conversation_id=conversation_id,
        user_input=user_input
    )
    
    if "error" in result:
        ai_response = "I'm sorry, I encountered an error. Please try again later."
    else:
        ai_response = result["response"]
    
    # Generate TwiML with AI response
    response_twiml = twilio_service.generate_response_twiml(ai_response)
    
    return Response(content=response_twiml, media_type="application/xml")


@router.post("/end")
async def end_call(
    request: Request,
    agent_service: AgentService = Depends(get_agent_service),
    storage_service: StorageService = Depends(get_storage_service)
):
    """Handle call completion and store transcript."""
    form_data = await request.form()
    call_sid = form_data.get("CallSid")
    recording_url = form_data.get("RecordingUrl")
    
    if call_sid not in active_conversations:
        return JSONResponse(
            content={"error": "Call not found"},
            status_code=404
        )
    
    conversation_id = active_conversations[call_sid]
    
    # End the conversation
    conversation = agent_service.end_conversation(conversation_id)
    
    # Get messages for transcript
    messages = agent_service.get_messages_for_transcript(conversation_id)
    
    # Upload transcript to GCS
    transcript_url = storage_service.upload_transcript(
        conversation_id,
        messages
    )
    
    # Update conversation with recording URL and transcript URL
    if recording_url:
        conversation["audio_url"] = recording_url
    conversation["transcript_url"] = transcript_url
    
    # Clean up
    del active_conversations[call_sid]
    
    return JSONResponse(
        content={
            "conversation_id": conversation_id,
            "transcript_url": transcript_url
        }
    )


@router.post("/record")
async def record_audio(
    request: Request,
    agent_service: AgentService = Depends(get_agent_service),
    storage_service: StorageService = Depends(get_storage_service)
):
    """Store audio recording from call."""
    form_data = await request.form()
    call_sid = form_data.get("CallSid")
    recording_sid = form_data.get("RecordingSid")
    recording_url = form_data.get("RecordingUrl")
    
    if call_sid in active_conversations:
        conversation_id = active_conversations[call_sid]
        conversation = agent_service.get_conversation(conversation_id)
        if conversation:
            conversation["audio_url"] = recording_url
    
    return JSONResponse(
        content={"status": "success", "recording_url": recording_url}
    )