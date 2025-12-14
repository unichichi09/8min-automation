import os
import re
import json
import numpy as np
import textwrap
import math
from moviepy import *
from PIL import Image, ImageFont, ImageDraw
import generate_audio

# --- Config Loading ---
CONFIG_PATH = "../config.json"
try:
    with open(CONFIG_PATH, 'r', encoding='utf-8') as f:
        config = json.load(f)
except FileNotFoundError:
    print(f"Error: Config file not found at {CONFIG_PATH}")
    exit(1)

# --- Paths & Constants ---
IMAGE_DIR = config["paths"]["image_dir"] # Default, overridden by args
BG_VIDEO_DIR = config["paths"]["background_video_dir"]
BGM_FILE = config["paths"]["bgm_path"]
EYECATCH_FILE = config["paths"].get("eyecatch_path", "../assets/videos/eyecatch.mp4")
FONT_PATH = config["paths"]["font_path"]

# Video Settings
SCREEN_SIZE = tuple(config["video"]["resolution"])
FPS = config["video"]["fps"]
BGM_VOLUME = config["audio"]["bgm_volume"]

# Subtitle Settings
SUB_CONF = config["video"]["subtitle"]

# Context Image Settings
IMG_CONF = config["video"]["context_image"]

# Character Colors (Vivid & Distinct)
CHARACTER_COLORS = {
    "青山龍星": "white",
    "ずんだもん": "#39c263",   # Zunda Green
    "四国めたん": "#ff3399",   # Metan Pink
    "春日部つむぎ": "#ffcc00", # Tsumugi Yellow
    "雨晴はう": "#66ccff",     # Hau Blue
    "冥鳴ひまり": "#9966ff",   # Himari Purple
    "玄野武宏": "#ff3333",     # Kurono Red
    "麒ヶ島宗麟": "#ff9933",   # Sorin Orange
    "default": "#cccccc"       # Default Grey
}

def normalize_character_name(name):
    """Normalizes character names to standard full names."""
    name = name.strip()
    if "ずんだ" in name: return "ずんだもん"
    if "めたん" in name: return "四国めたん"
    if "つむぎ" in name: return "春日部つむぎ"
    if "青山" in name: return "青山龍星"
    if "宗麟" in name: return "麒ヶ島宗麟"
    return name

# --- Helper Functions ---

def calculate_duration(text):
    """Estimates duration based on text length (fallback)."""
    base_time = 1.0
    char_time = 0.2 
    return base_time + (len(text) * char_time)

def parse_script(filepath):
    """Parses the markdown script to extract segments."""
    if not os.path.exists(filepath):
        print(f"Script file not found: {filepath}")
        return []
        
    with open(filepath, 'r', encoding='utf-8') as f:
        content = f.read()

    match = re.search(r'```(.*?)```', content, re.DOTALL)
    raw_script = match.group(1).strip() if match else content
    
    segments = []
    current_img_keyword = None
    
    lines = raw_script.split('\n')
    for line in lines:
        line = line.strip()
        if not line: continue
        
        # Check for [EYECATCH]
        if "[EYECATCH]" in line:
            segments.append({"type": "eyecatch"})
            continue
            
        # Check for [IMG: keyword] tag
        img_match = re.match(r'\[IMG:\s*(.*?)\]', line)
        if img_match:
            current_img_keyword = img_match.group(1).strip()
            continue
            
        # Handle "Character, Text" format
        if ',' not in line: continue
        if line.startswith('['): continue 
        
        try:
            parts = line.split(',', 1)
            char_name = normalize_character_name(parts[0].strip()) # Normalize here
            raw_text = parts[1].strip()
            
            # --- SAFETY NET: Auto-convert （ ） to { } for readings ---
            # If the user/LLM accidentally used （furigana）, convert it to {furigana}
            # Catch "Text（Reading）" pattern
            raw_text = re.sub(r'（(.*?)）', r'{\1}', raw_text)
            
            # Check for Audio Reading specified in {Brackets} 
            # Logic: 
            # Display: Remove {Content}.
            # Audio: Use {Content} effectively. 
            
            # 1. Display Text: Remove all {Reading} tags
            display_text = re.sub(r'\{(.*?)\}', '', raw_text).strip()
            
            # 2. Audio Text:
            # We want to replace "Target{Reading}" with "Reading".
            # Try to match preceding Kanji/Alphanum to replace it.
            # Pattern: ([Kanji/Alphanum]+){(Reading)} -> \2
            # Note: This is a heuristic. 
            # Case A: 2024{reading} -> reading
            # Case B: Kanji{reading} -> reading
            # Case C: English Words {reading} -> reading
            
            audio_text = raw_text
            # Replace English/Numbers+Space+{Reading} -> Reading
            audio_text = re.sub(r'([a-zA-Z0-9\s\.\,\!]+)\{(.*?)\}', r'\2', audio_text)
            # Replace Kanji+{Reading} -> Reading (Greedy match on Kanji)
            audio_text = re.sub(r'([一-龠]+)\{(.*?)\}', r'\2', audio_text)
            
            # Clean up any remaining braces that didn't match the prefix patterns (Just unwrap them)
            # e.g. ひらがな{reading} -> ひらがなreading (Voicevox handles this okay-ish)
            audio_text = re.sub(r'\{(.*?)\}', r'\1', audio_text)
            
            segments.append({
                "type": "dialogue",
                "character": char_name,
                "text": display_text,
                "audio_text": audio_text, 
                "duration": calculate_duration(audio_text), 
                "image_keyword": current_img_keyword
            })
        except ValueError:
            continue
            
    return segments

def get_base_custom_clip(duration, color=(30, 30, 30)):
    return ColorClip(size=SCREEN_SIZE, color=color, duration=duration)

def get_image_clip(keyword, duration, custom_image_dir=None):
    """Searches for an image file matching the keyword hash or name."""
    search_dir = custom_image_dir if custom_image_dir else IMAGE_DIR
    
    # 1. Try safe filename
    safe_key = re.sub(r'[\\/*?:"<>|]', "", keyword).replace(" ", "_") + ".jpg"
    path = os.path.join(search_dir, safe_key)
    
    if os.path.exists(path):
        try:
            # Crop to fill center
            img_clip = ImageClip(path).with_duration(duration)
            
            # Smart Scale/Crop
            img_w, img_h = img_clip.size
            screen_w, screen_h = SCREEN_SIZE
            
            # Scale to cover
            ratio_w = screen_w / img_w
            ratio_h = screen_h / img_h
            scale = max(ratio_w, ratio_h)
            
            img_clip = img_clip.resized(new_size=scale)
            img_clip = img_clip.with_position("center")
            
            # Settings
            target_w = int(screen_w * IMG_CONF["width_ratio"])
            target_h = int(screen_h * IMG_CONF["height_ratio"])
            pos_x = IMG_CONF["position_x"]
            pos_y = IMG_CONF["position_y"]
            
            # Add Border/Stroke? 
            # Simplified: Just resize and place
            final = img_clip.resized(width=target_w) # Force width
            final = final.with_position((pos_x, pos_y))
            
            # Add Stroke (Composite with larger white rect behind? or just simple)
            # For phase 6 visual polish, we want a stroke.
            # Let's add a white margin effect if possible, but keep it simple for stability.
            
            return final
        except Exception as e:
            print(f"Error loading image {path}: {e}")
            return None
    return None

def create_text_image(text, size=SCREEN_SIZE, color='white'):
    """Creates a text overlay image for Narrator (Aoyama) with dynamic scaling."""
    img = Image.new('RGBA', size, (0, 0, 0, 0))
    
    # Initial Font Config
    base_fontsize = SUB_CONF["font_size"]
    fontsize = base_fontsize
    min_fontsize = 50
    
    # Safe Area
    max_height = 600
    
    # Iterative Sizing
    while fontsize >= min_fontsize:
        try:
            font = ImageFont.truetype(FONT_PATH, fontsize)
        except:
            font = ImageFont.load_default()

        # Padding / Width
        padding_x = 50
        max_text_width = size[0] - (padding_x * 2)
        avg_char_width = fontsize * 1.0 
        chars_per_line = int(max_text_width / avg_char_width)
        if chars_per_line < 1: chars_per_line = 1
        
        # Basic Wrap
        raw_lines = textwrap.wrap(text, width=chars_per_line)
        
        # Kinsoku (Bracket Fix) logic
        refined_lines = []
        if raw_lines:
            refined_lines.append(raw_lines[0])
            for i in range(1, len(raw_lines)):
                line = raw_lines[i]
                prev = refined_lines[-1]
                if line.startswith("」") or line.startswith("。") or line.startswith("、"):
                     refined_lines[-1] = prev + line[0]
                     refined_lines.append(line[1:]) 
                elif prev.endswith("「"):
                     refined_lines[-1] = prev[:-1]
                     refined_lines.append("「" + line)
                else:
                     refined_lines.append(line)
            refined_lines = [l for l in refined_lines if l]
            lines = refined_lines
        else:
            lines = []

        # Calculate Height
        line_height = fontsize * 1.5
        total_text_height = len(lines) * line_height
        
        if total_text_height <= max_height:
            break
            
        fontsize -= 5
    
    # Draw Background Bar ("Zabuton")
    bottom_margin = SUB_CONF["bottom_margin"]
    start_y = size[1] - bottom_margin - total_text_height
    
    bar_height = total_text_height + 60 
    bar_y1 = start_y - 30
    bar_y2 = bar_y1 + bar_height
    
    overlay = Image.new('RGBA', size, (0, 0, 0, 0))
    draw_overlay = ImageDraw.Draw(overlay)
    
    bg_col = tuple(SUB_CONF["background_color"])
    draw_overlay.rectangle([0, bar_y1, size[0], bar_y2], fill=bg_col)
    img = Image.alpha_composite(img, overlay)
    draw = ImageDraw.Draw(img)

    # Styling
    stroke_color = tuple(SUB_CONF["stroke_color"]) if isinstance(SUB_CONF["stroke_color"], list) else SUB_CONF["stroke_color"]
    stroke_width = SUB_CONF["stroke_width"]
    
    current_y = start_y
    for line in lines:
        # Centering
        left, top, right, bottom = draw.textbbox((0, 0), line, font=font)
        text_w = right - left
        x = (size[0] - text_w) / 2
        
        if stroke_width > 0:
            draw.text((x, current_y), line, font=font, fill=stroke_color, stroke_width=stroke_width, stroke_fill=stroke_color)
        
        draw.text((x, current_y), line, font=font, fill=color)
        current_y += line_height
        
    return np.array(img)

def apply_kinsoku(text, chars_per_line):
    """Applies Japanese kinsoku shori (line breaking rules) robustly."""
    # First, use textwrap to get rough lines
    raw_lines = textwrap.wrap(text, width=chars_per_line)
    if not raw_lines: return []
    
    refined_lines = [raw_lines[0]]
    
    # Prohibited at start of line
    kinsoku_start = "」』）)}].,:;!?。、"
    # Prohibited at end of line
    kinsoku_end = "「『（({["
    
    for i in range(1, len(raw_lines)):
        current_line = raw_lines[i]
        prev_line = refined_lines[-1]
        
        # Check 1: Current line starts with prohibited char?
        # If so, append that char to previous line
        while current_line and current_line[0] in kinsoku_start:
             refined_lines[-1] += current_line[0]
             current_line = current_line[1:]
        
        # Check 2: Previous line ends with prohibited char?
        # If so, move that char to current line (start)
        # Note: We need to be careful not to infinite loop or empty the prev line too much
        if refined_lines[-1] and refined_lines[-1][-1] in kinsoku_end:
             char_to_move = refined_lines[-1][-1]
             refined_lines[-1] = refined_lines[-1][:-1]
             current_line = char_to_move + current_line
             
        if current_line:
             refined_lines.append(current_line)
             
    return refined_lines

def create_panel_image(text, character_name, char_color_hex, size=SCREEN_SIZE):
    """Creates a panel style overlay with DYNAMIC font sizing to prevent overflow."""
    img = Image.new('RGBA', size, (0, 0, 0, 0))
    # We will draw the panel and text on every iteration or just once? 
    # Better to calculate font size first, then draw.
    
    # 1. Panel Box Settings
    panel_w = 1700  # Significantly Wider
    panel_h = 650   # Significantly Taller
    panel_x = (size[0] - panel_w) // 2
    panel_y = (size[1] - panel_h) // 2
    
    # Border Color
    try:
        h = char_color_hex.lstrip('#')
        border_rgb = tuple(int(h[i:i+2], 16) for i in (0, 2, 4))
    except:
        # If color name "white", handle it
        if char_color_hex.lower() == "white":
             border_rgb = (255, 255, 255)
        else:
             border_rgb = (255, 105, 180) # Default Pink

    # Custom Logic for Aoyama (Dark Panel, White Text, BOTTOM position)
    if character_name == "青山龍星":
        panel_bg_color = (30, 30, 30, 230) # Dark semitransparent
        text_color = "white"
        
        # Position at BOTTOM to show images
        # Similar to original create_text_image logic
        bottom_margin = 50 # Hardcoded or readable from config if passed
        panel_y = size[1] - panel_h - bottom_margin
        
    else:
        # Others: Keep Center (Existing behavior)
        panel_bg_color = (255, 255, 255, 255) # White Opaque
        text_color = "black"
        # Center Y
        panel_y = (size[1] - panel_h) // 2


    # 2. Dynamic Font Sizing Loop
    font_size = 90 # Start slightly larger, reduce down
    min_font_size = 40
    
    found_good_size = False
    final_lines = []
    final_font = None
    
    while font_size >= min_font_size:
        try:
            font = ImageFont.truetype(FONT_PATH, font_size)
        except:
            font = ImageFont.load_default()
            
        # Calc Chars per line (conservative padding)
        # Internal width is panel_w - 60px padding
        safe_width = panel_w - 60
        avg_char_w = font_size # Rough estimate
        chars_per_line = int(safe_width / avg_char_w)
        
        # Apply Kinsoku (which might extend lines)
        lines = apply_kinsoku(text, chars_per_line)
        
        # Verify Width & Height
        max_line_w = 0
        draw_temp = ImageDraw.Draw(img)
        for line in lines:
             left, top, right, bottom = draw_temp.textbbox((0, 0), line, font=font)
             max_line_w = max(max_line_w, right - left)
             
        line_h = font_size * 1.5
        total_text_h = len(lines) * line_h
        
        # Check Fit
        if max_line_w <= safe_width and total_text_h <= (panel_h - 40):
            found_good_size = True
            final_lines = lines
            final_font = font
            break
            
        font_size -= 5
        
    if not found_good_size:
        # Fallback if text is absurdly long
        print(f"Warning: Text too long for panel: {text[:20]}...")
        final_lines = lines
        final_font = font # Use smallest
        
    # 3. Draw Final
    img_final = Image.new('RGBA', size, (0, 0, 0, 0))
    draw = ImageDraw.Draw(img_final)
    
    # RE-CALCULATE Height/Position for Aoyama (Dynamic Fit)
    # The loop ensured it FITS in max panel_h (650), but we don't want to USE all 650 if text is short.
    if character_name == "青山龍星":
        line_h_final = final_font.size * 1.5
        total_text_h_final = len(final_lines) * line_h_final
        # Add padding (top/bottom)
        dynamic_h = int(total_text_h_final + 80) 
        panel_h = max(200, dynamic_h) # Minimum 200px
        
        # Re-calc Y for bottom alignment
        bottom_margin = 50
        panel_y = size[1] - panel_h - bottom_margin
        
    # Draw Panel
    border_width = 15
    draw.rectangle([panel_x, panel_y, panel_x+panel_w, panel_y+panel_h], fill=panel_bg_color, outline=border_rgb, width=border_width)
    
    # Draw Text
    line_h = final_font.size * 1.5
    total_text_h = len(final_lines) * line_h
    start_text_y = panel_y + (panel_h - total_text_h) / 2
    
    curr_y = start_text_y
    for line in final_lines:
        left, top, right, bottom = draw.textbbox((0, 0), line, font=final_font)
        w = right - left
        x = panel_x + (panel_w - w) / 2
        draw.text((x, curr_y), line, font=final_font, fill=text_color)
        curr_y += line_h
        
    return np.array(img_final)

def generate_video(script_path=None, output_path=None, image_dir=None, audio_dir=None):
    # Use args or defaults
    target_script = script_path if script_path else SCRIPT_PATH
    target_output = output_path if output_path else OUTPUT_VIDEO
    target_image_dir = image_dir if image_dir else IMAGE_DIR
    target_audio_dir = audio_dir if audio_dir else config["paths"]["audio_dir"]

    # 1. Parse Script
    segments = parse_script(target_script)
    print(f"Script parsed. {len(segments)} segments found.")
    
    clips = []
    
    # Pre-load Eyecatch
    eyecatch_clip = None
    if os.path.exists(EYECATCH_FILE):
        try:
             eyecatch_clip = VideoFileClip(EYECATCH_FILE)
             print("Eyecatch loaded.")
        except Exception as e:
             print(f"Eyecatch load failed: {e}")

    # Use Voicevox check
    use_voicevox = config["audio"]["use_voicevox"]
    
    # Background Video Loop (Simple)
    # Just use 'news_bg.mp4' from BG_VIDEO_DIR or similar if exists, else ColorClip
    bg_path = os.path.join(BG_VIDEO_DIR, "news_bg.mp4")
    if not os.path.exists(bg_path):
         # Search for any mp4
         bgs = [f for f in os.listdir(BG_VIDEO_DIR) if f.endswith(".mp4")]
         if bgs: bg_path = os.path.join(BG_VIDEO_DIR, bgs[0])
    
    base_bg_clip = None
    if os.path.exists(bg_path):
        base_bg_clip = VideoFileClip(bg_path)
    
    # Loop Segments
    last_valid_aoyama_image = None
    
    for i, seg in enumerate(segments):
        # Handle Eyecatch
        if seg.get("type") == "eyecatch":
            if eyecatch_clip:
                clips.append(eyecatch_clip)
                print("Inserted Eyecatch.")
            continue

        # Audio
        audio_clip = None
        duration = 0
        
        # Determine Audio Text
        text_for_audio = seg.get('audio_text', seg['text'])
        
        if use_voicevox:
            wav_path = generate_audio.generate_audio_file(text_for_audio, seg['character'], i, output_dir=target_audio_dir)
            if wav_path and os.path.exists(wav_path):
                audio_clip = AudioFileClip(wav_path)
                duration = audio_clip.duration
            else:
                duration = calculate_duration(text_for_audio)
        else:
            duration = calculate_duration(text_for_audio)
            
        if duration < 1.0: duration = 1.0

        # Audio Padding Fix (Phase 22 - Correct Implementation)
        # Extend the base duration so ALL visual elements (BG, Image, Text) cover the full time
        duration += 0.2
        
        # Background
        bg_segment = None
        if base_bg_clip:
             # Loop if needed
             if base_bg_clip.duration < duration:
                  # Manual Loop
                  num_loops = math.ceil(duration / base_bg_clip.duration) + 1
                  bg_segment = concatenate_videoclips([base_bg_clip] * num_loops).subclipped(0, duration)
             else:
                  bg_segment = base_bg_clip.subclipped(0, duration)
        else:
             bg_segment = ColorClip(SCREEN_SIZE, color=(0,0,50), duration=duration)
        
        bg_segment = bg_segment.with_duration(duration)

        # Context Image (with Persistence)
        context_img = None
        
        # Logic:
        # 1. If [IMG: keyword] matches and exists -> New Image.
        # 2. If [IMG: keyword] matches but MISSING -> Reuse Last Valid Image.
        # 3. If no tag -> Reuse Last Valid Image (until scene change? No, current design is per-line persistence).
        
        target_keyword = seg.get('image_keyword')
        
        if seg['character'] == "青山龍星":
            if target_keyword:
                 # Try to get new image
                 new_clip = get_image_clip(target_keyword, duration, custom_image_dir=target_image_dir)
                 if new_clip:
                     context_img = new_clip
                     last_valid_aoyama_image = new_clip # Update persistence
                 else:
                     # Failed to find new image, fallback to persistence
                     if last_valid_aoyama_image:
                         context_img = last_valid_aoyama_image.with_duration(duration)
            else:
                 # No tag specified for this line, assume continuation of previous context
                 if last_valid_aoyama_image:
                     context_img = last_valid_aoyama_image.with_duration(duration)
        
        # If still no image (Start of video or massive failure), use fallback?
        # Maybe Phase 4. For now, persistence covers most rate limit gaps.

        # Text Overlay
        char_color = CHARACTER_COLORS.get(seg['character'], CHARACTER_COLORS["default"])
        # UNIFIED PANEL LOGIC: Now everyone uses Panel Image.
        img_arr = create_panel_image(seg['text'], seg['character'], char_color)
            
        txt_clip = ImageClip(img_arr).with_duration(duration)
        
        # Composite
        layers = [bg_segment]
        if context_img: layers.append(context_img)
        layers.append(txt_clip)
        
        combined = CompositeVideoClip(layers)
        if audio_clip:
             # Audio Padding Fix (Phase 27)
             # Add 0.1s silence BEFORE and AFTER the audio to prevent clipping at transitions
             try:
                 # Create a silent audio clip of 0.1s
                 # In MoviePy 1.0, AudioClip(make_frame, duration) or AudioArrayClip
                 # Easiest way: use a small chunk of the BGM muted? or just 0s array.
                 # Actually, simpler: just set the start of the audio 0.1s later in the composite?
                 # No, we want to extend the clip length.
                 
                 # Let's use `CompositeAudioClip` to pad.
                 # padding_silence = AudioClip(lambda t: [0, 0], duration=0.1) # This often fails with numpy shapes
                 # Robust way: Just use `set_start`.
                 # But we need the video clip to be longer. We already did `duration += 0.2`.
                 
                 # So, we just need to ensure the audio plays in the MIDDLE of that duration.
                 # Current duration = audio.duration + 0.2
                 # So if we set audio start to 0.1, it has 0.1 padding on both sides.
                 
                 combined = combined.with_audio(audio_clip.with_start(0.1))
             except Exception as e:
                 print(f"Warning: Failed to apply audio padding: {e}")
                 combined = combined.with_audio(audio_clip)
        
        clips.append(combined)
        print(f"Segment {i+1}/{len(segments)} done. Dur: {duration:.2f}s")

    print("Concatenating...")
    final_video = concatenate_videoclips(clips, method="compose")
    
    # BGM
    if os.path.exists(BGM_FILE):
        print(f"Adding BGM: {BGM_FILE}")
        bgm_clip = AudioFileClip(BGM_FILE)
        num_loops = math.ceil(final_video.duration / bgm_clip.duration) + 1
        bgm_looped = concatenate_audioclips([bgm_clip] * num_loops).subclipped(0, final_video.duration)
        
        try:
             bgm_looped = bgm_looped.with_effects([afx.MultiplyVolume(BGM_VOLUME)])
        except:
             bgm_looped = bgm_looped.volumex(BGM_VOLUME)
        
        final_audio = CompositeAudioClip([final_video.audio, bgm_looped])
        final_video = final_video.with_audio(final_audio)
    
    # Ensure directory exists for output
    out_dir = os.path.dirname(target_output)
    if out_dir and not os.path.exists(out_dir):
        os.makedirs(out_dir)

    print(f"Writing to {target_output}...")
    final_video.write_videofile(
        target_output, 
        fps=FPS, 
        codec="libx264", 
        audio_codec="aac"
    )
    print("Video Generation Complete.")

if __name__ == "__main__":
    generate_video()
