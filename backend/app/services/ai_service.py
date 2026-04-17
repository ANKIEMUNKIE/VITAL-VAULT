# app/services/ai_service.py
"""Cerebras API client for medical entity extraction.

Uses httpx for synchronous HTTP calls within Celery worker context.
Cerebras exposes an OpenAI-compatible Chat Completions endpoint.
"""

from __future__ import annotations

import json
import logging

import httpx

from app.config import settings

logger = logging.getLogger(__name__)

EXTRACTION_PROMPT = """
You are a medical data extraction assistant. Analyze the following medical document text
and return a structured JSON object. Be conservative — only extract information explicitly
stated in the document. Do not infer or guess missing values; use null instead.

Document Text:
---
{ocr_text}
---

Return ONLY valid JSON matching this exact schema:
{{
  "diagnosed_conditions": ["string"],
  "extracted_medications": [
    {{
      "name": "string",
      "generic_name": "string | null",
      "dosage": "string | null",
      "frequency": "string | null",
      "duration": "string | null",
      "route": "string | null"
    }}
  ],
  "extracted_dates": {{
    "visit_date": "YYYY-MM-DD | null",
    "next_appointment": "YYYY-MM-DD | null",
    "follow_up_by": "YYYY-MM-DD | null"
  }},
  "doctor_name": "string | null",
  "hospital_name": "string | null",
  "ai_summary": "2-3 sentence clinical summary | null",
  "confidence_score": 0.0
}}
"""


def call_cerebras_extraction(ocr_text: str) -> dict | None:
    """Call the Cerebras API to extract medical entities from OCR text.

    Args:
        ocr_text: Raw text extracted from the medical document.

    Returns:
        Parsed extraction dict on success, None on failure.
    """
    if not settings.CEREBRAS_API_KEY:
        logger.warning("CEREBRAS_API_KEY not set — cannot call AI extraction")
        return None

    prompt = EXTRACTION_PROMPT.format(ocr_text=ocr_text[:8000])  # Limit input size

    try:
        with httpx.Client(timeout=60.0) as client:
            response = client.post(
                settings.CEREBRAS_API_URL,
                headers={
                    "Authorization": f"Bearer {settings.CEREBRAS_API_KEY}",
                    "Content-Type": "application/json",
                },
                json={
                    "model": settings.CEREBRAS_MODEL,
                    "messages": [
                        {
                            "role": "system",
                            "content": "You are a medical data extraction assistant. Return only valid JSON.",
                        },
                        {
                            "role": "user",
                            "content": prompt,
                        },
                    ],
                    "temperature": 0.1,
                    "max_tokens": 2000,
                },
            )
            response.raise_for_status()

        data = response.json()
        content = data.get("choices", [{}])[0].get("message", {}).get("content", "")

        # Parse JSON from response — handle potential markdown code blocks
        if "```json" in content:
            content = content.split("```json")[1].split("```")[0].strip()
        elif "```" in content:
            content = content.split("```")[1].split("```")[0].strip()

        result = json.loads(content)

        logger.info(
            "Cerebras API extraction successful — confidence: %s",
            result.get("confidence_score"),
        )
        return result

    except httpx.HTTPStatusError as exc:
        logger.error(
            "Cerebras API HTTP error: %s %s",
            exc.response.status_code,
            exc.response.text[:200],
        )
        return None

    except json.JSONDecodeError:
        logger.error("Failed to parse Cerebras API response as JSON")
        return None

    except Exception:
        logger.exception("Unexpected error calling Cerebras API")
        return None


# ---------------------------------------------------------------------------
# Backward-compat alias kept so any other code importing call_grok_extraction
# continues to work without edits. Remove after full cleanup.
# ---------------------------------------------------------------------------
call_grok_extraction = call_cerebras_extraction
