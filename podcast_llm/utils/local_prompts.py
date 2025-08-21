#!/usr/bin/env python3
"""
Utility functions for working with local prompts.

This module provides functions to load prompts from local files instead of 
pulling them from LangChain Hub.
"""
import logging
import os
import json
from typing import Dict, Any
from langchain.prompts import ChatPromptTemplate

# Define the local prompts directory
LOCAL_PROMPTS_DIR = os.path.join(os.path.dirname(os.path.dirname(__file__)), "local_prompts")

# Define prompt mappings for different languages
PROMPT_MAPPINGS = {
    'en': {
        "podcast_outline": "podcast_outline",
        "podcast_wikipedia_suggestions": "podcast_wikipedia_suggestions", 
        "podcast_research_queries": "podcast_research_queries",
        "podcast_interviewer_role": "podcast_interviewer_role",
        "podcast_interviewee_role": "podcast_interviewee_role",
        "podcast_rewriter": "podcast_rewriter"
    },
    'zh': {
        "podcast_outline": "podcast_outline_zh",
        "podcast_wikipedia_suggestions": "podcast_wikipedia_suggestions_zh", 
        "podcast_research_queries": "podcast_research_queries_zh",
        "podcast_interviewer_role": "podcast_interviewer_role_zh",
        "podcast_interviewee_role": "podcast_interviewee_role_zh",
        "podcast_rewriter": "podcast_rewriter_zh"
    }
}

def load_local_prompt(prompt_name: str, language: str = 'en') -> ChatPromptTemplate:
    """
    Load a prompt from a local JSON file.
    
    Args:
        prompt_name (str): Name of the prompt file (without .json extension)
        language (str): Language code ('en' for English, 'zh' for Chinese)
        
    Returns:
        ChatPromptTemplate: The loaded prompt template
        
    Raises:
        FileNotFoundError: If the prompt file doesn't exist
        ValueError: If the prompt file format is invalid
    """
    # Get the appropriate prompt file name based on language
    logging.info(f"Loading prompt {prompt_name} for language {language}")
    if language in PROMPT_MAPPINGS and prompt_name in PROMPT_MAPPINGS[language]:
        file_name = PROMPT_MAPPINGS[language][prompt_name]
    else:
        # Fallback to English if language or prompt not found
        file_name = prompt_name
    
    prompt_file = os.path.join(LOCAL_PROMPTS_DIR, f"{file_name}.json")
    
    if not os.path.exists(prompt_file):
        raise FileNotFoundError(f"Prompt file not found: {prompt_file}")
    
    with open(prompt_file, 'r', encoding='utf-8') as f:
        prompt_data = json.load(f)
    
    if "messages" not in prompt_data:
        raise ValueError(f"Invalid prompt format in {prompt_file}: missing 'messages' key")
    
    # Convert messages to prompt templates
    messages = []
    for msg_data in prompt_data["messages"]:
        if msg_data["type"] == "SystemMessagePromptTemplate":
            messages.append(("system", msg_data["template"]))
        elif msg_data["type"] == "HumanMessagePromptTemplate":
            messages.append(("human", msg_data["template"]))
        else:
            # For other message types, treat as human messages
            messages.append(("human", msg_data["template"]))
    
    return ChatPromptTemplate.from_messages(messages)

def get_local_prompt(prompt_name: str, language: str = 'en'):
    """
    Get a prompt template, either from local storage or Hub as fallback.
    
    Args:
        prompt_name (str): Name of the prompt
        language (str): Language code ('en' for English, 'zh' for Chinese)
        
    Returns:
        ChatPromptTemplate: The prompt template
    """
    try:
        # Try to load from local storage first
        return load_local_prompt(prompt_name, language)
    except FileNotFoundError:
        # Fall back to loading from Hub
        from langchain import hub
        prompt_id = {
            "podcast_outline": "evandempsey/podcast_outline:6ceaa688",
            "podcast_wikipedia_suggestions": "evandempsey/podcast_wikipedia_suggestions:58c92df4",
            "podcast_research_queries": "evandempsey/podcast_research_queries:561acf5f",
            "podcast_interviewer_role": "evandempsey/podcast_interviewer_role:bc03af97",
            "podcast_interviewee_role": "evandempsey/podcast_interviewee_role:0832c140",
            "podcast_rewriter": "evandempsey/podcast_rewriter:181421e2"
        }.get(prompt_name)
        
        if prompt_id:
            return hub.pull(prompt_id)
        else:
            raise ValueError(f"Unknown prompt: {prompt_name}")