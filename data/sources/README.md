# data/sources/

Put your PDF sources here — books, lecture notes, papers.

Index them for RAG (Windows: swap `rag.sh` → `.\.ai\scripts\helpers\rag.ps1`):

```bash
./.ai/scripts/helpers/rag.sh ingest
```

Then query them:

```bash
./.ai/scripts/helpers/rag.sh query "Your question"
```

Files in this folder are tracked via **Git LFS**.
