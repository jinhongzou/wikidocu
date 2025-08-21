#!/usr/bin/env python3
"""
Download all prompts from LangChain Hub and save them locally.

This script downloads the prompts used by the podcast-llm system and saves them 
to local files for offline use and inspection.
"""

import os
import json
from langchain import hub

# Define the prompts to download
PROMPTS = {
    "podcast_outline": "evandempsey/podcast_outline:6ceaa688",
    "podcast_wikipedia_suggestions": "evandempsey/podcast_wikipedia_suggestions:58c92df4",
    "podcast_research_queries": "evandempsey/podcast_research_queries:561acf5f",
    "podcast_interviewer_role": "evandempsey/podcast_interviewer_role:bc03af97",
    "podcast_interviewee_role": "evandempsey/podcast_interviewee_role:0832c140",
    "podcast_rewriter": "evandempsey/podcast_rewriter:181421e2"
}

def download_prompt(prompt_name, prompt_id):
    """Download a single prompt and save it to a file."""
    print(f"Downloading {prompt_name}...")
    try:
        prompt = hub.pull(prompt_id)
        
        # Save as JSON
        prompt_data = {
            "id": prompt_id,
            "messages": []
        }
        
        for i, message in enumerate(prompt.messages):
            prompt_data["messages"].append({
                "index": i,
                "template": message.prompt.template if hasattr(message.prompt, 'template') else str(message.content),
                "type": type(message).__name__
            })
        
        # Save to file
        filename = f"{prompt_name}.json"
        with open(filename, 'w', encoding='utf-8') as f:
            json.dump(prompt_data, f, indent=2, ensure_ascii=False)
        
        print(f"Saved {prompt_name} to {filename}")
        return prompt_data
    except Exception as e:
        print(f"Error downloading {prompt_name}: {e}")
        return None

def main():
    """Main function to download all prompts."""
    # Create a directory for prompts if it doesn't exist
    prompts_dir = "local_prompts"
    if not os.path.exists(prompts_dir):
        os.makedirs(prompts_dir)
    
    # Change to prompts directory
    original_dir = os.getcwd()
    os.chdir(prompts_dir)
    
    print("Downloading prompts from LangChain Hub...")
    
    # Download all prompts
    downloaded_prompts = {}
    for name, prompt_id in PROMPTS.items():
        prompt_data = download_prompt(name, prompt_id)
        if prompt_data:
            downloaded_prompts[name] = prompt_data
    
    # Save a summary file
    with open("prompts_summary.json", 'w', encoding='utf-8') as f:
        json.dump(downloaded_prompts, f, indent=2, ensure_ascii=False)
    
    print(f"\nDownloaded {len(downloaded_prompts)} prompts to {prompts_dir}/")
    print(f"Created summary: prompts_summary.json")
    print("Note: Chinese prompt files (ending with _zh.json) are manually created.")
    os.chdir(original_dir)

if __name__ == "__main__":
    main()