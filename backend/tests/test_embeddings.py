import unittest

import pytest

from app.services.embeddings import HashEmbeddingProvider, OpenAICompatibleEmbeddingProvider, get_embedding_provider


class EmbeddingTests(unittest.TestCase):
    def test_hash_embedding_provider_returns_stable_fixed_size_vectors(self):
        provider = HashEmbeddingProvider(dimensions=8)

        first = provider.embed(["SNMP 协议", "SNMP 协议"])
        second = provider.embed(["SNMP 协议"])

        self.assertEqual(first[0], first[1])
        self.assertEqual(first[0], second[0])
        self.assertEqual(len(first[0]), 8)
        self.assertLess(abs(sum(value * value for value in first[0]) - 1.0), 0.000001)

    def test_hash_embedding_provider_keeps_different_texts_distinguishable(self):
        provider = HashEmbeddingProvider(dimensions=8)

        vectors = provider.embed(["SNMP 协议", "TCP 拥塞控制"])

        self.assertNotEqual(vectors[0], vectors[1])


def test_get_embedding_provider_uses_configured_hash_dimensions():
    provider = get_embedding_provider("hash", dimensions=16)

    assert isinstance(provider, HashEmbeddingProvider)
    assert provider.dimensions == 16
    assert len(provider.embed(["SNMP"])[0]) == 16


def test_get_embedding_provider_rejects_unsupported_provider():
    with pytest.raises(ValueError, match="Unsupported embedding provider"):
        get_embedding_provider("unknown")


class FakeEmbeddingResponse:
    def raise_for_status(self):
        pass

    def json(self):
        return {
            "data": [
                {"embedding": [0.1, 0.2, 0.3]},
                {"embedding": [0.4, 0.5, 0.6]},
            ]
        }


class FakeEmbeddingClient:
    def __init__(self):
        self.requests = []

    def __enter__(self):
        return self

    def __exit__(self, exc_type, exc, traceback):
        pass

    def post(self, url, json, headers):
        self.requests.append({"url": url, "json": json, "headers": headers})
        return FakeEmbeddingResponse()


def test_openai_compatible_embedding_provider_posts_embedding_request():
    fake_client = FakeEmbeddingClient()
    provider = OpenAICompatibleEmbeddingProvider(
        api_key="embedding-key",
        base_url="https://embedding.example/v1",
        model="bge-m3",
        dimensions=3,
        client_factory=lambda timeout: fake_client,
    )

    vectors = provider.embed(["first", "second"])

    assert vectors == [[0.1, 0.2, 0.3], [0.4, 0.5, 0.6]]
    assert fake_client.requests == [
        {
            "url": "https://embedding.example/v1/embeddings",
            "json": {"model": "bge-m3", "input": ["first", "second"], "dimensions": 3},
            "headers": {"Authorization": "Bearer embedding-key", "Content-Type": "application/json"},
        }
    ]


if __name__ == "__main__":
    unittest.main()
