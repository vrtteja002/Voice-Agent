from google.cloud import storage
import json
import os
from datetime import datetime
from typing import Dict, List, Any

from app.config import GCS_BUCKET_NAME


class StorageService:
    def __init__(self):
        self.storage_client = storage.Client()
        self.bucket = self.storage_client.bucket(GCS_BUCKET_NAME)

    def upload_file(self, source_file_path: str, destination_blob_name: str) -> str:
        """
        Upload a file to Google Cloud Storage.
        
        Args:
            source_file_path: Path to the local file
            destination_blob_name: Name to give the file in GCS
            
        Returns:
            Public URL of the uploaded file
        """
        blob = self.bucket.blob(destination_blob_name)
        blob.upload_from_filename(source_file_path)
        
        # Make the blob publicly accessible
        blob.make_public()
        
        # Delete the local file after uploading
        os.remove(source_file_path)
        
        return blob.public_url

    def upload_transcript(self, conversation_id: str, messages: List[Dict[str, Any]]) -> str:
        """
        Upload conversation transcript to GCS.
        
        Args:
            conversation_id: Unique ID for the conversation
            messages: List of message objects
            
        Returns:
            Public URL of the uploaded transcript
        """
        transcript_content = {
            "conversation_id": conversation_id,
            "timestamp": datetime.now().isoformat(),
            "messages": messages
        }
        
        # Convert to JSON string
        transcript_json = json.dumps(transcript_content, indent=2)
        
        # Create a blob and upload the transcript
        destination_blob_name = f"transcripts/{conversation_id}.json"
        blob = self.bucket.blob(destination_blob_name)
        blob.upload_from_string(transcript_json, content_type="application/json")
        
        # Make the blob publicly accessible
        blob.make_public()
        
        return blob.public_url