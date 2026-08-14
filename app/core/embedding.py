"""Embedding 服务.

支持两种向量化后端:
  - dashscope: 默认, 使用 text-embedding-v4
  - ollama: 本地 Ollama, 推荐 bge-m3

两种后端都实现 LangChain Embeddings 接口, 所以上层 Milvus/RAG 逻辑不用改。
切换 embedding 模型后必须重建 Milvus collection, 不能混用旧向量。
"""

from functools import lru_cache
from typing import List

import httpx
from langchain_core.embeddings import Embeddings
from langchain_openai import OpenAIEmbeddings
from loguru import logger

from app.config import settings
from app.exceptions import EmbeddingError


class OllamaEmbeddings(Embeddings):
    """LangChain Embeddings adapter for Ollama `/api/embed`."""

    def __init__(
        self,
        *,
        base_url: str,
        model: str,
        batch_size: int,
        timeout_sec: float,
    ) -> None:
        self.base_url = base_url.rstrip("/")
        self.model = model
        self.batch_size = max(1, batch_size)
        self.timeout_sec = max(1.0, timeout_sec)

    def embed_documents(self, texts: List[str]) -> List[List[float]]:
        """Embed a list of texts using Ollama."""
        if not texts:
            return []

        vectors: List[List[float]] = []
        for i in range(0, len(texts), self.batch_size):
            batch = texts[i : i + self.batch_size]
            vectors.extend(self._embed_batch(batch))
        return vectors

    def embed_query(self, text: str) -> List[float]:
        """Embed one query text."""
        vectors = self.embed_documents([text])
        if not vectors:
            raise EmbeddingError("Ollama embedding 返回空向量")
        return vectors[0]

    def _embed_batch(self, texts: List[str]) -> List[List[float]]:
        url = f"{self.base_url}/api/embed"
        payload = {"model": self.model, "input": texts}
        try:
            with httpx.Client(timeout=self.timeout_sec) as client:
                response = client.post(url, json=payload)
                response.raise_for_status()
                data = response.json()
        except httpx.HTTPStatusError as exc:
            detail = exc.response.text[:500] if exc.response is not None else ""
            raise EmbeddingError(
                f"Ollama embedding HTTP {exc.response.status_code}: {detail}"
            ) from exc
        except Exception as exc:
            raise EmbeddingError(
                f"Ollama embedding 调用失败: {type(exc).__name__}: {exc}"
            ) from exc

        embeddings = data.get("embeddings")
        if not isinstance(embeddings, list) or not embeddings:
            raise EmbeddingError(f"Ollama embedding 响应缺少 embeddings 字段: {data}")
        if len(embeddings) != len(texts):
            raise EmbeddingError(
                f"Ollama embedding 数量不匹配: input={len(texts)}, output={len(embeddings)}"
            )
        return [[float(x) for x in vector] for vector in embeddings]


class LocalTfidfEmbeddings(Embeddings):
    """LangChain Embeddings adapter using sklearn TfidfVectorizer (offline, no model download).

    Uses character n-grams + word n-grams for cross-lingual keyword-aware vectors.
    Fixed dimension via TruncatedSVD. Works without internet.
    """

    def __init__(self, *, dim: int = 768) -> None:
        import warnings
        warnings.filterwarnings("ignore", category=UserWarning)
        from sklearn.feature_extraction.text import TfidfVectorizer
        from sklearn.decomposition import TruncatedSVD
        self._dim = min(dim, 768)
        self._vectorizer = TfidfVectorizer(
            analyzer="char_wb",
            ngram_range=(2, 4),
            max_features=8192,
            lowercase=True,
        )
        self._svd = TruncatedSVD(n_components=self._dim, random_state=42)
        self._fitted = False

    def _ensure_fit(self, texts: List[str]) -> None:
        if self._fitted:
            return
        logger.info(f"Fitting TF-IDF vectorizer on {len(texts)} docs...")
        sparse = self._vectorizer.fit_transform(texts)
        n_features = sparse.shape[1]
        actual_dim = min(self._dim, n_features - 1) if n_features > 1 else min(self._dim, n_features)
        if actual_dim < 1:
            actual_dim = 1
        if actual_dim < self._dim:
            self._svd = TruncatedSVD(n_components=actual_dim, random_state=42)
            logger.info(f"TF-IDF SVD dim adjusted: {self._dim} → {actual_dim} (n_features={n_features})")
        self._svd.fit(sparse)
        self._fitted = True
        logger.info(f"TF-IDF embedding ready: dim={actual_dim}")

    def embed_documents(self, texts: List[str]) -> List[List[float]]:
        if not texts:
            return []
        self._ensure_fit(texts)
        sparse = self._vectorizer.transform(texts)
        dense = self._svd.transform(sparse)
        # Normalize
        import numpy as np
        norms = np.linalg.norm(dense, axis=1, keepdims=True)
        norms[norms == 0] = 1.0
        return (dense / norms).tolist()

    def embed_query(self, text: str) -> List[float]:
        vecs = self.embed_documents([text])
        if not vecs:
            raise EmbeddingError("TF-IDF embedding 返回空向量")
        return vecs[0]


class LocalSTEmbeddings(Embeddings):
    """LangChain Embeddings adapter for local sentence-transformers."""

    def __init__(self, *, model_name: str, device: str = "cpu", batch_size: int = 16) -> None:
        from sentence_transformers import SentenceTransformer
        logger.info(f"Loading local embedding model: {model_name} (device={device})")
        self._model = SentenceTransformer(model_name, device=device)
        self._batch_size = batch_size

    def embed_documents(self, texts: List[str]) -> List[List[float]]:
        if not texts:
            return []
        all_vectors: List[List[float]] = []
        for i in range(0, len(texts), self._batch_size):
            batch = texts[i : i + self._batch_size]
            vectors = self._model.encode(batch, normalize_embeddings=True)
            all_vectors.extend(vectors.tolist())
        return all_vectors

    def embed_query(self, text: str) -> List[float]:
        vectors = self.embed_documents([text])
        if not vectors:
            raise EmbeddingError("Local embedding 返回空向量")
        return vectors[0]


@lru_cache(maxsize=1)
def get_embeddings() -> Embeddings:
    """获取 Embedding 实例 (单例).

    Returns:
        Embeddings: LangChain Embeddings 接口的实例

    Raises:
        EmbeddingError: 如果配置不完整无法创建
    """
    provider = settings.embedding_provider
    if provider == "local":
        logger.info("创建本地 TF-IDF Embedding (离线, 无需下载模型)")
        return LocalTfidfEmbeddings(dim=768)
    if provider == "ollama":
        logger.info(
            f"创建 Ollama Embedding 客户端: model={settings.ollama_embedding_model}, "
            f"dim={settings.ollama_embedding_dim}, base_url={settings.ollama_base_url}"
        )
        return OllamaEmbeddings(
            base_url=settings.ollama_base_url,
            model=settings.ollama_embedding_model,
            batch_size=settings.ollama_embedding_batch_size,
            timeout_sec=settings.ollama_embedding_timeout_sec,
        )

    if not settings.dashscope_api_key:
        raise EmbeddingError("DASHSCOPE_API_KEY 未配置, 无法创建 Embedding 客户端")

    logger.info(
        f"创建 Embedding 客户端: model={settings.dashscope_embedding_model}, "
        f"dim={settings.dashscope_embedding_dim}"
    )

    return OpenAIEmbeddings(
        model=settings.dashscope_embedding_model,
        api_key=settings.dashscope_api_key,  # type: ignore[arg-type]
        base_url=settings.dashscope_base_url,
        dimensions=settings.dashscope_embedding_dim,
        check_embedding_ctx_length=False,  # DashScope 无 tiktoken, 关掉检查
        # DashScope text-embedding-v4 单次最多 10 个文本, 超过会 400.
        # OpenAIEmbeddings 默认 chunk_size=2048 会把所有文本一次发出去, 必须降到 10.
        chunk_size=10,
    )
