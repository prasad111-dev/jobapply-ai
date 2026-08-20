import openai
from typing import Dict, List, Optional
from app.core.config import get_settings

settings = get_settings()

class AIEngine:
    def __init__(self):
        if settings.OPENAI_API_KEY:
            openai.api_key = settings.OPENAI_API_KEY

    async def generate_cover_letter(self, job_title: str, company: str, job_description: str, user_profile: Dict) -> str:
        prompt = f"""Write a professional cover letter for the following job application:
        
Job Title: {job_title}
Company: {company}
Job Description: {job_description[:1000]}

Candidate Profile:
- Name: {user_profile.get('full_name', 'Applicant')}
- Skills: {', '.join(user_profile.get('skills', []))}
- Experience: {user_profile.get('experience_years', 0)} years
- Education: {str(user_profile.get('education', []))[:500]}

Requirements:
- Professional and concise (3-4 paragraphs)
- Highlight relevant skills and experience
- Show enthusiasm for the role
- Include a strong closing

Write the cover letter:"""

        try:
            if settings.OPENAI_API_KEY:
                client = openai.AsyncOpenAI(api_key=settings.OPENAI_API_KEY)
                response = await client.chat.completions.create(
                    model="gpt-3.5-turbo",
                    messages=[{"role": "user", "content": prompt}],
                    max_tokens=500,
                    temperature=0.7
                )
                return response.choices[0].message.content
            else:
                return self._generate_template_cover_letter(job_title, company, user_profile)
        except Exception as e:
            return self._generate_template_cover_letter(job_title, company, user_profile)

    def _generate_template_cover_letter(self, job_title: str, company: str, user_profile: Dict) -> str:
        name = user_profile.get('full_name', 'Applicant')
        skills = ', '.join(user_profile.get('skills', [])[:5])
        years = user_profile.get('experience_years', 0)
        
        return f"""Dear Hiring Manager,

I am writing to express my strong interest in the {job_title} position at {company}. With {years} years of experience in the field and skills in {skills}, I am confident I would be a valuable addition to your team.

Throughout my career, I have developed expertise in building scalable solutions and collaborating with cross-functional teams. My technical skills and problem-solving abilities make me well-suited for this role.

I am excited about the opportunity to contribute to {company}'s success and would welcome the chance to discuss how my background aligns with your needs. Thank you for considering my application.

Best regards,
{name}"""

    async def match_job_to_profile(self, job: Dict, user_profile: Dict) -> float:
        job_skills = set(job.get('skills_required', []))
        user_skills = set(user_profile.get('skills', []))
        
        if not job_skills:
            return 0.5
        
        skill_overlap = len(job_skills.intersection(user_skills)) / len(job_skills)
        
        experience_match = 1.0
        required_exp = job.get('experience_required', 0)
        user_exp = user_profile.get('experience_years', 0)
        if required_exp > 0:
            if user_exp >= required_exp:
                experience_match = 1.0
            elif user_exp >= required_exp * 0.7:
                experience_match = 0.7
            else:
                experience_match = 0.4
        
        score = (skill_overlap * 0.6) + (experience_match * 0.4)
        return round(min(score, 1.0), 2)

    async def generate_auto_answers(self, job: Dict, user_profile: Dict) -> Dict:
        """Generate answers for common job-application questions from the user profile.

        This is the 'zero typing' layer - answers come from the profile so the
        user never has to fill application forms manually.
        """
        answers = {
            "current_salary": user_profile.get("current_salary", ""),
            "expected_salary": user_profile.get("expected_salary", ""),
            "notice_period": user_profile.get("notice_period", ""),
            "work_authorization": user_profile.get("work_authorization", "Yes, authorized to work"),
            "availability": user_profile.get("availability", "Immediate"),
            "preferred_location": user_profile.get("preferred_location", user_profile.get("location", "")),
            "willing_to_relocate": "Yes" if user_profile.get("willing_to_relocate", True) else "No",
            "linkedin_url": user_profile.get("linkedin_url", ""),
            "portfolio_url": user_profile.get("portfolio_url", ""),
            "current_company": user_profile.get("current_company", ""),
            "current_title": user_profile.get("current_title", ""),
            "highest_education": self._highest_education(user_profile.get("education", [])),
            "why_interested": f"I am excited about the {job.get('title', 'this')} role at {job.get('company', 'your company')} because my experience aligns well with the responsibilities.",
            "resume_link": user_profile.get("resume_link", ""),
        }
        return {k: v for k, v in answers.items() if v}

    def _highest_education(self, education: List) -> str:
        if not education:
            return ""
        edu = education[0]
        if isinstance(edu, dict):
            return edu.get("degree", "")
        return str(edu)

    async def generate_form_responses(self, form_fields: List[Dict], user_profile: Dict) -> Dict:
        responses = {}
        for field in form_fields:
            field_name = field.get('name', '').lower()
            field_type = field.get('type', 'text')
            
            if 'name' in field_name and 'full' in field_name:
                responses[field['name']] = user_profile.get('full_name', '')
            elif 'email' in field_name:
                responses[field['name']] = user_profile.get('email', '')
            elif 'phone' in field_name:
                responses[field['name']] = user_profile.get('phone', '')
            elif 'experience' in field_name and 'year' in field_name:
                responses[field['name']] = str(user_profile.get('experience_years', 0))
            elif 'skill' in field_name:
                responses[field['name']] = ', '.join(user_profile.get('skills', []))
            elif 'resume' in field_name or 'cv' in field_name:
                responses[field['name']] = 'resume_upload'
            elif 'cover' in field_name:
                responses[field['name']] = user_profile.get('cover_letter', '')
            elif 'linkedin' in field_name:
                responses[field['name']] = user_profile.get('linkedin_url', '')
            elif 'portfolio' in field_name or 'website' in field_name:
                responses[field['name']] = user_profile.get('portfolio_url', '')
            elif 'location' in field_name or 'city' in field_name:
                responses[field['name']] = user_profile.get('location', '')
            elif 'salary' in field_name:
                responses[field['name']] = user_profile.get('expected_salary', '')
            elif field_type == 'textarea':
                responses[field['name']] = user_profile.get('cover_letter', 'Interested in this position.')
            else:
                responses[field['name']] = ''
        
        return responses

ai_engine = AIEngine()
