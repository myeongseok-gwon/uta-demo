import pandas as pd
import requests
from bs4 import BeautifulSoup
from googlesearch import search  # pip install googlesearch-python
import time
import csv

def fetch_page_text(url):
    """URL에 접근하여 페이지의 텍스트를 추출하고, 콤마를 제거."""
    try:
        headers = {
            "User-Agent": (
                "Mozilla/5.0 (Windows NT 10.0; Win64; x64) "
                "AppleWebKit/537.36 (KHTML, like Gecko) "
                "Chrome/90.0.4430.93 Safari/537.36"
            )
        }
        response = requests.get(url, headers=headers, timeout=10)
        if response.status_code == 200:
            soup = BeautifulSoup(response.text, 'html.parser')
            # 스크립트, 스타일, noscript 태그 제거
            for tag in soup(["script", "style", "noscript"]):
                tag.decompose()
            text = soup.get_text(separator=" ", strip=True)
            # 크롤링한 텍스트 내 콤마 제거
            return text.replace(",", "")
    except Exception as e:
        print(f"Error fetching {url}: {e}")
    return ""

def get_wikipedia_content(query):
    """구글 검색 결과 중 wikipedia.org 도메인이 포함된 첫번째 페이지(영문)의 내용을 반환."""
    wiki_text = ""
    try:
        # 영어 페이지 검색 (lang="en")
        for url in search(query, num_results=5, lang="en"):
            if "wikipedia.org" in url:
                print(f"  [WIKI] Found: {url}")
                wiki_text = fetch_page_text(url)
                break
    except Exception as e:
        print(f"Error during wikipedia search: {e}")
    return wiki_text

def get_latest_updates(query):
    """구글 검색 결과 중 위키피디아 외 첫 3개의 결과를 가져와 콘텐츠를 반환."""
    updates = []
    try:
        # 영어 결과에서 검색 (lang="en")
        for url in search(query, num_results=10, lang="en"):
            if "wikipedia.org" in url:
                continue  # 위키피디아 페이지는 제외
            print(f"  [UPDATE] Found: {url}")
            text = fetch_page_text(url)
            if text:
                updates.append(text)
            if len(updates) >= 3:
                break
    except Exception as e:
        print(f"Error during updates search: {e}")
    return "\n\n".join(updates)

def main():
    # influencer.csv 파일 읽기 (name 컬럼 포함)
    df = pd.read_csv("top_influencer_corpus.csv")
    results = []

    for idx, row in df.iterrows():
        name = row["influencer"]
        print(f"Processing '{name}'...")
        
        # 위키피디아 페이지 검색 및 크롤링 (영어)
        wiki_query = f"{name} wikipedia"
        wiki_content = get_wikipedia_content(wiki_query)
        
        # 최신 소식 검색 및 크롤링 (영어, 'latest' 키워드 사용)
        updates_query = f"{name}"
        updates_content = get_latest_updates(updates_query)
        
        results.append({
            "name": name.replace(",", ""),  # 이름에 콤마 제거
            "wikipedia_corpus": wiki_content,
            "updates_corpus": updates_content
        })
        
        # 구글에 과도한 요청을 방지하기 위해 sleep (필요에 따라 조정)
        time.sleep(5)

    # CSV 파일 저장: csv 모듈 사용 (콤마가 이미 제거된 상태)
    with open("influencer_corpus.csv", mode="w", newline="", encoding="utf-8-sig") as f:
        fieldnames = ["name", "wikipedia_corpus", "updates_corpus"]
        writer = csv.DictWriter(f, fieldnames=fieldnames, quoting=csv.QUOTE_ALL, escapechar='\\')
        writer.writeheader()
        for row in results:
            writer.writerow(row)
    
    print("저장 완료: influencer_corpus.csv")

if __name__ == "__main__":
    main()