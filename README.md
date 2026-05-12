# Naukri Job Scraper 🔍

A Python-based web scraper that collects job listings from Naukri.com for data-related roles — built as a personal project while learning web scraping.

---

## What it does

Scrapes job postings for the following roles:
- Data Engineer
- Data Analyst
- Power BI Developer
- Tableau Developer

Each run fetches **50 jobs** and saves them to a CSV file. Run it again and it automatically picks up from where it left off — no duplicate results.

Only jobs posted in the **last 6 months** are collected.

---

## Output

A `naukri_jobs.csv` file with these columns:

| Column | Description |
|---|---|
| Company Name | Name of the hiring company |
| Job Profile | Job title as listed |
| Role Category | Which role category it was scraped under |
| Skills Required | Tech skills mentioned in the listing |
| Salary | Salary range (or "Not Disclosed") |
| Posted | When the job was posted |
| Scraped On | Date you ran the script |

---

## Tech Stack

- Python 3.10+
- `requests` + `BeautifulSoup4` — for the basic scraper
- `Selenium` + `webdriver-manager` — for the browser-based scraper
- `lxml` — HTML parser
- `csv`, `json` — for output and offset tracking

---

## Setup

```bash
# Clone the repo
git clone https://github.com/your-username/naukri-job-scraper.git
cd naukri-job-scraper

# Install dependencies
pip install requests beautifulsoup4 lxml selenium webdriver-manager
```

> Chrome browser must be installed for the Selenium version.

---

How to run
```bash
python naukri_scraper_selenium.py
```

Every time you run either script:
- You get the next 50 jobs (pagination is handled automatically)
- Results get appended to `naukri_jobs.csv`
- Progress is saved in `naukri_offset.json`

---

## Project Structure

```
naukri-job-scraper/
├── naukri_scraper_selenium.py   # Selenium version
├── README.md
├── .gitignore
└── LICENSE
```
