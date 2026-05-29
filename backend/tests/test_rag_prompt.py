import unittest

from app.services.rag import RetrievedChunk, build_rag_prompt


class RagPromptTests(unittest.TestCase):
    def test_build_rag_prompt_includes_question_context_and_citation_rule(self):
        prompt = build_rag_prompt(
            question="帮我总结 SNMP 协议考试重点",
            chunks=[
                RetrievedChunk(
                    chunk_id=1,
                    document_title="网络管理.pdf",
                    course_title="计算机网络",
                    text="SNMP 使用管理站和代理，常见考试点包括 MIB、OID、Get、Set、Trap。",
                    page_number=12,
                    similarity=0.88,
                )
            ],
        )

        self.assertIn("帮我总结 SNMP 协议考试重点", prompt)
        self.assertIn("网络管理.pdf", prompt)
        self.assertIn("第 12 页", prompt)
        self.assertIn("引用来源", prompt)
        self.assertIn("不知道", prompt)


if __name__ == "__main__":
    unittest.main()
