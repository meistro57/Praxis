import time
import logging
import json
import httpx
from typing import Any, Dict, Type, TypeVar
from pydantic import BaseModel, ValidationError
from tenacity import Retrying, stop_after_attempt, wait_exponential, retry_if_exception
from app.models.failure import LLMRequestError, LLMResponseValidationError

logger = logging.getLogger(__name__)

T = TypeVar("T", bound=BaseModel)

def is_transient_error(exception: Exception) -> bool:
    """Return True if the exception is a transient network or server error."""
    if isinstance(exception, (httpx.TimeoutException, httpx.NetworkError, httpx.RequestError)):
        return True
    if isinstance(exception, httpx.HTTPStatusError):
        # 429 (Too Many Requests) or 5xx (Server Errors)
        return exception.response.status_code == 429 or exception.response.status_code >= 500
    return False

class LLMClient:
    def __init__(self, config: Any):
        self.config = config
        # Initialise HTTP client with configured timeout
        self.timeout = httpx.Timeout(
            connect=10.0,
            read=float(config.llm_timeout),
            write=float(config.llm_timeout),
            pool=30.0
        )
        self.client = httpx.Client(timeout=self.timeout)

    def _get_headers_and_url(self, model: str) -> tuple[Dict[str, str], str]:
        """Determine API endpoints and headers based on routing config."""
        # Check if direct DeepSeek routing is available and applicable
        is_deepseek_model = (
            model == self.config.deepseek_reasoner_model or 
            "deepseek" in model.lower()
        )
        
        if is_deepseek_model and self.config.deepseek_api_key:
            api_key = self.config.deepseek_api_key
            base_url = self.config.deepseek_base_url
            logger.debug(f"Routing model '{model}' directly to DeepSeek endpoint.")
        else:
            api_key = self.config.openrouter_api_key
            base_url = self.config.openrouter_base_url
            logger.debug(f"Routing model '{model}' to OpenRouter endpoint.")

        if not api_key:
            raise LLMRequestError("API Key is missing for the selected LLM provider.")

        headers = {
            "Authorization": f"Bearer {api_key}",
            "Content-Type": "application/json"
        }
        # Add OpenRouter specific headers if using OpenRouter
        if "openrouter.ai" in base_url:
            headers["HTTP-Referer"] = "https://github.com/meta-bridge/praxis"
            headers["X-Title"] = "Praxis Agent Coder"

        completions_url = f"{base_url.rstrip('/')}/chat/completions"
        return headers, completions_url

    def extract_json(self, text: str) -> str:
        """Extract a JSON substring from code blocks or raw response text."""
        text = text.strip()
        # Remove markdown wrappers if present
        if text.startswith("```"):
            # Check for ```json or ```
            if text.startswith("```json"):
                text = text[7:]
            else:
                text = text[3:]
            if text.endswith("```"):
                text = text[:-3]
        
        # If there are trailing/leading texts, try to extract first '{' to last '}'
        start_idx = text.find("{")
        end_idx = text.rfind("}")
        if start_idx != -1 and end_idx != -1 and end_idx > start_idx:
            text = text[start_idx:end_idx + 1]

        return text.strip()

    def generate_completions(
        self,
        system_prompt: str,
        user_prompt: str,
        model: str,
        response_model: Type[T]
    ) -> T:
        """
        Generate chat completions, extract JSON, validate against the Pydantic response_model,
        and log usage and latency. Implements transient failure retries.
        """
        headers, url = self._get_headers_and_url(model)
        
        # Determine actual model name to send to API
        api_model = model
        if "api.deepseek.com" in url:
            if "r1" in model.lower() or "reasoner" in model.lower():
                api_model = self.config.deepseek_reasoner_model
            elif "chat" in model.lower() or "v3" in model.lower():
                api_model = "deepseek-chat"

        payload = {
            "model": api_model,
            "messages": [
                {"role": "system", "content": system_prompt},
                {"role": "user", "content": user_prompt}
            ],
        }
        
        # Omit temperature for deepseek-reasoner to satisfy DeepSeek API contract
        if api_model != "deepseek-reasoner" and api_model != self.config.deepseek_reasoner_model:
            payload["temperature"] = 0.0

        # Log request if raw LLM logging is enabled (at DEBUG level)
        if self.config.log_raw_llm:
            logger.debug(f"Raw Request Payload:\n{json.dumps(payload, indent=2)}")

        # Configure retrier dynamically based on max retries setting
        retrier = Retrying(
            stop=stop_after_attempt(self.config.llm_max_retries + 1),
            wait=wait_exponential(multiplier=1.0, min=2.0, max=10.0),
            retry=retry_if_exception(is_transient_error),
            reraise=True
        )

        raw_content = ""
        start_time = time.time()
        retry_count = 0

        try:
            # Execute with tenacity retries
            for attempt in retrier:
                with attempt:
                    if attempt.retry_state.attempt_number > 1:
                        retry_count = attempt.retry_state.attempt_number - 1
                        logger.warning(
                            f"LLM request failed. Retrying (Attempt #{attempt.retry_state.attempt_number})..."
                        )
                    
                    response = self.client.post(url, headers=headers, json=payload)
                    response.raise_for_status()
                    
                    response_json = response.json()
                    raw_content = response_json["choices"][0]["message"]["content"]
                    
                    # Log token usage if provided by API
                    usage = response_json.get("usage", {})
                    logger.debug(f"LLM usage tokens: {usage}")

        except Exception as e:
            # Wrap standard httpx/network errors
            logger.exception(f"LLM Request failed: {e}")
            raise LLMRequestError(f"LLM Request failed after {retry_count} retries. Error: {e}") from e

        latency = time.time() - start_time
        logger.info(
            f"LLM request completed in {latency:.2f}s (retries: {retry_count}) using model: {model}"
        )

        if self.config.log_raw_llm:
            logger.debug(f"Raw Response Content:\n{raw_content}")

        # Extract and Validate JSON
        cleaned_json_str = ""
        try:
            cleaned_json_str = self.extract_json(raw_content)
            validated_model = response_model.model_validate_json(cleaned_json_str)
            return validated_model
        except ValidationError as val_err:
            logger.error(
                f"LLM Response Pydantic validation failed.\n"
                f"Cleaned output: {cleaned_json_str}\n"
                f"Validation errors: {val_err}"
            )
            # Store raw content in failure details
            raise LLMResponseValidationError(
                f"LLM response failed Pydantic validation: {val_err}. "
                f"Raw output is preserved in failure details."
            ) from val_err
        except Exception as parse_err:
            logger.error(f"LLM Response JSON parsing failed. Output: {raw_content}")
            raise LLMResponseValidationError(
                f"LLM response JSON parsing failed: {parse_err}. "
                f"Raw output is preserved in failure details."
            ) from parse_err

    def close(self) -> None:
        """Close the underlying HTTPX client."""
        self.client.close()
