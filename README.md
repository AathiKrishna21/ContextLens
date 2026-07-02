# docs/README.md

# ContextLens Engineering Knowledge Base

## Purpose

The `docs/` directory is the authoritative source of truth for ContextLens.

All architectural decisions, implementation details, engineering principles, and future evolution of the project are documented here before code is written.

This repository follows a **Documentation First** development methodology.

Every significant implementation should be traceable back to one or more documents within this directory.

---

# Documentation Hierarchy

The documentation is organized into layers, moving from high-level vision to implementation details.

```
Vision
    │
    ▼
Product Requirements (PRD)
    │
    ▼
Architecture
    │
    ▼
Architecture Decision Records (ADRs)
    │
    ▼
Component Specifications
    │
    ▼
Implementation Guides
    │
    ▼
Code
```

Each layer builds upon the previous one.

---

# Directory Structure

```
docs/
│
├── README.md
│
├── vision/
│   ├── VISION.md
│   ├── MISSION.md
│   ├── PRINCIPLES.md
│   └── ROADMAP.md
│
├── product/
│   ├── PRD.md
│   ├── Personas.md
│   ├── Competitive-Analysis.md
│   └── Use-Cases.md
│
├── architecture/
│   ├── 00-Overview.md
│   ├── 01-System-Architecture.md
│   ├── 02-Hexagonal-Architecture.md
│   ├── 03-Event-Driven-Architecture.md
│   ├── 04-Domain-Model.md
│   ├── 05-Component-Architecture.md
│   ├── 06-Canonical-Models.md
│   ├── 07-Provider-Architecture.md
│   ├── 08-Plugin-Architecture.md
│   ├── 09-Storage-Architecture.md
│   ├── 10-Deployment-Architecture.md
│   ├── 11-Security-Architecture.md
│   ├── 12-Performance-Architecture.md
│   └── diagrams/
│
├── adr/
│   ├── ADR-001-Documentation-First.md
│   ├── ADR-002-Hexagonal-Architecture.md
│   ├── ADR-003-Event-Driven-Core.md
│   ├── ADR-004-Canonical-Request-Model.md
│   ├── ADR-005-Capability-Based-Providers.md
│   ├── ADR-006-AsyncIO-First.md
│   ├── ADR-007-Dependency-Injection.md
│   ├── ADR-008-SQLite-MVP.md
│   ├── ADR-009-Local-First.md
│   ├── ADR-010-Deterministic-Analysis.md
│   └── ...
│
├── specs/
│   ├── proxy/
│   ├── analyzer/
│   ├── provider/
│   ├── storage/
│   ├── dashboard/
│   ├── tokenizer/
│   ├── plugins/
│   └── cli/
│
├── philosophy/
│   ├── Documentation-First.md
│   ├── Designing-for-AI-Contributors.md
│   ├── Local-First.md
│   ├── Everything-is-Replaceable-Except-the-Domain.md
│   └── Deterministic-Analysis.md
│
├── development/
│   ├── Coding-Standards.md
│   ├── Testing-Strategy.md
│   ├── Git-Workflow.md
│   ├── Release-Process.md
│   └── Code-Review-Checklist.md
│
└── ai/
    ├── Context.md
    ├── Architecture.md
    ├── Coding-Rules.md
    ├── Personas.md
    ├── Prompt-Library.md
    └── Review-Guidelines.md
```

---

# Documentation Standards

Every document in this repository should follow a consistent structure whenever applicable.

1. Purpose
2. Scope
3. Background
4. Requirements
5. Design
6. Alternatives Considered
7. Trade-offs
8. Risks
9. Future Evolution
10. References

This consistency makes the documentation easier for both humans and AI systems to understand.

---

# Source of Truth

The following precedence order applies when documentation conflicts:

1. ADRs
2. Architecture documents
3. Product Requirements
4. Component specifications
5. Implementation guides
6. Code

If code conflicts with the documented architecture, the discrepancy should be resolved through an ADR or documentation update before changing behavior.

---

# Guiding Principle

> Documentation is not an artifact produced after development.

> Documentation is the design from which development proceeds.