import unittest

from app.services.embeddings import HashEmbeddingProvider


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


if __name__ == "__main__":
    unittest.main()
