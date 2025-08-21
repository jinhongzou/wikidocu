#!/usr/bin/env python3
"""
Update local prompts to require Chinese conversation context.
"""

import os
import json

# Define the local prompts directory
LOCAL_PROMPTS_DIR = os.path.join(os.path.dirname(__file__), "local_prompts")

def update_prompt_for_chinese(prompt_name):
    """Update a prompt to require Chinese conversation context."""
    prompt_file = os.path.join(LOCAL_PROMPTS_DIR, f"{prompt_name}.json")
    
    if not os.path.exists(prompt_file):
        print(f"Prompt file not found: {prompt_file}")
        return False
    
    # Load the prompt
    with open(prompt_file, 'r', encoding='utf-8') as f:
        prompt_data = json.load(f)
    
    # Update the templates to require Chinese
    for message in prompt_data["messages"]:
        if message["type"] == "SystemMessagePromptTemplate":
            template = message["template"]
            # Replace the TONE section with Chinese requirement
            if "TONE:" in template:
                lines = template.split('\n')
                new_lines = []
                in_tone_section = False
                tone_section_replaced = False
                
                for line in lines:
                    if line.strip() == "TONE:":
                        in_tone_section = True
                        new_lines.append(line)
                        new_lines.append("- Use Chinese for all conversation.")
                        new_lines.append("- Speak informally, as if writing on IRC or Reddit.")
                        new_lines.append("- Use good grammar and punctuation.")
                        tone_section_replaced = True
                    elif in_tone_section and line.strip().startswith("-"):
                        # Skip original TONE lines
                        continue
                    elif in_tone_section and not line.strip().startswith("-") and line.strip():
                        # End of TONE section
                        in_tone_section = False
                        new_lines.append(line)
                    else:
                        new_lines.append(line)
                
                message["template"] = '\n'.join(new_lines)
            else:
                # Add TONE section with Chinese requirement
                template += "\n\nTONE: \n- Use Chinese for all conversation.\n- Speak informally, as if writing on IRC or Reddit.\n- Use good grammar and punctuation."
                message["template"] = template
    
    # Save the updated prompt
    with open(prompt_file, 'w', encoding='utf-8') as f:
        json.dump(prompt_data, f, indent=2, ensure_ascii=False)
    
    print(f"Updated {prompt_name} to require Chinese conversation context")
    return True

def main():
    """Main function to update all prompts for Chinese context."""
    prompt_names = [
        "podcast_interviewer_role",
        "podcast_interviewee_role", 
        "podcast_rewriter"
    ]
    
    print("Updating prompts to require Chinese conversation context...")
    
    # Update prompts
    for name in prompt_names:
        update_prompt_for_chinese(name)
    
    print("All prompts updated successfully!")

if __name__ == "__main__":
    main()