
import sys
import os
import sys
import os
import json

# Ensure we can import modules from current dir
sys.path.append(os.getcwd())

# Import the module to test
from generate_video import create_panel_image, create_text_image, apply_kinsoku, SCREEN_SIZE
from PIL import Image

def test_visuals():
    output_dir = "visual_test_output"
    if not os.path.exists(output_dir):
        os.makedirs(output_dir)

    print("--- Testing Kinsoku Shori ---")
    bad_break_text = "これはテストです。「カッコ」が行頭に来ないように。"
    # Force a width that would normally orphan the bracket
    # Assume font size 85, width 1400 -> approx 15 chars/line.
    # "これはテストです。" is 9 chars. "「" is the 10th.
    # If we set width to 9, "「" should wrap.
    # But wait, apply_kinsoku logic is what we are testing.
    # Let's test the specific logic function first.
    
    # Test 1: Panel Image (White Box)
    print("Generating Test Panel...")
    long_text = "「政治利用」って、お前らがいつもやってることでしょうが！特大ブーメランでお腹痛いわ！"
    # Provide a color hex (Pink)
    panel_img = create_panel_image(long_text, "名無し", "#ff3399", size=SCREEN_SIZE)
    
    # Save frame
    img = Image.fromarray(panel_img)
    img.save(os.path.join(output_dir, "test_panel_pink.png"))
    print(f"Saved {output_dir}/test_panel_pink.png")

    # Test 1.5: Panel Image (Green - Zundamon)
    print("Generating Green Panel...")
    zunda_text = "ボクは緑色なのだ。ちゃんと色が変わるかテストなのだ。"
    # Zundamon Color: #39c263
    panel_img_green = create_panel_image(zunda_text, "ずんだもん", "#39c263", size=SCREEN_SIZE)
    img_green = Image.fromarray(panel_img_green)
    img_green.save(os.path.join(output_dir, "test_panel_green.png"))
    print(f"Saved {output_dir}/test_panel_green.png")

    # Test 2: Subtitle Layout (Check Height)
    print("Generating Test Subtitle...")
    sub_text = "見ろ！この数字を。「高市内閣支持率 59.9%」！時事通信ですら認めざるを得ない、圧倒的な国民の支持だ！"
    sub_img_arr = create_text_image(sub_text, size=SCREEN_SIZE, color="white")
    
    sub_img = Image.fromarray(sub_img_arr)
    # Composite with a dummy background to check visibility
    bg = Image.new("RGB", SCREEN_SIZE, (50, 50, 50))
    bg.paste(sub_img, (0,0), sub_img)
    bg.save(os.path.join(output_dir, "test_subtitle_layout.png"))
    print(f"Saved {output_dir}/test_subtitle_layout.png")

if __name__ == "__main__":
    test_visuals()
