# perfect_bot_unified.py (FINAL MERGED VERSION: Keywords Filtering + AI Proposals)
import os
import re
import time
import json
import logging
import sqlite3
import threading
from datetime import datetime
from urllib.parse import urljoin
import html

# Third-party imports
import requests
from bs4 import BeautifulSoup
from selenium import webdriver
from selenium.webdriver.chrome.options import Options
from selenium.webdriver.chrome.service import Service
from selenium.webdriver.common.by import By
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
from webdriver_manager.chrome import ChromeDriverManager
from selenium.common.exceptions import TimeoutException
from openai import OpenAI

# =================================================================================
# SECTION 1: CONFIGURATION (MERGED FROM OLD CONFIG.PY)
# =================================================================================

# --- SECRETS (⚠️ بياناتك) ---
TG_BOT_TOKEN = "8203753766:AAG0wnqXsG_J5dgixGR1GJVnzxfMg6OMXcI"
SAMBANOVA_API_KEY = "bff3f26b-e7f6-4f34-ae84-e849d8d3cab5"

PERMANENT_SUBSCRIBERS = [
    "5030267584",
    "7056782790"
]

# --- BEHAVIOR SETTINGS ---
POLL_INTERVAL_SECONDS = 60
MIN_BUGET_USD = 250
MAX_AGE_HOURS = 24
SEND_SCORE_THRESHOLD = 0.05 # رجعنا الفلتر (أي وظيفة سكورها أقل من كده مش هتتبعت)

# ✅ تم التعديل: تفعيل الوضع الخفي للسيرفرات
HEADLESS_BROWSER = True 

# --- TECHNICAL SETTINGS ---
BASE_URL = "https://mostaql.com"
SEARCH_URL = "https://mostaql.com/projects"
DATABASE_PATH = "mostaql_jobs.db"
CHROME_PROFILE_PATH = "mostaql_chrome_profile"

# --- KEYWORDS FOR JOB SCORING (THE FILTER) ---
# القاموس القديم رجع عشان يفلتر الوظائف
KEYWORDS = {
    "graphics_and_logos": [
        "Graphic Designer", "Logo Designer", "Branding Specialist", "UI/UX Designer", "Social Media Designer",
        "Print Designer", "Illustrator", "Photoshop Expert", "Illustrator Expert", "Figma Designer",
        "Corporate Identity", "Brand Style Guide", "UI Kit", "UX Research", "Wireframing", "Prototyping",
        "Social Media Kit", "Ad Creative Design", "Infographic Design", "Photo Editor",
        "مصمم جرافيك", "مطلوب مصمم شعارات", "تصميم هوية بصرية كاملة", "مصمم واجهات مستخدم UI/UX",
        "تصاميم سوشيال ميديا", "خبير فوتوشوب", "محترف اليستريتور", "تصميم بوستات انستغرام",
        "تصميم هوية شركة", "بروفايل شركة", "تصميم إعلانات ممولة", "مصمم أيقونات", "تعديل صور",
        "رسم فيكتور", "تصميم كروت شخصية", "تصميم بروشور وفلاير", "تصميم لافتات"
    ],
    "motion_and_video": [
        "Video Editor", "Motion Graphics Artist", "2D Animator", "Video Producer", "Reels/Shorts Editor",
        "YouTube Video Editor", "Explainer Video Creator", "Logo Animation", "Video Ad Creator",
        "After Effects Expert", "Premiere Pro Expert", "Color Grading", "Sound Design",
        "مونتير", "محرر فيديو", "موشن جرافيك", "مصمم فيديوهات", "تعديل فيديو", "صانع محتوى فيديو",
        "مونتاج فيديوهات يوتيوب", "فيديو إعلاني", "تصميم فيديو موشن جرافيك", "خبير After Effects",
        "محترف بريمير برو", "عمل انترو احترافي", "تحريك شعار", "تصحيح ألوان الفيديو", "هندسة صوتية للفيديو"
    ],
    "3d_design": [
        "3D Artist", "3D Modeler", "3D Generalist", "Architectural Visualizer", "Product Renderer",
        "Character Artist", "3D Animator", "VFX Artist", "Blender Expert", "3ds Max Specialist",
        "CGI Artist", "3D Product Mockup", "Interior/Exterior Rendering",
        "مصمم ثلاثي الأبعاد", "نمذجة 3D", "تصميم منتجات 3D", "إظهار معماري", "رندر معماري",
        "تصميم شخصيات 3D", "خبير بلندر", "محترف 3ds Max", "تصميم مجسمات", "مشهد ثلاثي الأبعاد",
        "تصميم ديكور داخلي 3D"
    ],
    "web_development": [
        "Front-End Developer", "Back-End Developer", "Full-Stack Developer", "WordPress Developer",
        "Shopify Expert", "Web Designer", "React Developer", "PHP Laravel Developer", "Node.js Developer",
        "E-commerce Website", "Landing Page Design", "Website Customization", "Bug Fixes", "API Integration",
        "مطور مواقع", "مبرمج ويب", "مطور واجهات أمامية", "مطور Back-End", "خبير ووردبريس",
        "مطلوب مبرمج PHP Laravel", "إنشاء متجر إلكتروني", "تصميم وبرمجة موقع", "تطوير متجر شوبيفاي",
        "مطور Full-Stack", "تصميم صفحة هبوط", "تعديل على موقع قائم", "ربط بوابات الدفع", "خبير React.js"
    ],
    "mobile_app_development": [
        "Flutter Developer", "Mobile App Developer", "iOS Developer", "Android Developer",
        "Cross-Platform Developer", "React Native Developer", "Mobile UI/UX Designer",
        "App Development", "Build an App", "API Integration for App", "Firebase Expert",
        "مبرمج تطبيقات فلاتر", "مطور تطبيقات جوال", "تصميم وبرمجة تطبيق", "مطلوب مبرمج تطبيقات",
        "خبير Flutter", "مبرمج iOS", "مبرمج Android", "تطبيق لمتجر الكتروني", "ربط تطبيق مع لوحة تحكم",
        "تطوير تطبيق من الصفر"
    ],
    "voice_over": [
        "Voice Over Artist", "Voice Actor", "Narrator", "Dubbing Artist", "Audiobook Narrator",
        "Commercial Voice Over", "IVR System Voice", "Arabic Voice Over", "English Voice Over",
        "معلق صوتي", "فويس أوفر", "تسجيل صوتي احترافي", "التعليق الصوتي", "مطلوب فويس أوفر",
        "تسجيل إعلان صوتي", "دبلجة مقاطع فيديو", "التعليق باللغة العربية الفصحى", "فويس أوفر باللهجة الخليجية",
        "تسجيل كتاب صوتي", "الرد الآلي IVR"
    ],
    "ai_services": [
        "AI Specialist", "Machine Learning Engineer", "AI Content Creator", "Generative AI Artist",
        "Chatbot Developer", "AI Integration", "Stable Diffusion Expert", "Midjourney Artist",
        "خبير ذكاء اصطناعي", "توليد صور بالذكاء الاصطناعي", "متخصص Midjourney", "بناء شات بوت",
        "تطوير نماذج تعلم الآلة", "كتابة محتوى بالذكاء الاصطناعي", "دمج خدمات AI", "أتمتة مهام بالذكاء الاصطناعي"
    ],
    "print_and_packaging": [
        "Packaging Designer", "Book Cover Designer", "Layout Designer", "Print-Ready Files",
        "Publication Design", "Label Designer", "Box Packaging", "Die-line creation",
        "تصميم أغلفة كتب", "تصميم عبوات منتجات", "تغليف منتج", "تصميم ملصقات", "تنسيق كتاب للطباعة",
        "تصميم مجلات", "تصميم علب", "تجهيز ملفات للطباعة", "تصميم قائمة طعام (منيو)"
    ]
}

# =================================================================================
# SECTION 2: AI BRAIN (The Perfect Personas & Classy Intro)
# =================================================================================

client_ai = None
if SAMBANOVA_API_KEY and "xxxx" not in SAMBANOVA_API_KEY:
    try:
        client_ai = OpenAI(
            api_key=SAMBANOVA_API_KEY,
            base_url="https://api.sambanova.ai/v1",
        )
    except Exception as e:
        print(f"⚠️ Error initializing AI: {e}")

PROPOSAL_SYSTEM_PROMPT = """
أنت خبير ومستشار محترف (Top Rated Plus) في مجالك، ولديك ثقة عالية جداً بقدراتك.
مهمتك كتابة عرض يجمع بين "القوة التقنية" و"الطمأنينة" للعميل.

💎 **الشخصيات (خبراء بخبرة +10 سنوات):**
1. **[معماري/ديكور]** -> **المهندسة أمل محمد**. (اللغة: هندسية، راقية).
2. **[فيديو/موشن]** -> **المصمم أحمد محمد**. (اللغة: إبداعية، جذابة).
3. **[جرافيك/هوية]** -> **المصممة أميرة محمد**. (اللغة: فنية، تسويقية).
4. **[برمجة/تقنية]** -> **المهندس محمد سليمان**. (اللغة: دقيقة، تقنية).

🔥 **الهيكل الإجباري للرسالة (الالتزام بالترتيب والصياغة):**

1. **الترحيب:** (مرحبا أستاذ [الاسم]).

2. **التعريف + الطمأنينة (أهم جزء):**
   - ابدأ بـ: "معك [الاسم]، [الصفة] بخبرة تتجاوز 10 سنوات في [المجال الدقيق]."
   - **ثم فوراً اكتب جملة تأكيد الفهم:** "أؤكد لك أنني فهمت تماماً متطلبات مشروعك ومتطلعاتك العالية لإنشاء [هدف المشروع] بجودة فائقة وواقعية."

3. **التحليل الفني (إظهار العضلات):**
   - "لقد لفت انتباهي في تفاصيل المشروع أنك تحتاج..." (تحدث هنا عن التفاصيل التقنية الدقيقة).

4. **الحل المقترح:** (اشرح كيف ستنفذ العمل).

5. **الخاتمة (Classy Closing - شيك جداً):**
   - استخدم صيغ مثل: "يسعدني جداً أن أكون شريكاً في نجاح هذا المشروع"، "بانتظار تواصلكم الكريم للبدء على بركة الله".

⚠️ **تنبيهات:**
- لا تستخدم مقدمات إنشائية فارغة.
- الكلام موجه بصيغة المفرد المذكر.
"""

def generate_ai_proposal(job_description, client_name=""):
    """دالة توليد التقديم باستخدام Llama 3.3"""
    if not client_ai: return "⚠️ AI Key missing."
    
    clean_name = client_name.split()[0] if client_name else "عزيزي"
    clean_name = re.sub(r'[^\w\s]', '', clean_name).strip()

    try:
        user_content = (
            f"اسم العميل الأول: {clean_name}\n"
            f"تفاصيل المشروع:\n{job_description}"
        )
        response = client_ai.chat.completions.create(
            model="Meta-Llama-3.3-70B-Instruct",
            messages=[
                {"role": "system", "content": PROPOSAL_SYSTEM_PROMPT},
                {"role": "user", "content": user_content}
            ],
            temperature=0.3,
            top_p=0.9
        )
        return response.choices[0].message.content
    except Exception as e:
        logging.error(f"AI Generation Error: {e}")
        return "❌ Could not generate proposal."

# =================================================================================
# SECTION 3: INITIAL SETUP & DATABASE
# =================================================================================

logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s [%(levelname)s] (%(threadName)s) %(message)s",
    handlers=[logging.StreamHandler(), logging.FileHandler("bot.log", "a", "utf-8")]
)

DB_CONNECTION_LOCK = threading.Lock()

def get_db_connection():
    conn = sqlite3.connect(DATABASE_PATH, timeout=10, check_same_thread=False)
    return conn

def init_db(conn):
    logging.info("Initializing database...")
    with DB_CONNECTION_LOCK:
        cur = conn.cursor()
        cur.execute("""
        CREATE TABLE IF NOT EXISTS jobs (
            id TEXT PRIMARY KEY, title TEXT NOT NULL, url TEXT NOT NULL,
            first_seen TIMESTAMP NOT NULL, was_sent INTEGER DEFAULT 0,
            was_applied INTEGER DEFAULT 0, score REAL DEFAULT 0, max_budget REAL
        )""")
        cur.execute("CREATE TABLE IF NOT EXISTS subscribers (chat_id TEXT PRIMARY KEY)")
        conn.commit()
    logging.info("Database initialized successfully.")

def get_unseen_job_ids(conn, job_ids):
    if not job_ids: return []
    with DB_CONNECTION_LOCK:
        placeholders = ','.join('?' for _ in job_ids)
        query = f"SELECT id FROM jobs WHERE id IN ({placeholders})"
        cur = conn.cursor()
        cur.execute(query, job_ids)
        seen_ids = {row[0] for row in cur.fetchall()}
    return [job_id for job_id in job_ids if job_id not in seen_ids]

# =================================================================================
# SECTION 4: SCORING ENGINE (RESTORED FROM OLD CODE)
# =================================================================================
def normalize_text(text):
    if not text: return ""
    text = str(text).lower()
    # Simple normalization for matching
    text = re.sub(r"[ًٌٍَُِّْـ]", "", text) 
    text = text.replace("أ", "ا").replace("إ", "ا").replace("آ", "ا").replace("ى", "ي").replace("ة", "ه")
    return text

def calculate_relevance_score(text):
    """
    يقوم بحساب درجة التطابق بناءً على الكلمات المفتاحية في KEYWORDS
    """
    normalized_text = normalize_text(text)
    best_score = 0.0
    best_category = "General"
    matched_keywords = []

    for category, keywords in KEYWORDS.items():
        for keyword in keywords:
            normalized_keyword = normalize_text(keyword)
            # Check for exact word match or substring
            if normalized_keyword in normalized_text:
                # لو لقى كلمة، يديله سكور عالي (مثلاً 0.8)
                # ممكن نزود السكور لو لقى أكتر من كلمة، بس للتبسيط هنعتبر أي كلمة كفاية
                score = 0.8 
                if score > best_score:
                    best_score = score
                    best_category = category
                matched_keywords.append(keyword)
    
    # لو ملقاش أي كلمة، السكور هيبقى 0.0
    return best_score, matched_keywords, best_category

# =================================================================================
# SECTION 5: WEB SCRAPING
# =================================================================================
def perform_login(driver):
    logging.info("Checking login status...")
    try:
        driver.get(urljoin(BASE_URL, "/projects")); time.sleep(3)
        if "/login" in driver.current_url:
            logging.info("Not logged in. Proceeding with login form...")
            # ⚠️ Note: Make sure MOSTAQL_EMAIL & MOSTAQL_PASSWORD are defined in your env or code
            email_input = WebDriverWait(driver, 15).until(EC.presence_of_element_located((By.NAME, "email")))
            email_input.send_keys(MOSTAQL_EMAIL)
            driver.find_element(By.NAME, "password").send_keys(MOSTAQL_PASSWORD)
            driver.find_element(By.XPATH, "//button[contains(text(),'دخول')]").click()
            WebDriverWait(driver, 20).until(EC.not_(EC.url_contains("/login")))
            logging.info("Login successful!")
        else:
            logging.info("Already logged in via persistent Chrome profile.")
        return True
    except Exception:
        logging.exception("Selenium login process failed.")
        return False

def scrape_project_list(driver):
    logging.info("Scraping project list page...")
    try:
        driver.get(SEARCH_URL); time.sleep(5) # زيادة وقت الانتظار قليلاً
        
        # ✅ تم التعديل: إضافة سكرين شوت للـ Debug
        driver.save_screenshot("debug_page.png")
        logging.info("📸 Screenshot saved as debug_page.png (Check this if no jobs found)")

        WebDriverWait(driver, 20).until(EC.presence_of_element_located((By.CSS_SELECTOR, "tr.project-row")))
        soup = BeautifulSoup(driver.page_source, "lxml"); projects = []
        project_rows = soup.select('tr.project-row')
        for row in project_rows:
            link_tag = row.select_one("a[href*='/project/']")
            if not link_tag: continue
            
            bids_count = "0"
            bids_tag = row.select_one('li:-soup-contains("عرض")')
            if bids_tag:
                bids_match = re.search(r'\d+', bids_tag.get_text())
                if bids_match: bids_count = bids_match.group(0)

            url = urljoin(BASE_URL, link_tag['href'])
            job_id_match = re.search(r'/project/(\d+)', url)
            if not job_id_match: continue
            
            projects.append({
                'id': job_id_match.group(1), 
                'title': link_tag.get_text(strip=True), 
                'url': url,
                'bids_count': bids_count
            })
        logging.info(f"✅ Found {len(projects)} jobs on the page.")
        return projects
    except TimeoutException:
        logging.info("🟡 No jobs found on the page this time (Timeout)."); return []
    except Exception as e:
        logging.error(f"❌ Error in scrape_project_list: {e}"); return []
    
def get_job_details(driver, job_url):
    try:
        driver.get(job_url)
        WebDriverWait(driver, 20).until(EC.presence_of_element_located((By.CSS_SELECTOR, "div.carda__content")))
        soup = BeautifulSoup(driver.page_source, "lxml")
        
        description_tag = soup.select_one('div.carda__content')
        description = description_tag.get_text(separator="\n", strip=True) if description_tag else ""
        
        time_tag = soup.select_one('div.meta-value time')
        time_text = time_tag.get_text(strip=True) if time_tag else ""

        owner_details = {"name": "N/A", "joined": "N/A", "hire_rate": "N/A", "open_projects": "N/A"}
        owner_card = soup.select_one('div.profile_card')
        if owner_card:
            name_tag = owner_card.select_one('h5.profile__name bdi')
            if name_tag: owner_details['name'] = name_tag.get_text(strip=True)
            
            table_rows = owner_card.select('table.table-meta tr')
            for row in table_rows:
                cells = row.select('td')
                if len(cells) == 2:
                    key = cells[0].get_text(strip=True)
                    val = cells[1].get_text(strip=True)
                    if "تاريخ التسجيل" in key: owner_details['joined'] = val
                    elif "معدل التوظيف" in key: owner_details['hire_rate'] = val
                    elif "المشاريع المفتوحة" in key: owner_details['open_projects'] = val

        return {
            "description": description, 
            "time_text": time_text, 
            "full_html": driver.page_source,
            "owner_details": owner_details
        }
    except Exception as e:
        logging.warning(f"Failed to fetch details for {job_url}: {e}"); return None

def is_job_within_age_limit(time_text):
    if not time_text: return True
    try:
        text = time_text.lower()
        if any(s in text for s in ["دقيقة", "دقائق", "minute", "minutes", "لحظات"]): return True
        if any(s in text for s in ["ساعة", "ساعات", "hour", "hours"]):
            match = re.search(r'\d+', text)
            if match: return int(match.group()) <= MAX_AGE_HOURS
            return True
        if any(s in text for s in ["يوم", "أيام", "day", "شهر", "month"]): return False
        return True
    except: return True

def parse_max_budget(html_content):
    try:
        soup = BeautifulSoup(html_content, "lxml")
        budget_tag = soup.select_one('div.meta-value[data-type="project-budget_range"]')
        if budget_tag:
            text = budget_tag.get_text().replace(",", "")
            numbers = [float(n) for n in re.findall(r'\d+\.\d+|\d+', text)]
            if numbers: return max(numbers)
    except: pass
    try:
        soup = BeautifulSoup(html_content, "lxml")
        full_text = soup.get_text(" ", strip=True).replace(",", "")
        patterns = [r"(\d+)\s*-\s*(\d+)\s*\$", r"\$\s*(\d+)\s*-\s*(\d+)", r"(\d+)\s*دولار"]
        for pattern in patterns:
            matches = re.findall(pattern, full_text)
            if matches:
                flat = [float(n) for sub in matches for n in (sub if isinstance(sub, tuple) else (sub,))]
                if flat: return max(flat)
    except: pass
    return None

# =================================================================================
# SECTION 6: TELEGRAM BOT
# =================================================================================
class TelegramBot(threading.Thread):
    def __init__(self, conn):
        super().__init__(name="TelegramBot", daemon=True)
        self.api_url = f"https://api.telegram.org/bot{TG_BOT_TOKEN}"
        self.conn = conn
        self.offset = None
        self.running = True

    def send_job_notification(self, chat_id, job):
        safe_title = html.escape(job.get('title', 'No Title'))
        safe_url = job.get('url', '')
        time_posted = html.escape(job.get('time_posted', ''))
        
        owner = job.get('owner', {})
        owner_info = (
            f"-----------------------------------\n"
            f"👤 <b>Client:</b> {html.escape(owner.get('name', 'N/A'))} | "
            f"<b>Hire Rate:</b> {html.escape(owner.get('hire_rate', 'N/A'))}\n"
            f"-----------------------------------"
        )

        desc = html.escape(job.get('description', '')[:300] + "...")
        budget = f" | 💰 ${job['max_budget']:.0f}" if job.get('max_budget') else ""
        
        # --- إضافة التقديم الذكي ---
        ai_proposal = html.escape(job.get('ai_proposal', 'AI Proposal not generated.'))
        
        text = (
            f"✨ <b>New Relevant Job</b> ✨\n\n"
            f"<b>Title:</b> <a href=\"{safe_url}\">{safe_title}</a>\n"
            f"<b>Category:</b> {job.get('category', 'General')}\n"
            f"<b>Posted:</b> {time_posted}{budget}\n"
            f"{owner_info}\n\n"
            f"<b>Description:</b>\n{desc}\n\n"
            f"👇 <b>AI Suggested Proposal (Copy & Paste):</b>\n"
            f"<pre>{ai_proposal}</pre>"
        )
        
        reply_markup = {
            "inline_keyboard": [[
                {"text": "View Job ➡️", "url": job['url']},
                {"text": "Applied ✅", "callback_data": f"applied:{job['id']}"}
            ]]
        }
        
        try:
            payload = {
                "chat_id": chat_id,
                "text": text,
                "parse_mode": "HTML",
                "reply_markup": json.dumps(reply_markup),
                "disable_web_page_preview": True
            }
            requests.post(f"{self.api_url}/sendMessage", data=payload, timeout=15)
        except Exception as e:
            logging.error(f"Telegram Error: {e}")

    def run(self):
        logging.info("Telegram Bot poller started.")
        while self.running:
            try:
                params = {"timeout": 30, "offset": self.offset}
                response = requests.get(f"{self.api_url}/getUpdates", params=params, timeout=35)
                updates = response.json().get("result", [])
                for update in updates:
                    self.offset = update["update_id"] + 1
                    if "message" in update and update["message"].get("text") == "/start":
                        self.handle_start(update["message"])
            except: time.sleep(5)

    def handle_start(self, message):
        chat_id = str(message["chat"]["id"])
        with DB_CONNECTION_LOCK:
            self.conn.execute("INSERT OR IGNORE INTO subscribers (chat_id) VALUES (?)", (chat_id,))
            self.conn.commit()
        requests.post(f"{self.api_url}/sendMessage", data={"chat_id": chat_id, "text": "✅ Subscribed!"})

    def stop(self): self.running = False

# =================================================================================
# SECTION 7: MAIN APPLICATION
# =================================================================================
def main():
    db_conn = get_db_connection(); init_db(db_conn)
    tg_bot = TelegramBot(db_conn); tg_bot.start()
    driver = None
    
    try:
        # ✅ تم التعديل: إعدادات المتصفح الشاملة (Headless + Stealth + Linux Compatibility)
        opts = Options()
        opts.add_argument(f"--user-data-dir={os.path.abspath(CHROME_PROFILE_PATH)}")
        opts.add_argument("--no-sandbox") # ضروري لبيئة اللينكس
        opts.add_argument("--disable-dev-shm-usage") # ضروري لبيئة اللينكس
        opts.add_argument("--window-size=1920,1080")
        
        if HEADLESS_BROWSER:
            opts.add_argument("--headless=new")
        
        # --- إعدادات التخفي (Stealth Settings) ---
        opts.add_argument("user-agent=Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/114.0.0.0 Safari/537.36")
        opts.add_argument("--disable-blink-features=AutomationControlled")
        opts.add_experimental_option("excludeSwitches", ["enable-automation"])
        opts.add_experimental_option('useAutomationExtension', False)

        serv = Service(ChromeDriverManager().install())
        driver = webdriver.Chrome(service=serv, options=opts)
        
        # --- حقن كود جافاسكريبت لإخفاء الهوية ---
        driver.execute_script("Object.defineProperty(navigator, 'webdriver', {get: () => undefined})")
        
        if not perform_login(driver): return
        
        while True:
            logging.info("--- Starting Check Cycle ---")
            
            # Get Subscribers
            with DB_CONNECTION_LOCK:
                db_subs = [str(r[0]) for r in db_conn.execute("SELECT chat_id FROM subscribers").fetchall()]
            all_subs = set(db_subs + PERMANENT_SUBSCRIBERS)

            # Scrape
            jobs = scrape_project_list(driver)
            if not jobs: time.sleep(POLL_INTERVAL_SECONDS); continue

            # Filter New Jobs
            new_ids = get_unseen_job_ids(db_conn, [j['id'] for j in jobs])
            new_jobs = [j for j in jobs if j['id'] in new_ids]
            
            logging.info(f"Found {len(new_jobs)} new jobs.")

            for job in new_jobs:
                details = get_job_details(driver, job['url'])
                if not details: continue
                
                # Filter 1: Age
                if not is_job_within_age_limit(details['time_text']): continue
                
                # Budget Parsing
                max_budget = parse_max_budget(details['full_html'])
                
                # Filter 2: Budget
                if max_budget is not None and max_budget < MIN_BUGET_USD: continue
                
                # --- Filter 3: Keywords Scoring (The Old Efficient Logic) ---
                full_text = job['title'] + " " + details['description']
                score, matches, category = calculate_relevance_score(full_text)
                
                if score < SEND_SCORE_THRESHOLD:
                    logging.info(f"Skipping job {job['title']} (Score: {score} - Not relevant)")
                    continue

                logging.info(f"Generating AI Proposal for: {job['title']}...")
                
                # --- Step 4: AI Proposal ---
                ai_proposal = generate_ai_proposal(details['description'], details['owner_details'].get('name', ''))
                
                job_data = {
                    **job,
                    "max_budget": max_budget or 0,
                    "description": details['description'],
                    "time_posted": details['time_text'],
                    "owner": details['owner_details'],
                    "ai_proposal": ai_proposal,
                    "score": score,
                    "category": category
                }
                
                # Send to Telegram
                for chat_id in all_subs:
                    tg_bot.send_job_notification(chat_id, job_data)
                
                # Save to DB
                with DB_CONNECTION_LOCK:
                    db_conn.execute(
                        "INSERT INTO jobs (id, title, url, first_seen, was_sent, score, max_budget) VALUES (?, ?, ?, ?, ?, ?, ?)",
                        (job['id'], job['title'], job['url'], datetime.utcnow(), 1, score, max_budget)
                    )
                
                time.sleep(2)

            logging.info(f"Cycle done. Waiting {POLL_INTERVAL_SECONDS}s...")
            time.sleep(POLL_INTERVAL_SECONDS)
            
    except KeyboardInterrupt:
        logging.info("Stopping...")
    finally:
        if driver: driver.quit()
        tg_bot.stop(); db_conn.close()

if __name__ == "__main__":
    main()
