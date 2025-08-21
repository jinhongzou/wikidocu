import requests
import os
from typing import List
from langchain_core.embeddings import Embeddings
from langchain.text_splitter import RecursiveCharacterTextSplitter
import logging

logger = logging.getLogger(__name__)

class SiliconFlowEmbeddings(Embeddings):
    def __init__(
        self,
        api_key: str,
        base_url: str = "https://api.siliconflow.cn/v1/embeddings",
        model: str = "BAAI/bge-large-zh-v1.5",
        max_tokens: int = 512
    ):
        self.api_key = api_key
        self.base_url = base_url
        self.model = model
        self.max_tokens = max_tokens
        # 初始化文本分割器
        self.text_splitter = RecursiveCharacterTextSplitter(
            chunk_size=max_tokens,
            chunk_overlap=50,
            length_function=len,
            separators=["\n\n", "\n", ". ", " ", ""]
        )

    def embed_documents(self, texts: List[str]) -> List[List[float]]:
        """Embed a list of documents."""
        embeddings = []
        for text in texts:
            embedding = self.embed_query(text)
            embeddings.append(embedding)
        return embeddings

    def embed_query(self, text: str) -> List[float]:
        """Embed a query, handling long texts by chunking and averaging embeddings."""
        # 如果文本长度超过限制，进行分块处理
        if len(text) > self.max_tokens * 4:  # 简单的字符数检查
            logger.info(f"Text too long ({len(text)} chars), splitting into chunks...")
            # 使用文本分割器将长文本分割成块
            chunks = self.text_splitter.split_text(text)
            logger.info(f"Split text into {len(chunks)} chunks")
            
            # 获取每个块的嵌入并平均
            chunk_embeddings = []
            for i, chunk in enumerate(chunks):
                try:
                    chunk_embedding = self._get_embedding_for_chunk(chunk)
                    chunk_embeddings.append(chunk_embedding)
                    logger.info(f"Processed chunk {i+1}/{len(chunks)}")
                except Exception as e:
                    logger.warning(f"Failed to embed chunk {i+1}: {e}")
                    # 如果某个块失败，跳过它
                    continue
            
            if chunk_embeddings:
                # 对所有块的嵌入进行平均
                avg_embedding = self._average_embeddings(chunk_embeddings)
                return avg_embedding
            else:
                # 如果所有块都失败，抛出异常
                raise Exception("Failed to embed any chunk of the text")
        else:
            # 文本长度在限制内，直接处理
            return self._get_embedding_for_chunk(text)

    def _get_embedding_for_chunk(self, text: str) -> List[float]:
        """Get embedding for a single text chunk."""
        headers = {
            "Authorization": f"Bearer {self.api_key}",
            "Content-Type": "application/json"
        }
        
        payload = {
            "model": self.model,
            "input": text,
            "encoding_format": "float"
        }
        
        response = requests.post(
            self.base_url,
            json=payload,
            headers=headers
        )
        
        if response.status_code == 200:
            return response.json()["data"][0]["embedding"]
        else:
            raise Exception(f"Error in embedding: {response.text}")

    def _average_embeddings(self, embeddings: List[List[float]]) -> List[float]:
        """Average a list of embeddings."""
        if not embeddings:
            raise ValueError("Cannot average empty list of embeddings")
        
        # 计算平均嵌入
        avg_embedding = []
        for i in range(len(embeddings[0])):
            avg_value = sum(embedding[i] for embedding in embeddings) / len(embeddings)
            avg_embedding.append(avg_value)
        
        return avg_embedding

