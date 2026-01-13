"""
Project Aadhaar Sanket - AI Insight Engine

This module provides the core AI/ML interface for generating insights
from demographic data using Google's Gemini API.

Features:
- Context-aware query processing
- Retry logic with exponential backoff
- Response validation and sanitization
- Structured logging
- Graceful degradation on failures

Version: 1.0.0
"""

__all__ = ["InsightEngine"]

import time
from typing import Optional, Tuple

import google.generativeai as genai

from src.ai.config import GENERATION_CONFIG, SAFETY_SETTINGS, MODEL_NAME
from src.ai.system_context import SYSTEM_INSTRUCTION, QUERY_TEMPLATE
from src.ai.data_gateway import DataGateway
from src.ai.guardrails import check_safety
from src.exceptions import AIEngineError, APIConnectionError, ResponseValidationError
from src.logging_config import get_logger

# Module logger
logger = get_logger(__name__)

# Retry configuration
MAX_RETRIES = 3
BASE_DELAY_SECONDS = 1.0
MAX_DELAY_SECONDS = 10.0


class InsightEngine:
    """
    AI-powered insight generation engine.
    
    This engine connects to Google's Gemini API to generate natural language
    insights from demographic data. It implements guardrails, retry logic,
    and response validation for production reliability.
    
    Attributes:
        model: Gemini generative model instance
        gateway: Data gateway for context retrieval
    
    Example:
        >>> engine = InsightEngine()
        >>> response = engine.ask("What are the top migration hotspots?")
        >>> print(response)
    """
    
    def __init__(self):
        """Initialize the InsightEngine with Gemini model."""
        logger.info("Initializing InsightEngine...")
        
        try:
            self.model = genai.GenerativeModel(
                model_name=MODEL_NAME,
                system_instruction=SYSTEM_INSTRUCTION,
                generation_config=GENERATION_CONFIG,
                safety_settings=SAFETY_SETTINGS
            )
            self.gateway = DataGateway()
            logger.info(f"InsightEngine initialized with model: {MODEL_NAME}")
        except Exception as e:
            logger.error(f"Failed to initialize InsightEngine: {e}")
            raise AIEngineError(
                "Failed to initialize AI engine",
                details={"model": MODEL_NAME, "error": str(e)}
            )
    
    def _gather_context(self, query: str) -> str:
        """
        Gather relevant context data based on query keywords.
        
        Args:
            query: User's natural language query
            
        Returns:
            String representation of context data
        """
        query_lower = query.lower()
        context = {}
        
        try:
            if "national" in query_lower or "overall" in query_lower:
                context["national_summary"] = self.gateway.get_national_summary()
                
            if "top" in query_lower or "highest" in query_lower or "hotspot" in query_lower:
                context["top_districts"] = self.gateway.get_top_moving_districts(15)
                
            if "anomaly" in query_lower or "alert" in query_lower or "risk" in query_lower:
                context["anomalies"] = self.gateway.get_anomalies()
                
            # Default context if no specific keywords matched
            if not context:
                context["national_summary"] = self.gateway.get_national_summary()
                context["top_5_movers"] = self.gateway.get_top_moving_districts(5)
                
        except Exception as e:
            logger.warning(f"Context gathering partially failed: {e}")
            context["error"] = "Some data unavailable"
        
        return str(context)
    
    def _validate_response(self, response: str) -> str:
        """
        Validate and sanitize AI response.
        
        Args:
            response: Raw response from AI model
            
        Returns:
            Validated and sanitized response
            
        Raises:
            ResponseValidationError: If response is invalid
        """
        if not response or len(response.strip()) < 10:
            raise ResponseValidationError(
                "Response too short or empty",
                details={"length": len(response) if response else 0}
            )
        
        # Check for potentially harmful content
        forbidden_patterns = ["<script>", "javascript:", "data:", "onclick"]
        response_lower = response.lower()
        
        for pattern in forbidden_patterns:
            if pattern in response_lower:
                logger.warning(f"Filtered potentially harmful pattern: {pattern}")
                raise ResponseValidationError(
                    "Response contained forbidden content",
                    details={"pattern": pattern}
                )
        
        return response.strip()
    
    def _call_with_retry(
        self,
        prompt: str,
        max_retries: int = MAX_RETRIES
    ) -> str:
        """
        Call AI model with retry logic for transient failures.
        
        Implements exponential backoff with jitter.
        
        Args:
            prompt: Prompt to send to the model
            max_retries: Maximum number of retry attempts
            
        Returns:
            Model response text
            
        Raises:
            APIConnectionError: If all retries fail
        """
        last_exception = None
        
        for attempt in range(max_retries):
            try:
                logger.debug(f"AI call attempt {attempt + 1}/{max_retries}")
                response = self.model.generate_content(prompt)
                
                if response and response.text:
                    return response.text
                else:
                    raise ResponseValidationError("Empty response from model")
                    
            except ResponseValidationError:
                raise  # Don't retry validation errors
                
            except Exception as e:
                last_exception = e
                
                if attempt < max_retries - 1:
                    delay = min(
                        BASE_DELAY_SECONDS * (2 ** attempt),
                        MAX_DELAY_SECONDS
                    )
                    logger.warning(
                        f"AI call failed (attempt {attempt + 1}): {e}. "
                        f"Retrying in {delay:.1f}s..."
                    )
                    time.sleep(delay)
        
        logger.error(f"AI call failed after {max_retries} attempts")
        raise APIConnectionError(
            f"AI service unavailable after {max_retries} attempts",
            details={"last_error": str(last_exception)}
        )
    
    def ask(self, user_query: str) -> str:
        """
        Process a user query and generate an AI response.
        
        This is the main entry point for Q&A interactions.
        
        Args:
            user_query: Natural language question from user
            
        Returns:
            AI-generated response string
        """
        logger.info(f"Processing query: {user_query[:50]}...")
        
        # Step 1: Safety guardrails
        is_safe, reason = check_safety(user_query)
        if not is_safe:
            logger.warning(f"Query blocked by guardrails: {reason}")
            return f"[BLOCKED] {reason}"
        
        # Step 2: Context retrieval
        context_str = self._gather_context(user_query)
        
        # Step 3: Prompt construction
        final_prompt = QUERY_TEMPLATE.format(
            context_data=context_str,
            user_query=user_query
        )
        
        # Step 4: Generation with retry
        try:
            raw_response = self._call_with_retry(final_prompt)
            validated_response = self._validate_response(raw_response)
            logger.debug("Query processed successfully")
            return validated_response
            
        except ResponseValidationError as e:
            logger.error(f"Response validation failed: {e}")
            return "[ERROR] Generated response failed validation. Please try again."
            
        except APIConnectionError as e:
            logger.error(f"API connection failed: {e}")
            return "[ERROR] AI Service temporarily unavailable. Please try again later."
            
        except Exception as e:
            logger.exception(f"Unexpected error in ask(): {e}")
            return f"[ERROR] An unexpected error occurred: {str(e)}"
    
    def generate_daily_briefing(self) -> str:
        """
        Generate an automated daily intelligence briefing.
        
        Returns:
            Markdown-formatted briefing document
        """
        logger.info("Generating daily briefing...")
        
        try:
            national = self.gateway.get_national_summary()
            top_districts = self.gateway.get_top_moving_districts(5)
            
            prompt = f"""
            Generate a 'Daily Demographic Intelligence Briefing'.
            
            Data:
            National Summary: {national}
            Top movers: {top_districts}
            
            Format:
            - Headline
            - Bullet points of key movements
            - One policy recommendation
            """
            
            raw_response = self._call_with_retry(prompt)
            return self._validate_response(raw_response)
            
        except Exception as e:
            logger.error(f"Briefing generation failed: {e}")
            return (
                "# Daily Briefing\n\n"
                "**Status:** Generation failed\n\n"
                f"Error: {str(e)}\n\n"
                "Please try again or contact support."
            )
