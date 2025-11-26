import requests
from bs4 import BeautifulSoup
import pandas as pd
import time
from datetime import datetime

# --------------------------
# Helpers
# --------------------------
COUNTRIES = ["Kenya","Nigeria","South Africa","Uganda","Ghana","USA","UK","Canada","France","Germany","India"] 

def fetch_page(url):
    try:
        r = requests.get(url, headers={'User-Agent':'Mozilla/5.0'})
        if r.status_code == 200:
            return r.text
    except:
        return None
    return None

def extract_keywords(text):
    return ", ".join(text.lower().split())

def detect_country(title):
    if not title: return None
    for c in COUNTRIES:
        if c.lower() in title.lower():
            return c
    return None

def parse_date(date_str):
    if not date_str: return None
    try:
        return pd.to_datetime(date_str, errors='coerce').strftime("%Y-%m-%d")
    except:
        return None

def filter_readable(title):
    return title and len(title.strip()) > 5

# --------------------------
# Scraper functions
# --------------------------

def scrape_africacheck(pages=50):
    data=[]
    for p in range(pages):
        url=f"https://africacheck.org/fact-checks?f%5B0%5D=topics%3A152&page={p}"
        html=fetch_page(url)
        if not html: continue
        soup=BeautifulSoup(html,'html.parser')
        arts=soup.find_all("div", class_="search-result__content")
        for art in arts:
            a = art.find("a")
            title = a.text.strip() if a else None
            if not filter_readable(title): continue
            link = "https://africacheck.org"+a["href"] if a else None
            date_tag = art.find("time")
            date=parse_date(date_tag.text.strip()) if date_tag else None
            verdict_tag = art.find("span", class_="fact-check__verdict-text")
            verdict = verdict_tag.text.strip() if verdict_tag else "Unknown"
            label = "Fake" if verdict and any(k in verdict.lower() for k in ["false","fake","misleading"]) else "Real"
            country = detect_country(title)
            data.append({
                "source":"AfricaCheck",
                "medium":"news",
                "title":title,
                "url":link,
                "date":date,
                "verdict":verdict,
                "label":label,
                "country":country,
                "keywords":extract_keywords(title)
            })
        time.sleep(0.3)
    return data

def scrape_snopes(pages=50):
    data=[]
    for p in range(1,pages+1):
        url=f"https://www.snopes.com/fact-check/page/{p}/?s=politics"
        html=fetch_page(url)
        if not html: continue
        soup=BeautifulSoup(html,'html.parser')
        articles = soup.find_all("article")
        for art in articles:
            title_tag = art.find("h2")
            title = title_tag.text.strip() if title_tag else None
            if not filter_readable(title): continue
            link_tag = title_tag.find("a") if title_tag else None
            link = link_tag['href'] if link_tag else None
            date_tag = art.find("time")
            date=parse_date(date_tag['datetime'] if date_tag and date_tag.has_attr('datetime') else None)
            verdict_tag = art.find("span", class_="claim")
            verdict = verdict_tag.text.strip() if verdict_tag else "Fake"
            country = detect_country(title)
            data.append({
                "source":"Snopes",
                "medium":"fact-check",
                "title":title,
                "url":link,
                "date":date,
                "verdict":verdict,
                "label":"Fake",
                "country":country,
                "keywords":extract_keywords(title)
            })
        time.sleep(0.3)
    return data

def scrape_politifact(pages=50):
    data=[]
    for p in range(1,pages+1):
        url=f"https://www.politifact.com/factchecks/list/?page={p}&tag=politics"
        html=fetch_page(url)
        if not html: continue
        soup=BeautifulSoup(html,'html.parser')
        arts = soup.find_all("li", class_="o-listicle__item")
        for art in arts:
            title_tag = art.find("a")
            title = title_tag.text.strip() if title_tag else None
            if not filter_readable(title): continue
            link = "https://www.politifact.com"+title_tag['href'] if title_tag else None
            date_tag = art.find("footer")
            date=parse_date(date_tag.text.strip() if date_tag else None)
            verdict_tag = art.find("div", class_="m-statement__quote")
            verdict = verdict_tag.text.strip() if verdict_tag else "Fake"
            country = detect_country(title)
            data.append({
                "source":"PolitiFact",
                "medium":"fact-check",
                "title":title,
                "url":link,
                "date":date,
                "verdict":verdict,
                "label":"Fake",
                "country":country,
                "keywords":extract_keywords(title)
            })
        time.sleep(0.3)
    return data

def scrape_onion(pages=20):
    data=[]
    base_url="https://www.theonion.com/c/news-in-brief"
    for p in range(1,pages+1):
        url=f"{base_url}?page={p}"
        html=fetch_page(url)
        if not html: continue
        soup=BeautifulSoup(html,'html.parser')
        arts = soup.find_all("h2")
        for art in arts:
            title = art.text.strip()
            if not filter_readable(title): continue
            link_tag=art.find("a")
            link=link_tag['href'] if link_tag else None
            country=detect_country(title)
            data.append({
                "source":"The Onion",
                "medium":"satire",
                "title":title,
                "url":link,
                "date":None,
                "verdict":"Fake",
                "label":"Fake",
                "country":country,
                "keywords":extract_keywords(title)
            })
        time.sleep(0.3)
    return data

# --------------------------
# Real news sources
# --------------------------
def scrape_real_news_bbc(pages=30):
    data=[]
    base_url="https://www.bbc.com/news/politics"
    for p in range(1,pages+1):
        url=f"{base_url}?page={p}"
        html=fetch_page(url)
        if not html: continue
        soup=BeautifulSoup(html,'html.parser')
        arts = soup.find_all("a", {"class":"gs-c-promo-heading"})
        for art in arts:
            title = art.text.strip()
            if not filter_readable(title): continue
            link = "https://www.bbc.com" + art['href']
            date=None
            country=detect_country(title)
            data.append({
                "source":"BBC Politics",
                "medium":"news",
                "title":title,
                "url":link,
                "date":date,
                "verdict":"Real",
                "label":"Real",
                "country":country,
                "keywords":extract_keywords(title)
            })
        time.sleep(0.3)
    return data

# --------------------------
# Combine everything
# --------------------------
print("🔎 Scraping Fake + Real political news (global + African)...")

data=[]
data.extend(scrape_africacheck(pages=50))
data.extend(scrape_snopes(pages=50))
data.extend(scrape_politifact(pages=50))
data.extend(scrape_onion(pages=20))
data.extend(scrape_real_news_bbc(pages=30))  # Add more sources here like Reuters, Al Jazeera, AllAfrica

# Remove duplicates
df=pd.DataFrame(data)
df=df.drop_duplicates(subset=["title"]).reset_index(drop=True)

# Optional: sample 1500 rows if too big
if len(df)>1500:
    df=df.sample(1500, random_state=42)

# Save CSV
df.to_csv("mega_fake_real_political_news.csv", index=False, encoding="utf-8")
print(f"\n✅ CSV saved: mega_fake_real_political_news.csv")
print(df.info())
print(df.head())
