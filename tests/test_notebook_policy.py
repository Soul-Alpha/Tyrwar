import json
from pathlib import Path


NOTEBOOKS_DIR = Path(__file__).resolve().parents[1] / "notebooks"


def test_notebooks_are_thin_clean_interfaces() -> None:
    notebooks = sorted(NOTEBOOKS_DIR.glob("*.ipynb"))
    assert notebooks, "At least one governed notebook is expected"

    forbidden_fragments = {
        "MetaTrader5",
        "mt5.order_send",
        "mt5.login",
        "class TradingBot",
        "def calculate_rsi",
        "def generate_signal",
        "pandas_ta",
        "password=",
        "login=",
    }

    for notebook_path in notebooks:
        notebook = json.loads(notebook_path.read_text(encoding="utf-8"))
        code = "\n".join(
            "".join(cell.get("source", []))
            for cell in notebook.get("cells", [])
            if cell.get("cell_type") == "code"
        )

        for cell in notebook.get("cells", []):
            assert cell.get("execution_count") is None
            assert cell.get("outputs", []) == []

        assert "from tyrwar" in code
        for fragment in forbidden_fragments:
            assert fragment not in code, (
                f"{notebook_path.name} duplicates production logic or embeds sensitive runtime data: "
                f"{fragment}"
            )
