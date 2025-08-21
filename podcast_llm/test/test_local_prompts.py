#!/usr/bin/env python3
"""
Test script to verify that all local prompt functionality works correctly.
"""

import sys
import os

# Add the parent directory to the path so we can import podcast_llm modules
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from podcast_llm.utils.local_prompts import load_local_prompt, get_local_prompt

def test_load_all_prompts():
    """Test loading all prompts from local storage."""
    prompt_names = [
        "podcast_outline",
        "podcast_wikipedia_suggestions", 
        "podcast_research_queries",
        "podcast_interviewer_role",
        "podcast_interviewee_role",
        "podcast_rewriter"
    ]
    
    print("Testing local prompt loading...")
    
    for prompt_name in prompt_names:
        try:
            prompt = load_local_prompt(prompt_name)
            print(f"[PASS] Successfully loaded {prompt_name}")
            print(f"  Prompt type: {type(prompt)}")
            print(f"  Number of messages: {len(prompt.messages)}")
        except Exception as e:
            print(f"[FAIL] Failed to load {prompt_name}: {e}")
            return False
    
    return True

def test_get_all_prompts():
    """Test getting all prompts (with fallback to Hub)."""
    prompt_names = [
        "podcast_outline",
        "podcast_wikipedia_suggestions", 
        "podcast_research_queries",
        "podcast_interviewer_role",
        "podcast_interviewee_role",
        "podcast_rewriter"
    ]
    
    print("\nTesting get_local_prompt function...")
    
    for prompt_name in prompt_names:
        try:
            prompt = get_local_prompt(prompt_name)
            print(f"[PASS] Successfully got {prompt_name}")
            print(f"  Prompt type: {type(prompt)}")
        except Exception as e:
            print(f"[FAIL] Failed to get {prompt_name}: {e}")
            return False
    
    return True

def main():
    """Main test function."""
    print("Running local prompt tests...\n")
    
    # Test loading prompts directly
    if not test_load_all_prompts():
        print("\n[ERROR] Some tests failed!")
        return 1
    
    # Test getting prompts (with fallback)
    if not test_get_all_prompts():
        print("\n[ERROR] Some tests failed!")
        return 1
    
    print("\n[SUCCESS] All tests passed!")
    return 0

if __name__ == "__main__":
    sys.exit(main())