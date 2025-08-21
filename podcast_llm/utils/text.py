"""
Utilities for text processing and formatting in podcast generation.

This module provides utilities for working with text content in podcast scripts
and outlines. It handles formatting and conversion of podcast content into
different text representations.

Key components:
- generate_markdown_script: Converts podcast outline and script into markdown format
  for easy viewing and sharing

The module helps with:
- Converting internal podcast data structures to human-readable formats
- Generating documentation and review materials from podcast content
- Maintaining consistent text formatting across the application
"""


from podcast_llm.outline import PodcastOutline


def generate_markdown_script(topic: str, outline: PodcastOutline, script: list) -> None:
    """
    Generate a markdown formatted version of the podcast script.

    Args:
        topic (str): The main topic of the podcast
        outline (PodcastOutline): The podcast outline containing sections and key points
        script (list): List of dictionaries containing script lines with structure:
            {
                'speaker': str,  # Speaker identifier ('Interviewer' or 'Interviewee')
                'text': str      # Line content
            }

    Returns:
        str: Markdown formatted script including topic, outline and conversation
    """
    markdown = f'# {topic}\n\n'

    # Add outline
    markdown += '## Outline\n\n'
    for i, section in enumerate(outline.sections, 1):
        markdown += f'### Section {i}: {section.title}\n'
        for subsection in section.subsections:
            markdown += f'- {subsection.as_str}\n'
        markdown += '\n'

    # Add script
    markdown += '## Script\n\n'
    for line in script:
        markdown += f'**{line["speaker"]}**: {line["text"]}\n\n'

    return markdown
