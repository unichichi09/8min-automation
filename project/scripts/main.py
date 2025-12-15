import os
import sys
import argparse
import subprocess
import re
import json
import generate_video
import fetch_images

# Load Config
# Load Config
current_dir = os.path.dirname(os.path.abspath(__file__))
CONFIG_PATH = os.path.join(current_dir, "../config.json")
try:
    with open(CONFIG_PATH, 'r', encoding='utf-8') as f:
        config = json.load(f)
except FileNotFoundError:
    print("Config not found.")
    exit(1)

# Robust Path Finding
# main.py is in .../8分自動化/project/scripts/main.py
# We want .../8分自動化/projects
current_dir = os.path.dirname(os.path.abspath(__file__)) # .../scripts
project_root = os.path.dirname(current_dir) # .../project
repo_root = os.path.dirname(project_root) # .../8分自動化
PROJECTS_ROOT = os.path.join(repo_root, "projects")

print(f"DEBUG: PROJECTS_ROOT resolved to: {PROJECTS_ROOT}")

def create_project(project_name):
    """Creates directory structure for a new project."""
    base_dir = os.path.join(PROJECTS_ROOT, project_name)
    
    dirs = {
        "script": os.path.join(base_dir, "script"),
        "audio": os.path.join(base_dir, "audio"),
        "images": os.path.join(base_dir, "images"),
        "output": os.path.join(base_dir, "output")
    }
    
    for k, d in dirs.items():
        if not os.path.exists(d):
            os.makedirs(d)
            print(f"Created: {d}")
            
    # Create empty script file
    script_path = os.path.join(dirs["script"], "script.md")
    if not os.path.exists(script_path):
        with open(script_path, "w", encoding='utf-8') as f:
            f.write("# New Script\n\n[IMG: Placeholder]\nCharacter, Text\n")
        print(f"Initialized script at {script_path}")
        
    print(f"Project '{project_name}' ready.")
    return dirs

def run_project(project_name):
    """Runs the full pipeline for a specific project."""
    base_dir = os.path.join(PROJECTS_ROOT, project_name)
    if not os.path.exists(base_dir):
        print(f"Project {project_name} does not exist.")
        return

    script_dir = os.path.join(base_dir, "script")
    output_dir = os.path.join(base_dir, "output")
    image_dir = os.path.join(base_dir, "images")
    audio_dir = os.path.join(base_dir, "audio")
    
    if not os.path.exists(output_dir): os.makedirs(output_dir)
    if not os.path.exists(image_dir): os.makedirs(image_dir)
    if not os.path.exists(audio_dir): os.makedirs(audio_dir)
    
    script_files = []
    if os.path.exists(script_dir):
        script_files = [f for f in os.listdir(script_dir) if f.endswith(".md")]
    
    if not script_files:
        print("No markdown script found in script folder.")
        return
    script_path = os.path.join(script_dir, script_files[0]) # Use first found
    
    print(f"Using Script: {script_path}")
    
    # 2. Image Fetch
    print("Fetching images...")
    try:
        fetch_images.fetch_images_for_script(script_path=script_path, image_dir=image_dir)
    except Exception as e:
        print(f"Image fetch warning: {e}")
    
    # 3. Video Generation
    output_video_path = os.path.join(output_dir, f"{project_name}_video.mp4")
    
    # Call generate_video directly
    generate_video.generate_video(
        script_path=script_path,
        output_path=output_video_path,
        image_dir=image_dir,
        audio_dir=audio_dir
    )

def main():
    parser = argparse.ArgumentParser(description="Automated Video Generation - Project Manager")
    parser.add_argument("action", choices=["new", "run", "delete"], help="Action: 'new', 'run', or 'delete' project")
    parser.add_argument("project_name", help="Name of the project")
    parser.add_argument("--url", help="YouTube URL to source content from (for 'new' action)", default=None)

    args = parser.parse_args()
    
    if args.action == "new":
        dirs = create_project(args.project_name)
        if args.url:
            import fetch_transcript
            print(f"Fetching transcript from {args.url}...")
            transcript_path = os.path.join(dirs['script'], "source_transcript.txt")
            fetch_transcript.fetch_transcript(args.url, transcript_path)
    elif args.action == "run":
        run_project(args.project_name)
    elif args.action == "delete":
        delete_project(args.project_name)

def delete_project(project_name):
    """Deletes the entire project directory."""
    import shutil
    base_dir = os.path.join(PROJECTS_ROOT, project_name)
    
    if not os.path.exists(base_dir):
        print(f"Project '{project_name}' does not exist.")
        return

    print(f"WARNING: You are about to DELETE the entire project '{project_name}'.")
    print(f"Path: {base_dir}")
    choice = input("Are you sure you want to PERMANENTLY delete this project? (y/N): ").lower()
    
    if choice == 'y':
        try:
            shutil.rmtree(base_dir)
            print(f"Project '{project_name}' has been deleted.")
        except Exception as e:
            print(f"Error deleting project: {e}")
    else:
        print("Deletion cancelled.")

if __name__ == "__main__":
    main()
