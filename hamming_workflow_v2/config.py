import os
from dotenv import load_dotenv

# Load environment variables from .env file
load_dotenv()


class Config:
    """Configuration management for Hamming CI Workflow v2."""
    
    # API Configuration
    HAMMING_API_KEY = os.environ.get("HAMMING_API_KEY")
    HAMMING_API_BASE_URL = os.environ.get("HAMMING_API_BASE_URL", "https://app.hamming.ai/api/rest")
    
    # Agent Configuration
    AGENT_ID = os.environ.get("AGENT_ID")
    
    # Test Selection
    TAG_IDS = os.environ.get("TAG_IDS")
    TEST_CASE_IDS = os.environ.get("TEST_CASE_IDS")
    
    # Phone Numbers
    PHONE_NUMBERS = os.environ.get("PHONE_NUMBERS")
    
    # Monitoring Configuration
    POLL_INTERVAL_SECONDS = int(os.environ.get("POLL_INTERVAL_SECONDS", "10"))
    TIMEOUT_SECONDS = int(os.environ.get("TIMEOUT_SECONDS", "600"))
    
    @classmethod
    def validate_required(cls):
        """Validate that required configuration is present."""
        errors = []
        
        if not cls.HAMMING_API_KEY:
            errors.append("HAMMING_API_KEY is not set")
        
        if not cls.AGENT_ID:
            errors.append("AGENT_ID is not set")
        
        if not cls.PHONE_NUMBERS:
            errors.append("PHONE_NUMBERS is not set")
        
        if not cls.TAG_IDS and not cls.TEST_CASE_IDS:
            errors.append("Either TAG_IDS or TEST_CASE_IDS must be set")
        
        if errors:
            raise ValueError(f"Configuration errors: {'; '.join(errors)}")
    
    @classmethod
    def get_headers(cls):
        """Get headers for API requests."""
        return {
            "Content-Type": "application/json",
            "Authorization": f"Bearer {cls.HAMMING_API_KEY}"
        }