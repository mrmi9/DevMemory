import unittest

from app.services.document_parser import detect_document_kind


class DocumentDetectionTests(unittest.TestCase):
    def test_detect_document_kind_from_common_upload_extensions(self):
        self.assertEqual(detect_document_kind("network.pdf", "application/pdf"), "pdf")
        self.assertEqual(detect_document_kind("notes.docx", ""), "word")
        self.assertEqual(detect_document_kind("chapter.md", "text/markdown"), "markdown")
        self.assertEqual(detect_document_kind("scan.png", "image/png"), "image")
        self.assertEqual(detect_document_kind("photo.jpeg", "image/jpeg"), "image")

    def test_detect_document_kind_rejects_unsupported_files(self):
        with self.assertRaisesRegex(ValueError, "Unsupported"):
            detect_document_kind("archive.zip", "application/zip")


if __name__ == "__main__":
    unittest.main()
