"""Utility functions for working with embeddings models.

This module provides functionality for loading and managing embeddings models,
which are used to convert text into vector representations. Currently supports
OpenAI embeddings and ModelScope embeddings with potential to expand to other providers.

Functions:
    get_embeddings_model: Returns an initialized embeddings model based on config.
"""


import logging
import os
from langchain_openai import OpenAIEmbeddings
from langchain_community.embeddings import DashScopeEmbeddings

from podcast_llm.config import PodcastConfig
from podcast_llm.utils.siliconflow_embeddings import SiliconFlowEmbeddings

logger = logging.getLogger(__name__)


def get_embeddings_model(config: PodcastConfig, base_url: str = None, api_key: str = None):
    """Get the configured embeddings model instance.

    Args:
        config (PodcastConfig): Configuration object containing embeddings settings
        base_url (str, optional): Base URL for OpenAI-compatible APIs
        api_key (str, optional): API key for the embeddings service

    Returns:
        BaseEmbeddings: Initialized embeddings model instance based on config.embeddings_model.
            Currently supports 'openai' which returns OpenAIEmbeddings and 'dashscope' for 
            ModelScope embeddings.
            Defaults to OpenAIEmbeddings if model type not recognized.
    """
    # Default models
    models = {
        'openai': OpenAIEmbeddings,
        'dashscope': DashScopeEmbeddings,
        'siliconcloud': SiliconFlowEmbeddings
    }

    # Check if we're using DashScope (ModelScope)
    logger.info(f"Using embeddings model: {config.embeddings_model} ...")

    if config.embeddings_model == 'dashscope':
        dashscope_api_key = api_key or os.getenv("DASHSCOPE_API_KEY")
        if not dashscope_api_key:
            raise ValueError("DASHSCOPE_API_KEY is required for DashScope embeddings but not provided.")

        return DashScopeEmbeddings(
            model="text-embedding-v4",
            dashscope_api_key=dashscope_api_key
        )

    elif config.embeddings_model == 'siliconcloud':
        # Initialize embedding model
        return SiliconFlowEmbeddings(
            base_url="https://api.siliconflow.cn/v1/embeddings",
            api_key=os.getenv("SILICONFLOW_API_KEY"),
            model="BAAI/bge-m3"
        )

    else:
        # Default to OpenAIEmbeddings
        model_class = models.get(config.embeddings_model, OpenAIEmbeddings)
        return model_class()


