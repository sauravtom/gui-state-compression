# arXiv Submission Packet

Prepared files:

- `metadata.md`: title, abstract, category suggestion, and comments field.
- `../dist/arxiv/gui-state-compression-arxiv.tar.gz`: upload-ready source bundle.

Recommended submission path:

1. Go to <https://arxiv.org/submit>.
2. Start a new submission from the author account.
3. Use primary category `cs.AI` unless you prefer another category.
4. Upload `dist/arxiv/gui-state-compression-arxiv.tar.gz`.
5. Confirm the top-level TeX file is `main.tex`.
6. Verify the arXiv-generated PDF.
7. Paste the title, abstract, comments, and categories from `metadata.md`.
8. Submit after confirming author name, affiliation, license, and moderation/endorsement requirements.

Notes:

- arXiv prefers TeX/LaTeX source for long-term portability.
- arXiv submissions must come from registered authors and new categories may require endorsement.
- The source bundle only includes files required to compile the paper, avoiding repository code, logs, virtualenv files, and hidden metadata.
