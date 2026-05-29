from app.services.llm import DeepSeekClient


async def generate_cards(topic: str, context: str, count: int = 8) -> str:
    prompt = f"""基于以下资料，为主题“{topic}”生成 {count} 张复习卡片。
每张卡片用“Q:”和“A:”表示，答案要适合考前复习。

资料：
{context}
"""
    return await DeepSeekClient().complete(prompt)


async def generate_questions(topic: str, context: str, count: int = 6) -> str:
    prompt = f"""基于以下资料，为主题“{topic}”生成 {count} 道考试题。
请包含选择题、名词解释、简答题，并给出答案与解析。

资料：
{context}
"""
    return await DeepSeekClient().complete(prompt)


async def analyze_wrong_note(question: str, user_answer: str, correct_answer: str = "") -> str:
    prompt = f"""请整理下面这道错题，输出：错误原因、相关知识点、正确解法、复习建议和标签。

题目：
{question}

我的答案：
{user_answer}

参考答案：
{correct_answer or "未提供"}
"""
    return await DeepSeekClient().complete(prompt)


async def generate_mindmap(topic: str, context: str) -> str:
    prompt = f"""请基于资料生成 Markmap 兼容的 Markdown 思维导图。
根节点必须是“# {topic}”，下级节点使用二级、三级标题或列表。

资料：
{context}
"""
    return await DeepSeekClient().complete(prompt)
