from moviepy import ColorClip, CompositeVideoClip, ImageClip
import numpy as np
from PIL import Image, ImageDraw, ImageFont

def create_text_image(text, size=(1920, 1080), fontsize=100, color='white'):
    """Creates a text image using PIL."""
    img = Image.new('RGBA', size, (0, 0, 0, 0))
    draw = ImageDraw.Draw(img)
    
    try:
        font = ImageFont.truetype("/System/Library/Fonts/Supplemental/Arial Bold.ttf", fontsize)
    except:
        try:
             font = ImageFont.truetype("Arial", fontsize)
        except:
             font = ImageFont.load_default()
    
    try:
        left, top, right, bottom = draw.textbbox((0, 0), text, font=font)
        w, h = right - left, bottom - top
    except:
        w, h = draw.textsize(text, font=font)
        
    position = ((size[0] - w) / 2, (size[1] - h) / 2)
    
    draw.text(position, text, font=font, fill=color)
    return np.array(img)

def create_background():
    w, h = 1920, 1080
    bg_color = ColorClip(size=(w, h), color=(20, 20, 40), duration=10)
    
    img_array = create_text_image("BACKGROUND LOOP", size=(w, h))
    
    # MoviePy 2.0 API: use with_duration, with_opacity (requires effects?)
    # Check if with_opacity exists. Usually opacity is an effect.
    # If not, let's just skip opacity for now or check usage.
    # Actually, let's look for with_opacity or similar. 
    # But usually `clip.with_duration` works.
    
    txt_clip = ImageClip(img_array).with_duration(10)
    
    # Opacity in v2 often via effects.mask_opacity or similar.
    # Simplified: just use text on top, maybe no opacity change if tricky without knowing exact API.
    # But let's try `with_opacity` if it exists, or just skip opacity for the background text.
    
    video = CompositeVideoClip([bg_color, txt_clip])
    video.write_videofile("../assets/backgrounds/bg_loop_01.mp4", fps=24)

if __name__ == "__main__":
    create_background()
