import requests
from bs4 import BeautifulSoup
import sys
import time
import re
from urllib.parse import urljoin

def fetch_yahoojp_article(url):
    """
    Fetches the main body text from a Yahoo News article, handling pagination.
    """
    
    # Headers to mimic a browser to avoid some basic bot detection
    headers = {
        "User-Agent": "Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/91.0.4472.114 Safari/537.36"
    }

    aggregated_text = ""
    current_url = url
    page_count = 1
    
    print(f"Fetching: {current_url}")

    while current_url:
        try:
            response = requests.get(current_url, headers=headers, timeout=10)
            response.raise_for_status()
            
            soup = BeautifulSoup(response.content, 'html.parser')
            
            # Extract Title (only from first page usually, but safe to grab)
            if page_count == 1:
                title_tag = soup.find('h1')
                if title_tag:
                    print(f"Title: {title_tag.get_text(strip=True)}")
                    print("-" * 40)

            # Extract Body Text
            # Yahoo News body is often in a specific container.
            # Strategy: Yahoo JP News structure often uses specific class names or simply <p> tags inside a main wrapper.
            # Common selectors for Yahoo News Japan article body
            article_body = (
                soup.select_one('.article_body') or 
                soup.select_one('#uamods-article') or 
                soup.select_one('.sc-dJjYzT') or # Dynamic class fallback (often changes)
                soup.find('div', {'class': lambda x: x and ('articleBody' in x or 'highLightSearchTarget' in x)})
            )

            if article_body:
                # Get all paragraphs
                paragraphs = article_body.find_all('p')
                page_text = "\n".join([p.get_text(strip=True) for p in paragraphs])
                aggregated_text += page_text + "\n\n"
            else:
                # Fallback: simple p extraction if main body not found (risky but better than nothing)
                # But constrained to a likely container if possible
                main_col = soup.select_one('main') or soup.find('div', {'id': 'main'})
                if main_col:
                     paragraphs = main_col.find_all('p')
                     page_text = "\n".join([p.get_text(strip=True) for p in paragraphs])
                     aggregated_text += page_text + "\n\n"
                else:
                    print(f"Warning: Could not isolate article body on page {page_count}.")
            
            # Check for "Next Page" (次へ)
            next_link = None
            
            # 1. Specific class search (Yahoo often uses specific classes)
            next_btn = soup.select_one('li.pagination_item-next a') or soup.select_one('.pagination_item-next a')
            
            # 2. Yahoo specific attribute search (Robust against dynamic classes)
            if not next_btn:
                next_btn = soup.find('a', attrs={'data-cl-params': re.compile(r'link:next')})

            # 3. Text search within likely containers
            if not next_btn:
                pagination_container = soup.select_one('.pagination') or soup.select_one('ul[class*="pagination"]') or soup.select_one('.article_pager')
                if pagination_container:
                     for a in pagination_container.find_all('a'):
                        if "次へ" in a.get_text():
                            next_btn = a
                            break

            # 4. Global text search (Fallback)
            if not next_btn:
                 # Search all links for text "次へ" or "次ページ"
                 for a in soup.find_all('a'):
                     text = a.get_text(strip=True)
                     if "次へ" in text or "次のページ" in text:
                         next_btn = a
                         break
            
            if next_btn:
                next_link = next_btn.get('href')
                # Resolve relative URL
                next_link = urljoin(current_url, next_link)
                     
                print(f"Found next page: {next_link}")
                current_url = next_link
                page_count += 1
                time.sleep(1) # Be polite
            else:
                print("End of article reached.")
                current_url = None

        except Exception as e:
            print(f"Error fetching {current_url}: {e}")
            break
            
    return aggregated_text

if __name__ == "__main__":
    if len(sys.argv) < 2:
        print("Usage: python3 fetch_news.py <url>")
        sys.exit(1)
        
    target_url = sys.argv[1]
    full_text = fetch_yahoojp_article(target_url)
    
    print("\n" + "="*20 + " RESULT " + "="*20 + "\n")
    print(full_text)
