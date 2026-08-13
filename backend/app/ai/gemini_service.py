import json
import time

from google import genai
from google.genai import types

from app.config import settings


class GeminiService:
    """
    Handles communication with the Gemini Text API.

    Gemini returns:

    {
        "state_updates": {...},
        "response": "..."
    }

    One Gemini request handles:
    - understanding the customer's latest message
    - extracting state updates
    - generating Emma's response
    """

    # ============================================================
    # CONFIGURATION
    # ============================================================

    # Maximum time we allow one Gemini request to take.
    # HttpOptions timeout is milliseconds.
    REQUEST_TIMEOUT_MS = 30_000

    # We keep retries very small because this is a live voice
    # conversation. Emma should never make the customer wait
    # for minutes.
    MAX_RETRIES = 2

    # Short delays between temporary-error retries.
    RETRY_DELAYS = [1, 2]

    # ============================================================
    # INITIALIZATION
    # ============================================================

    def __init__(self):

        self.client = genai.Client(
            api_key=settings.GEMINI_API_KEY,

            # IMPORTANT:
            # Timeout is milliseconds.
            #
            # 30,000 ms = 30 seconds.
            #
            # This prevents the API call from hanging for
            # extremely long periods such as the 154 seconds
            # we saw in testing.
            http_options=types.HttpOptions(
                timeout=self.REQUEST_TIMEOUT_MS
            ),
        )

    # ============================================================
    # CHAT
    # ============================================================

    def chat(
        self,
        system_prompt: str,
        conversation: str,
    ) -> dict:

        """
        Send the conversation to Gemini.

        Returns:

        {
            "state_updates": {...},
            "response": "..."
        }
        """

        # ========================================================
        # PROMPT
        # ========================================================

        prompt = f"""
{system_prompt}

Conversation context:
{conversation}

You must perform TWO tasks.

TASK 1 — UNDERSTAND THE CUSTOMER

Identify information that the customer's latest message
actually provides or changes.

TASK 2 — RESPOND AS EMMA

Write Emma's natural conversational response.

IMPORTANT STATE RULES:

- Only update information supported by the customer's message.
- Never invent missing information.
- If a field was not provided or changed by the customer,
  return an empty string for that field.
- Do not erase existing information unless the customer
  clearly changes or removes it.
- If the customer changes a date, update only the date.
- If the customer changes a time, update only the time.
- If the customer changes a service, update only the service.
- Keep previously known information when the customer does
  not change it.
- Interpret relative dates using the current runtime date.
- Times must use 24-hour HH:MM format when understood.
- Only include people explicitly mentioned by the customer.
- If the customer clearly removes a person, return the
  updated people list.
- Do not claim an appointment is confirmed unless the
  current appointment status is "confirmed".
- Do not claim availability unless actual availability
  information has been provided.
- Never invent prices, services, employees, policies,
  opening hours, or availability.

IMPORTANT CONFIRMATION RULE:

If the customer says something like:

- yes
- yeah
- yep
- ya
- ja
- correct
- that's correct
- that's right
- exactly
- sure
- okay
- ok

do NOT invent new booking information.

If the customer says something like:

- no
- nope
- nop
- nah
- nein
- nee
- that's wrong
- not correct

do NOT erase information unless the customer actually
provides a correction.

UNCLEAR RESPONSES:

If the customer says:

- pardon
- sorry
- what?
- what was that?
- can you repeat?
- please repeat
- say that again
- I didn't hear you
- I don't understand
- I don't get you
- wie bitte
- nochmal
- noch einmal
- bitte wiederholen
- ich habe das nicht verstanden

do not change any booking information.

Simply respond naturally and repeat the current question
or information that Emma just gave.

CONTACT INFORMATION:

When the customer provides a phone number or email address,
extract exactly what the customer actually said.

Do not invent missing digits or characters.

For email addresses, preserve the exact spelling that
was provided.

For phone numbers, preserve the exact digits that were
provided.

STATE UPDATE FORMAT:

For fields that were NOT changed:
return "".

For fields that WERE changed:
return the new value.

For people:
return [] only when the customer explicitly indicates
there are no additional people.

The response must contain ONLY valid JSON.
"""

        # ========================================================
        # JSON SCHEMA
        # ========================================================

        schema = {
            "type": "object",
            "properties": {
                "state_updates": {
                    "type": "object",
                    "properties": {
                        "customer_name": {
                            "type": "string"
                        },
                        "phone": {
                            "type": "string"
                        },
                        "email": {
                            "type": "string"
                        },
                        "service": {
                            "type": "string"
                        },
                        "appointment_date": {
                            "type": "string"
                        },
                        "appointment_time": {
                            "type": "string"
                        },
                        "people": {
                            "type": "array",
                            "items": {
                                "type": "string"
                            }
                        }
                    },
                    "required": [
                        "customer_name",
                        "phone",
                        "email",
                        "service",
                        "appointment_date",
                        "appointment_time",
                        "people"
                    ]
                },
                "response": {
                    "type": "string"
                }
            },
            "required": [
                "state_updates",
                "response"
            ]
        }

        # ========================================================
        # GEMINI REQUEST
        # ========================================================

        for attempt in range(self.MAX_RETRIES + 1):

            start = time.perf_counter()

            try:

                print(
                    f"🤖 Chat Model: "
                    f"{settings.CHAT_MODEL}"
                )

                print(
                    f"⏳ Gemini request "
                    f"(attempt {attempt + 1}/"
                    f"{self.MAX_RETRIES + 1})"
                )

                response = (
                    self.client.models.generate_content(
                        model=settings.CHAT_MODEL,
                        contents=prompt,
                        config=types.GenerateContentConfig(
                            response_mime_type="application/json",
                            response_schema=schema,

                            # Keep Emma's output concise.
                            # We don't need long answers in a
                            # voice receptionist.
                            max_output_tokens=300,
                        ),
                    )
                )

                elapsed = (
                    time.perf_counter() - start
                )

                print(
                    f"✅ Gemini response received "
                    f"in {elapsed:.2f}s"
                )

                # ------------------------------------------------
                # Validate response text
                # ------------------------------------------------

                if not response.text:

                    raise ValueError(
                        "Gemini returned an empty response."
                    )

                # ------------------------------------------------
                # Parse JSON
                # ------------------------------------------------

                result = json.loads(
                    response.text
                )

                # ------------------------------------------------
                # Validate expected structure
                # ------------------------------------------------

                if not isinstance(result, dict):

                    raise ValueError(
                        "Gemini response is not a JSON object."
                    )

                if "state_updates" not in result:

                    raise ValueError(
                        "Gemini response is missing "
                        "'state_updates'."
                    )

                if "response" not in result:

                    raise ValueError(
                        "Gemini response is missing "
                        "'response'."
                    )

                return result

            # ====================================================
            # TIMEOUT / CONNECTION / API ERRORS
            # ====================================================

            except Exception as error:

                elapsed = (
                    time.perf_counter() - start
                )

                error_message = str(error)

                error_type = type(error).__name__

                print(
                    f"❌ Gemini error "
                    f"after {elapsed:.2f}s"
                )

                print(
                    f"   Type: {error_type}"
                )

                print(
                    f"   Error: {error_message}"
                )

                # ------------------------------------------------
                # Decide whether this error is temporary.
                # ------------------------------------------------

                temporary_error = (
                    "429" in error_message
                    or
                    "500" in error_message
                    or
                    "502" in error_message
                    or
                    "503" in error_message
                    or
                    "504" in error_message
                    or
                    "timeout" in error_message.lower()
                    or
                    "timed out" in error_message.lower()
                    or
                    "temporarily unavailable"
                    in error_message.lower()
                    or
                    "connection" in error_message.lower()
                )

                # ------------------------------------------------
                # Retry only temporary errors.
                # ------------------------------------------------

                if (
                    temporary_error
                    and attempt < self.MAX_RETRIES
                ):

                    delay = self.RETRY_DELAYS[
                        min(
                            attempt,
                            len(self.RETRY_DELAYS) - 1
                        )
                    ]

                    print(
                        f"⚠ Gemini temporary error."
                    )

                    print(
                        f"🔁 Retrying in "
                        f"{delay}s..."
                    )

                    # This service method is currently
                    # synchronous, so keep the delay short.
                    time.sleep(delay)

                    continue

                # ------------------------------------------------
                # Permanent error / all retries failed.
                # ------------------------------------------------

                print(
                    "🛑 Gemini request failed. "
                    "Returning safe fallback."
                )

                return {
                    "state_updates": {},
                    "response": (
                        "I'm sorry, I had a temporary "
                        "connection problem. "
                        "Could you please say that again?"
                    ),
                }

        # ========================================================
        # SAFETY FALLBACK
        # ========================================================

        return {
            "state_updates": {},
            "response": (
                "I'm sorry, I had a temporary "
                "connection problem. "
                "Could you please say that again?"
            ),
        }