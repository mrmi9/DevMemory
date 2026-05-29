import re


def serialize_study_card_row(card) -> dict:
    last_reviewed_at = getattr(card, "last_reviewed_at", None)
    next_review_at = getattr(card, "next_review_at", None)
    return {
        "id": card.id,
        "course_id": card.course_id,
        "front": card.front,
        "back": card.back,
        "source": card.source,
        "mastery": card.mastery,
        "review_count": getattr(card, "review_count", 0) or 0,
        "last_reviewed_at": last_reviewed_at.isoformat() if last_reviewed_at else None,
        "next_review_at": next_review_at.isoformat() if next_review_at else None,
        "created_at": card.created_at.isoformat(),
    }


def serialize_generated_question_row(question) -> dict:
    return {
        "id": question.id,
        "course_id": question.course_id,
        "question_type": question.question_type,
        "prompt": question.prompt,
        "answer": question.answer,
        "explanation": question.explanation,
        "created_at": question.created_at.isoformat(),
    }


def serialize_wrong_note_row(note) -> dict:
    return {
        "id": note.id,
        "course_id": note.course_id,
        "title": note.title,
        "original_question": note.original_question,
        "user_answer": note.user_answer,
        "correct_answer": note.correct_answer,
        "analysis": note.analysis,
        "tags": note.tags or [],
        "created_at": note.created_at.isoformat(),
    }


def build_wrong_note_from_question(question) -> dict:
    prompt = question.prompt.strip()
    answer = question.answer.strip()
    explanation = question.explanation.strip()
    title = prompt[:197] + "..." if len(prompt) > 200 else prompt
    return {
        "course_id": question.course_id,
        "title": title,
        "original_question": prompt,
        "user_answer": "",
        "correct_answer": answer,
        "analysis": explanation,
        "tags": ["generated-question", question.question_type],
    }


def parse_generated_cards(content: str) -> list[tuple[str, str]]:
    cards: list[tuple[str, str]] = []
    current_question = ""
    current_answer_lines: list[str] = []
    for raw_line in content.splitlines():
        line = raw_line.strip()
        if not line:
            continue
        line = _strip_marker_emphasis(line)
        if _is_card_heading(line):
            continue
        lower = line.lower()
        if lower.startswith("q:") or lower.startswith("question:"):
            if current_question and current_answer_lines:
                cards.append((current_question, "\n".join(current_answer_lines).strip()))
            current_question = line.split(":", 1)[1].strip()
            current_answer_lines = []
            continue
        if lower.startswith("a:") or lower.startswith("answer:"):
            current_answer_lines = [line.split(":", 1)[1].strip()]
            continue
        if current_answer_lines:
            current_answer_lines.append(line)
    if current_question and current_answer_lines:
        cards.append((current_question, "\n".join(current_answer_lines).strip()))
    return [(front, back) for front, back in cards if front and back]


def parse_generated_questions(content: str) -> list[dict]:
    normalized = content.strip()
    if not normalized:
        return []
    parsed = _parse_marked_question_blocks(normalized)
    if parsed:
        return parsed
    return [
        {
            "question_type": "mixed",
            "prompt": "Generated question set",
            "answer": normalized,
            "explanation": "",
        }
    ]


def _parse_marked_question_blocks(content: str) -> list[dict]:
    questions: list[dict] = []
    current = _empty_question()
    section = ""
    for raw_line in content.splitlines():
        line = raw_line.strip()
        if not line:
            continue
        line = _strip_marker_emphasis(line)
        marker, value = _split_question_marker(line)
        if marker == "prompt":
            if _has_question_content(current):
                questions.append(_finalize_question(current))
            current = _empty_question()
            current["prompt"] = value
            section = "prompt"
            continue
        if marker == "answer":
            current["answer"] = value
            section = "answer"
            continue
        if marker == "explanation":
            current["explanation"] = value
            section = "explanation"
            continue
        if section in {"prompt", "answer", "explanation"}:
            current[section] = _append_line(current[section], line)
    if _has_question_content(current):
        questions.append(_finalize_question(current))
    return [question for question in questions if question["prompt"] and question["answer"]]


def _empty_question() -> dict:
    return {"question_type": "mixed", "prompt": "", "answer": "", "explanation": ""}


def _has_question_content(question: dict) -> bool:
    return bool(question["prompt"] or question["answer"] or question["explanation"])


def _finalize_question(question: dict) -> dict:
    return {
        "question_type": question["question_type"],
        "prompt": question["prompt"].strip(),
        "answer": question["answer"].strip(),
        "explanation": question["explanation"].strip(),
    }


def _split_question_marker(line: str) -> tuple[str, str]:
    normalized = line.lstrip("-*0123456789.、)） ")
    patterns = [
        ("prompt", r"^(?:q|question|prompt|题目|问题|试题)[:：]\s*(.+)$"),
        ("answer", r"^(?:a|answer|答案|参考答案)[:：]\s*(.*)$"),
        ("explanation", r"^(?:explanation|analysis|解析|说明)[:：]\s*(.*)$"),
    ]
    for marker, pattern in patterns:
        match = re.match(pattern, normalized, flags=re.IGNORECASE)
        if match:
            return marker, match.group(1).strip()
    return "", line


def _append_line(existing: str, line: str) -> str:
    if not existing:
        return line
    return f"{existing}\n{line}"


def _strip_marker_emphasis(line: str) -> str:
    return re.sub(r"^\*{1,2}([^:*]+:)\*{1,2}", r"\1", line).strip()


def _is_card_heading(line: str) -> bool:
    plain = line.strip("* ").lower()
    return plain.startswith("card ") or plain.startswith("卡片 ")
