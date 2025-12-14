import os
import re
import sys
import time
import requests
import hashlib
from urllib.parse import urlparse

# Try importing duckduckgo_search
try:
    from duckduckgo_search import DDGS
except ImportError:
    print("Error: duckduckgo_search library not found.")
    print("Please run: pip3 install duckduckgo-search")
    sys.exit(1)

INPUT_SCRIPT = "../../youtube_script_long.md"
IMAGE_DIR = "../assets/images"

# Ban list for domains (Japanese media, rights holders)
BAN_DOMAINS = [
    "bunshun.jp", "shueisha.co.jp", "kodansha.co.jp", 
    "nhk.or.jp", "tbs.co.jp", "fujitv.co.jp", "tv-asahi.co.jp", "ntv.co.jp",
    "nikkei.com", "asahi.com", "yomiuri.co.jp", "mainichi.jp",
    "yahoo.co.jp", "gettyimages", "istockphoto", "shutterstock", "adobe",
    "dailyshincho.jp", "friday.kodansha.co.jp", "gendai.media", "post.tv-asahi.co.jp",
    "jprime.jp", "cyzo.com", "news-postseven.com", "j-cast.com", "sankei.com", "shujoprime.jp"
]

def is_safe_url(url):
    """Checks if the URL domain is in the ban list."""
    try:
        domain = urlparse(url).netloc
        for ban in BAN_DOMAINS:
            if ban in domain:
                return False
        return True
    except:
        return False

def download_image(url, keyword, output_dir=IMAGE_DIR):
    """Downloads an image and saves it with a hash name."""
    try:
        # Generate hash for filename
        url_hash = hashlib.md5(url.encode()).hexdigest()
        ext = os.path.splitext(url)[1]
        if not ext or len(ext) > 5: ext = ".jpg"
        
        # Safe Keyword
        safe_keyword = re.sub(r'[\\/*?:"<>|]', "", keyword).replace(" ", "_")
        filename = f"{safe_keyword}.jpg" 
        filepath = os.path.join(output_dir, filename)
        
        if os.path.exists(filepath):
            print(f"Image already exists for {keyword}")
            return filepath

        print(f"Downloading {url} for {keyword}...")
        response = requests.get(url, timeout=10)
        response.raise_for_status()
        
        with open(filepath, 'wb') as f:
            f.write(response.content)
            
        print(f"Saved to {filepath}")
        return filepath
    except Exception as e:
        print(f"Failed to download {url}: {e}")
        return None

def fetch_images_for_script(script_path=None, image_dir=None):
    target_script = script_path if script_path else INPUT_SCRIPT
    target_dir = image_dir if image_dir else IMAGE_DIR

    if not os.path.exists(target_dir):
        os.makedirs(target_dir)

    with open(target_script, 'r', encoding='utf-8') as f:
        content = f.read()

    # Parse script to find [IMG] tags assigned ONLY to Aoyama Ryusei
    matches = []
    
    lines = content.split('\n')
    pending_keywords = []

    for line in lines:
        line = line.strip()
        if not line: continue
        
        # 1. Check for IMG tag
        img_match = re.match(r'\[IMG:\s*(.*?)\]', line)
        if img_match:
            keyword = img_match.group(1).strip()
            if keyword:
                pending_keywords.append(keyword)
            continue
            
        # 2. Check for Character Line
        if ',' in line and not line.startswith('['):
            try:
                parts = line.split(',', 1)
                char_name = parts[0].strip()
                
                # Normalize name (simple check)
                if "青山" in char_name:
                    # If it's Aoyama, authorize the pending images
                    matches.extend(pending_keywords)
                else:
                    # If it's anyone else, discard the images (Waste prevention)
                    if pending_keywords:
                        print(f"Skipping unused images for {char_name}: {pending_keywords}")
                
                # Reset pending
                pending_keywords = []
            except:
                pass

    # Unique list while preserving order
    matches = list(dict.fromkeys(matches))
    print(f"Found {len(matches)} image requests (Aoyama only).")
    
    # Session Management
    ddgs = DDGS()

    try:
        for keyword in matches:
            keyword = keyword.strip()
            if not keyword: continue
            
            print(f"Searching for: {keyword}")
            
            found_image = False
            # Exponential Backoff Retry Loop
            max_retries = 4
            results = []
            
            for attempt in range(max_retries):
                try:
                    # Add negative keywords to avoid stock/vectors
                    safe_query = f"{keyword} -stock -watermark -vector -drawing -illustration -logo -text -sign -PRIME -週刊"
                    
                    results = ddgs.images(
                        safe_query,
                        region="jp-jp", # Search in Japan context
                        safesearch="off",
                        size="Large", # Prioritize higher quality
                        type_image="photo",
                        layout="Wide",
                        max_results=15
                    )
                    break # Success
                except Exception as e:
                    print(f"Search failed (attempt {attempt+1}): {e}")
                    
                    # SMART REFRESH: Re-init session on error
                    print("Refreshing DDGS session due to error...")
                    try:
                        ddgs = DDGS()
                    except:
                        pass
                        
                    # Exponential Backoff: 5 * (2^attempt)
                    wait_time = 5 * (2 ** attempt)
                    print(f"Waiting {wait_time}s...")
                    time.sleep(wait_time)
            
            if not results:
                # Last ditch effort with fallback size, using fresh session
                print(f"Warning: Could not get results for {keyword} after retries. Refreshing session and trying fallback size...")
                ddgs = DDGS()
                try:
                    results = ddgs.images(
                        keyword, region="jp-jp", safesearch="off", size="Medium", 
                        type_image="photo", layout="Wide", max_results=15
                    )
                except:
                    pass

            if not results:
                print(f"Warning: Really could not find suitable image for {keyword}")
                continue
            
            for res in results:
                image_url = res['image']
                
                # Check domain
                if not is_safe_url(image_url):
                    print(f"Skipping banned domain: {image_url}")
                    continue
                
                # Try downloading
                # Pass target_dir
                path = download_image(image_url, keyword, output_dir=target_dir)
                if path:
                    # Check Resolution
                    try:
                        from PIL import Image
                        with Image.open(path) as img:
                            w, h = img.size
                            if w < 600 or h < 360:
                                print(f"Image too small ({w}x{h}), deleting: {path}")
                                os.remove(path)
                                continue # Try next result
                    except Exception as e:
                       print(f"Error checking image size: {e}")
                       
                    found_image = True
                    break # Stop after 1 successful image per keyword
            
            if not found_image:
                print(f"Warning: Could not find suitable image for {keyword}")

            # Random jitter wait to look human (10-20s)
            import random
            sleep_time = random.uniform(10, 20)
            print(f"Waiting {sleep_time:.1f}s to respect rate limits...")
            time.sleep(sleep_time)
            
    except Exception as e:
        print(f"Critical Error in fetch loop: {e}")

if __name__ == "__main__":
    if len(sys.argv) > 1:
        INPUT_SCRIPT = sys.argv[1]
    fetch_images_for_script()
