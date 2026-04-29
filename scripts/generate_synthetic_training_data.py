from __future__ import annotations

import argparse
from dataclasses import dataclass
from datetime import datetime, timedelta, timezone
from pathlib import Path

import numpy as np
import pandas as pd


@dataclass(frozen=True)
class ProfileTemplate:
    name: str
    weight: float
    phq9_range: tuple[int, int]
    gad7_range: tuple[int, int]
    rosenberg_range: tuple[int, int]
    bigfive_range: tuple[int, int]
    mood_choices: tuple[str, ...]
    trend_range: tuple[int, int]


PROFILE_TEMPLATES = (
    ProfileTemplate(
        name="low_risk",
        weight=0.40,
        phq9_range=(0, 5),
        gad7_range=(0, 5),
        rosenberg_range=(14, 20),
        bigfive_range=(12, 20),
        mood_choices=("Calm", "Neutral"),
        trend_range=(-6, 2),
    ),
    ProfileTemplate(
        name="moderate_risk",
        weight=0.35,
        phq9_range=(6, 12),
        gad7_range=(5, 12),
        rosenberg_range=(9, 16),
        bigfive_range=(8, 16),
        mood_choices=("Neutral", "Stressed", "Anxious"),
        trend_range=(-2, 5),
    ),
    ProfileTemplate(
        name="high_risk",
        weight=0.25,
        phq9_range=(13, 24),
        gad7_range=(11, 21),
        rosenberg_range=(2, 11),
        bigfive_range=(4, 12),
        mood_choices=("Stressed", "Anxious", "Low"),
        trend_range=(1, 10),
    ),
)


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(
        description="Generate dev-only synthetic assessment rows for ML training."
    )
    parser.add_argument(
        "--rows",
        type=int,
        default=10000,
        help="Number of synthetic assessment rows to generate.",
    )
    parser.add_argument(
        "--users",
        type=int,
        default=1200,
        help="Approximate number of synthetic users to simulate.",
    )
    parser.add_argument(
        "--seed",
        type=int,
        default=42,
        help="Random seed for reproducibility.",
    )
    parser.add_argument(
        "--output",
        type=str,
        default=str(Path("data") / "generated" / "synthetic_assessments.csv"),
        help="CSV output path.",
    )
    return parser.parse_args()


def weighted_template_choice(rng: np.random.Generator) -> ProfileTemplate:
    weights = np.array([template.weight for template in PROFILE_TEMPLATES], dtype=float)
    weights = weights / weights.sum()
    index = int(rng.choice(len(PROFILE_TEMPLATES), p=weights))
    return PROFILE_TEMPLATES[index]


def bounded_score(rng: np.random.Generator, low: int, high: int, jitter: int = 2) -> int:
    midpoint = (low + high) / 2
    sampled = int(round(rng.normal(loc=midpoint, scale=max(1.0, (high - low) / 5))))
    sampled += int(rng.integers(-jitter, jitter + 1))
    return int(np.clip(sampled, low, high))


def build_synthetic_rows(row_count: int, user_count: int, seed: int) -> pd.DataFrame:
    rng = np.random.default_rng(seed)
    user_ids = np.arange(100000, 100000 + user_count)
    attempt_counters: dict[int, int] = {}
    rows: list[dict] = []
    attempt_id = 1
    base_time = datetime.now(timezone.utc) - timedelta(days=365)

    for _ in range(row_count):
        template = weighted_template_choice(rng)
        user_id = int(rng.choice(user_ids))
        attempt_number = attempt_counters.get(user_id, 0) + 1
        attempt_counters[user_id] = attempt_number

        created_at = base_time + timedelta(hours=int(rng.integers(0, 24 * 365)))
        phq9 = bounded_score(rng, *template.phq9_range)
        gad7 = bounded_score(rng, *template.gad7_range)
        rosenberg = bounded_score(rng, *template.rosenberg_range)
        bigfive = bounded_score(rng, *template.bigfive_range)
        mood_label = str(rng.choice(template.mood_choices))
        trend = int(rng.integers(template.trend_range[0], template.trend_range[1] + 1))

        rows.append(
            {
                "user_id": user_id,
                "attempt_id": attempt_id,
                "attempt_number": attempt_number,
                "created_at": created_at.isoformat(),
                "mood_label": mood_label,
                "phq9": phq9,
                "gad7": gad7,
                "rosenberg": rosenberg,
                "bigfive": bigfive,
                "trend": trend,
            }
        )
        attempt_id += 1

    df = pd.DataFrame(rows).sort_values(["user_id", "attempt_number", "attempt_id"]).reset_index(drop=True)
    return df


def main() -> None:
    args = parse_args()
    output_path = Path(args.output)
    output_path.parent.mkdir(parents=True, exist_ok=True)

    synthetic_df = build_synthetic_rows(
        row_count=args.rows,
        user_count=args.users,
        seed=args.seed,
    )
    synthetic_df.to_csv(output_path, index=False)

    class_counts = (synthetic_df["phq9"] >= 10).astype(int).value_counts().sort_index().to_dict()

    print(f"Generated rows: {len(synthetic_df)}")
    print(f"Output file: {output_path.resolve()}")
    print(f"Unique users: {synthetic_df['user_id'].nunique()}")
    print(f"Class distribution by PHQ9>=10: {class_counts}")


if __name__ == "__main__":
    main()
