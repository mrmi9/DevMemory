from dataclasses import dataclass
from datetime import datetime

import pytest
from pydantic import ValidationError

from app.schemas import StudyCardMasteryUpdate
from app.services.study_library import (
    build_wrong_note_from_question,
    parse_generated_cards,
    parse_generated_questions,
    serialize_generated_question_row,
    serialize_study_card_row,
    serialize_wrong_note_row,
)


@dataclass
class FakeWrongNote:
    id: str = "wrong-1"
    course_id: str | None = "course-1"
    title: str = "SNMP trap"
    original_question: str = "What is an SNMP trap?"
    user_answer: str = "A polling request"
    correct_answer: str = "A device-initiated notification"
    analysis: str = "Confused polling with event notification."
    tags: list[str] | None = None
    created_at: datetime = datetime(2026, 5, 29, 13, 45, 0)


def test_serialize_wrong_note_row_exposes_review_fields():
    payload = serialize_wrong_note_row(FakeWrongNote(tags=["SNMP", "trap"]))

    assert payload == {
        "id": "wrong-1",
        "course_id": "course-1",
        "title": "SNMP trap",
        "original_question": "What is an SNMP trap?",
        "user_answer": "A polling request",
        "correct_answer": "A device-initiated notification",
        "analysis": "Confused polling with event notification.",
        "tags": ["SNMP", "trap"],
        "created_at": "2026-05-29T13:45:00",
    }


@dataclass
class FakeStudyCard:
    id: str = "card-1"
    course_id: str | None = "course-1"
    front: str = "What does SNMP manage?"
    back: str = "Network devices and their management data."
    source: str = "ai"
    mastery: int = 0
    created_at: datetime = datetime(2026, 5, 29, 14, 5, 0)


@dataclass
class FakeGeneratedQuestion:
    id: str = "question-1"
    course_id: str | None = "course-1"
    question_type: str = "mixed"
    prompt: str = "Explain SNMP trap."
    answer: str = "It is a device-initiated notification."
    explanation: str = "Trap is event-driven."
    created_at: datetime = datetime(2026, 5, 29, 14, 25, 0)


def test_serialize_study_card_row_exposes_review_fields():
    payload = serialize_study_card_row(FakeStudyCard())

    assert payload == {
        "id": "card-1",
        "course_id": "course-1",
        "front": "What does SNMP manage?",
        "back": "Network devices and their management data.",
        "source": "ai",
        "mastery": 0,
        "created_at": "2026-05-29T14:05:00",
    }


def test_serialize_generated_question_row_exposes_review_fields():
    payload = serialize_generated_question_row(FakeGeneratedQuestion())

    assert payload == {
        "id": "question-1",
        "course_id": "course-1",
        "question_type": "mixed",
        "prompt": "Explain SNMP trap.",
        "answer": "It is a device-initiated notification.",
        "explanation": "Trap is event-driven.",
        "created_at": "2026-05-29T14:25:00",
    }


def test_build_wrong_note_from_question_prefills_review_content():
    payload = build_wrong_note_from_question(
        FakeGeneratedQuestion(
            question_type="short-answer",
            prompt="  Explain SNMP trap.  ",
            answer="  It is a device-initiated notification.  ",
            explanation="  Trap is event-driven.  ",
        )
    )

    assert payload == {
        "course_id": "course-1",
        "title": "Explain SNMP trap.",
        "original_question": "Explain SNMP trap.",
        "user_answer": "",
        "correct_answer": "It is a device-initiated notification.",
        "analysis": "Trap is event-driven.",
        "tags": ["generated-question", "short-answer"],
    }


def test_parse_generated_cards_reads_q_a_blocks():
    cards = parse_generated_cards(
        """
Q: What is an SNMP trap?
A: A device-initiated notification.

Q: What is MIB?
A: A managed object information model.
"""
    )

    assert cards == [
        ("What is an SNMP trap?", "A device-initiated notification."),
        ("What is MIB?", "A managed object information model."),
    ]


def test_parse_generated_questions_keeps_unstructured_output_as_review_set():
    questions = parse_generated_questions(
        """
1. Multiple choice: Which UDP port does SNMP Trap use?
Answer: 162.
Explanation: Managers receive trap notifications on UDP 162.
"""
    )

    assert questions == [
        {
            "question_type": "mixed",
            "prompt": "Generated question set",
            "answer": "1. Multiple choice: Which UDP port does SNMP Trap use?\nAnswer: 162.\nExplanation: Managers receive trap notifications on UDP 162.",
            "explanation": "",
        }
    ]


def test_parse_generated_questions_splits_q_answer_explanation_blocks():
    questions = parse_generated_questions(
        """
Q: Which UDP port does SNMP Trap use?
Answer: 162.
Explanation: Managers receive trap notifications on UDP 162.

Q: What mode does SNMP Trap use?
Answer: Event-driven push.
Explanation: The agent sends a notification without manager polling.
"""
    )

    assert questions == [
        {
            "question_type": "mixed",
            "prompt": "Which UDP port does SNMP Trap use?",
            "answer": "162.",
            "explanation": "Managers receive trap notifications on UDP 162.",
        },
        {
            "question_type": "mixed",
            "prompt": "What mode does SNMP Trap use?",
            "answer": "Event-driven push.",
            "explanation": "The agent sends a notification without manager polling.",
        },
    ]


def test_parse_generated_questions_splits_chinese_marked_blocks():
    questions = parse_generated_questions(
        """
题目：SNMP Trap 的作用是什么？
答案：由代理主动通知管理站异常事件。
解析：Trap 是事件驱动，不需要管理站轮询。

题目：Trap 默认使用哪个 UDP 端口？
答案：162。
解析：管理站在 UDP 162 接收 Trap。
"""
    )

    assert questions == [
        {
            "question_type": "mixed",
            "prompt": "SNMP Trap 的作用是什么？",
            "answer": "由代理主动通知管理站异常事件。",
            "explanation": "Trap 是事件驱动，不需要管理站轮询。",
        },
        {
            "question_type": "mixed",
            "prompt": "Trap 默认使用哪个 UDP 端口？",
            "answer": "162。",
            "explanation": "管理站在 UDP 162 接收 Trap。",
        },
    ]


def test_parse_generated_cards_reads_markdown_bold_q_a_blocks():
    cards = parse_generated_cards(
        """
**Card 1**
**Q:** What is an SNMP trap?
**A:** A device-initiated notification.

**Card 2**
**Q:** What is MIB?
**A:** A managed object information model.
"""
    )

    assert cards == [
        ("What is an SNMP trap?", "A device-initiated notification."),
        ("What is MIB?", "A managed object information model."),
    ]


def test_study_card_mastery_update_accepts_only_review_scale():
    assert StudyCardMasteryUpdate(mastery=3).mastery == 3

    with pytest.raises(ValidationError):
        StudyCardMasteryUpdate(mastery=-1)

    with pytest.raises(ValidationError):
        StudyCardMasteryUpdate(mastery=6)
