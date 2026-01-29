import streamlit as st
import requests
from bs4 import BeautifulSoup
import pandas as pd
import time
from urllib.parse import quote_plus

# --- FUNGSI SCRAPING ---
def get_soup(url):
    headers = {
        'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/91.0.4472.124 Safari/537.36'
    }
    try:
        response = requests.get(url, headers=headers, timeout=10)
        response.raise_for_status()
        return BeautifulSoup(response.text, 'html.parser')
    except Exception as e:
        return None

def scrape_article_details(url, year_filter):
    soup = get_soup(url)
    if not soup: return None
    try:
        title_tag = soup.find('h1', class_='post-title') or soup.find('h1', class_='article-title') or soup.find('h1')
        title = title_tag.get_text(strip=True) if title_tag else "Judul tidak ditemukan"

        date_tag = soup.find('span', class_='article-date') or soup.find('span', class_='date') or soup.find('time')
        date_text = date_tag.get_text(strip=True) if date_tag else ""
        
        if not date_text:
            date_meta = soup.find('meta', property='article:published_time')
            date_text = date_meta['content'] if date_meta else ""

        if year_filter not in date_text:
            return None

        content_div = soup.find('div', class_='post-content') or \
                      soup.find('div', class_='article-content') or \
                      soup.find('div', itemprop='articleBody')
        
        if content_div:
            for extra in content_div(["script", "style", "div", "iframe", "ads"]):
                extra.decompose()
            content = content_div.get_text(separator=' ', strip=True)
        else:
            content = "Konten tidak ditemukan"

        return {'Judul Berita': title, 'Tanggal': date_text, 'Isi Berita': content, 'Link Sumber': url}
    except:
        return None

# --- ANTARMUKA STREAMLIT ---
st.set_page_config(page_title="Antara Sumbar Scraper", page_icon="📰")
st.title("📰 Antara News Sumbar Scraper")
st.write("Aplikasi untuk mengambil berita berdasarkan kata kunci dan tahun.")

with st.sidebar:
    st.header("Pengaturan Parameter")
    keyword = st.text_input("Kata Kunci", placeholder="Contoh: Kota Solok")
    tahun = st.text_input("Tahun", placeholder="Contoh: 2025")
    max_pages = st.number_input("Jumlah Halaman", min_value=1, max_value=100, value=5)
    start_button = st.button("Mulai Scrapping")

if start_button and keyword and tahun:
    base_url = "https://sumbar.antaranews.com"
    search_query = quote_plus(keyword)
    results = []
    
    progress_bar = st.progress(0)
    status_text = st.empty()
    
    for page in range(1, max_pages + 1):
        status_text.text(f"Mencari di halaman {page}...")
        search_url = f"{base_url}/search?q={search_query}&page={page}"
        soup = get_soup(search_url)
        
        if not soup: break
        articles = soup.find_all('article') or soup.select('div.simple-post')
        if not articles: break

        for article in articles:
            a_tag = article.find('a', href=True)
            if not a_tag: continue
            link = a_tag['href']
            if not link.startswith('http'): link = base_url + link
            
            details = scrape_article_details(link, tahun)
            if details:
                results.append(details)
        
        progress_bar.progress(page / max_pages)
        time.sleep(0.5)

    status_text.text("Proses Selesai!")
    
    if results:
        df = pd.DataFrame(results)
        st.success(f"Berhasil mengambil {len(df)} artikel!")
        st.dataframe(df.head())
        
        # Tombol Download
        csv = df.to_csv(index=False).encode('utf-8')
        st.download_button(
            label="📥 Download Data Berita (CSV)",
            data=csv,
            file_name=f"berita_{keyword}_{tahun}.csv",
            mime="text/csv",
        )
    else:
        st.warning("Tidak ada berita yang cocok ditemukan.")
