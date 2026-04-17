import logging
import json
import re
import time
from abc import ABC, abstractmethod
from typing import Optional, Dict

logger = logging.getLogger(__name__)

class BaseAgent(ABC):
    """
    Standardizes all CrewAI and LLM operations across the app.
    Implements robust error-handling, rate-limit retries, and JSON extraction.
    """
    
    @abstractmethod
    def execute(self, *args, **kwargs) -> Dict:
        pass
    
    def extract_json(self, raw: str) -> Optional[Dict]:
        """Safely extract JSON from messy LLM response."""
        if not raw:
            return None
            
        try:
            return json.loads(raw)
        except json.JSONDecodeError:
            pass
            
        try:
            # Regex extraction for JSON objects
            match = re.search(r"\{.*\}", raw, re.DOTALL)
            if match:
                return json.loads(match.group())
        except json.JSONDecodeError:
            pass
            
        logger.error(f"Failed to extract JSON from LLM: {raw[:200]}")
        return None

    def execute_with_retries(self, func, *args, retries=3):
        """Exponential backoff mechanism for rate-limited AI models."""
        for attempt in range(retries):
            try:
                return func(*args)
            except Exception as e:
                err_msg = str(e).lower()
                if "rate limit" in err_msg or "429" in err_msg:
                    delay = (attempt + 1) * 3
                    logger.warning(f"Rate limited. Retrying in {delay}s...")
                    time.sleep(delay)
                else:
                    logger.error(f"Agent Execution Error: {e}")
                    raise
                    
        raise Exception("Agent failed after maximum retries.")
