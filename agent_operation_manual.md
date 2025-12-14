# Agent Operation Manual: 8-Minute Video Automation

## 1. Core Directive

**`prompt_8min.md` is the Absolute Law.**
All script generation strictures (character tone, prohibited behaviors like name-calling, length, etc.) are defined there. Your primary duty is to **strictly observe** that prompt.

## 2. Image Constraints (Agent Behavior)

While the script defines _what_ images to search for, **YOU (the Agent) must ensure the QUALITY of the fetched images**:

- **ABSOLUTE NG**: Images with **logos, watermarks, or text overlays** from weekly magazines (週刊誌), TV stations, or news tickers.
- **Action**: When fetching images, inspect the results. If a bad image is found, find a cleaner alternative.

## 3. Workflow Steps

### Step 1: Initialize

- Command: `python3 project/scripts/main.py new [YYYYMMDD_ProjectName]`
- Location: Ensure project is provided in `projects/` directory.

### Step 2: Script Generation & Self-Correction

1.  **Generate**: Write `script.md` based on Source Text + `prompt_8min.md`.
2.  **STOP & THINK (Self-Correction)**:
    - Before proceeding, review your generated script.
    - **Did you strictly follow `prompt_8min.md`?**
      - Length > 6000 chars?
      - No character name calling?
      - Correct character roles?
    - _If any violation is found, rewrite immediately._

### Step 3: Production & Verification

1.  **Run**: `python3 project/scripts/main.py run [ProjectName]`
2.  **Verify**:
    - Check for "Search failed" errors (Rate limits).
    - Check final video file size and duration.
    - Create `walkthrough.md`.

## 4. File Management

- **Repo Root**: `/Users/nishikigitisato/Desktop/8分自動化`
- **Projects**: `projects/`
