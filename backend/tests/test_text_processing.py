import unittest

from app.services.chunking import chunk_text, clean_text


class TextProcessingTests(unittest.TestCase):
    def test_clean_text_normalizes_whitespace_without_losing_chinese_text(self):
        raw = "  SNMP   协议\n\n用于   网络管理。\r\n考试重点：OID。 "

        self.assertEqual(clean_text(raw), "SNMP 协议\n用于 网络管理。\n考试重点：OID。")

    def test_chunk_text_splits_with_overlap_and_metadata(self):
        text = "一二三四五六七八九十ABCDEFGHIJ"

        chunks = chunk_text(text, max_chars=10, overlap=2)

        self.assertEqual([chunk.text for chunk in chunks], ["一二三四五六七八九十", "九十ABCDEFGH", "GHIJ"])
        self.assertEqual([chunk.index for chunk in chunks], [0, 1, 2])
        self.assertEqual(chunks[1].char_start, 8)
        self.assertEqual(chunks[1].char_end, 18)

    def test_chunk_text_rejects_overlap_that_is_not_smaller_than_chunk_size(self):
        with self.assertRaisesRegex(ValueError, "overlap"):
            chunk_text("abc", max_chars=3, overlap=3)


if __name__ == "__main__":
    unittest.main()
