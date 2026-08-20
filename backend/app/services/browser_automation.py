import asyncio
import logging
import random
import os
import re
from typing import Dict, List, Optional

try:
    from playwright.async_api import async_playwright, Browser, Page, BrowserContext
    PLAYWRIGHT_AVAILABLE = True
except ImportError:
    PLAYWRIGHT_AVAILABLE = False

logger = logging.getLogger(__name__)

CHROME_PATHS = [
    "/usr/bin/google-chrome",
    "/usr/bin/google-chrome-stable",
    "/usr/bin/chromium-browser",
    "/usr/bin/chromium",
]


def _find_chrome():
    for p in CHROME_PATHS:
        if os.path.exists(p):
            return p
    # Playwright's own Chromium (used on Render / when no system Chrome exists)
    try:
        from playwright._impl._driver import compute_driver_executable
    except Exception:
        compute_driver_executable = None
    pw_root = os.environ.get("PLAYWRIGHT_BROWSERS_PATH", "")
    if pw_root:
        candidates = [
            os.path.join(pw_root, "chromium-*/chrome-linux/chrome"),
            os.path.join(pw_root, "chromium-*/chrome-linux64/chrome"),
        ]
        for pattern in candidates:
            import glob
            matches = sorted(glob.glob(pattern))
            if matches:
                return matches[0]
    return None


class PlatformAutomation:
    """Platform-specific login, scrape, and apply logic."""

    @staticmethod
    async def login(page: Page, platform: str, username: str, password: str) -> bool:
        handlers = {
            "indeed": PlatformAutomation._login_indeed,
            "linkedin": PlatformAutomation._login_linkedin,
            "naukri": PlatformAutomation._login_naukri,
            "glassdoor": PlatformAutomation._login_glassdoor,
            "internshala": PlatformAutomation._login_internshala,
            "shine": PlatformAutomation._login_shine,
        }
        handler = handlers.get(platform)
        if not handler:
            logger.warning(f"No login handler for {platform}")
            return False
        return await handler(page, username, password)

    @staticmethod
    async def _login_indeed(page: Page, username: str, password: str) -> bool:
        try:
            await page.goto("https://secure.indeed.com/auth", wait_until="domcontentloaded", timeout=30000)
            await asyncio.sleep(random.uniform(2, 4))

            email_filled = False
            for sel in ['input[name="email"]', 'input[type="email"]', '#email', 'input[placeholder*="Email" i]']:
                try:
                    el = await page.wait_for_selector(sel, timeout=3000)
                    if el:
                        await el.click()
                        await el.fill(username)
                        email_filled = True
                        break
                except:
                    continue

            if not email_filled:
                logger.error("Indeed: email field not found")
                return False

            await asyncio.sleep(random.uniform(0.5, 1.5))

            for sel in ['input[name="password"]', 'input[type="password"]', '#password']:
                try:
                    el = await page.wait_for_selector(sel, timeout=3000)
                    if el:
                        await el.click()
                        await el.fill(password)
                        break
                except:
                    continue

            await asyncio.sleep(random.uniform(0.5, 1.5))

            for sel in ['button[type="submit"]', '#signInButton', 'button:has-text("Sign in")', 'button:has-text("Log in")']:
                try:
                    el = await page.wait_for_selector(sel, timeout=3000)
                    if el:
                        await el.click()
                        break
                except:
                    continue

            await asyncio.sleep(random.uniform(4, 6))
            url = page.url
            return "myjobs" in url or "jobs" in url or "profile" in url or "indeed.com" in url

        except Exception as e:
            logger.error(f"Indeed login error: {e}")
            return False

    @staticmethod
    async def _login_linkedin(page: Page, username: str, password: str) -> bool:
        try:
            await page.goto("https://www.linkedin.com/login", wait_until="domcontentloaded", timeout=30000)
            await asyncio.sleep(random.uniform(2, 4))

            for sel in ['input[name="session_key"]', '#session_key', 'input[type="email"]']:
                try:
                    el = await page.wait_for_selector(sel, timeout=3000)
                    if el:
                        await el.click()
                        await el.fill(username)
                        break
                except:
                    continue

            await asyncio.sleep(random.uniform(0.5, 1.5))

            for sel in ['input[name="session_password"]', '#session_password', 'input[type="password"]']:
                try:
                    el = await page.wait_for_selector(sel, timeout=3000)
                    if el:
                        await el.click()
                        await el.fill(password)
                        break
                except:
                    continue

            await asyncio.sleep(random.uniform(0.5, 1.5))

            for sel in ['button[type="submit"]', 'button:has-text("Sign in")', 'button:has-text("Log in")']:
                try:
                    el = await page.wait_for_selector(sel, timeout=3000)
                    if el:
                        await el.click()
                        break
                except:
                    continue

            await asyncio.sleep(random.uniform(4, 6))
            url = page.url
            return "feed" in url or "mynetwork" in url or "linkedin.com/in" in url

        except Exception as e:
            logger.error(f"LinkedIn login error: {e}")
            return False

    @staticmethod
    async def _login_naukri(page: Page, username: str, password: str) -> bool:
        try:
            await page.goto("https://www.naukri.com/nlogin/login", wait_until="domcontentloaded", timeout=30000)
            await asyncio.sleep(random.uniform(2, 4))

            for sel in ['input[name="username"]', '#username', 'input[type="email"]', 'input[placeholder*="Email" i]']:
                try:
                    el = await page.wait_for_selector(sel, timeout=3000)
                    if el:
                        await el.click()
                        await el.fill(username)
                        break
                except:
                    continue

            await asyncio.sleep(random.uniform(0.5, 1.5))

            for sel in ['input[name="password"]', '#password', 'input[type="password"]']:
                try:
                    el = await page.wait_for_selector(sel, timeout=3000)
                    if el:
                        await el.click()
                        await el.fill(password)
                        break
                except:
                    continue

            await asyncio.sleep(random.uniform(0.5, 1.5))

            for sel in ['button[type="submit"]', 'button:has-text("Login")', 'button:has-text("Log in")']:
                try:
                    el = await page.wait_for_selector(sel, timeout=3000)
                    if el:
                        await el.click()
                        break
                except:
                    continue

            await asyncio.sleep(random.uniform(4, 6))
            url = page.url
            return "naukri" in url and "login" not in url.lower()

        except Exception as e:
            logger.error(f"Naukri login error: {e}")
            return False

    @staticmethod
    async def _login_internshala(page: Page, username: str, password: str) -> bool:
        """Internshala login: /login/user with email + password + csrf token."""
        try:
            await page.goto("https://internshala.com/login/user", wait_until="domcontentloaded", timeout=30000)
            await asyncio.sleep(random.uniform(2, 4))

            csrf = await page.query_selector('input[name="csrf_test_name"]')
            if csrf:
                try:
                    val = await csrf.get_attribute("value")
                    if val:
                        logger.info("Internshala CSRF token captured")
                except Exception:
                    pass

            for sel in ['input[name="email"]', 'input[type="email"]']:
                try:
                    el = await page.wait_for_selector(sel, timeout=3000)
                    if el:
                        await el.click()
                        await el.fill(username)
                        break
                except:
                    continue

            await asyncio.sleep(random.uniform(0.5, 1.5))

            for sel in ['input[name="password"]', 'input[type="password"]']:
                try:
                    el = await page.wait_for_selector(sel, timeout=3000)
                    if el:
                        await el.click()
                        await el.fill(password)
                        break
                except:
                    continue

            await asyncio.sleep(random.uniform(0.5, 1.5))

            for sel in ['button[type="submit"]', 'button:has-text("Login")', 'input[type="submit"]']:
                try:
                    el = await page.wait_for_selector(sel, timeout=3000)
                    if el:
                        await el.click()
                        break
                except:
                    continue

            await asyncio.sleep(random.uniform(4, 6))
            url = page.url
            return "internshala" in url and "login" not in url.lower()

        except Exception as e:
            logger.error(f"Internshala login error: {e}")
            return False

    @staticmethod
    async def _login_shine(page: Page, username: str, password: str) -> bool:
        """Shine.com login: email -> Login Via Password -> email + password -> Log In."""
        try:
            await page.goto("https://www.shine.com/pages/myshine/login", wait_until="domcontentloaded", timeout=30000)
            await asyncio.sleep(random.uniform(2, 4))

            # click "Login Via Password" tab
            try:
                tab = await page.wait_for_selector('button:has-text("Login Via Password")', timeout=5000)
                if tab:
                    await tab.click()
                    await asyncio.sleep(random.uniform(2, 3))
            except Exception:
                pass

            for sel in ['input[type="email"]', 'input[placeholder*="email" i]', 'input[name="email"]']:
                try:
                    el = await page.wait_for_selector(sel, timeout=3000)
                    if el:
                        await el.click()
                        await el.fill(username)
                        break
                except:
                    continue

            await asyncio.sleep(random.uniform(0.5, 1.5))

            for sel in ['input[type="password"]', 'input[name="password"]']:
                try:
                    el = await page.wait_for_selector(sel, timeout=3000)
                    if el:
                        await el.click()
                        await el.fill(password)
                        break
                except:
                    continue

            await asyncio.sleep(random.uniform(0.5, 1.5))

            for sel in ['button:has-text("Log In")', 'button:has-text("Login")', 'button[type="submit"]']:
                try:
                    el = await page.wait_for_selector(sel, timeout=3000)
                    if el:
                        await el.click()
                        break
                except:
                    continue

            await asyncio.sleep(random.uniform(4, 6))
            url = page.url
            return "shine" in url and "login" not in url.lower()

        except Exception as e:
            logger.error(f"Shine login error: {e}")
            return False

    @staticmethod
    async def _login_glassdoor(page: Page, username: str, password: str) -> bool:
        try:
            await page.goto("https://www.glassdoor.com/profile/login_input.htm", wait_until="domcontentloaded", timeout=30000)
            await asyncio.sleep(random.uniform(2, 4))

            for sel in ['input[name="email"]', '#email', 'input[type="email"]']:
                try:
                    el = await page.wait_for_selector(sel, timeout=3000)
                    if el:
                        await el.click()
                        await el.fill(username)
                        break
                except:
                    continue

            await asyncio.sleep(random.uniform(0.5, 1.5))

            for sel in ['input[name="password"]', '#password', 'input[type="password"]']:
                try:
                    el = await page.wait_for_selector(sel, timeout=3000)
                    if el:
                        await el.click()
                        await el.fill(password)
                        break
                except:
                    continue

            await asyncio.sleep(random.uniform(0.5, 1.5))

            for sel in ['button[type="submit"]', 'button:has-text("Sign in")', 'button:has-text("Log in")']:
                try:
                    el = await page.wait_for_selector(sel, timeout=3000)
                    if el:
                        await el.click()
                        break
                except:
                    continue

            await asyncio.sleep(random.uniform(4, 6))
            return "glassdoor.com" in page.url and "login" not in page.url.lower()

        except Exception as e:
            logger.error(f"Glassdoor login error: {e}")
            return False

    @staticmethod
    async def apply_to_job(page: Page, job_url: str, user_profile: Dict, resume_path: str = None, cover_letter: str = None, auto_answers: Dict = None) -> Dict:
        result = {"status": "failed", "filled_fields": [], "error": None, "screenshot_url": None}

        if "naukri.com" in job_url:
            return await PlatformAutomation._apply_naukri(page, job_url, user_profile, resume_path, cover_letter, auto_answers or {})

        if "internshala.com" in job_url:
            return await PlatformAutomation._apply_internshala(page, job_url, user_profile, resume_path, cover_letter, auto_answers or {})

        return await PlatformAutomation._apply_generic(page, job_url, user_profile, resume_path, cover_letter, auto_answers or {})

    @staticmethod
    async def _apply_naukri(page: Page, job_url: str, user_profile: Dict, resume_path: str = None, cover_letter: str = None, auto_answers: Dict = None) -> Dict:
        """Naukri apply flow: job detail page -> Apply button -> modal form -> submit."""
        result = {"status": "failed", "filled_fields": [], "error": None, "screenshot_url": None}
        try:
            await page.goto(job_url, wait_until="domcontentloaded", timeout=30000)
            await asyncio.sleep(random.uniform(3, 5))

            if "login" in page.url.lower() or "nlogin" in page.url.lower():
                result["error"] = "Not logged in - please connect your Naukri account first."
                return result

            applied_click = False
            apply_selectors = [
                '#apply-button',
                'button#apply-button',
                'button[class*="apply-button"]',
                'button[class*="applyButton"]',
                'button[class*="apply_"]',
                'a[class*="applyButton"]',
                'button:has-text("Apply")',
                'a:has-text("Apply")',
                'button:has-text("Easy Apply")',
                'button:has-text("Quick Apply")',
            ]
            for sel in apply_selectors:
                try:
                    el = await page.wait_for_selector(sel, timeout=2500)
                    if el:
                        await el.scroll_into_view_if_needed()
                        await asyncio.sleep(random.uniform(0.5, 1))
                        await el.click()
                        applied_click = True
                        break
                except:
                    continue

            if not applied_click:
                result["error"] = "Apply button not found on this job. The role may already be applied or closed."
                return result

            await asyncio.sleep(random.uniform(3, 5))

            field_values = PlatformAutomation._build_field_values(user_profile, cover_letter, auto_answers)
            selectors_map = {
                "full_name": ['input[name="fullName"]', 'input[name="full_name"]', 'input[placeholder*="Full Name" i]', 'input[placeholder*="full name" i]'],
                "email": ['input[name="email"]', 'input[type="email"]', '#email', 'input[placeholder*="Email" i]'],
                "phone": ['input[name="mobile"]', 'input[name="phone"]', 'input[type="tel"]', 'input[placeholder*="Mobile" i]', 'input[placeholder*="Phone" i]'],
                "location": ['input[name="location"]', 'input[placeholder*="Location" i]', 'input[placeholder*="City" i]'],
                "current_company": ['input[name="currentCompany"]', 'input[placeholder*="Current Company" i]', 'input[placeholder*="Company" i]'],
                "current_title": ['input[name="currentTitle"]', 'input[placeholder*="Current Designation" i]', 'input[placeholder*="Designation" i]'],
                "experience": ['input[name="experience"]', 'input[placeholder*="Experience" i]'],
                "expected_salary": ['input[name="expectedSalary"]', 'input[placeholder*="Expected" i]'],
                "current_salary": ['input[name="currentSalary"]', 'input[placeholder*="Current CTC" i]', 'input[placeholder*="Current Salary" i]'],
                "notice_period": ['select[name="noticePeriod"]', 'input[name="noticePeriod"]', 'input[placeholder*="Notice" i]', 'select[placeholder*="Notice" i]'],
                "cover_letter": ['textarea[name="coverLetter"]', 'textarea[placeholder*="cover" i]', 'textarea[class*="textArea"]'],
            }

            for field_name, selectors in selectors_map.items():
                value = field_values.get(field_name, "")
                if not value:
                    continue
                for sel in selectors:
                    try:
                        el = await page.wait_for_selector(sel, timeout=1500)
                        if el:
                            tag = (await el.evaluate("el => el.tagName")).lower()
                            await el.scroll_into_view_if_needed()
                            await asyncio.sleep(random.uniform(0.2, 0.4))
                            if tag == "select":
                                try:
                                    await el.select_option(value)
                                except:
                                    pass
                            else:
                                await el.click()
                                await el.fill("")
                                await el.type(value, delay=random.randint(15, 40))
                            result["filled_fields"].append(field_name)
                            await asyncio.sleep(random.uniform(0.3, 0.6))
                            break
                    except:
                        continue

            if resume_path and os.path.exists(resume_path):
                try:
                    file_inputs = await page.query_selector_all('input[type="file"]')
                    if file_inputs:
                        await file_inputs[0].set_input_files(resume_path)
                        result["filled_fields"].append("resume")
                        await asyncio.sleep(random.uniform(2, 4))
                except Exception as e:
                    logger.warning(f"Naukri resume upload failed: {e}")

            submit_selectors = [
                'button[class*="submitApplication"]',
                'button[class*="submitButton"]',
                'button:has-text("Submit Application")',
                'button:has-text("Submit")',
                'button:has-text("Send Application")',
                'button:has-text("Save & Submit")',
                'button[type="submit"]',
            ]
            for sel in submit_selectors:
                try:
                    el = await page.wait_for_selector(sel, timeout=2500)
                    if el:
                        await el.scroll_into_view_if_needed()
                        await asyncio.sleep(random.uniform(0.5, 1))
                        await el.click()
                        result["status"] = "submitted"
                        await asyncio.sleep(random.uniform(3, 5))
                        break
                except:
                    continue

            if result["status"] == "failed":
                if result["filled_fields"]:
                    result["status"] = "form_filled"
                    result["error"] = "Application form filled but submit button not found. Please submit manually."
                else:
                    result["error"] = "Could not locate the application form on this job page."

        except Exception as e:
            result["error"] = str(e)[:200]
            logger.error(f"Naukri apply error: {e}")

        return result

    @staticmethod
    async def _apply_internshala(page: Page, job_url: str, user_profile: Dict, resume_path: str = None, cover_letter: str = None, auto_answers: Dict = None) -> Dict:
        """Internshala apply: job detail -> Apply now -> application form -> submit."""
        result = {"status": "failed", "filled_fields": [], "error": None, "screenshot_url": None}
        try:
            await page.goto(job_url, wait_until="domcontentloaded", timeout=30000)
            await asyncio.sleep(random.uniform(3, 5))

            if "login" in page.url.lower():
                result["error"] = "Not logged in - please connect your Internshala account first."
                return result

            applied_click = False
            apply_selectors = [
                '#apply',
                'a[id="apply"]',
                'button[class*="apply"]',
                'a[class*="apply"]',
                'button:has-text("Apply now")',
                'a:has-text("Apply now")',
                'button:has-text("Apply")',
                'a:has-text("Apply")',
            ]
            for sel in apply_selectors:
                try:
                    el = await page.wait_for_selector(sel, timeout=3000)
                    if el:
                        await el.scroll_into_view_if_needed()
                        await asyncio.sleep(random.uniform(0.5, 1))
                        await el.click()
                        applied_click = True
                        break
                except:
                    continue

            if not applied_click:
                result["error"] = "Apply button not found on this Internshala internship."
                return result

            await asyncio.sleep(random.uniform(3, 5))

            field_values = PlatformAutomation._build_field_values(user_profile, cover_letter, auto_answers)

            # Answer "Why should you be hired for this internship?" + availability questions
            textarea_selectors = [
                'textarea[name="why_should_we_hire_you"]',
                'textarea[placeholder*="why should you be hired" i]',
                'textarea[placeholder*="why should" i]',
                'textarea',
            ]
            for sel in textarea_selectors:
                try:
                    el = await page.wait_for_selector(sel, timeout=2500)
                    if el:
                        answer = cover_letter or auto_answers.get("why_interested", "") or (
                            f"I am a skilled candidate with experience in {', '.join(user_profile.get('skills', [])[:4]) or 'the relevant skills'}. "
                            "I am excited about this opportunity and believe I would be a strong addition to the team."
                        )
                        await el.scroll_into_view_if_needed()
                        await el.click()
                        await el.fill("")
                        await el.type(answer, delay=random.randint(10, 25))
                        result["filled_fields"].append("why_should_we_hire_you")
                        break
                except:
                    continue

            # availability/start-date selects
            selects = await page.query_selector_all('select')
            availability_map = {
                "immediately": "Immediately", "1 week": "Within a week",
                "2 weeks": "Within 2 weeks", "1 month": "Within a month",
            }
            preferred = (auto_answers or {}).get("availability", "").lower()
            for sel in selects:
                try:
                    options = await sel.eval_on_selector_all('option', 'opts => opts.map(o => o.innerText.trim())')
                    chosen = None
                    for o in options:
                        ol = o.lower()
                        if preferred:
                            if preferred in ol:
                                chosen = o
                                break
                        elif any(k in ol for k in ["immediately", "within a week"]):
                            chosen = o
                            break
                    if chosen:
                        await sel.select_option(label=chosen)
                        result["filled_fields"].append("availability")
                except:
                    continue

            # duration select
            for sel in await page.query_selector_all('select'):
                try:
                    options = await sel.eval_on_selector_all('option', 'opts => opts.map(o => o.innerText.trim())')
                    for o in options:
                        if any(k in o.lower() for k in ["6 months", "3 months", "2 months"]):
                            await sel.select_option(label=o)
                            result["filled_fields"].append("duration")
                            break
                except:
                    continue

            if resume_path and os.path.exists(resume_path):
                try:
                    file_inputs = await page.query_selector_all('input[type="file"]')
                    if file_inputs:
                        await file_inputs[0].set_input_files(resume_path)
                        result["filled_fields"].append("resume")
                        await asyncio.sleep(random.uniform(2, 4))
                except Exception as e:
                    logger.warning(f"Internshala resume upload failed: {e}")

            submit_selectors = [
                'button[class*="submit"]',
                'button[type="submit"]',
                'button:has-text("Submit")',
                'button:has-text("Send Application")',
                'button:has-text("Apply")',
            ]
            for sel in submit_selectors:
                try:
                    el = await page.wait_for_selector(sel, timeout=2500)
                    if el:
                        await el.scroll_into_view_if_needed()
                        await asyncio.sleep(random.uniform(0.5, 1))
                        await el.click()
                        result["status"] = "submitted"
                        await asyncio.sleep(random.uniform(3, 5))
                        break
                except:
                    continue

            if result["status"] == "failed":
                if result["filled_fields"]:
                    result["status"] = "form_filled"
                    result["error"] = "Application form filled but submit button not found. Please submit manually."
                else:
                    result["error"] = "Could not locate the Internshala application form."

        except Exception as e:
            result["error"] = str(e)[:200]
            logger.error(f"Internshala apply error: {e}")

        return result

    @staticmethod
    def _build_field_values(user_profile: Dict, cover_letter: str, auto_answers: Dict) -> Dict:
        return {
            "full_name": user_profile.get("full_name", ""),
            "first_name": user_profile.get("full_name", "").split()[0] if user_profile.get("full_name") else "",
            "last_name": (user_profile.get("full_name", "").split()[-1] if user_profile.get("full_name") and len(user_profile.get("full_name", "").split()) > 1 else ""),
            "email": user_profile.get("email", ""),
            "phone": user_profile.get("phone", ""),
            "linkedin": user_profile.get("linkedin_url", ""),
            "portfolio": user_profile.get("portfolio_url", ""),
            "location": user_profile.get("location", ""),
            "experience": str(user_profile.get("experience_years", "")),
            "skills": ", ".join(user_profile.get("skills", [])),
            "cover_letter": cover_letter or "",
            "expected_salary": auto_answers.get("expected_salary", ""),
            "current_salary": auto_answers.get("current_salary", ""),
            "notice_period": auto_answers.get("notice_period", ""),
            "work_authorization": auto_answers.get("work_authorization", ""),
            "availability": auto_answers.get("availability", ""),
            "preferred_location": auto_answers.get("preferred_location", ""),
            "current_company": auto_answers.get("current_company", ""),
            "current_title": auto_answers.get("current_title", ""),
            "highest_education": auto_answers.get("highest_education", ""),
            "why_interested": auto_answers.get("why_interested", ""),
            "relocate": auto_answers.get("willing_to_relocate", ""),
        }

    @staticmethod
    async def _apply_generic(page: Page, job_url: str, user_profile: Dict, resume_path: str = None, cover_letter: str = None, auto_answers: Dict = None) -> Dict:
        result = {"status": "failed", "filled_fields": [], "error": None, "screenshot_url": None}

        try:
            await page.goto(job_url, wait_until="domcontentloaded", timeout=30000)
            await asyncio.sleep(random.uniform(2, 4))

            answers = auto_answers or {}
            field_values = {
                "full_name": user_profile.get("full_name", ""),
                "first_name": user_profile.get("full_name", "").split()[0] if user_profile.get("full_name") else "",
                "last_name": (user_profile.get("full_name", "").split()[-1] if user_profile.get("full_name") and len(user_profile.get("full_name", "").split()) > 1 else ""),
                "email": user_profile.get("email", ""),
                "phone": user_profile.get("phone", ""),
                "linkedin": user_profile.get("linkedin_url", ""),
                "portfolio": user_profile.get("portfolio_url", ""),
                "location": user_profile.get("location", ""),
                "experience": str(user_profile.get("experience_years", "")),
                "skills": ", ".join(user_profile.get("skills", [])),
                "cover_letter": cover_letter or "",
                "expected_salary": answers.get("expected_salary", ""),
                "current_salary": answers.get("current_salary", ""),
                "notice_period": answers.get("notice_period", ""),
                "work_authorization": answers.get("work_authorization", ""),
                "availability": answers.get("availability", ""),
                "preferred_location": answers.get("preferred_location", ""),
                "current_company": answers.get("current_company", ""),
                "current_title": answers.get("current_title", ""),
                "highest_education": answers.get("highest_education", ""),
                "why_interested": answers.get("why_interested", ""),
                "relocate": answers.get("willing_to_relocate", ""),
            }

            selectors_map = {
                "full_name": ['input[name="fullName"]', 'input[name="full_name"]', '#fullName', '#full-name', 'input[placeholder*="Full Name" i]', 'input[placeholder*="full name" i]'],
                "first_name": ['input[name="firstName"]', 'input[name="first_name"]', '#firstName', 'input[placeholder*="First Name" i]'],
                "last_name": ['input[name="lastName"]', 'input[name="last_name"]', '#lastName', 'input[placeholder*="Last Name" i]'],
                "email": ['input[name="email"]', 'input[type="email"]', '#email', 'input[placeholder*="Email" i]'],
                "phone": ['input[name="phone"]', 'input[name="telephone"]', 'input[type="tel"]', '#phone', 'input[placeholder*="Phone" i]'],
                "linkedin": ['input[name="linkedin"]', 'input[name="linkedinUrl"]', 'input[placeholder*="LinkedIn" i]'],
                "portfolio": ['input[name="portfolio"]', 'input[name="website"]', 'input[placeholder*="Portfolio" i]', 'input[placeholder*="Website" i]'],
                "location": ['input[name="location"]', 'input[name="city"]', '#location', 'input[placeholder*="Location" i]', 'input[placeholder*="City" i]'],
                "experience": ['input[name="experience"]', 'input[name="yearsOfExperience"]', '#experience', 'input[placeholder*="Experience" i]'],
                "skills": ['textarea[name="skills"]', 'input[name="skills"]', '#skills', 'textarea[placeholder*="Skills" i]'],
                "cover_letter": ['textarea[name="coverLetter"]', 'textarea[name="cover_letter"]', '#coverLetter', 'textarea[placeholder*="cover" i]'],
                "expected_salary": ['input[name="expectedSalary"]', 'input[name="expected_salary"]', 'input[placeholder*="Expected Salary" i]', 'input[placeholder*="expected salary" i]'],
                "current_salary": ['input[name="currentSalary"]', 'input[name="current_salary"]', 'input[placeholder*="Current Salary" i]', 'input[placeholder*="current salary" i]'],
                "notice_period": ['input[name="noticePeriod"]', 'input[name="notice_period"]', 'input[placeholder*="Notice" i]', 'select[name="notice_period"]'],
                "work_authorization": ['input[name="workAuthorization"]', 'input[name="work_authorization"]', 'input[placeholder*="Work Authorization" i]', 'select[name="work_authorization"]'],
                "availability": ['input[name="availability"]', 'input[name="start_date"]', 'input[placeholder*="Availability" i]', 'input[placeholder*="Start Date" i]', 'input[placeholder*="start date" i]'],
                "preferred_location": ['input[name="preferredLocation"]', 'input[name="preferred_location"]', 'input[placeholder*="Preferred Location" i]'],
                "current_company": ['input[name="currentCompany"]', 'input[name="current_company"]', 'input[placeholder*="Current Company" i]', 'input[placeholder*="current company" i]'],
                "current_title": ['input[name="currentTitle"]', 'input[name="current_title"]', 'input[placeholder*="Current Designation" i]', 'input[placeholder*="current designation" i]'],
                "highest_education": ['input[name="education"]', 'input[name="highest_education"]', 'input[placeholder*="Education" i]', 'select[name="education"]'],
                "why_interested": ['textarea[name="why_interested"]', 'textarea[placeholder*="Why are you interested" i]', 'textarea[placeholder*="why do you want" i]'],
                "relocate": ['input[name="willingToRelocate"]', 'input[name="willing_to_relocate"]', 'select[name="willing_to_relocate"]'],
            }

            for field_name, selectors in selectors_map.items():
                value = field_values.get(field_name, "")
                if not value:
                    continue
                for sel in selectors:
                    try:
                        el = await page.query_selector(sel)
                        if el:
                            await el.click()
                            await el.fill("")
                            await asyncio.sleep(random.uniform(0.1, 0.3))
                            for char in value:
                                await el.type(char, delay=random.randint(20, 60))
                            result["filled_fields"].append(field_name)
                            await asyncio.sleep(random.uniform(0.3, 0.7))
                            break
                    except:
                        continue

            if resume_path and os.path.exists(resume_path):
                try:
                    file_inputs = await page.query_selector_all('input[type="file"]')
                    if file_inputs:
                        await file_inputs[0].set_input_files(resume_path)
                        result["filled_fields"].append("resume")
                        await asyncio.sleep(random.uniform(2, 4))
                except Exception as e:
                    logger.warning(f"Resume upload failed: {e}")

            submit_selectors = [
                'button[type="submit"]', 'input[type="submit"]',
                '#submit', '#apply', '.apply-btn',
                'button:has-text("Apply")', 'button:has-text("Submit")',
                'button:has-text("Send")', 'button:has-text("Apply Now")',
                'a:has-text("Apply Now")', 'button:has-text("Quick Apply")',
            ]
            for sel in submit_selectors:
                try:
                    el = await page.wait_for_selector(sel, timeout=3000)
                    if el:
                        await el.scroll_into_view_if_needed()
                        await asyncio.sleep(random.uniform(0.5, 1))
                        await el.click()
                        result["status"] = "submitted"
                        await asyncio.sleep(random.uniform(3, 5))
                        break
                except:
                    continue

            if result["status"] == "failed":
                if result["filled_fields"]:
                    result["status"] = "form_filled"
                    result["error"] = "Form filled but submit button not found. Please submit manually."
                else:
                    result["error"] = "Could not find application form fields on this page."

        except Exception as e:
            result["error"] = str(e)[:200]
            logger.error(f"Apply error: {e}")

        return result


class BrowserAutomation:
    def __init__(self):
        self.browser: Optional[Browser] = None
        self.context: Optional[BrowserContext] = None
        self._playwright = None
        self.chrome_path = _find_chrome()

    async def _get_browser(self):
        if not PLAYWRIGHT_AVAILABLE:
            raise RuntimeError("Playwright not installed")
        if not self.chrome_path:
            raise RuntimeError("No Chrome/Chromium found on system")
        if not self.browser:
            self._playwright = await async_playwright().start()
            self.browser = await self._playwright.chromium.launch(
                headless=True,
                executable_path=self.chrome_path,
                args=[
                    '--no-sandbox', '--disable-setuid-sandbox',
                    '--disable-dev-shm-usage', '--disable-gpu',
                    '--disable-blink-features=AutomationControlled',
                    '--disable-quic',
                    '--disable-features=NetworkService',
                    '--disable-http2',
                ]
            )
            self.context = await self.browser.new_context(
                user_agent='Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36',
                viewport={'width': 1920, 'height': 1080},
                locale='en-US',
            )
        return self.context

    async def close(self):
        if self.context:
            try: await self.context.close()
            except: pass
        if self.browser:
            try: await self.browser.close()
            except: pass
        if self._playwright:
            try: await self._playwright.stop()
            except: pass
        self.browser = None
        self.context = None
        self._playwright = None

    async def apply_to_job_realtime(self, platform: str, job_url: str, username: str, password: str, user_profile: Dict, resume_path: str = None, cover_letter: str = None, auto_answers: Dict = None, user_id: int = None) -> Dict:
        context = await self._get_browser()
        result = {"login_success": False, "apply_result": None, "error": None, "used_session": False}

        try:
            from app.services.session_storage import load_session_cookies, save_session_cookies

            session_loaded = False
            if user_id:
                cookies = load_session_cookies(user_id, platform)
                if cookies:
                    try:
                        await context.add_cookies(cookies)
                        session_loaded = True
                        logger.info(f"Reusing saved session for user {user_id} on {platform}")
                    except Exception as e:
                        logger.warning(f"Could not reuse session cookies: {e}")

            page = await context.new_page()

            if session_loaded:
                try:
                    await page.goto(job_url, wait_until="domcontentloaded", timeout=30000)
                    await asyncio.sleep(random.uniform(3, 5))
                    still_logged_in = "login" not in page.url.lower()
                    if still_logged_in:
                        result["login_success"] = True
                        result["used_session"] = True
                        apply_result = await PlatformAutomation.apply_to_job(
                            page, job_url, user_profile, resume_path=resume_path, cover_letter=cover_letter, auto_answers=auto_answers
                        )
                        result["apply_result"] = apply_result
                        await page.close()
                        return result
                except Exception as e:
                    logger.warning(f"Session reuse check failed, falling back to login: {e}")
                try:
                    await page.close()
                except:
                    pass
                page = await context.new_page()

            logged_in = await PlatformAutomation.login(page, platform, username, password)
            result["login_success"] = logged_in

            if user_id and logged_in:
                try:
                    save_session_cookies(user_id, platform, await context.cookies())
                except Exception as e:
                    logger.warning(f"Failed to persist session: {e}")

            if not logged_in:
                result["error"] = f"Login to {platform} failed. Check credentials."
                await page.close()
                return result

            apply_result = await PlatformAutomation.apply_to_job(
                page, job_url, user_profile, resume_path=resume_path, cover_letter=cover_letter, auto_answers=auto_answers
            )
            result["apply_result"] = apply_result

        except Exception as e:
            result["error"] = str(e)[:200]
            logger.error(f"Realtime apply error: {e}")
        finally:
            try:
                await page.close()
            except:
                pass

        return result

    async def test_platform_connection(self, platform: str, username: str, password: str, user_id: int = None) -> Dict:
        """Verify credentials by actually logging in. Saves session cookies on success.

        This is the 'connect' experience - the user enters their real password once,
        we log in to confirm it works, and store the session so future applies don't
        need the password again.
        """
        context = await self._get_browser()
        page = await context.new_page()
        result = {"success": False, "message": "", "login_success": False, "session_saved": False}

        try:
            logged_in = await PlatformAutomation.login(page, platform, username, password)
            result["login_success"] = logged_in

            if logged_in:
                result["success"] = True
                result["message"] = f"Connected to {platform} successfully. Session saved - auto-apply is ready."
                if user_id:
                    try:
                        from app.services.session_storage import save_session_cookies
                        result["session_saved"] = save_session_cookies(user_id, platform, await context.cookies())
                    except Exception as e:
                        logger.warning(f"Session save failed during connection test: {e}")
            else:
                result["message"] = f"Login to {platform} failed. Check your username and password."
                try:
                    body = await page.inner_text('body')
                    if 'captcha' in body.lower() or 'verification' in body.lower():
                        result["message"] = f"{platform} is showing a bot/captcha verification. Please complete it once in your browser, then reconnect."
                except Exception:
                    pass

        except Exception as e:
            result["message"] = f"Connection test error: {str(e)[:200]}"
            logger.error(f"Connection test error for {platform}: {e}")
        finally:
            try:
                await page.close()
            except:
                pass

        return result

    async def login_to_platform(self, page: Page, platform_name: str, username: str, password: str) -> bool:
        return await PlatformAutomation.login(page, platform_name, username, password)

    async def apply_to_job(self, page: Page, job_url: str, user_profile: Dict, resume_path: str = None, cover_letter: str = None) -> Dict:
        return await PlatformAutomation.apply_to_job(page, job_url, user_profile, resume_path=resume_path, cover_letter=cover_letter)

    async def scrape_jobs(self, platform_name: str, query: str = "") -> List[Dict]:
        context = await self._get_browser()
        page = await context.new_page()
        jobs = []

        platform_urls = {
            'indeed': f'https://www.indeed.com/jobs?q={query}',
            'linkedin': f'https://www.linkedin.com/jobs/search/?keywords={query}',
            'naukri': f'https://www.naukri.com/{query.replace(" ", "-")}-jobs',
            'glassdoor': f'https://www.glassdoor.com/Job/jobs.htm?sc.keyword={query}',
            'foundit': f'https://www.foundit.com/search/{query}',
            'shine': f'https://www.shine.com/job/search?q={query}',
        }
        url = platform_urls.get(platform_name, f'https://www.{platform_name}.com/jobs?q={query}')

        try:
            await page.goto(url, wait_until="domcontentloaded", timeout=30000)
            await asyncio.sleep(random.uniform(4, 7))

            body_text = await page.inner_text('body')
            if 'captcha' in body_text.lower() or 'verification required' in body_text.lower():
                logger.warning(f"Bot protection detected on {platform_name}")
                await page.close()
                return jobs

            if platform_name == 'naukri':
                jobs = await self._parse_naukri(page)
            elif platform_name == 'indeed':
                jobs = await self._parse_indeed(page)
            elif platform_name == 'linkedin':
                jobs = await self._parse_linkedin(page)
            else:
                jobs = await self._parse_generic(page, platform_name)

            if not jobs:
                jobs = await self._parse_by_links(page, platform_name)

        except Exception as e:
            logger.error(f"Scraping error for {platform_name}: {e}")
        finally:
            await page.close()

        return jobs

_NAUKRI_TITLE_WORDS = {
    "python", "developer", "developers", "software", "senior", "junior", "lead",
    "backend", "frontend", "full", "stack", "walk", "in", "walkin", "direct",
    "fresher", "intern", "internship", "data", "machine", "learning", "ai",
    "engineer", "engineering", "sdet", "qa", "test", "testing", "devops",
    "cloud", "java", "react", "node", "angular", "sql", "analyst", "role",
    "urgent", "hiring", "opening", "openings", "requirement", "apply", "now",
    "senior", "staff", "principal", "architect", "manager", "engineer",
}

_NAUKRI_CITIES = {
    "bengaluru", "bangalore", "hyderabad", "secunderabad", "pune", "chennai",
    "mumbai", "gurugram", "gurgaon", "noida", "delhi", "new-delhi", "kolkata",
    "ahmedabad", "indore", "coimbatore", "kerala", "thane", "remote", "jaipur",
    "lucknow", "chandigarh", "mohali", "nagpur", "vizag", "visakhapatnam",
    "work-from-home", "anywhere", "india", "kolkata", "trivandrum", "kochi",
}


def _parse_naukri_company(link: str) -> str:
    """Extract the company from a Naukri job slug.

    Slug format: job-listings-<title>-<company>-<city>-<exp>-<id>
    e.g. job-listings-python-developer-tata-consultancy-services-indore-4-to-9-years-170826033457
    """
    try:
        parts = link.split('/')
        slug = parts[-1] if parts[-1] else parts[-2]
        slug = slug.replace("job-listings-", "")
        tokens = [t for t in slug.split('-') if t]
        # find first city token -> everything after it is location/exp/id
        cut = len(tokens)
        for i, t in enumerate(tokens):
            if t.lower() in _NAUKRI_CITIES:
                cut = i
                break
        # drop trailing exp/id markers (e.g. "0", "to", "5", "years")
        head = tokens[:cut]
        while head and (head[-1].isdigit() or head[-1].lower() in ("to", "years", "year")):
            head.pop()
        # strip leading title/role words, keep remaining = company
        while head and head[0].lower() in _NAUKRI_TITLE_WORDS:
            head.pop(0)
        company = " ".join(head).title() if head else ""
        return company[:150] or "Unknown"
    except Exception:
        return "Unknown"


    async def _parse_naukri(self, page: Page) -> List[Dict]:
        jobs = []
        cards = await page.query_selector_all('.cust-job-tuple, [data-job-id]')
        logger.info(f"Naukri: found {len(cards)} cards")

        for card in cards[:20]:
            try:
                title = ""
                link = ""
                company = ""
                location = ""

                title_el = await card.query_selector('a.title')
                if title_el:
                    title = (await title_el.inner_text()).strip()
                    link = await title_el.get_attribute('href') or ""

                company_el = await card.query_selector('.companyName, .companyLoc, [class*="companyName"]')
                if company_el:
                    company = (await company_el.inner_text()).strip()
                if not company:
                    company = _parse_naukri_company(link)

                loc_el = await card.query_selector('.locWdth, .add-span, [class*="location"]')
                if loc_el:
                    location = (await loc_el.inner_text()).strip()

                if title:
                    full_link = link if link.startswith('http') else f"https://www.naukri.com{link}"
                    jobs.append({
                        'title': title, 'company': company or 'Unknown',
                        'location': location, 'platform_source': 'naukri',
                        'platform_url': full_link,
                        'platform_job_id': f"naukri_{hash(title + company)}",
                        'job_type': 'full-time',
                        'remote_option': 'remote' in (title + location).lower(),
                        'skills_required': [],
                    })
            except Exception as e:
                logger.warning(f"Naukri parse error: {e}")

        return jobs

    async def _parse_indeed(self, page: Page) -> List[Dict]:
        jobs = []
        cards = await page.query_selector_all('.result, .job_seen_beacon, .slider_item')
        logger.info(f"Indeed: found {len(cards)} cards")

        for card in cards[:20]:
            try:
                title_el = await card.query_selector('h2 a, .jobTitle a, a[data-jk]')
                if not title_el:
                    continue
                title = (await title_el.inner_text()).strip()
                link = await title_el.get_attribute('href') or ""

                company_el = await card.query_selector('.companyName, .company_name, .company')
                company = (await company_el.inner_text()).strip() if company_el else "Unknown"

                loc_el = await card.query_selector('.companyLocation, .location')
                location = (await loc_el.inner_text()).strip() if loc_el else ""

                if title:
                    full_link = link if link.startswith('http') else f"https://www.indeed.com{link}"
                    jobs.append({
                        'title': title, 'company': company,
                        'location': location, 'platform_source': 'indeed',
                        'platform_url': full_link,
                        'platform_job_id': f"indeed_{hash(title + company)}",
                        'job_type': 'full-time',
                        'remote_option': 'remote' in (title + location).lower(),
                        'skills_required': [],
                    })
            except Exception as e:
                logger.warning(f"Indeed parse error: {e}")

        return jobs

    async def _parse_linkedin(self, page: Page) -> List[Dict]:
        jobs = []
        cards = await page.query_selector_all('.base-card, .jobs-search__result-card')
        logger.info(f"LinkedIn: found {len(cards)} cards")

        for card in cards[:20]:
            try:
                title_el = await card.query_selector('.base-search-card__title, h3')
                if not title_el:
                    continue
                title = (await title_el.inner_text()).strip()
                link_el = await card.query_selector('a')
                link = await link_el.get_attribute('href') if link_el else ""

                company_el = await card.query_selector('.base-search-card__subtitle, .hidden-nested-link')
                company = (await company_el.inner_text()).strip() if company_el else "Unknown"

                loc_el = await card.query_selector('.job-search-card__location')
                location = (await loc_el.inner_text()).strip() if loc_el else ""

                if title:
                    jobs.append({
                        'title': title, 'company': company,
                        'location': location, 'platform_source': 'linkedin',
                        'platform_url': link or "",
                        'platform_job_id': f"linkedin_{hash(title + company)}",
                        'job_type': 'full-time',
                        'remote_option': 'remote' in (title + location).lower(),
                        'skills_required': [],
                    })
            except Exception as e:
                logger.warning(f"LinkedIn parse error: {e}")

        return jobs

    async def _parse_generic(self, page: Page, platform_name: str) -> List[Dict]:
        jobs = []
        for sel in ['article', '.job-card', '.card', '[class*="job"]', '[class*="listing"]']:
            cards = await page.query_selector_all(sel)
            if len(cards) >= 3:
                for card in cards[:20]:
                    try:
                        link_el = await card.query_selector('a')
                        if not link_el:
                            continue
                        title = (await link_el.inner_text()).strip()
                        href = await link_el.get_attribute('href') or ""
                        if title and len(title) > 3 and len(title) < 200:
                            full_link = href if href.startswith('http') else f"https://www.{platform_name}.com{href}"
                            jobs.append({
                                'title': title, 'company': 'Unknown', 'location': '',
                                'platform_source': platform_name, 'platform_url': full_link,
                                'platform_job_id': f"{platform_name}_{hash(title)}",
                                'job_type': 'full-time', 'remote_option': False,
                                'skills_required': [],
                            })
                    except:
                        continue
                if jobs:
                    break
        return jobs

    async def _parse_by_links(self, page: Page, platform_name: str) -> List[Dict]:
        jobs = []
        all_links = await page.query_selector_all('a')
        seen = set()
        for link_el in all_links:
            try:
                href = await link_el.get_attribute('href') or ''
                text = (await link_el.inner_text()).strip()
                if text and 5 < len(text) < 150 and href and href not in seen:
                    if any(kw in href.lower() for kw in ['/job', '/viewjob', '/listing', 'jobid', 'jk=']):
                        seen.add(href)
                        full_link = href if href.startswith('http') else f"https://www.{platform_name}.com{href}"
                        jobs.append({
                            'title': text, 'company': 'Unknown', 'location': '',
                            'platform_source': platform_name, 'platform_url': full_link,
                            'platform_job_id': f"{platform_name}_{hash(text)}",
                            'job_type': 'full-time', 'remote_option': False,
                            'skills_required': [],
                        })
            except:
                continue
            if len(jobs) >= 20:
                break
        return jobs

    async def fill_application_form(self, platform_url: str, user_profile: Dict, cover_letter: str = None) -> Dict:
        context = await self._get_browser()
        page = await context.new_page()
        try:
            return await PlatformAutomation.apply_to_job(page, platform_url, user_profile, cover_letter=cover_letter)
        finally:
            await page.close()


browser_automation = BrowserAutomation()
