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


@dataclass(frozen=True)
class RetrievalQuality:
    confidence: str
    notes: list[str]


def evaluate_retrieval_quality(chunks: list[RetrievedChunk]) -> RetrievalQuality:
    if not chunks:
        return RetrievalQuality(confidence="none", notes=["没有检索到可用资料，回答应明确提示资料不足。"])

    max_similarity = max(chunk.similarity for chunk in chunks)
    notes: list[str] = []
    if max_similarity < 0.25:
        notes.append(f"最高相似度较低（{max_similarity:.2f}），回答只能作为弱参考。")
        confidence = "weak"
    elif max_similarity < 0.6:
        notes.append(f"最高相似度中等（{max_similarity:.2f}），需要核对引用内容。")
        confidence = "medium"
    elif len(chunks) < 2:
        notes.append("引用资料较少，建议补充更多相关资料后再确认结论。")
        confidence = "medium"
    else:
        notes.append("引用资料较充分，可以结合引用片段复核答案。")
        confidence = "high"
    return RetrievalQuality(confidence=confidence, notes=notes)


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
