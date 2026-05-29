from __future__ import annotations

import argparse
import re
import textwrap
from pathlib import Path
from typing import Iterable, List


def _strip_latex(tex: str) -> str:
    tex = re.sub(r"\\begin\{(?:figure|table)\}.*?\\end\{(?:figure|table)\}", "", tex, flags=re.S)
    tex = re.sub(r"\\begin\{verbatim\}(.*?)\\end\{verbatim\}", r"\1", tex, flags=re.S)
    tex = re.sub(r"\\documentclass.*?\n", "", tex)
    tex = re.sub(r"\\usepackage.*?\n", "", tex)
    tex = re.sub(r"\\title\{([^}]*)\}", r"\n\1\n", tex)
    tex = re.sub(r"\\author\{([^}]*)\}", r"\1\n", tex)
    tex = re.sub(r"\\date\{([^}]*)\}", r"\1\n", tex)
    tex = re.sub(r"\\section\{([^}]*)\}", r"\n\n\1\n", tex)
    tex = re.sub(r"\\subsection\{([^}]*)\}", r"\n\1\n", tex)
    tex = re.sub(r"\\begin\{abstract\}", "\nAbstract\n", tex)
    tex = tex.replace("\\end{abstract}", "")
    tex = re.sub(r"\\cite\{[^}]*\}", "[citation]", tex)
    tex = re.sub(r"\\label\{[^}]*\}", "", tex)
    tex = re.sub(r"\\ref\{[^}]*\}", "reference", tex)
    tex = re.sub(r"\\bibliographystyle\{[^}]*\}", "", tex)
    tex = re.sub(r"\\bibliography\{[^}]*\}", "", tex)
    tex = tex.replace("\\maketitle", "")
    tex = tex.replace("\\begin{document}", "").replace("\\end{document}", "")
    tex = tex.replace("\\%", "%").replace("\\ldots", "...").replace("$\\times$", "x")
    tex = re.sub(r"\$([^$]*)\$", r"\1", tex)
    tex = re.sub(r"\\[a-zA-Z]+\*?(?:\[[^]]*\])?(?:\{([^}]*)\})?", r"\1", tex)
    tex = tex.replace("{", "").replace("}", "")
    tex = re.sub(r"\n{3,}", "\n\n", tex)
    return tex.strip()


def _wrapped_lines(text: str, width: int = 95) -> List[str]:
    lines: List[str] = []
    for paragraph in text.splitlines():
        if not paragraph.strip():
            lines.append("")
            continue
        lines.extend(textwrap.wrap(paragraph, width=width, replace_whitespace=False))
    return lines


def render_pdf(tex_path: str | Path, output_path: str | Path, figure_dir: str | Path) -> None:
    import matplotlib.image as mpimg
    import matplotlib.pyplot as plt
    from matplotlib.backends.backend_pdf import PdfPages

    tex = Path(tex_path).read_text(encoding="utf-8")
    text = _strip_latex(tex)
    lines = _wrapped_lines(text)
    output_path = Path(output_path)
    output_path.parent.mkdir(parents=True, exist_ok=True)
    figures = [
        "tokens_success_by_method.png",
        "success_vs_compression_ratio.png",
        "latency_by_method.png",
        "failure_categories.png",
    ]

    with PdfPages(output_path) as pdf:
        per_page = 48
        for page_start in range(0, len(lines), per_page):
            fig = plt.figure(figsize=(8.5, 11))
            fig.patch.set_facecolor("white")
            y = 0.96
            for line in lines[page_start : page_start + per_page]:
                if not line:
                    y -= 0.018
                    continue
                fig.text(0.08, y, line, ha="left", va="top", fontsize=9.2, family="DejaVu Sans")
                y -= 0.018
            fig.text(0.5, 0.035, f"Draft PDF fallback page {page_start // per_page + 1}", ha="center", fontsize=8)
            pdf.savefig(fig)
            plt.close(fig)

        for figure_name in figures:
            path = Path(figure_dir) / figure_name
            if not path.exists():
                continue
            image = mpimg.imread(path)
            fig, ax = plt.subplots(figsize=(8.5, 6.5))
            ax.imshow(image)
            ax.axis("off")
            fig.tight_layout()
            pdf.savefig(fig)
            plt.close(fig)


def main() -> None:
    parser = argparse.ArgumentParser(description="Render a simple PDF fallback from the LaTeX draft.")
    parser.add_argument("--tex", default="paper/main.tex")
    parser.add_argument("--output", default="paper/main.pdf")
    parser.add_argument("--figure-dir", default="paper/figures")
    args = parser.parse_args()
    render_pdf(args.tex, args.output, args.figure_dir)
    print(f"wrote fallback PDF to {args.output}")


if __name__ == "__main__":
    main()
