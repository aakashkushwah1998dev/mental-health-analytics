import pytest

from src.services.scoring import QuestionScore, compute_category_total, score_answer


@pytest.mark.parametrize(
    ("raw_value", "is_reversed", "expected"),
    [
        (0, False, 0),
        (1, False, 1),
        (2, False, 2),
        (3, False, 3),
        (0, True, 3),
        (1, True, 2),
        (2, True, 1),
        (3, True, 0),
    ],
)
def test_score_answer_handles_forward_and_reverse_scoring(raw_value: int, is_reversed: bool, expected: int) -> None:
    assert score_answer(raw_value, is_reversed) == expected


def test_compute_category_total_uses_reverse_score_rules() -> None:
    rows = [
        QuestionScore(question_id=1, category_name="Rosenberg", is_reversed=False),
        QuestionScore(question_id=2, category_name="Rosenberg", is_reversed=True),
        QuestionScore(question_id=3, category_name="Rosenberg", is_reversed=True),
    ]
    responses = {
        1: 3,
        2: 0,
        3: 2,
    }

    assert compute_category_total(rows, responses) == 7


def test_score_answer_rejects_values_outside_supported_scale() -> None:
    with pytest.raises(ValueError):
        score_answer(4, False)
