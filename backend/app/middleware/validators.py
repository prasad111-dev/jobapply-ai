import re
from typing import Optional

class InputValidator:
    MAX_NAME_LENGTH = 100
    MAX_EMAIL_LENGTH = 254
    MAX_PHONE_LENGTH = 20
    MAX_URL_LENGTH = 2048
    MAX_TEXT_LENGTH = 10000
    MAX_SKILLS = 50

    @staticmethod
    def validate_email(email: str) -> tuple[bool, str]:
        if not email:
            return False, "Email is required"
        if len(email) > 254:
            return False, "Email too long"
        pattern = r'^[a-zA-Z0-9._%+-]+@[a-zA-Z0-9.-]+\.[a-zA-Z]{2,}$'
        if not re.match(pattern, email):
            return False, "Invalid email format"
        return True, ""

    @staticmethod
    def validate_name(name: str) -> tuple[bool, str]:
        if not name:
            return False, "Name is required"
        if len(name) > 100:
            return False, "Name too long"
        if not re.match(r'^[a-zA-Z\s\-\']+$', name):
            return False, "Name contains invalid characters"
        return True, ""

    @staticmethod
    def validate_phone(phone: str) -> tuple[bool, str]:
        if not phone:
            return True, ""
        cleaned = re.sub(r'[\s\-\(\)\+]', '', phone)
        if not cleaned.isdigit():
            return False, "Phone must contain only digits"
        if len(cleaned) < 7 or len(cleaned) > 15:
            return False, "Phone number length invalid"
        return True, ""

    @staticmethod
    def validate_url(url: str) -> tuple[bool, str]:
        if not url:
            return True, ""
        if len(url) > 2048:
            return False, "URL too long"
        pattern = r'^https?://.+'
        if not re.match(pattern, url):
            return False, "URL must start with http:// or https://"
        return True, ""

    @staticmethod
    def sanitize_text(text: str, max_length: int = 10000) -> str:
        if not text:
            return ""
        text = text.strip()
        text = re.sub(r'<[^>]+>', '', text)
        text = text[:max_length]
        return text

    @staticmethod
    def validate_skills(skills: list) -> tuple[bool, str]:
        if not skills:
            return True, ""
        if len(skills) > 50:
            return False, "Too many skills (max 50)"
        for skill in skills:
            if len(str(skill)) > 100:
                return False, f"Skill name too long: {skill}"
        return True, ""
