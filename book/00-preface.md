# Preface

## About This Book

This book is the definitive guide to **MSD** (Merisio Schema Definition), a domain-specific language for defining MERISE conceptual data models as plain text. MSD is part of the Merisio project — a visual MCD editor with automatic MLD generation and PostgreSQL SQL export.

The book serves two audiences:

1. **Users** who want to write MCDs as text files instead of (or alongside) the graphical editor. Chapters 1–3 and the appendices are all you need.

2. **Developers** who want to understand, extend, or learn from the implementation. Chapters 4–10 walk through every module in the pipeline, from tokenisation to force-directed layout.

## Conventions

Throughout this book:

- `monospace` text refers to code, filenames, or terminal commands.
- **Bold** text introduces new terms or highlights key concepts.
- Blocks labelled with a filename (e.g. `src/msd/lexer.py`) contain excerpts from the Merisio source code.
- MSD examples use the `.msd` file extension.
- The term "MCD" refers to a *Modèle Conceptuel de Données* (Conceptual Data Model) in the MERISE methodology.

## Prerequisites

- Familiarity with database modelling concepts (entities, attributes, primary keys, relationships)
- For the implementation chapters: intermediate Python knowledge (dataclasses, enums, generators)
- For the layout chapter: basic understanding of graph theory and iterative algorithms

## How to Read This Book

The chapters are designed to be read in order, but each one is largely self-contained:

| Chapters | Audience | Topic |
|----------|----------|-------|
| 1–3 | All users | The DSL: syntax, semantics, and usage |
| 4–6 | Developers | The pipeline: lexer → parser → builder |
| 7 | Developers | The auto-layout algorithm |
| 8 | Developers | CLI and GUI integration |
| 9 | Developers | Error handling and recovery |
| 10 | Developers | Testing strategy |
| A–C | All users | Grammar, type reference, glossary |

## Acknowledgements

MSD was designed as an improvement over the Mocodo DSL, addressing its limitations: implicit primary keys, missing data types, and ambiguous single-line syntax. The Merisio project itself was inspired by AnalyseSI, a Java-based MERISE tool widely used in French computer science education.

---

*Achraf Soltani, February 2026*
