# docs/

This directory holds your entire LaTeX project. It is set up automatically by the `latex_architect` agent when you say **"počni pisati"** for the first time.

## Structure (after setup)

```
docs/
├── main.tex          ← root document (\input{} chapters)
├── references.bib    ← BibTeX database
├── chapters/         ← individual chapter .tex files
├── figures/          ← images, diagrams, graphs
├── tables/           ← complex tables as standalone .tex files
└── code/             ← code listings for display in the document
```

## How to start

Tell your AI agent:
```
počni pisati
```
`latex_architect` will:
1. Read `STATE.md` and `project.yaml` for project context.
2. Copy the correct template from `~/.agentbrain/templates/` into this directory.
3. Replace placeholders (project name, year, etc.).
4. Compile the empty template to verify everything works.
5. Hand off to `writer` for content.

## Building the PDF

```powershell
.\.ai\scripts\helpers\build-docs.ps1    # Windows
./.ai/scripts/helpers/build-docs.sh    # Linux / macOS
```

The generated PDF appears in `docs/` and is then copied to `dist/<version>/`.
