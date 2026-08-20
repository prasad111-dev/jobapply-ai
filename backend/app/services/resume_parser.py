import pdfplumber
import io
from docx import Document
import re
from typing import Dict, List

class ResumeParser:
    SKILL_KEYWORDS = [
        "python", "java", "javascript", "typescript", "react", "angular", "vue",
        "node.js", "express", "django", "flask", "fastapi", "spring",
        "aws", "azure", "gcp", "docker", "kubernetes", "linux",
        "sql", "mongodb", "postgresql", "redis", "elasticsearch",
        "machine learning", "deep learning", "tensorflow", "pytorch",
        "git", "ci/cd", "jenkins", "terraform", "ansible",
        "html", "css", "sass", "bootstrap", "tailwind",
        "rest api", "graphql", "grpc", "microservices",
        "agile", "scrum", "jira", "confluence",
        "c", "c++", "c#", "go", "rust", "php", "ruby", "swift", "kotlin",
        "figma", "sketch", "adobe xd", "photoshop", "illustrator",
        "excel", "powerpoint", "word", "tableau", "power bi",
        "blockchain", "web3", "solidity",
        "devops", "sre", "cloud architect", "data engineer", "data scientist",
        "product manager", "project manager", "business analyst",
        "qa", "sDET", "automation testing", "manual testing",
        "ui/ux", "frontend", "backend", "full stack", "mobile",
        "ios", "android", "flutter", "react native",
    ]

    def parse(self, content: bytes, filename: str) -> Dict:
        if filename.endswith('.pdf'):
            raw_text = self._extract_pdf(content)
        elif filename.endswith(('.docx', '.doc')):
            raw_text = self._extract_docx(content)
        else:
            raw_text = ""
        
        return {
            "raw_text": raw_text,
            "skills": self._extract_skills(raw_text),
            "experience_years": self._extract_experience(raw_text),
            "education": self._extract_education(raw_text),
            "contact_info": self._extract_contact(raw_text),
            "summary": self._extract_summary(raw_text),
        }

    def _extract_pdf(self, content: bytes) -> str:
        text = ""
        with pdfplumber.open(io.BytesIO(content)) as pdf:
            for page in pdf.pages:
                text += page.extract_text() or ""
        return text

    def _extract_docx(self, content: bytes) -> str:
        doc = Document(io.BytesIO(content))
        return "\n".join([para.text for para in doc.paragraphs])

    def _extract_skills(self, text: str) -> List[str]:
        text_lower = text.lower()
        return [skill for skill in self.SKILL_KEYWORDS if skill in text_lower]

    def _extract_experience(self, text: str) -> int:
        patterns = [
            r'(\d+)\+?\s*years?\s*(?:of\s*)?experience',
            r'experience\s*:\s*(\d+)\+?\s*years?',
            r'(\d+)\+?\s*years?\s*(?:in|of)\s*(?:software|engineering|development)',
        ]
        for pattern in patterns:
            match = re.search(pattern, text, re.IGNORECASE)
            if match:
                return int(match.group(1))
        return 0

    def _extract_education(self, text: str) -> List[Dict]:
        education = []
        degree_patterns = [
            (r"\b(bachelor(?:s)? of (?:technology|engineering|science|arts|commerce))\b", r"B.Tech/B.E/B.Sc"),
            (r"\b(b\.?tech)\b", "B.Tech"),
            (r"\b(b\.?e\.?)\b", "B.E"),
            (r"\b(b\.?sc)\b", "B.Sc"),
            (r"\b(b\.?com)\b", "B.Com"),
            (r"\b(b\.?a\b)", "B.A"),
            (r"\b(master(?:s)? of (?:technology|engineering|science|business administration|computer applications))\b", "M.Tech/M.E/M.Sc"),
            (r"\b(m\.?tech)\b", "M.Tech"),
            (r"\b(m\.?e\.?)\b", "M.E"),
            (r"\b(m\.?sc)\b", "M.Sc"),
            (r"\b(m\.?ca)\b", "MCA"),
            (r"\b(m\.?ba)\b", "MBA"),
            (r"\b(phd|ph\.?d|doctorate)\b", "PhD"),
            (r"\b(diploma|certificate)\b", "Diploma/Certificate"),
        ]
        seen = set()
        for pattern, label in degree_patterns:
            matches = re.finditer(pattern, text, re.IGNORECASE)
            for match in matches:
                degree = match.group(1).strip()
                key = degree.lower()
                if key in seen:
                    continue
                seen.add(key)
                education.append({"degree": label, "context": text[max(0,match.start()-50):match.end()+50].strip()})
        return education

    def _extract_contact(self, text: str) -> Dict:
        email_match = re.search(r'[\w.+-]+@[\w-]+\.[\w.]+', text)
        phone_match = re.search(r'[\+]?[\d\s\-\(\)]{10,15}', text)
        return {
            "email": email_match.group(0) if email_match else None,
            "phone": phone_match.group(0).strip() if phone_match else None,
        }

    def _extract_summary(self, text: str) -> str:
        lines = text.split('\n')
        summary_keywords = ['summary', 'objective', 'profile', 'about']
        for i, line in enumerate(lines):
            if any(kw in line.lower() for kw in summary_keywords):
                return '\n'.join(lines[i+1:i+5]).strip()
        return text[:500] if text else ""
