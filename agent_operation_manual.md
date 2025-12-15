# Agent Operation Manual: 3-Minute Video Automation

## 0. Installation (First Time Setup)

Before using this tool on a new machine, follow these steps to set up the environment.

1.  **Prerequisites**:

    - **macOS** (Tested on macOS Sequoia)
    - **Python 3** installed.
    - **VOICEVOX**: Must be installed and running. [Download here](https://voicevox.hiroshiba.jp/).

2.  **Run Setup Script**:
    Open a terminal in the root directory and run:

    ```bash
    chmod +x setup.sh
    ./setup.sh
    ```

    This script will:

    - Install necessary Python libraries (MoviePy, etc.) from `requirements.txt`.
    - Install ImageMagick (via Homebrew) if missing.
    - Check if VOICEVOX is running.

3.  **Verification**:
    If the script ends with `Setup Complete!`, you are ready to proceed to **Step 1: Initialize**.

## 1. Core Directive

**`prompt_3min.md` is the Absolute Law.**
All script generation strictures are defined there. Your primary duty is to **strictly observe** that prompt.

## 2. Quality Constraints (Agent Behavior)

### Script Quality

- **Length is Vital**: To guarantee >3 minutes, **aim for approx 1400-2000 chars**.
- **Number Formatting**: Ensure no spaces exist around numbers (e.g., `1 2 月 ` -> `12月`) to prevent robotic pauses. Use `sed` or regex to clean this.

### Visual Constraints

- **ABSOLUTE NG**: Images with **logos, watermarks, or text overlays** from weekly magazines (週刊誌), TV stations, or news tickers.
- **Aoyama's Panel**: Must be **Dark Panel with White Text** at the bottom. (Handled by code, but verify visually).

## 3. Workflow Steps

### Step 1: Initialize

- Command: `python3 main.py new [YYYYMMDD_ProjectName]`
- Location: Ensure project is provided in `projects/` directory.

### Step 2: Script Generation & Self-Correction

1.  **Generate**: Write `script.md` based on Source Text + `prompt_3min.md`.
2.  **STOP & THINK (Self-Correction)**:
    - Before proceeding, review your generated script.

### Step 4: Cleanup (Manual)

All intermediate files (images, audio, script) are contained within the `projects/[ProjectName]` folder.
Once you have moved the final video (`output/video.mp4`) to your desired location, you can simply **delete the `projects/[ProjectName]` folder manually** (Move to Trash).

This will safely remove all temporary assets associated with that video without affecting other projects.

### Step 3: Production & Verification

1.  **Run**: `python3 main.py run [ProjectName]`
    - **Note**: Image fetching now uses **Smart Refresh & Backoff**. It may take time (random waits). **DO NOT interrupt** unless it hangs for >5 mins.
2.  **Verify**:
    - **Audio**: Check for unnatural pauses (especially numbers).
    - **Visuals**: Ensure images persist (no empty backgrounds).
    - **Duration**: Confirm video length > 3:00.
3.  **Deliver**:
    - Create `youtube_metadata.md`.
    - Present `output/video.mp4` and `thumbnail.jpg`.

## 4. File Management

- **Repo Root**: `/Users/nishikigitisato/Desktop/3分自動化`
- **Projects**: `projects/`
