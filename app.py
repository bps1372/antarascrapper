import streamlit as st
import requests
from bs4 import BeautifulSoup
import pandas as pd
import time
from urllib.parse import quote_plus

# ===================== CONFIG =====================
st.set_page_config(
    page_title="Antara News Sumbar Scraper",
    page_icon="📰",
    layout="wide"
)

# ===================== CUSTOM CSS =====================
st.markdown("""
<style>
/* Global */
body {
    background-color: #0e1117;
    color: #fafafa;
    font-family: 'Inter', sans-serif;
}

/* Title */
.main-title {
    font-size: 42px;
    font-weight: 800;
    margin-bottom: 0;
}
.subtitle {
    font-size: 16px;
    color: #9aa0a6;
    margin-bottom: 30px;
}

/* Sidebar */
[data-testid="stSidebar"] {
    background: linear-gradient(180deg, #111827, #020617);
    border-right: 1px solid #1f2937;
}

/* Button */
.stButton > button {
    background: linear-gradient(90deg, #2563eb, #1d4ed8);
    color: white;
    border-radius: 12px;
    padding: 0.6rem 1.2rem;
    font-weight: 600;
    border: none;
}
.stButton > button:hover {
    background: linear-gradient(90deg, #1e40af, #1e3a8a);
}

/* Input */
input, textarea {
    border-radius: 10px !important;
}

/* Footer */
.footer {
    position: fixed;
    left: 0;
    bottom: 0;
    width: 100%;
    background-color: #020617;
    color: #9ca3af;
    text-align: center;
    padding: 8px;
    font-size: 13px;
    border-top: 1px solid #1f2937;
}
</style>
""", unsafe_allow_html=True)

# ===================== FUNGSI SCRAPING =====================
def get_soup(url):
    headers = {
        'User-Agent': 'Mozilla/5.0'
    }
    try:
        response = requests.get(url, headers=headers, timeout=10)
        response.raise_for_status()
        return BeautifulSoup(response.text, 'html.parser')
    except:
        return None

def scrape_article_details(url, year_filter):
    soup = get_soup(url)
    if not soup:
        return None

    try:
        title = soup.find('h1').get_text(strip=True)

        date_tag = soup.find('time') or soup.find('span')
        date_text = date_tag.get_text(strip=True) if date_tag else ""

        if year_filter not in date_text:
            return None

        content_div = soup.find('div', itemprop='articleBody')
        content = content_div.get_text(" ", strip=True) if content_div else ""

        return {
            "Judul Berita": title,
            "Tanggal": date_text,
            "Isi Berita": content,
            "Link Sumber": url
        }
    except:
        return None

# ===================== MAIN UI =====================
st.markdown("<div class='main-title'>📰 Antara News Sumbar Scraper</div>", unsafe_allow_html=True)
st.markdown("<div class='subtitle'>Aplikasi pengambilan berita Antara Sumbar berdasarkan kata kunci dan tahun</div>", unsafe_allow_html=True)

with st.sidebar:
    st.header("⚙️ Pengaturan Parameter")
    keyword = st.text_input("Kata Kunci", value="Contoh: Kota Solok")
    tahun = st.text_input("Tahun", value="Contoh: 2026")
    max_pages = st.number_input("Jumlah Halaman", min_value=1, max_value=1000, value=1)
    start_button = st.button("🚀 Mulai Scrapping")

# ===================== PROCESS =====================
if start_button and keyword and tahun:
    base_url = "https://sumbar.antaranews.com"
    search_query = quote_plus(keyword)
    results = []

    progress = st.progress(0)
    status = st.empty()

    for page in range(1, max_pages + 1):
        status.info(f"🔍 Memindai halaman {page}...")
        search_url = f"{base_url}/search?q={search_query}&page={page}"
        soup = get_soup(search_url)

        if not soup:
            break

        articles = soup.find_all('article')
        if not articles:
            break

        for art in articles:
            a = art.find('a', href=True)
            if not a:
                continue
            link = a['href']
            if not link.startswith('http'):
                link = base_url + link

            detail = scrape_article_details(link, tahun)
            if detail:
                results.append(detail)

        progress.progress(page / max_pages)
        time.sleep(0.4)

    status.success("✅ Proses selesai")

    if results:
        df = pd.DataFrame(results)
        st.success(f"📊 Berhasil mengambil {len(df)} berita")
        st.dataframe(df, use_container_width=True)

        csv = df.to_csv(index=False).encode("utf-8")
        st.download_button(
            "📥 Download CSV",
            csv,
            file_name=f"berita_{keyword}_{tahun}.csv",
            mime="text/csv"
        )
    else:
        st.warning("⚠️ Tidak ada berita ditemukan")

# ===================== FOOTER =====================
st.markdown("""
<div class="footer">
© BPS Kota Solok 1372 - 2026
</div>
""", unsafe_allow_html=True)
