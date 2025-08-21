"""
播客脚本撰写模块。

该模块负责生成自然、口语化的播客对话脚本。  
它利用大语言模型（LLMs），根据播客大纲和研究资料，自动生成主持人与嘉宾之间生动有趣的问答对话。

主要功能包括：
- 将大纲章节转化为自然的对话内容  
- 保持对话的上下文连贯性和流畅性  
- 格式化对话历史以适配提示词上下文  
- 基于前一个回答生成后续追问问题  
- 以正确的说话人标签组织完整的播客脚本结构  

该模块基于 LangChain 和 GPT-4，生成动态的多轮对话，在确保涵盖大纲关键内容的同时，使对话听起来真实自然。模块还包含速率限制机制，并支持长篇内容的生成。

示例：
```python
script = write_podcast_script(
    config=podcast_config,
    outline=episode_outline,
    background_info=research_docs
)
print(script.as_str)
```
"""

import logging
from typing import List, Optional
from langchain.text_splitter import RecursiveCharacterTextSplitter
from langchain_community.vectorstores import InMemoryVectorStore
from langchain_core.documents import Document
from podcast_llm.outline import (
    format_wikipedia_document
)
import logging
from langchain import hub
from langchain_openai import ChatOpenAI
from podcast_llm.outline import PodcastOutline
from langchain_core.rate_limiters import InMemoryRateLimiter
from langchain.chains.llm import LLMChain
from langchain_core.vectorstores.base import VectorStoreRetriever
from podcast_llm.config import PodcastConfig
from podcast_llm.utils.embeddings import get_embeddings_model
from podcast_llm.utils.llm import get_long_context_llm
from podcast_llm.utils.local_prompts import get_local_prompt
from podcast_llm.models import (
    PodcastOutline,
    PodcastSection,
    PodcastSubsection,
    Script,
    Question,
    Answer
)
from podcast_llm.utils.rate_limits import retry_with_exponential_backoff
from podcast_llm.utils.content_search import content_search

logger = logging.getLogger(__name__)

def format_conversation_history(conversation_history: list) -> str:
    """
    Format a conversation history into a readable string.

    Takes a list of Question and Answer objects representing a conversation history
    and formats them into a structured string with clear speaker labels. Each
    question is prefixed with "Interviewer:" and each answer with "Interviewee:".

    Args:
        conversation_history (list): List of alternating Question and Answer objects
            representing the conversation history

    Returns:
        str: Formatted string containing the full conversation with speaker labels
    """
    conversation = ""
    for c in conversation_history:
        if type(c) == Question:
            conversation += f"Interviewer: {c.as_str}\n"
        else:
            conversation += f"Interviewee: {c.as_str}\n"

    return conversation

# 将向量存储检索返回的文档列表格式化为可读字符串。它通过列表推导式提取每个文档的page_content属性，然后使用双换行符\n\n将所有文档内容连接成一个字符串返回，便于LLM参考背景信息生成回复。
def format_vector_results(docs: List[Document]):
    """
    Format retrieved vector store documents into a readable string.

    Takes a list of document objects returned from a vector store retrieval and 
    formats their content into a single string, with documents separated by newlines.
    This is used to format relevant background information for the LLM to reference
    when generating responses.

    Args:
        docs: List of document objects from vector store retrieval, each containing
            page_content attribute with the document text

    Returns:
        str: Concatenated document contents separated by double newlines
    """
    return "\n\n".join([d.page_content for d in docs])

@retry_with_exponential_backoff(max_retries=10, base_delay=2.0)
def ask_question(topic: str, 
                 outline: PodcastOutline, 
                 section: PodcastSection, 
                 subsection: PodcastSubsection, 
                 background_info: list, 
                 draft_discussion: list, 
                 interviewer_chain: LLMChain) -> Question:
    """
    Generate the next interview question based on the conversation context.

    Uses LangChain and an LLM to generate a natural follow-up question that advances
    the discussion while staying focused on the current subsection topic. Takes into
    account the full conversation history and background research to ask relevant and
    insightful questions.

    Args:
        topic (str): The main podcast topic
        outline (PodcastOutline): The structured outline for the episode
        section (PodcastSection): The current section being discussed
        subsection (PodcastSubsection): The current subsection being discussed
        background_info (list): List of Wikipedia document objects with research material
        draft_discussion (list): List of previous Question and Answer objects
        interviewer_chain (LLMChain): The LangChain chain for generating questions

    Returns:
        Question: A structured Question object containing the generated question text
    """

    background_info = "\n\n".join([format_wikipedia_document(d) for d in background_info])
    logger.info(f"[ask_question]: 背景信息提取量= {len(background_info)}")

    ask_question =  interviewer_chain.invoke({
        'topic': topic,
        'outline': outline.as_str,
        'section': section.title,
        'subsection': subsection.title,
        'background_info':background_info,
        'conversation_history': format_conversation_history(draft_discussion)
    })

    return ask_question

@retry_with_exponential_backoff(max_retries=10, base_delay=2.0)
def answer_question(topic: str,
                    outline: PodcastOutline,
                    section: PodcastSection,
                    subsection: PodcastSubsection,
                    background_info: list, 
                    draft_discussion: list,
                    retriever: VectorStoreRetriever,
                    interviewee_chain: LLMChain) -> Answer:
    """
    Generate an answer to the current interview question.

    Uses LangChain and an LLM to generate a natural, informative response based on the 
    retrieved background information and conversation context. The response stays focused
    on the current subsection topic while maintaining a conversational tone.

    Args:
        topic (str): The main podcast topic
        outline (PodcastOutline): The structured outline for the episode
        section (PodcastSection): The current section being discussed 
        subsection (PodcastSubsection): The current subsection being discussed
        draft_discussion (list): List of previous Question and Answer objects
        retriever (VectorStoreRetriever): Retriever for getting relevant background info
        interviewee_chain (LLMChain): The LangChain chain for generating answers

    Returns:
        Answer: A structured Answer object containing the generated response text
    """
    
    background_information=content_search(research_topic=draft_discussion[-1].question,
                                          context="\n\n".join([format_wikipedia_document(d) for d in background_info])
                                         )

    logger.info(f"[answer_question]:背景信息提取量= {len(background_information)}")

    answer_prompt = interviewee_chain.invoke({
        'topic': topic,
        'outline': outline.as_str,
        'section': section.title,
        'subsection': subsection.title,
        'word_count': 100,
        'background_information': background_information,
        'conversation_history': format_conversation_history(draft_discussion),
        'question': draft_discussion[-1].as_str
    })

    return answer_prompt

def discuss(config: PodcastConfig,
            topic: str, 
            outline: PodcastOutline, 
            background_info: List[Document], 
            vector_store: InMemoryVectorStore, 
            qa_rounds: int,
            base_url: Optional[str] = None,
            language: str = 'en') -> list:
    """
    模拟播客讨论，通过多轮问答生成自然流畅的对话内容。

    该函数协调生成播客访谈中的提问与回答，使用不同的语言模型链分别处理采访者和受访者角色，
    并通过速率限制控制API调用频率。讨论内容按照播客大纲结构展开，每个子章节通过多轮问答进行深入探讨。

    Args:
        config (PodcastConfig): 播客配置对象，包含模型参数等设置
        topic (str): 播客的主要话题
        outline (PodcastOutline): 包含章节和子章节的大纲结构
        background_info (List[Document]): 包含背景资料的文档列表（如维基百科内容）
        vector_store (InMemoryVectorStore): 存储索引研究内容的向量数据库
        qa_rounds (int): 每个子章节中问答交互的轮数
        base_url (str, optional): 可选的基础URL，用于兼容OpenAI接口的API服务

    Returns:
        list: 由交替出现的Question和Answer对象组成的讨论内容列表
    """
    logger.info(f"正在模拟关于：{topic} 的讨论...")

    # Try to load interviewer prompt from local storage first, fallback to Hub
    try:
        interviewer_prompt = get_local_prompt("podcast_interviewer_role", language)
        logger.info(f"Got prompt from local storage: podcast_interviewer_role ({language})")
    except Exception as e:
        logger.warning(f"Failed to load prompt from local storage: {e}. Falling back to Hub.")
        interviewer_prompthub_path = "evandempsey/podcast_interviewer_role:bc03af97"
        interviewer_prompt = hub.pull(interviewer_prompthub_path)
        logger.info(f"Got prompt from hub: {interviewer_prompthub_path}")

    # Try to load interviewee prompt from local storage first, fallback to Hub
    try:
        interviewee_prompt = get_local_prompt("podcast_interviewee_role", language)
        logger.info(f"Got prompt from local storage: podcast_interviewee_role ({language})")
    except Exception as e:
        logger.warning(f"Failed to load prompt from local storage: {e}. Falling back to Hub.")
        interviewee_prompthub_path = "evandempsey/podcast_interviewee_role:0832c140"
        interviewee_prompt = hub.pull(interviewee_prompthub_path)
        logger.info(f"Got prompt from hub: {interviewee_prompthub_path}")

    rate_limiter = InMemoryRateLimiter(
        requests_per_second=0.2,
        check_every_n_seconds=0.1,
        max_bucket_size=10
    )

    interviewer_llm = get_long_context_llm(config, rate_limiter, base_url)
    interviewee_llm = get_long_context_llm(config, rate_limiter, base_url)
    interviewer_chain = interviewer_prompt | interviewer_llm.with_structured_output(Question)
    interviewee_chain = interviewee_prompt | interviewee_llm.with_structured_output(Answer)

    retriever = vector_store.as_retriever(k=5)

    draft_discussion = []

    for section in outline.sections:
        for subsection in section.subsections:
            logger.info(f"Discussing section '{section.title}' subsection '{subsection.title}'")
            for _ in range(qa_rounds):
                draft_discussion.append(ask_question(
                    topic, 
                    outline, 
                    section,
                    subsection,
                    background_info, 
                    draft_discussion, 
                    interviewer_chain
                ))
                draft_discussion.append(answer_question(
                    topic,
                    outline,
                    section,
                    subsection,
                    background_info,
                    draft_discussion,
                    retriever,
                    interviewee_chain
                ))

    return draft_discussion


def write_draft_script(config: PodcastConfig,
                       topic: str, 
                       outline: PodcastOutline, 
                       background_info: List[Document], 
                       deep_info: List[Document], 
                       qa_rounds: int,
                       base_url: Optional[str] = None,
                       language: str = 'en'):
    """
    Write a complete draft podcast script through simulated Q&A discussion.

    This function orchestrates the generation of a podcast script by:
    1. Creating a vector store from background research and deep dive articles
    2. Splitting content into manageable chunks for retrieval
    3. Simulating an interview-style discussion with alternating questions and answers
    
    Args:
        topic (str): The main topic of the podcast episode
        outline (PodcastOutline): Structured outline containing sections and subsections
        background_info (list): List of Wikipedia document objects with background research
        deep_info (list): List of specialized articles for in-depth discussion
        qa_rounds (int): Number of question-answer exchanges per subsection
        base_url (str, optional): Base URL for OpenAI-compatible APIs
        language (str): Language for prompts ('en' for English, 'zh' for Chinese)

    Returns:
        list: Alternating Question and Answer objects representing the complete discussion

    The function uses LangChain and GPT-4 to generate natural-sounding dialogue,
    with the vector store enabling relevant information retrieval for detailed responses.
    The resulting script follows the outline structure while maintaining conversational flow.
    """
    logger.info(f"Writing podcast script on: {topic}")

    logger.info("Creating vector store for documents.")
    text_splitter = RecursiveCharacterTextSplitter(
        chunk_size=1000,
        chunk_overlap=200,
        length_function=len,
        separators=["\n\n", "\n", " ", ""]
    )

    # Process background Wikipedia articles
    background_texts = []
    for doc in background_info:
        background_texts.append(doc.page_content)
    
    # Process deep research articles
    deep_texts = []
    for article in deep_info:
        deep_texts.append(article.page_content)

    # Combine all texts and split into chunks
    all_texts = background_texts + deep_texts # background_info与deep_info是一样的
    chunks = text_splitter.create_documents(all_texts)

    # Create vector store
    embeddings = get_embeddings_model(config, base_url=base_url)
    vector_store = InMemoryVectorStore.from_documents(
        documents=chunks,
        embedding=embeddings
    )

    draft_script = discuss(config, topic, outline, background_info, vector_store, qa_rounds, base_url, language)
    return draft_script


@retry_with_exponential_backoff(max_retries=10, base_delay=2.0)
def rewrite_script_section(section: list, rewriter_chain) -> list:
    """
    Rewrite a section of the podcast script to improve flow and naturalness.

    Takes a section of the draft script (a sequence of Question/Answer exchanges) and uses 
    the rewriter chain to improve the conversational flow, word choice, and overall quality
    while maintaining the core content and structure.

    Args:
        section (list): List of Question/Answer objects representing a script section
        rewriter_chain (LLMChain): Chain configured with prompt and model for rewriting

    Returns:
        list: List of dictionaries containing rewritten lines with structure:
            {
                'speaker': str,  # Speaker identifier ('Interviewer' or 'Interviewee')
                'text': str      # Rewritten line content
            }
    """
    rewritten = rewriter_chain.invoke({
        "script": format_conversation_history(section)
    })

    return [{'speaker': line.speaker, 'text': line.text} for line in rewritten.lines]


def write_final_script(config: PodcastConfig, topic: str, draft_script: list, batch_size: int = 4, base_url: Optional[str] = None, language: str = 'en') -> list:
    """
    Rewrite a draft podcast script to improve flow, naturalness and quality.

    Takes a draft script consisting of Question/Answer exchanges and processes it in batches,
    using an LLM to improve the conversational flow, word choice, and overall quality while 
    maintaining the core content and structure. The script is processed in batches to manage
    context length and rate limits.

    Args:
        draft_script (list): List of Question/Answer objects representing the full draft script
        batch_size (int, optional): Number of Q/A exchanges to process in each batch. Defaults to 4.
        base_url (str, optional): Base URL for OpenAI-compatible APIs
        language (str): Language for prompts ('en' for English, 'zh' for Chinese)

    Returns:
        list: List of dictionaries containing the rewritten script lines with structure:
            {
                'speaker': str,  # Speaker identifier ('Interviewer' or 'Interviewee') 
                'text': str      # Rewritten line content
            }
    """
    logger.info("Processing draft script in batches")

    # Try to load rewriter prompt from local storage first, fallback to Hub
    try:
        rewriter_prompt = get_local_prompt("podcast_rewriter", language)
        logger.info(f"Got prompt from local storage: podcast_rewriter ({language})")
    except Exception as e:
        logger.warning(f"Failed to load prompt from local storage: {e}. Falling back to Hub.")
        rewriter_prompthub_path = "evandempsey/podcast_rewriter:181421e2"
        rewriter_prompt = hub.pull(rewriter_prompthub_path)
        logger.info(f"Got prompt from hub: {rewriter_prompthub_path}")

    rate_limiter = InMemoryRateLimiter(
        requests_per_second=0.2,
        check_every_n_seconds=0.1,
        max_bucket_size=10
    )

    long_context_llm = get_long_context_llm(config, rate_limiter, base_url)
    rewriter_chain = rewriter_prompt | long_context_llm.with_structured_output(Script)
    
    final_script = []
    
    # Process script in batches of bath_size
    for i in range(0, len(draft_script), batch_size):
        logger.info(f"Rewriting lines {i+1} to {i+batch_size} of {len(draft_script)}")
        batch = draft_script[i:i + batch_size]
        final_script.extend(rewrite_script_section(batch, rewriter_chain))

    # Add intro line
    final_script.insert(0, {
        'speaker': 'Interviewer',
        'text': config.intro.format(topic=topic, podcast_name=config.podcast_name)
    })

    # Add outro line
    final_script.append({
        'speaker': 'Interviewer',
        'text': config.outro.format(topic=topic, podcast_name=config.podcast_name)
    })
        
    return final_script
