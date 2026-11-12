import json
import time
from google import genai
from google.genai import types
from pydantic import ValidationError
from app.config import GEMINI_API_KEY, GEMINI_MODEL
from app.schemas.ai_insight import AIInsightContent
from app.services.ai_prompt import SYSTEM_PROMPT


class AIServiceError(Exception):
    pass


def generate_spending_insights(financial_data: dict) -> dict:
    if not GEMINI_API_KEY:
        raise AIServiceError("Gemini API key is not configured.")

    try:
        client = genai.Client(
            api_key=GEMINI_API_KEY,
            http_options=types.HttpOptions(timeout=90000)
        )

        prompt = (
            SYSTEM_PROMPT
            + "\n\nAnalyze this monthly financial data:\n"
            + json.dumps(financial_data, ensure_ascii=False)
        )

        response = None
        for attempt in range(3):
            try:
                response = client.models.generate_content(
                    model=GEMINI_MODEL,
                    contents=prompt,
                    config=types.GenerateContentConfig(
                        response_mime_type="application/json",
                        response_schema=AIInsightContent,
                        temperature=0.3,
                        max_output_tokens=800
                    )
                )
                break

            except Exception as exc:
                error_message = str(exc)

                if (
                        ("503" in error_message or "UNAVAILABLE" in error_message
                         or "504" in error_message or "DEADLINE_EXCEEDED" in error_message)
                        and attempt < 2
                ):
                    time.sleep(2 ** (attempt + 1))
                    continue
                raise

        if not response.text:
            raise AIServiceError("Gemini returned an empty response.")

        validated_result = AIInsightContent.model_validate_json(
            response.text
        )

        return validated_result.model_dump()

    except ValidationError as exc:
        print("GEMINI VALIDATION ERROR:", repr(exc))
        raise AIServiceError(
            "Gemini returned an invalid response format."
        ) from exc

    except AIServiceError:
        raise

    except Exception as exc:
        print("GEMINI ORIGINAL ERROR:", repr(exc))
        raise AIServiceError(
            "Gemini service is temporarily unavailable. Check terminal for details."
        ) from exc

