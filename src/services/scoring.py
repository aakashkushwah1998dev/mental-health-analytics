from __future__ import annotations

from dataclasses import dataclass


MAX_LIKERT_SCORE = 3


@dataclass(frozen=True)
class QuestionScore:
    question_id: int
    category_name: str
    is_reversed: bool


def score_answer(raw_value: int, is_reversed: bool, *, max_score: int = MAX_LIKERT_SCORE) -> int:
    if raw_value < 0 or raw_value > max_score:
        raise ValueError(f"raw_value must be between 0 and {max_score}, got {raw_value}")
    return max_score - raw_value if is_reversed else raw_value


def compute_category_total(question_rows: list[QuestionScore], responses: dict[int, int]) -> int:
    total_score = 0
    for row in question_rows:
        raw_value = responses.get(row.question_id, 0)
        total_score += score_answer(raw_value, row.is_reversed)
    return total_score
