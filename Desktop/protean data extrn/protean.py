import requests
from bs4 import BeautifulSoup
import re
from urllib.parse import urljoin
import sqlite3
from datetime import datetime
import ollama


# ---------- EMAIL + PHONE EXTRACTORS ----------
def extract_emails(text):
    return re.findall(r'[a-zA-Z0-9_.+-]+@[a-zA-Z0-9-]+\.[a-zA-Z0-9-.]+', text)


def extract_phones(text):
    return re.findall(r'\+?\d[\d\s\-\(\)\.]{6,}\d', text)


# ---------- AI SECTOR DETECTOR ----------
def ai_detect_sector(about_text):
    try:
        prompt = f"""
        You are an expert classifier. Based on the ABOUT text below, identify the company's business sector.
        Return ONLY the sector name.

        ABOUT TEXT:
        {about_text}
        """

        response = ollama.chat(
            model="gpt-oss:120b-cloud",
            options={
                "num_predict": 250,
                "temperature": 0.4
            },
            messages=[{"role": "user", "content": prompt}]
        )

        return response["message"]["content"].strip()

    except Exception as e:
        print("AI Sector Detection Error:", e)
        return "Unknown"


FALLBACK_GHANA_ECOMMERCE_SITES = [
    "https://www.jumia.com.gh",
    "https://www.melcom.com",
    "https://tonaton.com",
    "https://jiji.com.gh",
    "https://zoobashop.com",
    "https://kikuu.com.gh",
    "https://www.amazon.com",
    "https://www.ebay.com",
    "https://www.aliexpress.com",
    "https://www.alibaba.com",
    "https://www.etsy.com",
    "https://www.walmart.com",
    "https://www.target.com",
    "https://www.bestbuy.com",
    "https://www.asos.com",
    "https://www.hm.com",
    "https://www.zara.com",
    "https://www.nike.com",
    "https://www.adidas.com",
    "https://www.ikea.com",
]


# ---------- GHANA E-COMMERCE GENERATOR ----------
def generate_ghana_ecommerce_sites():
    """Use DuckDuckGo search to find Ghana e-commerce websites, with a static fallback list."""
    try:
        query = "Ghana e-commerce online shopping websites"
        resp = requests.get(
            "https://duckduckgo.com/html/",
            params={"q": query},
            timeout=10,
            headers={"User-Agent": "Mozilla/5.0"},
        )

        if resp.status_code != 200:
            return FALLBACK_GHANA_ECOMMERCE_SITES

        soup = BeautifulSoup(resp.text, "html.parser")
        sites = []
        seen_domains = set()

        for a in soup.select("a.result__a"):
            href = a.get("href")
            if not href:
                continue

            url = href
            if "uddg=" in href:
                idx = href.rfind("uddg=")
                encoded = href[idx + 5 :]
                url = requests.utils.unquote(encoded)

            if not url.startswith("http"):
                continue

            domain = url.split("//")[-1].split("/")[0]
            if domain in seen_domains:
                continue

            seen_domains.add(domain)
            sites.append("https://" + domain)

            if len(sites) >= 20:
                break

        # Top up with fallback sites until we have up to 20 unique domains
        if len(sites) < 20:
            for fb in FALLBACK_GHANA_ECOMMERCE_SITES:
                if len(sites) >= 20:
                    break
                fb_domain = fb.split("//")[-1].split("/")[0]
                if fb_domain in seen_domains:
                    continue
                seen_domains.add(fb_domain)
                sites.append(fb)

        # If still nothing usable, fall back to static list
        return sites or FALLBACK_GHANA_ECOMMERCE_SITES

    except Exception as e:
        print("Ghana E-commerce Generator Error:", e)
        return FALLBACK_GHANA_ECOMMERCE_SITES


# ---------- WEBSITE SCRAPER ----------
def get_website_info(url):
    try:
        response = requests.get(url, timeout=10)
        html = response.text
        soup = BeautifulSoup(html, 'html.parser')

        title = soup.title.string.strip() if soup.title else "Not Found"
        domain = url.split("//")[-1].split("/")[0]

        # Extract ABOUT text (but DO NOT PRINT)
        about_text = "Not Found"
        for path in ["/about", "/about-us", "/company", "/who-we-are", "/overview"]:
            try:
                r = requests.get(urljoin(url, path), timeout=5)
                if r.status_code == 200:
                    about_soup = BeautifulSoup(r.text, 'html.parser')
                    about_text = about_soup.get_text(" ", strip=True)[:1200]
                    break
            except:
                continue

        # Contact info (search main page, about text, and contact pages)
        emails, phones = set(), set()

        # From main page text
        try:
            main_text = soup.get_text(" ", strip=True)
            emails.update(extract_emails(main_text))
            phones.update(extract_phones(main_text))
        except Exception:
            pass

        # From mailto:/tel: links on main page
        try:
            for a in soup.find_all("a", href=True):
                href = a["href"]
                if href.startswith("mailto:"):
                    emails.add(href.split(":", 1)[1].split("?", 1)[0])
                elif href.startswith("tel:"):
                    phones.add(href.split(":", 1)[1].split("?", 1)[0])
        except Exception:
            pass

        # From about text
        if about_text and about_text != "Not Found":
            try:
                emails.update(extract_emails(about_text))
                phones.update(extract_phones(about_text))
            except Exception:
                pass

        # From common contact pages
        contact_paths = [
            "/contact",
            "/contact-us",
            "/contactus",
            "/contacts",
            "/support",
            "/help",
            "/customer-service",
            "/customer-care",
        ]
        for path in contact_paths:
            try:
                r = requests.get(urljoin(url, path), timeout=5)
                if r.status_code == 200:
                    contact_soup = BeautifulSoup(r.text, "html.parser")
                    text = contact_soup.get_text(" ", strip=True)
                    emails.update(extract_emails(text))
                    phones.update(extract_phones(text))

                    for a in contact_soup.find_all("a", href=True):
                        href = a["href"]
                        if href.startswith("mailto:"):
                            emails.add(href.split(":", 1)[1].split("?", 1)[0])
                        elif href.startswith("tel:"):
                            phones.add(href.split(":", 1)[1].split("?", 1)[0])
            except Exception:
                continue

        # From links that look like contact/support/help pages
        try:
            candidate_links = set()
            for a in soup.find_all("a", href=True):
                href = a["href"]
                text = (a.get_text(" ", strip=True) or "").lower()
                href_lower = href.lower()
                if any(kw in text for kw in ["contact", "support", "help", "customer service", "customer care"]) or \
                   any(kw in href_lower for kw in ["contact", "support", "help", "customer"]):
                    candidate_links.add(urljoin(url, href))

            for link in list(candidate_links)[:5]:
                try:
                    r = requests.get(link, timeout=5)
                    if r.status_code != 200:
                        continue
                    link_soup = BeautifulSoup(r.text, "html.parser")
                    text = link_soup.get_text(" ", strip=True)
                    emails.update(extract_emails(text))
                    phones.update(extract_phones(text))

                    for a in link_soup.find_all("a", href=True):
                        href = a["href"]
                        if href.startswith("mailto:"):
                            emails.add(href.split(":", 1)[1].split("?", 1)[0])
                        elif href.startswith("tel:"):
                            phones.add(href.split(":", 1)[1].split("?", 1)[0])
                except Exception:
                    continue
        except Exception:
            pass

        # AI Detect sector
        sector = ai_detect_sector(about_text if about_text != "Not Found" else html)

        return {
            "URL": url,
            "Website": title,
            "Domain": domain,
            "Sector": sector,
            "Emails": ', '.join(sorted(emails)) if emails else "None",
            "Phones": ', '.join(sorted(phones)) if phones else "None",
        }

    except Exception as e:
        print(f"Error fetching {url}: {e}")
        return None


def init_db(db_path="website_info.db"):
    conn = sqlite3.connect(db_path)
    try:
        cursor = conn.cursor()
        cursor.execute(
            """
            CREATE TABLE IF NOT EXISTS website_info (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                url TEXT,
                website TEXT,
                domain TEXT,
                sector TEXT,
                emails TEXT,
                phones TEXT,
                created_at TEXT
            )
            """
        )
        conn.commit()
    finally:
        conn.close()


def save_website_info_to_db(info, db_path="website_info.db"):
    init_db(db_path)
    conn = sqlite3.connect(db_path)
    try:
        cursor = conn.cursor()
        cursor.execute(
            """
            INSERT INTO website_info (url, website, domain, sector, emails, phones, created_at)
            VALUES (?, ?, ?, ?, ?, ?, ?)
            """,
            (
                info.get("URL"),
                info.get("Website"),
                info.get("Domain"),
                info.get("Sector"),
                info.get("Emails"),
                info.get("Phones"),
                datetime.utcnow().isoformat(),
            ),
        )
        conn.commit()
    except Exception as e:
        print("DB Error:", e)
    finally:
        conn.close()


# -------------------------
# SINGLE USER INPUT
# -------------------------
if __name__ == "__main__":
    url = input("Enter website URL: ").strip()
    if not url.startswith("http"):
        url = "https://" + url

    info = get_website_info(url)

    if info:
        print("\n===== WEBSITE INFORMATION =====")
        for k, v in info.items():
            print(f"{k}: {v}")

        save_website_info_to_db(info)

        print("\nSaved website info to SQLite database")

    else:
        print("Failed to fetch website information.")
