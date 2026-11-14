"""Choose a real embedding provider (API or local) and implement this contract."""
from typing import Protocol


class Embedder(Protocol):
    model_name: str
    dimensions: int

    def embed_documents(self, texts: list[str]) -> list[list[float]]:
        """Return one vector per input text, in the same order."""
        ...

    def embed_query(self, question: str) -> list[float]:
        """Return a query vector compatible with the stored document vectors."""
        ...


class MyEmbedder:
    """TODO: implement a provider adapter; do not silently fall back to mock vectors."""

    def __init__(self, model_name: str, revision: str, cache_folder: str, batch_size: int = 16) -> None:
        import torch
        from sentence_transformers import SentenceTransformer
        torch.manual_seed(42)
        torch.set_num_threads(4)
        self.model_name = model_name
        self.model = SentenceTransformer(model_name, revision=revision, cache_folder=cache_folder,
                                         device="cpu", local_files_only=True)
        self.dimensions = self.model.get_sentence_embedding_dimension()
        self.batch_size = batch_size
        self.max_observed_tokens = 0

    def _encode(self, texts: list[str], prefix: str) -> list[list[float]]:
        if not texts:
            return []
        inputs = [prefix + text for text in texts]
        lengths = [len(x) for x in self.model.tokenizer(inputs, truncation=False)["input_ids"]]
        self.max_observed_tokens = max(self.max_observed_tokens, max(lengths))
        if max(lengths) > self.model.max_seq_length:
            raise ValueError("Input exceeds model token limit; refusing silent truncation")
        return self.model.encode(inputs, batch_size=self.batch_size, normalize_embeddings=True,
                                 show_progress_bar=True).tolist()

    def embed_documents(self, texts: list[str]) -> list[list[float]]:
        return self._encode(texts, "passage: ")

    def embed_query(self, question: str) -> list[float]:
        return self._encode([question], "query: ")[0]
