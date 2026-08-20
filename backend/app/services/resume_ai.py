import json
import logging
import re
from typing import Dict, List, Optional

from app.core.config import get_settings
from app.services.resume_parser import ResumeParser

settings = get_settings()
logger = logging.getLogger(__name__)

EMAIL_RE = re.compile(r"[\w.+-]+@[\w-]+\.[\w.]+")
PHONE_RE = re.compile(r"(\+?\d[\d\s\-()]{8,15}\d)")
LINKEDIN_RE = re.compile(r"linkedin\.com[/][\w\-/]+", re.IGNORECASE)
PORTFOLIO_RE = re.compile(r"(https?://[^\s]+)")


class ResumeAIExtractor:
    """AI-powered resume parsing that fills the ENTIRE profile from one PDF."""

    @staticmethod
    def extract_contact(raw_text: str) -> Dict:
        data = {}
        em = EMAIL_RE.search(raw_text)
        ph = PHONE_RE.search(raw_text)
        li = LINKEDIN_RE.search(raw_text)
        if em:
            data["email"] = em.group(0)
        if ph:
            data["phone"] = ph.group(1).strip()
        if li:
            data["linkedin_url"] = "https://" + li.group(0) if not li.group(0).startswith("http") else li.group(0)

        lines = [l.strip() for l in raw_text.split("\n") if l.strip()]
        for line in lines[:15]:
            low = line.lower()
            if any(kw in low for kw in ["portfolio", "github", "personal website", "website", "blog"]):
                m = PORTFOLIO_RE.search(line)
                if m:
                    data["portfolio_url"] = m.group(0)
                    break
        return data

    CITY_KEYWORDS = ["bangalore", "bengaluru", "mumbai", "delhi", "new delhi", "pune", "hyderabad", "chennai", "gurgaon", "gurugram", "noida", "kolkata", "ahmedabad", "jaipur", "indore", "kochi", "chandigarh", "remote"]

    @staticmethod
    def extract_location(raw_text: str) -> Optional[str]:
        for line in raw_text.split("\n"):
            line = line.strip()
            if not line or len(line) > 100:
                continue
            low = line.lower()
            matched = None
            for city in ResumeAIExtractor.CITY_KEYWORDS:
                if city in low:
                    matched = city
                    break
            if matched:
                city_label = matched.title()
                if matched == "new delhi":
                    city_label = "New Delhi"
                return city_label
        return None

    @staticmethod
    def extract_name(raw_text: str) -> Optional[str]:
        lines = [l.strip() for l in raw_text.split("\n") if l.strip() and len(l.strip()) < 50]
        for line in lines[:5]:
            if re.fullmatch(r"[A-Za-z][A-Za-z.\s'\-]{2,39}", line):
                if not any(kw in line.lower() for kw in ["resume", "cv", "curriculum", "summary", "experience", "contact", "profile", "skills", "education"]):
                    return line.title()
        return None

    async def parse(self, content: bytes, filename: str) -> Dict:
        parser = ResumeParser()
        local = parser.parse(content, filename)
        raw_text = local.get("raw_text", "")

        profile = {
            "raw_text": raw_text,
            "skills": local.get("skills", []),
            "experience_years": local.get("experience_years", 0),
            "education": local.get("education", []),
            "summary": local.get("summary", ""),
        }

        contact = self.extract_contact(raw_text)
        profile.update(contact)
        loc = self.extract_location(raw_text)
        if loc:
            profile["location"] = loc
        name = self.extract_name(raw_text)
        if name:
            profile["full_name"] = name

        if settings.OPENAI_API_KEY:
            ai_data = await self._ai_enhance(raw_text)
            if ai_data:
                for key in ["full_name", "phone", "location", "linkedin_url", "portfolio_url", "expected_salary"]:
                    if ai_data.get(key) and not profile.get(key):
                        profile[key] = ai_data[key]
                if ai_data.get("skills") and not profile.get("skills"):
                    profile["skills"] = ai_data["skills"]
                if ai_data.get("education") and not profile.get("education"):
                    profile["education"] = ai_data["education"]
                if ai_data.get("experience_years") is not None:
                    profile["experience_years"] = ai_data["experience_years"]

        return profile

    async def _ai_enhance(self, raw_text: str) -> Optional[Dict]:
        try:
            import openai
            client = openai.AsyncOpenAI(api_key=settings.OPENAI_API_KEY)
            prompt = f"""Extract structured profile data from this resume text. Return ONLY valid JSON with these keys:
full_name, phone, location, linkedin_url, portfolio_url, expected_salary, summary, skills (array), education (array of {{degree, institution}}), experience_years (number).

Resume text:
{raw_text[:3000]}"""
            response = await client.chat.completions.create(
                model="gpt-3.5-turbo",
                messages=[{"role": "user", "content": prompt}],
                max_tokens=700,
                temperature=0.2,
            )
            content = response.choices[0].message.content
            content = content.strip()
            if content.startswith("```"):
                content = content.split("```")[1]
                if content.startswith("json"):
                    content = content[4:]
            return json.loads(content)
        except Exception as e:
            logger.warning(f"AI resume enhancement failed: {e}")
            return None


resume_ai = ResumeAIExtractor()