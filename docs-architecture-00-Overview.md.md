# `docs/architecture/00-Overview.md`

# ContextLens Architecture Overview

**Version:** 0.1

**Status:** Draft

**Owner:** Architecture

---

# Purpose

This document defines the architectural vision of ContextLens.

It is the primary architectural reference for the project and serves as the foundation for every subsequent design document, ADR, specification, and implementation.

All architectural decisions should be consistent with the principles defined here.

---

# What is ContextLens?

ContextLens is a local-first observability platform for AI-powered development workflows.

It provides visibility into how AI prompts are constructed, how context is consumed, how tokens are used, and how requests flow between AI clients and LLM providers.

Rather than acting as another AI application, ContextLens acts as an intelligent observability layer.

Its purpose is to answer questions such as:

- Why did this request consume 40,000 tokens?
- Which files contributed to the context?
- Which resources were duplicated?
- Which prompts are inefficient?
- How can context be optimized without changing behavior?

---

# Architectural Vision

ContextLens is built around a simple philosophy:

> **Observe everything. Own nothing.**

The system should observe requests flowing through it without becoming tightly coupled to any AI provider, client, storage engine, or user interface.

Every external dependency must be replaceable.

The Core Domain must remain stable.

---

# Architectural Goals

- Provider agnostic
- Client agnostic
- Local-first
- Extensible
- Testable
- Observable
- Deterministic
- Low latency
- Low overhead
- AI-friendly architecture
- Documentation-first development

---

# Guiding Principles

## 1. Documentation First

Documentation is treated as the source of truth.

Code implements documentation—not the other way around.

---

## 2. Core Domain First

Business logic belongs in the Domain.

Frameworks and infrastructure exist to support the Domain.

---

## 3. Dependency Rule

Dependencies always point inward.

Adapters depend on Ports.

Ports depend on the Application layer.

The Application layer depends on the Domain.

The Domain depends on nothing.

---

## 4. Provider Independence

No component outside a provider adapter should understand provider-specific request formats.

All providers are normalized into canonical domain models.

---

## 5. Local First

ContextLens performs analysis locally whenever possible.

External services are optional.

The platform should remain useful without internet connectivity beyond the configured AI provider.

---

## 6. Deterministic Analysis

Observability must not require additional LLM requests.

Analysis should be reproducible and explainable.

---

# Architectural Style

ContextLens combines three complementary architectural patterns.

## Hexagonal Architecture

Hexagonal Architecture isolates business logic from infrastructure.

The Domain is protected by Ports and Adapters.

External systems communicate with the Core through well-defined interfaces.

Benefits:

- Testability
- Replaceable infrastructure
- Provider independence
- Long-term maintainability

---

## Event-Driven Architecture

Communication between major components occurs through domain events.

Examples include:

- RequestReceived
- ProviderDetected
- PromptParsed
- TokensCounted
- ResponseReceived
- UsageComputed
- RecommendationGenerated

Benefits:

- Loose coupling
- Plugin friendliness
- Easier feature expansion
- Independent processing pipelines

---

## Domain-Driven Design (Lite)

ContextLens adopts a lightweight domain model.

Core entities include:

- Session
- Request
- Response
- Prompt
- Context
- Usage
- Recommendation
- Provider Capability

The project intentionally avoids unnecessary enterprise complexity.

---

# Layered Architecture

```text
                 External Systems

     AI Clients • Providers • Storage • UI

                 ─────────────────────

                   Adapters Layer

                 ─────────────────────

                      Ports Layer

                 ─────────────────────

                 Application Layer

                 ─────────────────────

                     Domain Layer
```

---

# Responsibilities

## Domain

Defines business concepts and rules.

Contains no framework dependencies.

## Application

Implements use cases and orchestration.

Coordinates domain operations.

## Ports

Defines interfaces required by the application.

Examples:

- StoragePort
- ProviderPort
- DashboardPort
- TokenizerPort
- EventBusPort

## Adapters

Concrete implementations of ports.

Examples:

- SQLite
- FastAPI
- Rich/Textual
- Anthropic
- OpenAI
- Bedrock

---

# Canonical Models

Every provider request is transformed into a common representation before reaching the Core.

This prevents provider-specific logic from spreading across the codebase.

Canonical models include:

- CanonicalRequest
- CanonicalResponse
- CanonicalMessage
- CanonicalUsage
- CanonicalToolCall

---

# Capability-Based Providers

Providers expose capabilities instead of requiring type checks.

Examples:

- Streaming
- Tool Calling
- Vision
- Prompt Caching
- Reasoning Metadata
- Usage Reporting

Consumers ask what a provider supports—not which provider it is.

---

# Event Lifecycle

A typical request follows this lifecycle:

1. Request received
2. Provider detected
3. Request normalized
4. Tokens counted
5. Request forwarded
6. Response received
7. Usage computed
8. Events published
9. Session persisted
10. Dashboard updated
11. Analyzers executed
12. Recommendations generated

---

# Extensibility Strategy

ContextLens is designed to be extended through:

- Provider adapters
- Storage adapters
- Dashboard adapters
- Exporters
- Plugins
- Analyzers

New functionality should be added without modifying the Core Domain.

---

# Performance Philosophy

The observability layer should introduce minimal overhead.

Target objectives:

- Low memory usage
- Async-first processing
- Efficient local tokenization
- Minimal request latency
- Streaming support

Performance is considered a first-class architectural concern.

---

# Security Philosophy

ContextLens follows a privacy-first approach.

Principles include:

- Local processing by default
- No hidden telemetry
- Explicit export configuration
- Least-privilege design
- Clear separation of sensitive data

---

# Testing Philosophy

Every architectural layer must be independently testable.

Testing priorities:

1. Domain
2. Application
3. Ports
4. Adapters
5. End-to-end flows

The Core Domain should be executable without infrastructure dependencies.

---

# Documentation Philosophy

Documentation is treated as part of the product.

Every major component must include:

- Purpose
- Responsibilities
- Interfaces
- Diagrams
- Acceptance criteria
- Related ADRs

Architecture documentation evolves alongside the implementation.

---

# Future Evolution

The architecture intentionally leaves room for:

- Distributed deployments
- OpenTelemetry integration
- Prometheus exporters
- Kubernetes-native deployment
- Team collaboration
- Additional providers
- New analyzers
- Enterprise storage backends

These additions should not require changes to the Core Domain.

---

# Architecture Summary

ContextLens is designed as a provider-agnostic, local-first, event-driven observability platform built on Hexagonal Architecture.

The Core Domain remains independent of frameworks and infrastructure.

All external systems communicate through Ports and Adapters.

Canonical models ensure provider independence.

Events enable extensibility.

Documentation serves as the primary source of truth.

This document establishes the architectural foundation upon which all future ContextLens components will be designed and implemented.