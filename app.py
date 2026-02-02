import streamlit as st
import requests
from bs4 import BeautifulSoup
import pandas as pd
import time
from urllib.parse import quote_plus
import io

# ===================== CONFIG =====================
st.set_page_config(
    page_title="Data NewsScraper - BPS1372",
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

/* Logo & Title Header */
.header-container {
    display: flex;
    align-items: center;
    gap: 20px;
    margin-bottom: 10px;
}
.logo-img {
    width: 80px;
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

/* Sidebar Logo */
.sidebar-logo {
    display: block;
    margin-left: auto;
    margin-right: auto;
    width: 150px;
    margin-bottom: 20px;
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
    width: 100%;
}
.stButton > button:hover {
    background: linear-gradient(90deg, #1e40af, #1e3a8a);
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
    z-index: 100;
}
</style>
""", unsafe_allow_html=True)

# URL Logo
LOGO_URL = "https://bps1372.github.io/ARUNA/assest/9.png"

# ===================== FUNGSI SCRAPING =====================
def get_soup(url):
    headers = {'User-Agent': 'Mozilla/5.0'}
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

# ===================== SIDEBAR =====================
with st.sidebar:
    st.header("⚙️ Pengaturan")
    keyword = st.text_input("Keyword", placeholder="Contoh: Kota Solok")
    tahun = st.text_input("Tahun", placeholder="Contoh: 2026")
    max_pages = st.number_input("Jumlah Halaman (default 100)", min_value=1, max_value=1000, value= 20)
    start_button = st.button("🚀 Mulai Scrapping")
    st.markdown("---")
    st.info("Gunakan keyword spesifik untuk hasil yang lebih akurat.")

# ===================== MAIN UI =====================
# Header dengan Logo dan Judul
st.markdown(f"""
    <div class="header-container">
        <img src="{LOGO_URL}" class="logo-img">
        <div class="main-title">Data NewsScraper - BPS1372</div>
    </div>
""", unsafe_allow_html=True)

st.markdown("""
<div class='subtitle'>
Aplikasi data scrapping berita pada situs berita ANTARA Sumbar (https://sumbar.antaranews.com/) berdasarkan keyword dan tahun. <br> <br>
Penggunaan data ini juga sangat bisa digunakan salah satunya dalam rangka pemenuhan Fenomena PDRB Triwulanan.
</div>
""", unsafe_allow_html=True)

# ===================== PROCESS =====================
if start_button:
    if not keyword or not tahun:
        st.warning("⚠️ Mohon isi keyword dan tahun terlebih dahulu.")
    else:
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
                if not a: continue
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

            buffer = io.BytesIO()
            with pd.ExcelWriter(buffer, engine='openpyxl') as writer:
                df.to_excel(writer, index=False, sheet_name='Data Berita')
            
            st.download_button(
                label="📥 Download Excel (.xlsx)",
                data=buffer.getvalue(),
                file_name=f"berita_{keyword}_{tahun}.xlsx",
                mime="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet"
            )
        else:
            st.warning("⚠️ Tidak ada berita ditemukan untuk parameter tersebut.")

# ===================== FOOTER =====================
st.markdown("""
<div class="footer">
© BPS Kota Solok - 2026
</div>
""", unsafe_allow_html=True)
