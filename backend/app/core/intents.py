from enum import Enum

class Intent(Enum):
    GREETING = "greeting"
    COMPANY_INFO = "company_info"
    SERVICES = "services"
    OPENING_HOURS = "opening_hours"
    CONTACT_INFO = "contact_info"
    LOCATION = "location"
    APPOINTMENT = "appointment"
    PRICING = "pricing"
    HUMAN_SUPPORT = "human_support"
    GOODBYE = "goodbye"
    UNKNOWN = "unknown"