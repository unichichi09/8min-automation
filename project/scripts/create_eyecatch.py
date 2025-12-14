import numpy as np
from PIL import Image
from moviepy import *
import os
import math

# Paths
INPUT_IMG = "../assets/images/eyecatch_base.jpg"
OUTPUT_GIF = "../assets/images/eyecatch.gif"
OUTPUT_MP4 = "../assets/videos/eyecatch.mp4"

def create_eyecatch_animation():
    print(f"Loading {INPUT_IMG}...")
    
    if not os.path.exists(INPUT_IMG):
        print("Image not found!")
        return

    # Load image
    pil_img = Image.open(INPUT_IMG).convert("RGB")
    width, height = pil_img.size
    img_arr = np.array(pil_img)
    
    # Create Mask for "Flame" (Reddish/Orange/Yellow)
    # Simple RGB Thresholds
    # Flame: High R (>200), G (>50), B (<100)?
    # Let's be lenient.
    # The angry face is Red. The flame is Yellow/Orange.
    # We want flame AND face? Or just flame?
    # User said "Flame swaying".
    # Face is usually solid red: R~255, G~0, B~0.
    # Flame is Yellow/Orange: R~255, G~100-255, B~0.
    # So if G > 50 and R > 200, it's likely flame (Yellowish).
    # If G < 50, it's the face (Red).
    
    R = img_arr[:,:,0]
    G = img_arr[:,:,1]
    B = img_arr[:,:,2]
    
    # Mask for Yellow/Orange (Flame)
    # R > 200, G > 50, B < 100
    mask_flame = (R > 180) & (G > 60) & (B < 150)
    
    # Convert mask to float 0-1
    mask_flame_f = mask_flame.astype(float)
    # Expand to 3 channels
    mask_3ch = np.stack([mask_flame_f]*3, axis=2)

    duration = 3.0
    fps = 24
    
    def make_frame(t):
        # Apply swaying effect to flame pixels
        # Simple wave: Shift X based on Y and Time
        frames_arr = img_arr.copy()
        
        # We only manipulate rows where mask exists? 
        # Easier: Distort entire image into a separate buffer, then composite.
        
        distorted = np.zeros_like(frames_arr)
        
        # Wave Parameters
        freq = 0.05
        amp = 3.0
        speed = 10.0
        
        # Optimize: Iterate over rows is slow in pure python?
        # Actually in standard python loop over 1080 rows is fine for 3s video (72 frames).
        
        # Pre-calc shift for each row
        # shift = amp * sin(y * freq - t * speed)
        y_indices = np.arange(height)
        shifts = np.sin(y_indices * freq - t * speed) * amp
        
        # We want top of image (low y) to sway MORE?
        # Flame is usually at top? 
        # Or just uniform sway is fine for "flicker".
        # Let's add noise for flicker.
        shifts += np.random.normal(0, 1.0)
        
        shifts = shifts.astype(int)
        
        # Apply shifts
        # Can we do this vectorized?
        # np.roll axis=1? But shift varies per row.
        # Loop is necessary or advanced indexing.
        for y in range(height):
            shift = shifts[y]
            if shift == 0:
                distorted[y] = frames_arr[y]
            else:
                distorted[y] = np.roll(frames_arr[y], shift, axis=0) # axis 0 of row is pixels? No, frames_arr[y] is (W, 3). So axis 0 is width.
        
        # Composite
        # Final = Original * (1-Mask) + Distorted * Mask
        # This means only the flame parts swaying effectively replaces the original flame parts.
        # But if we shift the flame pixels, the mask should move too?
        # No, simpler: We presume the distortion is small enough that we modify pixels "under" the flame mask area.
        # Actually, if we stick to the STATIC mask, the flame edges will look clipped if they move out of mask.
        # Ideally we distort the image, then masked result?
        # If we mask, then distort, we move the flame.
        
        # Let's try: Distort the Whole Image (Yellow parts). 
        # Then mix.
        
        # Artifacts issues: If we shift yellow pixels into non-yellow area, mask won't cover them.
        # Better: Just distort the flame parts in-place?
        
        # Simplest visual result:
        # Just use the distorted image where the Original Mask was? No, that cuts off.
        # Use the Distorted Image where the Distorted Mask is? Hard to track.
        
        # Compromise:
        # Just distort the whole image, but modulate the *strength* of the distortion by the color mask?
        # i.e. Output(x,y) = Source(x + shift * mask(x,y), y)
        # That's equivalent to mapping.
        
        # Since we don't have remap, let's just stick to the row-roll on the masked composite.
        # Result = Original * (1 - Mask) + Distorted * Mask
        # This keeps the Face stable, but FLAME pixels inside the mask will wobble.
        # It's a "texture wobble" effect, looking like heat haze. Acceptable for "Mera Mera".
        
        final = frames_arr * (1 - mask_3ch) + distorted * mask_3ch
        
        return final.astype(np.uint8)

    # ... (Image Processing Loop) ...
    clip = VideoClip(make_frame, duration=duration)
    
    # --- Audio Generation (Fire Rumble) ---
    print("Generating Fire SE...")
    audio_fps = 44100
    
    def make_fire_audio(t):
        # t is a numpy array of times
        # Generate Brownian-like noise (Integration of white noise)
        # But for 'make_frame', t is a float? No, AudioClip expects a function t -> value(s) or an array.
        # It's easier to generate an AudioArrayClip or just compute the array.
        return np.random.uniform(-1, 1, size=t.shape) # White noise placeholder logic if needed
        
    # Better: Generate numpy array first
    num_samples = int(duration * audio_fps)
    
    # White Noise
    white_noise = np.random.normal(0, 0.5, num_samples)
    
    # Low Pass Filter (Simple Moving Average) to make it "Rumble"
    # Fire is low frequency noise.
    # Window size determines cutoff. 
    window_size = 50 
    brown_noise = np.convolve(white_noise, np.ones(window_size)/window_size, mode='same')
    
    # Modulate Amplitude for "Flicker" sound
    # Use a low freq sine wave + random to modulate volume
    t_arr = np.linspace(0, duration, num_samples)
    modulator = 0.5 + 0.5 * np.sin(2 * np.pi * 5 * t_arr) # 5Hz flicker
    modulator += np.random.normal(0, 0.1, num_samples) 
    modulator = np.clip(modulator, 0, 1)
    
    final_audio = brown_noise * (modulator * 2.0) # Boost volume
    
    # Fade In/Out
    fade_len = int(0.5 * audio_fps)
    envelope = np.ones(num_samples)
    envelope[:fade_len] = np.linspace(0, 1, fade_len)
    envelope[-fade_len:] = np.linspace(1, 0, fade_len)
    final_audio *= envelope
    
    # Normalize
    max_val = np.max(np.abs(final_audio))
    if max_val > 0:
        final_audio = final_audio / max_val * 0.5 # Lower volume to 50% to prevent loudness
    
    # Convert to MoviePy AudioClip
    # AudioClip expects shape (N, 2) for stereo or (N,) for mono?
    # ArrayAudioClip expects (N, nchannels)
    final_audio_stereo = np.column_stack((final_audio, final_audio))
    audio_clip = AudioArrayClip(final_audio_stereo, fps=audio_fps)
    
    clip = clip.with_audio(audio_clip)

    # Save output
    print(f"Writing {OUTPUT_GIF}...")
    clip.write_gif(OUTPUT_GIF, fps=15)
    
    print(f"Writing {OUTPUT_MP4}...")
    mp4_dir = os.path.dirname(OUTPUT_MP4)
    if not os.path.exists(mp4_dir): os.makedirs(mp4_dir)
    clip.write_videofile(OUTPUT_MP4, fps=24, codec="libx264", audio_codec="aac")

if __name__ == "__main__":
    create_eyecatch_animation()
