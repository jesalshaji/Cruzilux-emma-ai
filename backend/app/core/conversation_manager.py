from datetime import date, datetime
import re

from app.ai.gemini_service import GeminiService
from app.core.prompt_manager import PromptManager
from app.core.runtime_context import RuntimeContext


class ConversationManager:
    """
    Manages one temporary Emma conversation.

    Responsibilities:
    - Conversation history
    - English / German language state
    - Runtime date/time/timezone
    - Appointment state
    - Booking workflow
    - Contact verification
    - Demo booking trigger

    Gemini understands the customer's message.
    Python controls the booking workflow.
    """

    def __init__(self):

        self.gemini = GeminiService()
        self.prompt_manager = PromptManager()

        self.history = []

        # ------------------------------------
        # Language
        # ------------------------------------

        self.current_language = None
        self.candidate_language = None
        self.candidate_count = 0

        # ------------------------------------
        # Appointment state
        # ------------------------------------

        self.state = {
            "customer_name": None,
            "phone": None,
            "email": None,
            "service": None,
            "appointment_date": None,
            "appointment_time": None,
            "people": [],
            "appointment_status": "none",

            # collecting
            # confirming
            # ready_for_contact
            # verifying_phone
            # verifying_email
            # ready_for_booking
            # confirmed
            "booking_stage": "collecting",

            "phone_confirmed": False,
            "email_confirmed": False,
        }

        # ------------------------------------
        # Demo booking event
        # ------------------------------------

        self.booking_event = None

        # Set when Gemini tries to store a date that is already in the past.
        self.invalid_past_date = False

        # ------------------------------------
        # Runtime context
        # ------------------------------------

        company = (
            self.prompt_manager
            .company_manager
            .get_company()
        )

        self.runtime_context = RuntimeContext(
            company.get(
                "timezone",
                "Europe/Vienna",
            )
        )

    # ============================================================
    # LANGUAGE
    # ============================================================

    def _detect_language_request(self, message: str):
        """
        Detect explicit requests to switch Emma's conversation language.

        This is intentionally deterministic. We do not rely on Gemini
        to decide the application's active TTS language.
        """

        text = message.lower().strip()

        # Normalize common punctuation
        text = (
            text
            .replace(",", " ")
            .replace(".", " ")
            .replace("!", " ")
            .replace("?", " ")
            .replace(":", " ")
            .replace(";", " ")
        )

        # ------------------------------------------------------------
        # ENGLISH
        # ------------------------------------------------------------

        english_requests = [
            "speak english",
            "speak in english",
            "speak to me in english",
            "talk in english",
            "talk to me in english",
            "respond in english",
            "reply in english",
            "answer in english",
            "in english",
            "english please",
            "please speak english",
            "please speak in english",
            "can we speak english",
            "can we speak in english",
            "can you speak english",
            "can you speak in english",
            "let's speak english",
            "lets speak english",
            "switch to english",
            "switch into english",
            "change to english",
            "change into english",
            "change the language to english",
            "change response to english",
            "change the response to english",
            "change your response to english",
            "respond to me in english",
            "continue in english",
            "continue speaking english",
            "continue speaking in english",
        ]

        # ------------------------------------------------------------
        # GERMAN
        # ------------------------------------------------------------

        german_requests = [
            "speak german",
            "speak in german",
            "speak to me in german",
            "talk in german",
            "talk to me in german",
            "respond in german",
            "reply in german",
            "answer in german",
            "in german",
            "german please",
            "please speak german",
            "please speak in german",
            "can we speak german",
            "can we speak in german",
            "can you speak german",
            "can you speak in german",
            "let's speak german",
            "lets speak german",
            "switch to german",
            "switch into german",
            "change to german",
            "change into german",
            "change the language to german",
            "change response to german",
            "change the response to german",
            "change your response to german",
            "respond to me in german",
            "continue in german",
            "continue speaking german",
            "continue speaking in german",

            # German requests
            "sprechen sie deutsch",
            "sprich deutsch",
            "sprich bitte deutsch",
            "auf deutsch",
            "bitte auf deutsch",
            "können wir deutsch sprechen",
            "koennen wir deutsch sprechen",
            "können sie deutsch sprechen",
            "koennen sie deutsch sprechen",
            "kannst du deutsch sprechen",
            "kannst du auf deutsch sprechen",
            "bitte deutsch",
            "deutsch bitte",
        ]

        # ------------------------------------------------------------
        # Check exact phrases first
        # ------------------------------------------------------------

        for phrase in english_requests:
            if phrase in text:
                return "en"

        for phrase in german_requests:
            if phrase in text:
                return "de"

        return None

    def _detect_message_language(self, message: str):

        text = message.lower()

        german_words = [
            "ich",
            "möchte",
            "mochte",
            "einen",
            "eine",
            "einem",
            "termin",
            "morgen",
            "heute",
            "bitte",
            "danke",
            "und",
            "oder",
            "für",
            "fuer",
            "haben",
            "können",
            "koennen",
            "sprechen",
            "deutsch",
            "zahn",
            "reinigung",
            "haarschnitt",
            "bart",
            "mein",
            "meine",
            "telefonnummer",
            "email",
        ]

        english_words = [
            "i",
            "want",
            "would",
            "like",
            "book",
            "appointment",
            "tomorrow",
            "today",
            "please",
            "thank",
            "and",
            "or",
            "for",
            "have",
            "can",
            "speak",
            "english",
            "cleaning",
            "checkup",
            "phone",
            "email",
        ]

        german_score = sum(
            1 for word in german_words
            if word in text
        )

        english_score = sum(
            1 for word in english_words
            if word in text
        )

        if german_score == 0 and english_score == 0:
            return None

        if german_score > english_score:
            return "de"

        if english_score > german_score:
            return "en"

        return None

    def _update_language(self, message: str):

        explicit = self._detect_language_request(message)

        if explicit:

            self.current_language = explicit
            self.candidate_language = None
            self.candidate_count = 0

            return

        detected = self._detect_message_language(message)

        if detected is None:
            return

        if self.current_language is None:

            self.current_language = detected

            return

        if detected == self.current_language:

            self.candidate_language = None
            self.candidate_count = 0

            return

        if detected == self.candidate_language:

            self.candidate_count += 1

        else:

            self.candidate_language = detected
            self.candidate_count = 1

        # Do not automatically switch languages from ordinary speech.
        # An explicit request such as "switch to German" is handled
        # immediately at the top of this method.

    def _build_language_context(self):

        language = (
            "German"
            if self.current_language == "de"
            else "English"
            if self.current_language == "en"
            else "the customer's established language"
        )

        return f"""
Current conversation language: {language}.

Keep responding in the current conversation language.

Do not switch languages because of a single unusual,
mixed, or uncertain transcription.

If the customer explicitly asks to change language,
follow that request immediately.
"""

    # ============================================================
    # RUNTIME
    # ============================================================

    def _build_runtime_context(self):

        runtime = self.runtime_context.get_context()

        return f"""
Current date: {runtime["current_date"]}
Current time: {runtime["current_time"]}
Current day: {runtime["current_day"]}
Timezone: {runtime["timezone"]}

Use this information when interpreting:
- today
- tomorrow
- day after tomorrow
- Friday
- next Monday
- next week
"""

    # ============================================================
    # STATE
    # ============================================================

    def _build_state_context(self):

        state = self.state

        people = state.get("people") or []

        people_text = (
            ", ".join(str(x) for x in people)
            if people
            else "None"
        )

        return f"""
Current appointment state:

Customer name:
{state["customer_name"] or "Unknown"}

Phone:
{state["phone"] or "Unknown"}

Email:
{state["email"] or "Unknown"}

Service:
{state["service"] or "Unknown"}

Appointment date:
{state["appointment_date"] or "Unknown"}

Appointment time:
{state["appointment_time"] or "Unknown"}

People:
{people_text}

Appointment status:
{state["appointment_status"]}

Booking stage:
{state["booking_stage"]}

Phone confirmed:
{state["phone_confirmed"]}

Email confirmed:
{state["email_confirmed"]}


IMPORTANT BOOKING RULES:

- Python controls the booking stage.
- Gemini extracts information.
- Never claim an appointment is confirmed unless Python
  has actually created the appointment.
- If the customer changes the date, update it.
- If the customer changes the time, update it.
- If the customer changes the service, update it.
- If the customer changes who the appointment is for,
  update the people field.
- Preserve previously known information unless the
  customer explicitly changes it.
"""

    # ============================================================
    # STATE UPDATE
    # ============================================================

    def _clean_email(self, value):

        if not value:
            return None

        value = str(value).strip()

        # Remove markdown mailto formatting that sometimes
        # appears in transcribed / generated text.
        match = re.search(
            r"mailto:([^\s)\]]+)",
            value,
            re.IGNORECASE,
        )

        if match:
            value = match.group(1)

        value = re.sub(
            r"^\[|\]$",
            "",
            value,
        )

        value = value.strip()

        return value

    def _clean_phone(self, value):

        if not value:
            return None

        value = str(value)

        # Keep + for international numbers.
        value = re.sub(
            r"[^\d+]",
            "",
            value,
        )

        return value or None

    def _update_state(self, updates: dict):

        if not updates:
            return

        # Reset this per customer turn. It is only used to explain why
        # a supplied appointment date was rejected.
        self.invalid_past_date = False

        simple_fields = [
            "customer_name",
            "service",
            "appointment_date",
            "appointment_time",
        ]

        for field in simple_fields:

            value = updates.get(field)

            if not value:
                continue

            if field == "appointment_date":

                try:
                    proposed = date.fromisoformat(str(value))
                    runtime = self.runtime_context.get_context()
                    today = date.fromisoformat(
                        runtime["current_date"]
                    )

                    # Never allow a booking date in the past.
                    if proposed < today:
                        self.invalid_past_date = True
                        continue

                except (TypeError, ValueError, KeyError):
                    # If Gemini returned a malformed date, do not overwrite
                    # an existing valid date.
                    continue

            self.state[field] = value

        phone = updates.get("phone")

        if phone:

            cleaned_phone = self._clean_phone(phone)

            if cleaned_phone:
                previous_phone = self.state.get("phone")
                self.state["phone"] = cleaned_phone

                # Gemini may repeat an already-known number on later turns.
                # Repeating the SAME number must not reset its confirmation.
                # Only a genuinely changed number requires confirmation again.
                if cleaned_phone != previous_phone:
                    self.state["phone_confirmed"] = False

        email = updates.get("email")

        if email:

            cleaned_email = self._clean_email(email)

            if cleaned_email:
                previous_email = self.state.get("email")
                self.state["email"] = cleaned_email

                # Same rule for email: identical value keeps confirmation;
                # a changed email requires confirmation again.
                if cleaned_email != previous_email:
                    self.state["email_confirmed"] = False

        people = updates.get("people")

        if people is not None:
            self.state["people"] = people

    # ============================================================
    # BOOKING VALIDATION
    # ============================================================

    def _has_required_booking_details(self):

        return all(
            self.state.get(field)
            for field in [
                "customer_name",
                "service",
                "appointment_date",
                "appointment_time",
            ]
        )

    def _format_phone_for_speech(self, phone=None):
        """Format a stored phone number as individual digits for TTS."""

        phone = phone or self.state.get("phone")

        if not phone:
            return "unknown"

        digits = re.sub(r"\D", "", str(phone))

        if not digits:
            return "unknown"

        english_digits = {
            "0": "zero", "1": "one", "2": "two", "3": "three",
            "4": "four", "5": "five", "6": "six", "7": "seven",
            "8": "eight", "9": "nine",
        }

        german_digits = {
            "0": "null", "1": "eins", "2": "zwei", "3": "drei",
            "4": "vier", "5": "fünf", "6": "sechs", "7": "sieben",
            "8": "acht", "9": "neun",
        }

        words = german_digits if self.current_language == "de" else english_digits
        return " ".join(words[digit] for digit in digits)

    def _is_valid_phone(self):

        phone = self.state.get("phone")

        if not phone:
            return False

        digits = re.sub(
            r"\D",
            "",
            phone,
        )

        # Broad international demo validation.
        # Production can use a proper phone-number library.
        return 7 <= len(digits) <= 15

    def _is_valid_email(self):

        email = self.state.get("email")

        if not email:
            return False

        pattern = (
            r"^[^@\s]+@[^@\s]+\.[^@\s]+$"
        )

        return bool(
            re.match(
                pattern,
                email,
                re.IGNORECASE,
            )
        )

    # ============================================================
    # CONFIRMATION DETECTION
    # ============================================================


    def _detect_unclear(self, message: str) -> bool:
        """
        Detect common requests for repetition/clarification.

        An unclear answer never changes booking data. The current
        booking stage remains unchanged so Emma can repeat the question.
        """
        text = self._normalize_confirmation_text(message)

        if not text:
            return True

        phrases = [
            # English
            "pardon",
            "pardon me",
            "sorry",
            "sorry what",
            "what was that",
            "what did you say",
            "come again",
            "say that again",
            "can you repeat",
            "could you repeat",
            "please repeat",
            "repeat that",
            "repeat the question",
            "one more time",
            "i didnt hear",
            "i did not hear",
            "i didnt catch that",
            "i did not catch that",
            "i dont understand",
            "i do not understand",
            "i didnt understand",
            "i did not understand",
            "i dont get you",
            "i do not get you",
            "could you say that again",
            "can you say that again",

            # German
            "wie bitte",
            "bitte was",
            "was haben sie gesagt",
            "was hast du gesagt",
            "noch einmal",
            "nochmal",
            "noch einmal bitte",
            "nochmal bitte",
            "bitte wiederholen",
            "können sie das wiederholen",
            "koennen sie das wiederholen",
            "kannst du das wiederholen",
            "ich habe das nicht verstanden",
            "ich habe das nicht gehört",
            "ich habe das nicht gehoert",
            "wie war das",
            "noch mal",
        ]

        return any(
            phrase == text or phrase in text
            for phrase in phrases
        )

    def _detect_confirmation(self, message: str) -> bool:
        """
        Detect natural positive confirmations in English and German.

        Conservative on purpose: phrases containing a clear correction
        such as "yes, but..." should not be treated as a final confirmation.
        """

        text = self._normalize_confirmation_text(message)

        if not text:
            return False

        # A clear correction/change takes priority over confirmation.
        correction_markers = [
            "but",
            "instead",
            "change",
            "make it",
            "actually",
            "rather",
            "sondern",
            "aber",
            "stattdessen",
            "ändern",
            "aendern",
        ]

        if any(marker in text for marker in correction_markers):
            return False

        exact_positive = {
            "yes",
            "yeah",
            "yep",
            "yup",
            "ya",
            "sure",
            "correct",
            "right",
            "exactly",
            "ja",
            "jaja",
            "genau",
            "richtig",
            "stimmt",
            "passt",
            "korrekt",
        }

        if text in exact_positive:
            return True

        positive_phrases = [
            "thats right",
            "that's right",
            "thats correct",
            "that's correct",
            "that is correct",
            "that is right",
            "yes correct",
            "yes thats correct",
            "yes that's correct",
            "yes thats right",
            "yes that's right",
            "ja genau",
            "genau so",
            "das ist richtig",
            "das stimmt",
            "das passt",
        ]

        return any(phrase in text for phrase in positive_phrases)

    def _normalize_confirmation_text(self, message: str) -> str:
        """Normalize short spoken confirmation text."""
        import re

        text = (message or "").lower().strip()

        # Remove punctuation and collapse whitespace.
        text = re.sub(r"[^a-zA-ZäöüÄÖÜß0-9\s']", " ", text)
        text = re.sub(r"\s+", " ", text).strip()

        return text

    def _detect_negative(self, message: str) -> bool:
        """
        Detect natural negative confirmations in English and German.
        """

        text = self._normalize_confirmation_text(message)

        if not text:
            return False

        exact_negative = {
            "no",
            "nope",
            "nop",
            "nah",
            "na",
            "no thanks",
            "not really",
            "wrong",
            "nein",
            "nee",
            "ne",
            "nei",
            "nö",
            "nicht",
            "falsch",
        }

        if text in exact_negative:
            return True

        negative_phrases = [
            "not correct",
            "thats wrong",
            "that's wrong",
            "that is wrong",
            "thats not correct",
            "that's not correct",
            "that is not correct",
            "not right",
            "thats not right",
            "that's not right",
            "stimmt nicht",
            "das stimmt nicht",
            "nicht richtig",
            "das ist falsch",
            "das ist nicht richtig",
            "nein danke",
            "nee danke",
        ]

        return any(phrase in text for phrase in negative_phrases)

    def _update_booking_stage(self, message: str):
        """
        Deterministic booking state machine.

        Gemini extracts information.
        Python decides what happens next.

        YES  -> continue
        NO   -> correct/re-enter
        UNCLEAR -> repeat current question without changing state
        """
        previous = self.state["booking_stage"]
        stage = previous
        has_core = self._has_required_booking_details()

        if stage == "collecting":
            stage = "confirming" if has_core else "collecting"

        elif stage == "confirming":
            if self._detect_confirmation(message) and has_core:
                stage = "ready_for_contact"
            elif self._detect_negative(message):
                stage = "confirming" if has_core else "collecting"
            elif self._detect_unclear(message):
                stage = "confirming"
            else:
                # A normal message may contain a correction such as a
                # new date/time/service. Re-review the updated appointment.
                stage = "confirming" if has_core else "collecting"

        elif stage == "ready_for_contact":
            if not self.state.get("phone"):
                stage = "ready_for_contact"
            elif not self.state.get("phone_confirmed"):
                stage = (
                    "verifying_phone"
                    if self._is_valid_phone()
                    else "ready_for_contact"
                )
            elif not self.state.get("email"):
                stage = "verifying_email"
            elif not self.state.get("email_confirmed"):
                stage = "verifying_email"
            else:
                stage = "ready_for_booking"

        elif stage == "verifying_phone":
            if self._detect_confirmation(message):
                if self._is_valid_phone():
                    self.state["phone_confirmed"] = True
                    stage = "verifying_email"
                else:
                    stage = "ready_for_contact"

            elif self._detect_negative(message):
                self.state["phone"] = None
                self.state["phone_confirmed"] = False
                stage = "ready_for_contact"

            elif self._detect_unclear(message):
                # Keep the number and stage exactly as they are.
                stage = "verifying_phone"

            else:
                # A new number may have been supplied.
                stage = "verifying_phone"

        elif stage == "verifying_email":
            if self._detect_confirmation(message):
                if self._is_valid_email():
                    self.state["email_confirmed"] = True
                    stage = (
                        "ready_for_booking"
                        if self.state.get("phone_confirmed")
                        else "ready_for_contact"
                    )
                else:
                    stage = "verifying_email"

            elif self._detect_negative(message):
                self.state["email"] = None
                self.state["email_confirmed"] = False
                stage = "verifying_email"

            elif self._detect_unclear(message):
                # Keep the email and stage exactly as they are.
                stage = "verifying_email"

            else:
                stage = "verifying_email"

        elif stage == "ready_for_booking":
            # Once both contact details are already confirmed, an explicit
            # YES must immediately finalize the demo booking. This check is
            # intentionally first so repeated Gemini state extraction cannot
            # send the conversation back to contact verification.
            if (
                has_core
                and self.state.get("phone_confirmed")
                and self.state.get("email_confirmed")
                and self._detect_confirmation(message)
            ):
                stage = "confirmed"

            elif not has_core:
                stage = "collecting"

            elif not self.state.get("phone_confirmed"):
                stage = "verifying_phone"

            elif not self.state.get("email_confirmed"):
                stage = "verifying_email"

            elif self._detect_negative(message):
                stage = "ready_for_booking"

            elif self._detect_unclear(message):
                stage = "ready_for_booking"

            else:
                stage = "ready_for_booking"

        elif stage == "confirmed":
            stage = "confirmed"

        self.state["booking_stage"] = stage
        return previous, stage

    # ============================================================
    # FORMATTING
    # ============================================================

    def _format_booking_date(self):

        value = self.state.get("appointment_date")

        if not value:
            return "the requested date"

        try:

            parsed = date.fromisoformat(value)

            if self.current_language == "de":

                months = [
                    "Januar",
                    "Februar",
                    "März",
                    "April",
                    "Mai",
                    "Juni",
                    "Juli",
                    "August",
                    "September",
                    "Oktober",
                    "November",
                    "Dezember",
                ]

                return (
                    f"{parsed.day}. "
                    f"{months[parsed.month - 1]} "
                    f"{parsed.year}"
                )

            return parsed.strftime(
                "%B %d, %Y"
            )

        except Exception:

            return str(value)

    def _format_booking_time(self):

        value = self.state.get("appointment_time")

        if not value:
            return "the requested time"

        try:

            parsed = datetime.strptime(
                value,
                "%H:%M",
            )

            if self.current_language == "de":

                return parsed.strftime(
                    "%H:%M"
                )

            return (
                parsed.strftime(
                    "%I:%M %p"
                ).lstrip("0")
            )

        except Exception:

            return str(value)

    # ============================================================
    # DETERMINISTIC BOOKING RESPONSES
    # ============================================================

    def _build_stage_response(self, previous, current):
        """Generate deterministic booking responses only when Python must override Gemini.

        Emma remains a natural voice agent while the booking stage is unchanged.
        Python only takes control when:
        - the booking stage actually changes, or
        - a past appointment date must be rejected.
        """
        if previous == current and not self.invalid_past_date:
            return None

        language = self.current_language or "en"
        service = self.state.get("service") or "appointment"
        date_text = self._format_booking_date()
        time_text = self._format_booking_time()

        if language == "de":
            if current == "collecting":
                if self.invalid_past_date:
                    return (
                        "Entschuldigung, dieser Tag ist bereits vorbei. "
                        "Welchen Tag möchten Sie stattdessen?"
                    )
                if not self.state.get("service"):
                    return "Welche zahnmedizinische Behandlung möchten Sie gerne buchen?"
                if not self.state.get("appointment_date"):
                    return "Für welchen Tag möchten Sie den Termin buchen?"
                if not self.state.get("appointment_time"):
                    return "Welche Uhrzeit würde Ihnen am besten passen?"
                if not self.state.get("customer_name"):
                    return "Wie ist bitte Ihr Name?"

            if current == "confirming":
                intent = getattr(self, "_last_confirmation_intent", None)

                if intent == "no":
                    return "Kein Problem. Was möchten Sie an dem Termin ändern?"

                if intent == "unclear":
                    return (
                        f"Kein Problem. Ich wiederhole es: Ihr Termin "
                        f"für {service} ist am {date_text} um "
                        f"{time_text} Uhr. Ist alles so richtig?"
                    )

                return (
                    f"Ich habe Ihren Termin für {service} am "
                    f"{date_text} um {time_text} Uhr vorgemerkt. "
                    f"Ist alles so richtig?"
                )

            if current == "ready_for_contact":
                if not self.state.get("phone"):
                    return "Perfekt. Könnten Sie mir bitte Ihre Telefonnummer geben?"
                if not self.state.get("phone_confirmed"):
                    spoken_phone = self._format_phone_for_speech()
                    return (
                        f"Ich habe Ihre Telefonnummer als {spoken_phone} verstanden. "
                        f"Ist diese Nummer richtig?"
                    )
                return "Danke. Welche E-Mail-Adresse soll ich für Ihre Bestätigung verwenden?"

            if current == "verifying_phone":
                spoken_phone = self._format_phone_for_speech()
                return (
                    f"Ich habe Ihre Telefonnummer als {spoken_phone} verstanden. "
                    f"Ist diese Nummer richtig?"
                )

            if current == "verifying_email":
                if self.state.get("email"):
                    return f"Ich habe Ihre E-Mail-Adresse als {self.state['email']} verstanden. Ist diese E-Mail-Adresse richtig?"
                return "Welche E-Mail-Adresse soll ich für Ihre Bestätigung verwenden?"

            if current == "ready_for_booking":
                return f"Perfekt. Ihre Telefonnummer und E-Mail-Adresse sind bestätigt. Soll ich den Termin für {service} am {date_text} um {time_text} jetzt buchen?"

            if current == "confirmed":
                return f"Perfekt. Ihr Termin für {service} am {date_text} um {time_text} wurde erfolgreich vorgemerkt."

            return None

        if current == "collecting":
            if self.invalid_past_date:
                return (
                    "Sorry, that day has already passed. "
                    "What day would you like instead?"
                )
            if not self.state.get("service"):
                return "What dental service would you like to book?"
            if not self.state.get("appointment_date"):
                return "What day would you like to come in?"
            if not self.state.get("appointment_time"):
                return "What time would work best for you?"
            if not self.state.get("customer_name"):
                return "May I have your name, please?"

        if current == "confirming":
            intent = getattr(self, "_last_confirmation_intent", None)

            if intent == "no":
                return (
                    "No problem. What would you like to change "
                    "about the appointment?"
                )

            if intent == "unclear":
                return (
                    f"No problem. Let me repeat that: I have your "
                    f"{service} appointment for {date_text} at "
                    f"{time_text}. Is everything correct?"
                )

            return (
                f"I have your {service} appointment for "
                f"{date_text} at {time_text}. Is everything correct?"
            )

        if current == "ready_for_contact":
            if not self.state.get("phone"):
                return "Perfect. Could I have your phone number, please?"
            if not self.state.get("phone_confirmed"):
                spoken_phone = self._format_phone_for_speech()
                return (
                    f"I heard your phone number as {spoken_phone}. "
                    f"Is that number correct?"
                )
            return "Thank you. What email address should I use for your confirmation?"

        if current == "verifying_phone":
            spoken_phone = self._format_phone_for_speech()
            return (
                f"I heard your phone number as {spoken_phone}. "
                f"Is that number correct?"
            )

        if current == "verifying_email":
            if self.state.get("email"):
                return f"I heard your email address as {self.state['email']}. Is that email address correct?"
            return "What email address should I use for your confirmation?"

        if current == "ready_for_booking":
            return f"Perfect. Your phone number and email are confirmed. Would you like me to book your {service} appointment for {date_text} at {time_text} now?"

        if current == "confirmed":
            return f"Perfect. Your {service} appointment for {date_text} at {time_text} has been successfully recorded."

        return None

    # ============================================================
    # DEMO BOOKING EVENT
    # ============================================================

    def _create_demo_booking_event(self):

        import uuid

        confirmation_id = (
            "CRX-"
            + uuid.uuid4()
            .hex[:6]
            .upper()
        )

        appointment = {
            "confirmation_id": confirmation_id,
            "customer_name": self.state["customer_name"],
            "phone": self.state["phone"],
            "email": self.state["email"],
            "service": self.state["service"],
            "appointment_date": self.state[
                "appointment_date"
            ],
            "appointment_time": self.state[
                "appointment_time"
            ],
            "people": self.state["people"],
            "status": "demo_confirmed",
            "demo_mode": True,
        }

        self.state["appointment_status"] = (
            "confirmed"
        )

        self.booking_event = appointment

        return appointment

    def consume_booking_event(self):

        event = self.booking_event

        self.booking_event = None

        return event

    # ============================================================
    # MAIN PROCESS
    # ============================================================

    async def process_message(
        self,
        message: str,
    ) -> str:

        # ----------------------------------------
        # Language
        # ----------------------------------------

        self._update_language(message)

        # ----------------------------------------
        # History
        # ----------------------------------------

        self.history.append(
            {
                "role": "customer",
                "message": message,
            }
        )

        # ----------------------------------------
        # Gemini context
        # ----------------------------------------

        system_prompt = (
            self.prompt_manager
            .get_system_prompt()
        )

        conversation = ""

        conversation += (
            self._build_runtime_context()
        )

        conversation += "\n"

        conversation += (
            self._build_language_context()
        )

        conversation += "\n"

        conversation += (
            self._build_state_context()
        )

        conversation += (
            "\nConversation history:\n"
        )

        for item in self.history:

            if item["role"] == "customer":

                conversation += (
                    f"Customer: "
                    f"{item['message']}\n"
                )

            else:

                conversation += (
                    f"Emma: "
                    f"{item['message']}\n"
                )

        # ----------------------------------------
        # Gemini
        # ----------------------------------------

        result = self.gemini.chat(
            system_prompt=system_prompt,
            conversation=conversation,
        )

        if not isinstance(result, dict):

            reply = str(result).strip()

            self.history.append(
                {
                    "role": "emma",
                    "message": reply,
                }
            )

            return reply

        # ----------------------------------------
        # Apply extracted information
        # ----------------------------------------

        updates = result.get(
            "state_updates",
            {},
        )

        print(
            f"🧠 State Updates: {updates}"
        )

        previous_state = self.state.copy()

        self._last_confirmation_intent = (
            "yes"
            if self._detect_confirmation(message)
            else "no"
            if self._detect_negative(message)
            else "unclear"
            if self._detect_unclear(message)
            else None
        )

        self._update_state(updates)

        # ----------------------------------------
        # Reject appointments in the past
        # ----------------------------------------
        #
        # Gemini may correctly extract a date such as "yesterday",
        # but a dental appointment cannot be booked for a past date.
        # Clear only the invalid date so Emma can ask for a valid one.
        if self.state.get("appointment_date"):
            try:
                from datetime import datetime

                today = datetime.now().date()
                requested_date = datetime.strptime(
                    self.state["appointment_date"],
                    "%Y-%m-%d",
                ).date()

                if requested_date < today:
                    self.state["appointment_date"] = None

            except (TypeError, ValueError):
                pass

        # If service/date/time/person changes after review/contact collection,
        # require the appointment to be reviewed again. Contact data is kept.
        core_changed = any(
            previous_state.get(field) != self.state.get(field)
            for field in ["service", "appointment_date", "appointment_time", "people"]
        )

        if core_changed and self.state["booking_stage"] in {
            "ready_for_contact", "verifying_phone", "verifying_email", "ready_for_booking"
        }:
            self.state["booking_stage"] = (
                "confirming" if self._has_required_booking_details() else "collecting"
            )
            if self.state["appointment_status"] == "confirmed":
                self.state["appointment_status"] = "none"

        # ----------------------------------------
        # Booking stage
        # ----------------------------------------

        previous_stage, current_stage = (
            self._update_booking_stage(
                message
            )
        )

        print(
            f"📋 Current State: "
            f"{self.state}"
        )

        # ----------------------------------------
        # Demo booking
        # ----------------------------------------

        if (
            current_stage == "confirmed"
            and self._has_required_booking_details()
            and self.state.get("phone_confirmed")
            and self.state.get("email_confirmed")
            and self.state["appointment_status"] != "confirmed"
        ):

            self._create_demo_booking_event()

            # Deterministic final response.
            if self.current_language == "de":

                reply = (
                    "Perfekt. Ihr Termin wurde "
                    "erfolgreich für die Demo gebucht. "
                    "Die Bestätigung wurde vorbereitet. "
                    "Dies ist eine Demo, daher wird "
                    "keine echte E-Mail versendet."
                )

            else:

                reply = (
                    "Perfect. Your appointment has "
                    "been successfully booked in the "
                    "demo system. The confirmation "
                    "has been prepared. This is a demo, "
                    "so no real email will be sent."
                )

        else:

            # ------------------------------------
            # Deterministic stage response
            # ------------------------------------

            stage_reply = (
                self._build_stage_response(
                    previous_stage,
                    current_stage,
                )
            )

            if stage_reply:

                reply = stage_reply

            else:

                reply = result.get(
                    "response",
                    "",
                ).strip()

        # ----------------------------------------
        # Fallback
        # ----------------------------------------

        if not reply:

            reply = (
                "I'm sorry, I didn't quite "
                "catch that. Could you please "
                "say that again?"
            )

        # ----------------------------------------
        # Save Emma response
        # ----------------------------------------

        self.history.append(
            {
                "role": "emma",
                "message": reply,
            }
        )

        return reply