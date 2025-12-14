import requests
import json
import os
import time
import re

# Load Config
CONFIG_PATH = "../config.json"
with open(CONFIG_PATH, 'r', encoding='utf-8') as f:
    config = json.load(f)

# VOICEVOX Settings
BASE_URL = config["audio"]["voicevox_url"]
AUDIO_DIR = config["paths"]["audio_dir"]

# Character to Speaker ID Mapping
SPEAKER_MAP = config["audio"]["speakers"]

def normalize_text(text):
    """
    Normalizes text for VOICEVOX pronunciation.
    Corrects common misreadings, acronyms, and English terms.
    """
    # 1. Acronyms / English
    replacements = {
        r"G7": "ジーセブン",
        r"APEC": "エイペック",
        r"Switch": "スイッチ",
        r"SWITCH": "スイッチ",
        r"PB": "ピービー",
        r"GDP": "ジーディーピー",
        r"FRB": "エフアールビー",
        r"NASDAQ": "ナスダック",
        r"Amazon": "アマゾン",
        r"Apple": "アップル",
        r"Canon": "キヤノン",
        r"J15": "ジェイジュウゴ",
        r"F15": "エフジュウゴ",
    }
    
    # 2. Kanjis / Vocabulary
    vocab_replacements = {
        r"美味": "おい", # 美味しい -> おいしい
        r"本日": "ほんじつ",
        r"明日": "あす",
        r"御社": "おんしゃ",
        r"貴社": "きしゃ",
        r"早苗": "さなえ",
        r"高市": "たかいち",
        r"石破": "いしば",
        r"総理": "そうり",
        r"習近平": "しゅうきんぺい",
    }
    
    # 0. Clean Number Spacing & Commas (Crucial for Voicevox Counters)
    # Fix "12,500" -> "12500"
    text = re.sub(r'(\d{1,3}),(\d{3})', r'\1\2', text) # Simple 1,000 pattern
    text = re.sub(r'(\d+),(\d+)', r'\1\2', text)       # Catch all digit,digit

    # Fix "2025 年" -> "2025年" (Remove space between Number and Non-Space)
    text = re.sub(r'(\d+)\s+([^\d\s])', r'\1\2', text)
    
    # 3. Specific patterns
    # Fix "第2章" -> "だいにしょう" (User QA Request)
    text = re.sub(r"第([0-9０-９]+)章", r"だい\1しょう", text)
  
    processed_text = text
    
    # 4. Apply replacements (Acronyms & Vocab FIRST)
    # ...
    for pattern, reading in replacements.items():
        processed_text = re.sub(pattern, reading, processed_text, flags=re.IGNORECASE)
        
    for pattern, reading in vocab_replacements.items():
        processed_text = re.sub(pattern, reading, processed_text)

    # 5. Number Conversion (REMOVED)
    # Voicevox handles numbers natively now that spaces/commas are gone.
        
    return processed_text

def convert_numbers_to_japanese(text):
    """
    Finds numeric sequences in text and converts them to Japanese reading.
    e.g. "12万人" -> "じゅうに万人" -> Voicevox reads "じゅうにまんにん" corretly.
    Simple implementation for integers.
    """
    def num2ja(num_str):
        try:
            n = int(num_str)
        except:
            return num_str
            
        if n == 0: return "ゼロ"
        
        digits = {0:"", 1:"いち", 2:"に", 3:"さん", 4:"よん", 5:"ご", 6:"ろく", 7:"なな", 8:"はち", 9:"きゅう"}
        units = {10:"じゅう", 100:"ひゃく", 1000:"せん", 10000:"まん", 100000000:"おく"}
        
        # Simple recursive conversion for up to Oku
        if n >= 100000000:
            upper = n // 100000000
            lower = n % 100000000
            return num2ja(str(upper)) + "おく" + (num2ja(str(lower)) if lower > 0 else "")
        elif n >= 10000:
            upper = n // 10000
            lower = n % 10000
            return num2ja(str(upper)) + "まん" + (num2ja(str(lower)) if lower > 0 else "")
            
        # Below Man (10000)
        s = ""
        # Sen (1000)
        thou = (n % 10000) // 1000
        if thou == 1: s += "せん"
        elif thou > 1: s += digits[thou] + "せん"
        
        # Hyaku (100)
        hund = (n % 1000) // 100
        if hund == 1: s += "ひゃく"
        elif hund > 1: s += digits[hund] + "ひゃく"
        
        # Jyu (10)
        ten = (n % 100) // 10
        if ten == 1: s += "じゅう"
        elif ten > 1: s += digits[ten] + "じゅう"
        
        # One (1)
        one = n % 10
        if one > 0:
            s += digits[one]
            
        # Fixes for special readings
        s = s.replace("さんひゃく", "さんびゃく")
        s = s.replace("ろくひゃく", "ろっぴゃく")
        s = s.replace("はちひゃく", "はっぴゃく")
        s = s.replace("さんせん", "さんぜん")
        s = s.replace("はちせん", "はっせん")
        
        return s

    # Regex to find numbers
    # Support commas (e.g. 12,500 -> 12500)
    # Match digits followed optionally by (,digits) groups
    return re.sub(r'\d+(?:,\d+)*', lambda m: num2ja(m.group(0).replace(',', '')), text)


def check_voicevox_connection():
    try:
        response = requests.get(f"{BASE_URL}/version", timeout=1)
        if response.status_code == 200:
            return True
    except requests.exceptions.ConnectionError:
        return False
    return False

def generate_audio_file(text, character_name, index, output_dir=None):
    """
    Generates an audio file for the given text and character.
    Returns the path to the saved wav file.
    """
    # Use provided dir or fallback to config
    target_dir = output_dir if output_dir else AUDIO_DIR
    
    if not os.path.exists(target_dir):
        os.makedirs(target_dir)

    speaker_id = SPEAKER_MAP.get(character_name, SPEAKER_MAP["default"])
    file_path = os.path.join(target_dir, f"{index:04d}_{character_name}.wav")

    # 1. Audio Query
    try:
        # Phase 7: Pronunciation Fixes / Text Normalization
        normalized_text = normalize_text(text)
        print(f"  [Auto-Correcting] '{text}' -> '{normalized_text}'")
        
        query_payload = {"text": normalized_text, "speaker": speaker_id}
        r_query = requests.post(f"{BASE_URL}/audio_query", params=query_payload)
        r_query.raise_for_status()
        query_data = r_query.json()
    except Exception as e:
        print(f"Error querying VOICEVOX: {e}")
        return None

    # 2. Synthesis
    try:
        # Speed adjustment (Phase 7/9: Use Config)
        query_data['speedScale'] = config["audio"]["global_speed_scale"]
        
        r_synth = requests.post(f"{BASE_URL}/synthesis", params={"speaker": speaker_id}, json=query_data)
        r_synth.raise_for_status()
    except Exception as e:
         print(f"Error synthesizing audio: {e}")
         return None

    # 3. Save
    with open(file_path, "wb") as f:
        f.write(r_synth.content)

    return file_path
