"""
Naukri Job Scraper  

Requirements: pip install selenium webdriver-manager beautifulsoup4 lxml

Chrome must be installed on your machine.

Usage:
    python naukri_scraper_selenium.py
"""

from selenium import webdriver
from selenium.webdriver.chrome.service import Service
from selenium.webdriver.chrome.options import Options
from selenium.webdriver.common.by import By
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
from webdriver_manager.chrome import ChromeDriverManager
from bs4 import BeautifulSoup
import csv, json, time, random
from datetime import datetime, timedelta
from pathlib import Path

# CONFIG  (same as requests version)

JOBS_PER_RUN   = 50
OFFSET_FILE    = "naukri_offset.json"
OUTPUT_CSV     = "naukri_jobs.csv"
SIX_MONTHS_AGO = datetime.now() - timedelta(days=180)

ROLES = [
    {"label": "Data Engineer",       "keyword": "data-engineer",       "experience": "0to3"},
    {"label": "Data Analyst",        "keyword": "data-analyst",        "experience": "0to3"},
    {"label": "Power BI Developer",  "keyword": "power-bi-developer",  "experience": "0to3"},
    {"label": "Tableau Developer",   "keyword": "tableau-developer",   "experience": "0to3"},
]

CSV_FIELDS = ["Company Name", "Job Profile", "Role Category", "Skills Required", "Salary", "Posted", "Scraped On"]


# BROWSER SETUP

def create_driver(headless: bool = False) -> webdriver.Chrome:
    opts = Options()
    if headless:
        opts.add_argument("--headless=new")
    opts.add_argument("--no-sandbox")
    opts.add_argument("--disable-dev-shm-usage")
    opts.add_argument("--window-size=1920,1080")
    opts.add_argument("--disable-blink-features=AutomationControlled")
    opts.add_experimental_option("excludeSwitches", ["enable-automation"])
    opts.add_experimental_option("useAutomationExtension", False)
    opts.add_argument(
        "user-agent=Mozilla/5.0 (Windows NT 10.0; Win64; x64) "
        "AppleWebKit/537.36 (KHTML, like Gecko) Chrome/123.0.0.0 Safari/537.36"
    )

    service = Service(ChromeDriverManager().install())
    driver  = webdriver.Chrome(service=service, options=opts)

    # Patch navigator.webdriver flag
    driver.execute_script("Object.defineProperty(navigator, 'webdriver', {get: () => undefined})")
    return driver


# DATE / OFFSET UTILS  (identical to requests version)


def parse_posted_date(date_str: str) -> datetime | None:
    if not date_str:
        return None
    s = date_str.lower().strip()
    if "just now" in s or "today" in s:
        return datetime.now()
    if "day" in s:
        n = int("".join(filter(str.isdigit, s)) or "1")
        return datetime.now() - timedelta(days=n)
    if "month" in s:
        n = int("".join(filter(str.isdigit, s)) or "1")
        return datetime.now() - timedelta(days=n * 30)
    if "year" in s:
        return datetime.now() - timedelta(days=400)
    return None

def is_within_6_months(date_str: str) -> bool:
    dt = parse_posted_date(date_str)
    return True if dt is None else dt >= SIX_MONTHS_AGO

def load_offsets() -> dict:
    if Path(OFFSET_FILE).exists():
        with open(OFFSET_FILE) as f:
            return json.load(f)
    return {r["label"]: 1 for r in ROLES}

def save_offsets(offsets: dict):
    with open(OFFSET_FILE, "w") as f:
        json.dump(offsets, f, indent=2)

def build_url(keyword: str, experience: str, page: int) -> str:
    base = f"https://www.naukri.com/{keyword}-jobs"
    if page > 1:
        base += f"-{page}"
    return base + f"?experience={experience}&jobAge=180"

# SCRAPING WITH SELENIUM

def scrape_page(driver: webdriver.Chrome, url: str, role_label: str) -> list[dict]:
    jobs = []
    try:
        driver.get(url)
        # Wait for job cards to appear
        WebDriverWait(driver, 12).until(
            EC.presence_of_element_located((By.CSS_SELECTOR, "article.jobTuple, div.srp-jobtuple-wrapper, div[class*='jobTuple']"))
        )
        time.sleep(random.uniform(1.5, 3))   # let lazy content load

        # Scroll down to trigger lazy-loaded cards
        driver.execute_script("window.scrollTo(0, document.body.scrollHeight / 2);")
        time.sleep(1)
        driver.execute_script("window.scrollTo(0, document.body.scrollHeight);")
        time.sleep(1)

        soup  = BeautifulSoup(driver.page_source, "lxml")
        cards = (
            soup.select("article.jobTuple")
            or soup.select("div.srp-jobtuple-wrapper")
            or soup.select("article[class*='jobTuple']")
        )

        print(f"    Found {len(cards)} cards on page")

        for card in cards:
            try:
                company_tag = (
                    card.select_one("a.comp-name")
                    or card.select_one("span.comp-name")
                    or card.select_one("[class*='comp-name']")
                )
                company = company_tag.get_text(strip=True) if company_tag else "N/A"

                title_tag = (
                    card.select_one("a.title")
                    or card.select_one("a[class*='title']")
                )
                title = title_tag.get_text(strip=True) if title_tag else role_label

                skill_tags = (
                    card.select("li.tag-li")
                    or card.select("span[class*='skill']")
                    or card.select("ul[class*='tags'] li")
                )
                skills = ", ".join(t.get_text(strip=True) for t in skill_tags) if skill_tags else "N/A"

                salary_tag = (
                    card.select_one("span.salary-text")
                    or card.select_one("[class*='salary']")
                )
                salary = salary_tag.get_text(strip=True) if salary_tag else "Not Disclosed"

                date_tag = (
                    card.select_one("span.job-post-day")
                    or card.select_one("[class*='postDate']")
                    or card.select_one("span[class*='date']")
                )
                posted = date_tag.get_text(strip=True) if date_tag else ""

                if not is_within_6_months(posted):
                    continue

                jobs.append({
                    "Company Name":    company,
                    "Job Profile":     title,
                    "Role Category":   role_label,
                    "Skills Required": skills,
                    "Salary":          salary,
                    "Posted":          posted,
                    "Scraped On":      datetime.now().strftime("%Y-%m-%d"),
                })
            except Exception as e:
                print(f"    [!] Card parse error: {e}")
    except Exception as e:
        print(f"  [!] Page load error for {url}: {e}")
    return jobs


# CSV WRITE

def write_to_csv(jobs: list[dict], filepath: str):
    file_exists = Path(filepath).exists()
    with open(filepath, "a", newline="", encoding="utf-8") as f:
        writer = csv.DictWriter(f, fieldnames=CSV_FIELDS)
        if not file_exists:
            writer.writeheader()
        writer.writerows(jobs)
    print(f"  ✔  Written {len(jobs)} jobs → {filepath}")


# MAIN

def main():
    print("=" * 60)
    print("  Naukri Selenium Scraper  —  50 jobs per run")
    print("=" * 60)

    offsets       = load_offsets()
    all_jobs      = []
    slots_per_role = JOBS_PER_RUN // len(ROLES)
    extra          = JOBS_PER_RUN % len(ROLES)

    # Set headless=False if you want to watch the browser
    driver = create_driver(headless=False)

    try:
        for i, role in enumerate(ROLES):
            target = slots_per_role + (1 if i < extra else 0)
            label  = role["label"]
            page   = offsets.get(label, 1)

            print(f"\n[{label}]  page {page}  (target: {target} jobs)")
            collected = []

            while len(collected) < target:
                url = build_url(role["keyword"], role["experience"], page)
                print(f"  GET {url}")
                page_jobs = scrape_page(driver, url, label)

                if not page_jobs:
                    print("  [!] Empty page — stopping this role.")
                    break

                collected.extend(page_jobs)
                page += 1

            collected = collected[:target]
            all_jobs.extend(collected)
            offsets[label] = page
            print(f"  → {len(collected)} jobs collected. Next run starts at page {page}.")

    finally:
        driver.quit()

    if all_jobs:
        write_to_csv(all_jobs, OUTPUT_CSV)
        print(f"\n✅  Total jobs saved: {len(all_jobs)}")
        print(f"   CSV: {Path(OUTPUT_CSV).resolve()}")
    else:
        print("\n⚠️  No jobs collected. Try headless=False to debug.")

    save_offsets(offsets)
    print(f"   Offsets saved to '{OFFSET_FILE}'.\n")


if __name__ == "__main__":
    main()
