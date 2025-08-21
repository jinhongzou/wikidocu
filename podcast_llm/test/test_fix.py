#!/usr/bin/env python3
"""
Test script to verify the fix for the language parameter issue.
"""

from podcast_llm.utils.local_prompts import get_local_prompt

try:
    # Test with English
    prompt_en = get_local_prompt("podcast_outline", "en")
    print("English prompt loaded successfully")
    
    # Test with Chinese
    prompt_zh = get_local_prompt("podcast_outline", "zh")
    print("Chinese prompt loaded successfully")
    
    print("All tests passed!")
except Exception as e:
    print(f"Test failed with error: {e}")