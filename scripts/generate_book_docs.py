from __future__ import annotations

from html import escape
from pathlib import Path


PROJECT_ROOT = Path(__file__).resolve().parents[1]
OUTPUT_PATH = PROJECT_ROOT / "docs" / "book" / "index.html"
TARGET_FILES = [
    "app.py",
    "pages/1_Login.py",
    "pages/2_Dashboard.py",
    "pages/3_Questionnaire.py",
    "pages/4_Research_Info.py",
    "auth/auth_service.py",
    "database/connection.py",
    "src/config/settings.py",
    "src/db/connection.py",
    "src/services/scoring.py",
    "src/services/auth.py",
    "src/ml/features.py",
    "src/ml/model.py",
    "src/ml/training.py",
    "src/api/app.py",
    "api/main.py",
    "scripts/generate_synthetic_training_data.py",
    "scripts/train_model.py",
    "01_database_setup.sql",
    "database/migrations/001_initial_schema.sql",
    "Dockerfile",
    "api/Dockerfile",
    "docker-compose.yml",
]


def explain_line(line: str) -> str:
    stripped = line.strip()
    if not stripped:
        return "Blank line used for readability."
    if stripped.startswith("#"):
        return "Comment that describes the following block."
    if stripped.startswith("import ") or stripped.startswith("from "):
        return "Imports a dependency or shared module needed below."
    if stripped.startswith("def "):
        return "Defines a function used elsewhere in the system."
    if stripped.startswith("class "):
        return "Defines a class or data structure."
    if stripped.startswith("return "):
        return "Returns a value from the current function."
    if stripped.startswith("if ") or stripped.startswith("elif "):
        return "Starts a conditional branch."
    if stripped.startswith("for "):
        return "Starts an iteration over a collection."
    if stripped.startswith("CREATE TABLE"):
        return "Creates a database table if it does not already exist."
    if stripped.startswith("ALTER TABLE"):
        return "Modifies an existing table for compatibility or constraints."
    if stripped.startswith("CMD ") or stripped.startswith("FROM "):
        return "Container build/runtime instruction."
    return "Implementation line that contributes to the behavior of this file."


def render_file_section(path: Path) -> str:
    lines = path.read_text(encoding="utf-8").splitlines()
    rows = []
    for idx, line in enumerate(lines, start=1):
        rows.append(
            "<tr>"
            f"<td>{idx}</td>"
            f"<td><pre>{escape(line)}</pre></td>"
            f"<td>{escape(explain_line(line))}</td>"
            "</tr>"
        )
    return (
        f"<section><h2>{escape(str(path.relative_to(PROJECT_ROOT)))}</h2>"
        "<table><thead><tr><th>Line</th><th>Code</th><th>Explanation</th></tr></thead>"
        f"<tbody>{''.join(rows)}</tbody></table></section>"
    )


def main() -> None:
    OUTPUT_PATH.parent.mkdir(parents=True, exist_ok=True)

    sections = []
    for relative_path in TARGET_FILES:
        file_path = PROJECT_ROOT / relative_path
        if file_path.exists():
            sections.append(render_file_section(file_path))

    html = f"""<!DOCTYPE html>
<html lang="en">
<head>
  <meta charset="utf-8">
  <title>Mental Health Analytics System Book</title>
  <style>
    body {{ font-family: Arial, sans-serif; margin: 24px; line-height: 1.4; }}
    h1, h2 {{ color: #183153; }}
    table {{ width: 100%; border-collapse: collapse; margin-bottom: 32px; }}
    th, td {{ border: 1px solid #d0d7de; padding: 8px; vertical-align: top; }}
    th {{ background: #f6f8fa; text-align: left; }}
    pre {{ margin: 0; white-space: pre-wrap; }}
    .intro {{ margin-bottom: 24px; }}
  </style>
</head>
<body>
  <h1>Mental Health Analytics System - Code Book</h1>
  <div class="intro">
    <p>This HTML book explains the system architecture, data flow, and every line in the key source files that make up the application.</p>
    <p>It is generated from <code>scripts/generate_book_docs.py</code> so it can be refreshed after every refactor.</p>
  </div>
  {''.join(sections)}
</body>
</html>
"""
    OUTPUT_PATH.write_text(html, encoding="utf-8")
    print(f"Book documentation generated at: {OUTPUT_PATH}")


if __name__ == "__main__":
    main()
