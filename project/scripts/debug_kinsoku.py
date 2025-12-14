
import textwrap

def apply_kinsoku_ref(text, chars_per_line):
    """Current implementation ref."""
    raw_lines = textwrap.wrap(text, width=chars_per_line)
    refined_lines = []
    if raw_lines:
        refined_lines.append(raw_lines[0])
        for i in range(1, len(raw_lines)):
            line = raw_lines[i]
            prev = refined_lines[-1]
            if line.startswith("」") or line.startswith("。") or line.startswith("、") or line.startswith("？") or line.startswith("！"):
                 refined_lines[-1] = prev + line[0]
                 refined_lines.append(line[1:]) 
            elif prev.endswith("「"): 
                 refined_lines[-1] = prev[:-1]
                 refined_lines.append("「" + line)
            else:
                 refined_lines.append(line)
        refined_lines = [l for l in refined_lines if l]
        return refined_lines
    return []

# Test Case
text = "「埼玉のギャルなめんなよ！枠からはみ出したら承知しないからね！」"
font_size = 85
panel_w = 1400
chars = int((panel_w - 100) / font_size) # 15

print(f"Chars per line: {chars}")
lines = apply_kinsoku_ref(text, chars)
print("--- Result ---")
for l in lines:
    print(f"'{l}'")
