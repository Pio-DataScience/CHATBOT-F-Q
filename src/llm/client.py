# src/llm/client.py
import logging
import os
import time

import requests

logger = logging.getLogger(__name__)


class LLMRetryError(Exception):
    """Raised when all retry attempts are exhausted."""
    pass


class LLMEmptyResponseError(Exception):
    """Raised when LLM returns empty or invalid response."""
    pass


class LMClient:
    def __init__(self, base_url=None, model=None,
                 temperature=0.2, timeout=500, max_retries=3,
                 retry_delay=5, backoff_factor=2.0):
        """
        Initialize LLM client with resilient configuration.
        
        Args:
            base_url: LLM API base URL
            model: Model name to use
            temperature: Sampling temperature (0.0-1.0)
            timeout: Request timeout in seconds (default: 500)
            max_retries: Maximum number of retry attempts (default: 3)
            retry_delay: Initial delay between retries in seconds (default: 5)
            backoff_factor: Exponential backoff multiplier (default: 2.0)
        """
        self.base = base_url or os.getenv("LMSTUDIO_BASE_URL",
                                          "http://localhost:1234/v1")
        self.model = model or os.getenv("LMSTUDIO_MODEL", "")
        self.temperature = temperature
        self.timeout = timeout
        self.max_retries = max_retries
        self.retry_delay = retry_delay
        self.backoff_factor = backoff_factor

        logger.info("Initializing LLM client with resilient configuration")
        logger.info("Base URL: %s", self.base)
        logger.info("Model: %s", self.model or "(default)")
        logger.info("Temperature: %s", self.temperature)
        logger.info("Timeout: %d seconds", self.timeout)
        logger.info("Max retries: %d", self.max_retries)
        logger.info("Retry delay: %ds (backoff factor: %.1fx)",
                    self.retry_delay, self.backoff_factor)

    def _is_valid_response(self, content):
        """
        Validate that the response is not empty or meaningless.
        
        Args:
            content: Response content from LLM
            
        Returns:
            bool: True if response is valid, False otherwise
        """
        if not content:
            return False
        
        # Remove whitespace and check if empty
        stripped = content.strip()
        if not stripped:
            return False
        
        # Check if response is too short to be meaningful
        if len(stripped) < 10:
            logger.warning("Response too short: '%s'", stripped)
            return False
        
        # Check if response is just error message or placeholder
        error_indicators = [
            "error", "failed", "unable", "cannot process",
            "try again", "invalid", "null", "none"
        ]
        lower_content = stripped.lower()
        if any(indicator in lower_content for indicator in error_indicators) and len(stripped) < 50:
            logger.warning("Response appears to be error message: '%s'", stripped[:100])
            return False
        
        return True

    def _make_request(self, url, payload, attempt):
        """
        Make a single HTTP request to the LLM API.
        
        Args:
            url: API endpoint URL
            payload: Request payload
            attempt: Current attempt number (for logging)
            
        Returns:
            str: Response content from LLM
            
        Raises:
            Various exceptions for different failure modes
        """
        start_time = time.time()
        
        logger.info("[Attempt %d/%d] Sending request to LLM API",
                    attempt, self.max_retries)
        
        try:
            r = requests.post(url, json=payload, timeout=self.timeout)
            elapsed = time.time() - start_time

            logger.debug("Request completed in %.2f seconds", elapsed)
            logger.debug("Response status: %d", r.status_code)

            r.raise_for_status()

            response_data = r.json()
            
            # Validate response structure
            if "choices" not in response_data or not response_data["choices"]:
                raise LLMEmptyResponseError("No choices in response")
            
            if "message" not in response_data["choices"][0]:
                raise LLMEmptyResponseError("No message in first choice")
            
            message = response_data["choices"][0]["message"]
            finish_reason = response_data["choices"][0].get("finish_reason", "")
            
            # Get content field - reasoning models put final answer here AFTER reasoning
            content = message.get("content", "")
            
            # Check if response was truncated DURING reasoning phase (content will be empty)
            if finish_reason == "length" and not content:
                logger.error("Model hit token limit during reasoning phase - content field is empty")
                logger.error("This means max_tokens is too small. Need to increase it significantly.")
                raise LLMEmptyResponseError("Response truncated during reasoning - increase max_tokens")
            
            # Validate content
            if not self._is_valid_response(content):
                logger.debug("Content: '%s'", content[:100])
                logger.debug("Finish reason: %s", finish_reason)
                raise LLMEmptyResponseError(f"Invalid or empty content: '{content[:100]}'")

            # Log response details
            if "usage" in response_data:
                usage = response_data["usage"]
                logger.info("Token usage - prompt: %d, completion: %d, total: %d",
                            usage.get("prompt_tokens", 0),
                            usage.get("completion_tokens", 0),
                            usage.get("total_tokens", 0))

            logger.info("✓ Received valid response (%d characters) in %.2f seconds",
                        len(content), elapsed)
            logger.debug("Response preview: %s",
                         content[:200] + "..." if len(content) > 200 else content)

            return content

        except requests.exceptions.Timeout as e:
            logger.error("✗ Request timed out after %d seconds", self.timeout)
            raise
        except requests.exceptions.ConnectionError as e:
            logger.error("✗ Connection error to LLM API: %s", e)
            raise
        except requests.exceptions.HTTPError as e:
            logger.error("✗ HTTP error from LLM API: %s (status: %d)",
                         e, e.response.status_code if hasattr(e, 'response') else 'N/A')
            if hasattr(e.response, 'text'):
                logger.error("Error response body: %s", e.response.text[:500])
            raise
        except LLMEmptyResponseError as e:
            logger.error("✗ Empty or invalid response: %s", e)
            raise
        except Exception as e:
            logger.error("✗ Unexpected error during LLM request: %s", e)
            raise

    def chat(self, messages, max_tokens=1024):
        """
        Send chat completion request to LLM with automatic retry logic.
        
        This method implements resilient communication with exponential backoff:
        - Retries on timeout, connection errors, empty responses
        - Exponential backoff between retries
        - Validates response content
        - Comprehensive error logging
        
        Args:
            messages: List of message dictionaries for chat completion
            max_tokens: Maximum tokens to generate (default: 512 - sufficient for direct JSON output)
                       Note: Non-reasoning models need less tokens as they output JSON directly
            
        Returns:
            str: Generated response content
            
        Raises:
            LLMRetryError: When all retry attempts are exhausted
            LLMEmptyResponseError: When response validation fails on all attempts
        """
        url = f"{self.base}/chat/completions"

        logger.info("=" * 80)
        logger.info("Starting LLM chat completion request")
        logger.debug("Messages count: %d", len(messages))
        logger.debug("Max tokens: %d", max_tokens)

        # Log message preview
        for i, msg in enumerate(messages):
            content = msg.get('content', '')
            content_preview = (content[:100] + '...'
                               if len(content) > 100
                               else content)
            logger.debug("Message %d [%s]: %s", i+1, msg.get('role', '?'),
                         content_preview)

        payload = {
            "model": self.model,
            "messages": messages,
            "temperature": self.temperature,
            "max_tokens": max_tokens,
        }

        last_exception = None
        
        for attempt in range(1, self.max_retries + 1):
            try:
                content = self._make_request(url, payload, attempt)
                
                if attempt > 1:
                    logger.info("✓ Request succeeded on attempt %d/%d",
                                attempt, self.max_retries)
                
                return content
                
            except (requests.exceptions.Timeout,
                    requests.exceptions.ConnectionError,
                    requests.exceptions.HTTPError,
                    LLMEmptyResponseError) as e:
                
                last_exception = e
                
                if attempt < self.max_retries:
                    delay = self.retry_delay * (self.backoff_factor ** (attempt - 1))
                    logger.warning("Attempt %d/%d failed: %s",
                                   attempt, self.max_retries, str(e))
                    logger.info("Retrying in %.1f seconds...", delay)
                    time.sleep(delay)
                else:
                    logger.error("All %d attempts failed. Last error: %s",
                                 self.max_retries, str(e))
                    
            except Exception as e:
                # Unexpected errors - don't retry
                logger.error("Unexpected error (not retrying): %s", e)
                raise

        # All retries exhausted
        error_msg = (f"Failed after {self.max_retries} attempts. "
                     f"Last error: {last_exception}")
        logger.error("=" * 80)
        logger.error("LLM REQUEST FAILED: %s", error_msg)
        logger.error("=" * 80)
        raise LLMRetryError(error_msg)
