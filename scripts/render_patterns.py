"""Renders each theme pattern's example to docs/pattern-renders/<name>-<width>.png with
md2ui's CLI, so the patterns can be reviewed as pictures. `home` is composed from the
section patterns it lists, in its order. Run with the backend venv's Python, whose md2ui
is the release backend/requirements.txt pins:

    backend/.venv/bin/python scripts/render_patterns.py [--out DIR] [name ...]

`--out DIR` writes the pictures elsewhere, e.g. `docs/pattern-renders/before` to keep the
baseline of a change beside its result.
"""
import re
import subprocess
import sys
import tempfile
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
THEME = ROOT / "backend/md2ui_theme/THEME.md"
PATTERNS = THEME.parent / "patterns"
OUT = ROOT / "docs/pattern-renders"
# md2ui's CLI, from the venv whose Python runs this.
MD2UI = Path(sys.executable).parent / "md2ui"
WIDTHS = (1120, 390)
HOME = ["headline", "offer-cards", "track-card", "product-cards", "deal-rows", "home"]


def example(name: str) -> str:
    text = (PATTERNS / f"{name}.md").read_text()
    match = re.search(r"```markdown\n(.*?)\n```", text, re.S)
    if not match:
        raise SystemExit(f"{name}: no ```markdown example")
    return match.group(1)


def main(names: list[str], out_dir: Path = OUT) -> None:
    out_dir.mkdir(parents=True, exist_ok=True)
    names = names or sorted(p.stem for p in PATTERNS.glob("*.md"))
    for name in names:
        doc = "\n\n".join(example(n) for n in HOME) if name == "home" else example(name)
        with tempfile.TemporaryDirectory() as tmp:
            src = Path(tmp) / f"{name}.md"
            src.write_text(doc + "\n")
            check = subprocess.run([MD2UI, "check", src, "--theme", THEME], capture_output=True, text=True)
            issues = [l for l in check.stdout.splitlines() if l and not l.startswith("[") and "repeated-offer" not in l]
            for width in WIDTHS:
                out = out_dir / f"{name}-{width}.png"
                subprocess.run([MD2UI, "render", src, "--theme", THEME, "--width", str(width), "--out", out],
                               capture_output=True, check=True)
            print(f"{name}: ok" + "".join(f"\n  {i}" for i in issues))


if __name__ == "__main__":
    args = sys.argv[1:]
    out_dir = OUT
    if args[:1] == ["--out"]:
        out_dir, args = (ROOT / args[1]).resolve(), args[2:]
    main(args, out_dir)
