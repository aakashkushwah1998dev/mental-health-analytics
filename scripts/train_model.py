from pathlib import Path
import argparse
import sys

sys.path.append(str(Path(__file__).resolve().parents[1]))

from src.ml.training import train_torch_model, write_ml_update  # noqa: E402


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description="Train the PyTorch mental-health risk model.")
    parser.add_argument(
        "--synthetic-only",
        action="store_true",
        help="Train only from generated synthetic training data.",
    )
    parser.add_argument(
        "--auto-generate-synthetic",
        action="store_true",
        help="Generate synthetic training CSV automatically if it does not exist.",
    )
    return parser.parse_args()


def main() -> None:
    args = parse_args()
    artifacts = train_torch_model(
        synthetic_only=args.synthetic_only,
        auto_generate_synthetic=args.auto_generate_synthetic,
    )
    update_path = write_ml_update(artifacts)
    print(f"Model saved to: {artifacts.model_path}")
    print(f"Metadata saved to: {artifacts.metadata_path}")
    print(f"Metrics saved to: {artifacts.metrics_path}")
    print(f"Training rows: {artifacts.training_rows}")
    print(f"Real rows: {artifacts.real_training_rows}")
    print(f"Synthetic rows: {artifacts.synthetic_training_rows}")
    print(f"Accuracy: {artifacts.accuracy:.4f}")
    print(f"ML update report refreshed: {update_path}")


if __name__ == "__main__":
    main()
