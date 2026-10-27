# Glossary

The ubiquitous language for this skill repository.
Use each Title Case term for its defined meaning rather than introducing a synonym.
Add new domain terms here in the same change that introduces them.
Give each term its own alphabetical H2 and a node in the relationship diagram.

```mermaid
flowchart LR
    M["Maintainer"]:::people
    R["Requirement"]:::rule
    A["Agent"]:::people
    D["Dialect"]:::record
    DR["Decision Record"]:::record
    CS["Canonical Skill"]:::info
    P["Plugin"]:::pipeline
    GF["Generated File"]:::record
    S["Signal"]:::info
    N["Noise"]:::forbidden
    M -- states --> R
    R -- guides --> A
    A -- uses --> D
    D -- organises --> DR
    DR -->|records| R
    CS -- implements --> R
    CS -- mirrored into --> P
    P -- contains --> GF
    DR -- renders --> GF
    S -- improves safeguards in --> CS
    N -- improves review filters for --> CS
    classDef people fill:#1e40af,stroke:#93c5fd,color:#fff,stroke-width:2px
    classDef info fill:#92400e,stroke:#fcd34d,color:#fff,stroke-width:2px
    classDef rule fill:#6d28d9,stroke:#c4b5fd,color:#fff,stroke-width:2px
    classDef forbidden fill:#b91c1c,stroke:#fca5a5,color:#fff,stroke-width:2px
    classDef pipeline fill:#047857,stroke:#6ee7b7,color:#fff,stroke-width:2px
    classDef record fill:#334155,stroke:#cbd5e1,color:#fff,stroke-width:2px
```

## Agent

A coding assistant working under [AGENTS.md](AGENTS.md) and applicable scoped instructions.

## Canonical Skill

The authoritative skill directory under `skills/`, containing runtime instructions and supporting resources.
Plugins contain generated copies of Canonical Skills.

## Decision Record

A decision and its reasoning captured in the root [ADR surface](adrs/index.md) or an existing scoped decision log.
An accepted argument remains immutable; a later Decision Record can supersede it.

## Dialect

The declared documentation layout and naming conventions in [docs/CONVENTIONS.md](docs/CONVENTIONS.md).

## Generated File

A file produced from an authoritative source by a documented regeneration command.
Edit the source, then regenerate the file.

## Maintainer

The person responsible for the repository's Requirements and accepted decisions.

## Noise

Review feedback that lacks actionable evidence or distracts from the pull request's intent.
The resulting lesson improves the filter for future reviews.

## Plugin

An installable composition of Canonical Skills and optional hooks, declared in `plugins/composition.yaml`.

## Requirement

A behavior or constraint explicitly required by the Maintainer.

## Signal

Review feedback supported by evidence and worth acting on within the pull request's intent.
The resulting fix strengthens safeguards against that category of problem.
