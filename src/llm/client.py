# src/llm/client.py
import logging
import os
import requests
import time

logger = logging.getLogger(__name__)


class LMClient:
    def __init__(self, base_url=None, model=None,
                 temperature=0.2, timeout=120):
        """Initialize LLM client with configuration."""
        self.base = base_url or os.getenv("LMSTUDIO_BASE_URL",
                                          "http://localhost:1234/v1")
        self.model = model or os.getenv("LMSTUDIO_MODEL", "")
        self.temperature = temperature
        self.timeout = timeout

        logger.info("Initializing LLM client")
        logger.info("Base URL: %s", self.base)
        logger.info("Model: %s", self.model or "(default)")
        logger.info("Temperature: %s", self.temperature)
        logger.info("Timeout: %d seconds", self.timeout)

    def chat(self, messages, max_tokens=256):
        """Send chat completion request to LLM."""
        start_time = time.time()
        url = f"{self.base}/chat/completions"

        logger.debug("Preparing chat completion request")
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

        logger.info("Sending request to LLM API: %s", url)

        try:
            r = requests.post(url, json=payload, timeout=self.timeout)
            elapsed = time.time() - start_time

            logger.debug("Request completed in %.2f seconds", elapsed)
            logger.debug("Response status: %d", r.status_code)

            r.raise_for_status()

            response_data = r.json()
            content = response_data["choices"][0]["message"]["content"]

            # Log response details
            if "usage" in response_data:
                usage = response_data["usage"]
                logger.info("Token usage - prompt: %d, completion: %d, "
                            "total: %d",
                            usage.get("prompt_tokens", 0),
                            usage.get("completion_tokens", 0),
                            usage.get("total_tokens", 0))

            logger.info("Received response (%d characters) in %.2f seconds",
                        len(content), elapsed)
            logger.debug("Response preview: %s", content[:200] + "..."
                         if len(content) > 200 else content)

            return content

        except requests.exceptions.Timeout:
            logger.error("Request timed out after %d seconds", self.timeout)
            raise
        except requests.exceptions.ConnectionError as e:
            logger.error("Connection error to LLM API: %s", e)
            raise
        except requests.exceptions.HTTPError as e:
            logger.error("HTTP error from LLM API: %s", e)
            if hasattr(e.response, 'text'):
                logger.error("Error response body: %s", e.response.text)
            raise
        except Exception as e:
            logger.error("Unexpected error during LLM request: %s", e)
            raise
