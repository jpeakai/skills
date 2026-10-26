# Choose a flavour that fits the repository

Flavours size the organisation around a shared set of documents.
A shelving plan distinguishes gaps in that organisation from recommendations to change its scale.
This visual guide accompanies the complete [flavour reference](flavours.md).
Code font names an exact file, directory or flavour.

<details>
<summary>Guide contents</summary>

<!--TOC-->

- [Choose a flavour that fits the repository](#choose-a-flavour-that-fits-the-repository)
  - [Every flavour keeps the same core](#every-flavour-keeps-the-same-core)
  - [Choose a starting preset, preserve local decisions](#choose-a-starting-preset-preserve-local-decisions)
  - [Separate required fixes from optional graduation](#separate-required-fixes-from-optional-graduation)

<!--TOC-->

</details>

## Every flavour keeps the same core

What changes when a repository chooses a larger preset?
The core still covers orientation, contribution, coding standards, agent instructions, decisions and vocabulary.

```mermaid
%%{init: {"theme":"base","themeCSS":".edgeLabel rect { opacity: 1; fill: #334155; }","flowchart":{"htmlLabels":false},"themeVariables":{"primaryTextColor":"#ffffff","textColor":"#ffffff","lineColor":"#94a3b8","edgeLabelBackground":"#334155"}}}%%
flowchart LR
    C["Shared core documents<br/>and required links"]:::document
    C --> M["minimal<br/>Compact organisation"]:::preset
    C --> S["standard<br/>Separate contributor and topic docs"]:::preset
    C --> R["rigorous<br/>Categorised and scoped docs"]:::preset
    M --> D["Local dialect<br/>declared conventions and choices"]:::rule
    S --> D
    R --> D
    D --> P["Shelving plan<br/>gaps and graduation recommendations"]:::result
    classDef document fill:#1e40af,stroke:#dbeafe,color:#ffffff,stroke-width:2px
    classDef preset fill:#5b21b6,stroke:#ede9fe,color:#ffffff,stroke-width:2px
    classDef rule fill:#fef3c7,stroke:#b45309,color:#1e293b,stroke-width:2px
    classDef result fill:#065f46,stroke:#d1fae5,color:#ffffff,stroke-width:2px
    classDef decision fill:#92400e,stroke:#fef3c7,color:#ffffff,stroke-width:2px
```

**A smaller flavour makes the documents shorter and the layout flatter; it retains the core documents and links.**

<details>
<summary>Required core documents and the links between them</summary>

Which connections make the core usable by both people and agents?
The conventions link applies whenever that file exists.

```mermaid
%%{init: {"theme":"base","themeCSS":".edgeLabel rect { opacity: 1; fill: #334155; }","flowchart":{"htmlLabels":false},"themeVariables":{"primaryTextColor":"#ffffff","textColor":"#ffffff","lineColor":"#94a3b8","edgeLabelBackground":"#334155"}}}%%
flowchart LR
    R["README.md"]:::document --> C["CONTRIBUTING.md"]:::document
    C -->|follow before writing code| S["CODING_STANDARDS.md"]:::document
    A["AGENTS.md"]:::document -->|follow before writing code| S
    A -->|check before asking| D["ADR surface"]:::document
    A -->|canonical names and same-change updates| G["GLOSSARY.md"]:::document
    A -->|when present| V["docs/CONVENTIONS.md"]:::rule
    CL["CLAUDE.md<br/>only @AGENTS.md"]:::document -->|imports| A
    classDef document fill:#1e40af,stroke:#dbeafe,color:#ffffff,stroke-width:2px
    classDef preset fill:#5b21b6,stroke:#ede9fe,color:#ffffff,stroke-width:2px
    classDef rule fill:#fef3c7,stroke:#b45309,color:#1e293b,stroke-width:2px
    classDef result fill:#065f46,stroke:#d1fae5,color:#ffffff,stroke-width:2px
    classDef decision fill:#92400e,stroke:#fef3c7,color:#ffffff,stroke-width:2px
```

**Presence and links are both part of the core contract.**

</details>

The main layout differences are how readers reach the detail:

| Flavour | Human documentation | Agent and decision documentation |
|---|---|---|
| `minimal` | Sections in `README.md`, brief `CONTRIBUTING.md` | Root agent pair and a single `ADRs.md` log |
| `standard` | README hub, full contributor workflow, flat `docs/topic.md` files | `docs/CONVENTIONS.md`, scoped agent pairs where needed, declared decision layout |
| `rigorous` | Diátaxis categories, `docs/internals/`, directory README indexes | Per-package agent pairs, indexed decision files and linked scoped logs |

The [full comparison](flavours.md#the-three-flavours) also covers health files, glossary organisation and decision layouts.

## Choose a starting preset, preserve local decisions

How does init choose a flavour without overwriting an existing layout?
User rulings outrank declared conventions, observed practice and defaults, in that order.
Multiple teams, external contributors, regulation or a public platform suggest a rigorous context.

```mermaid
%%{init: {"theme":"base","themeCSS":".edgeLabel rect { opacity: 1; fill: #334155; }","flowchart":{"htmlLabels":false},"themeVariables":{"primaryTextColor":"#ffffff","textColor":"#ffffff","lineColor":"#94a3b8","edgeLabelBackground":"#334155"}}}%%
flowchart TD
    L["Preserve declared conventions<br/>and consistent observed practice"]:::rule
    L --> Q{"Flavour supplied?"}:::decision
    Q -->|yes| F["Use supplied flavour<br/>for undecided choices"]:::preset
    Q -->|no| H{"Rigorous context?"}:::decision
    H -->|yes| R["rigorous"]:::preset
    H -->|no| T{"Team with<br/>other consumers?"}:::decision
    T -->|yes| S["standard"]:::preset
    T -->|no| M["minimal"]:::preset
    F --> D["Record the dialect<br/>Mark defaults for maintainer veto"]:::result
    R --> D
    S --> D
    M --> D
    classDef document fill:#1e40af,stroke:#dbeafe,color:#ffffff,stroke-width:2px
    classDef preset fill:#5b21b6,stroke:#ede9fe,color:#ffffff,stroke-width:2px
    classDef rule fill:#fef3c7,stroke:#b45309,color:#1e293b,stroke-width:2px
    classDef result fill:#065f46,stroke:#d1fae5,color:#ffffff,stroke-width:2px
    classDef decision fill:#92400e,stroke:#fef3c7,color:#ffffff,stroke-width:2px
```

**A preset fills undecided choices; declared and consistently observed conventions keep their authority.**

For example, choosing `standard` for a repository with an established decision directory does not require moving that directory.
Init records the observed choice in the dialect instead.
See the [authority ladder](../SKILL.md#step-0-discover-the-dialect-every-mode) and [init workflow](../SKILL.md#init-mode).

## Separate required fixes from optional graduation

Does outgrowing a flavour make a compliant repository wrong?
Audit checks against the resolved dialect and reports scale changes separately in the shelving plan's **Graduation** section.
The two checks are independent: a repository can need both repairs and graduation recommendations.

```mermaid
%%{init: {"theme":"base","themeCSS":".edgeLabel rect { opacity: 1; fill: #334155; }","flowchart":{"htmlLabels":false},"themeVariables":{"primaryTextColor":"#ffffff","textColor":"#ffffff","lineColor":"#94a3b8","edgeLabelBackground":"#334155"}}}%%
flowchart TD
    A["Audit against the resolved dialect"]:::rule
    A --> G{"Required doc missing,<br/>misfiled or unlinked?"}:::decision
    A --> S{"Layout outgrown<br/>or mostly empty?"}:::decision
    G -->|yes| F["Shelving-plan finding<br/>Repair the documented gap"]:::result
    G -->|no| K["No change<br/>for this check"]:::result
    S -->|yes| R["Graduation recommendation<br/>Expand or consolidate the layout"]:::result
    S -->|no| K
    F --> U{"Maintainer authorises<br/>the proposed change?"}:::decision
    R --> U
    U -->|yes| P["Apply the authorised change"]:::result
    U -->|no| K
    classDef document fill:#1e40af,stroke:#dbeafe,color:#ffffff,stroke-width:2px
    classDef preset fill:#5b21b6,stroke:#ede9fe,color:#ffffff,stroke-width:2px
    classDef rule fill:#fef3c7,stroke:#b45309,color:#1e293b,stroke-width:2px
    classDef result fill:#065f46,stroke:#d1fae5,color:#ffffff,stroke-width:2px
    classDef decision fill:#92400e,stroke:#fef3c7,color:#ffffff,stroke-width:2px
```

**Graduation is a recommendation requiring acceptance, and it can simplify a layout as well as expand one.**

These examples show how the distinction appears in a shelving plan:

| Observation | Plan section | Proposed action |
|---|---|---|
| `CONTRIBUTING.md` is missing | Findings | Add the required contributor guide, even for `minimal` |
| Flat topic files mix genres readers confuse | Graduation | Recommend categorised folders, subject to acceptance |
| A `rigorous` layout has mostly empty topic folders | Graduation | Recommend consolidation, subject to acceptance |

File-count and size triggers are approximate prompts to inspect the layout, not automatic migration rules.
Use the [graduation-trigger reference](flavours.md#graduation-triggers-when-to-introduce-each-scale-up-element) for the individual thresholds.
Use the [shelving-plan contract](../SKILL.md#4-the-shelving-plan) to report findings and recommendations.
