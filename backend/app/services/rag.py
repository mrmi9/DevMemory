from dataclasses import dataclass


@dataclass(frozen=True)
class RetrievedChunk:
    chunk_id: int
    document_title: str
    course_title: str
    text: str
    page_number: int | None
    similarity: float
    document_id: str = ""


def build_rag_prompt(question: str, chunks: list[RetrievedChunk]) -> str:
    context_blocks = []
    for index, chunk in enumerate(chunks, start=1):
        page = f"第 {chunk.page_number} 页" if chunk.page_number else "页码未知"
        context_blocks.append(
            "\n".join(
                [
                    f"[资料 {index}] 课程：{chunk.course_title}",
                    f"文档：{chunk.document_title}，位置：{page}，相似度：{chunk.similarity:.3f}",
                    chunk.text,
                ]
            )
        )
    context = "\n\n".join(context_blocks) if context_blocks else "没有检索到可用资料。"
    return f"""你是一个严谨的个人学习知识库助手。
请只基于下面的课程资料回答问题；如果资料不足，请明确说“不知道”，并建议用户上传或选择更相关的资料。
回答需要结构清晰，适合复习考试。涉及结论时请在句末标注引用来源，例如：[资料 1]。

问题：
{question}

可用资料：
{context}

请输出：
1. 直接答案
2. 考试重点
3. 易错点
4. 引用来源
"""
