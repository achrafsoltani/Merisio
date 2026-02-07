# The MSD Book

**Merisio Schema Definition — Language Reference & Implementation Guide**

A comprehensive guide to MSD, the text-based DSL for defining MERISE conceptual data models.

## Table of Contents

### Front Matter

- [Preface](00-preface.md)

### Part I: The Language

- [Chapter 1: Introduction](01-introduction.md) — What MSD is, why it exists, and how it compares to alternatives
- [Chapter 2: Quick Start](02-quick-start.md) — Write your first MSD file and convert it to a Merisio project
- [Chapter 3: Syntax Reference](03-syntax-reference.md) — Complete reference for every MSD construct

### Part II: The Implementation

- [Chapter 4: The Lexer](04-the-lexer.md) — Tokenisation, context sensitivity, and error detection
- [Chapter 5: The Parser](05-the-parser.md) — Recursive descent parsing and error recovery
- [Chapter 6: The Builder](06-the-builder.md) — Project construction, semantic validation, and "did you mean?" suggestions
- [Chapter 7: The Auto-Layout Algorithm](07-auto-layout.md) — Fruchterman-Reingold force-directed graph placement
- [Chapter 8: CLI and GUI Integration](08-integration.md) — The `parse` command and the Import MSD menu
- [Chapter 9: Error Handling and Recovery](09-error-handling.md) — The error system, panic-mode recovery, and message quality

### Part III: Quality

- [Chapter 10: Testing](10-testing.md) — Test strategy, organisation, and patterns (64 tests)

### Appendices

- [Appendix A: Formal Grammar](A-grammar.md) — EBNF grammar specification
- [Appendix B: Data Type Reference](B-type-reference.md) — Detailed guide to all 13 supported types
- [Appendix C: Glossary](C-glossary.md) — Definitions of key terms

## About

This book is part of the [Merisio](https://github.com/achrafsoltani/Merisio) project — a visual MCD (Conceptual Data Model) editor with automatic MLD generation and PostgreSQL SQL export.

MSD version: 1.0 | Merisio version: 1.3.1
