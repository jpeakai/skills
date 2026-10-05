# librarian architecture

How one `/librarian` invocation expands into work.
Each lens below has an overview that stays visible and a detailed reference you can expand.
The last section lists the permutation axes and the eval scenario that covers each one.

Colour key, shared by every diagram:

| Colour | Kind |
|---|---|
| Blue | Invocation and arguments |
| Violet | Authority and decisions |
| Green | Pipeline steps |
| Slate | Skill resources and scripts |
| Amber | Artifacts written or reported |
| Red | Forbidden outcomes |

## 1. Mode dispatch

Every mode runs Step 0 first, then branches on the first argument.

```mermaid
flowchart LR
    INV["/librarian args"]:::input
    S0["Step 0<br/>resolve dialect"]:::rule
    AUD["audit<br/>(default)"]:::step
    APP["apply"]:::step
    INI["init"]:::step
    IDX["index"]:::step
    PLAN["Shelving plan"]:::artifact
    MOV["Moves, extracts,<br/>stubs, links"]:::artifact
    CORE["Core documents"]:::artifact
    GEN["Generated siblings"]:::artifact

    INV --> S0
    S0 --> AUD --> PLAN
    S0 --> APP --> MOV
    S0 --> INI --> CORE
    S0 --> IDX --> GEN
    PLAN -. feeds .-> APP

    classDef input    fill:#1e40af,stroke:#93c5fd,color:#fff,stroke-width:2px
    classDef rule     fill:#6d28d9,stroke:#c4b5fd,color:#fff,stroke-width:2px
    classDef step     fill:#047857,stroke:#6ee7b7,color:#fff,stroke-width:2px
    classDef artifact fill:#92400e,stroke:#fcd34d,color:#fff,stroke-width:2px
```

*Four modes, one shared dialect step.* Audit is the only read-only mode.

<details>
<summary>Complete diagram: arguments, resources and outputs per mode</summary>

```mermaid
flowchart LR
    subgraph ARGS["Arguments"]
        BARE["bare"]:::input
        PATH["path scope"]:::input
        FLV["minimal / standard /<br/>rigorous"]:::input
        CONV["okf-yaml / okf-yml"]:::input
    end

    subgraph MODES["Modes"]
        AUD["audit"]:::step
        APP["apply"]:::step
        INI["init"]:::step
        IDX["index"]:::step
    end

    subgraph RES["Resources loaded"]
        BASE["baseline.md"]:::resource
        SMELL["misplacement_smells.md"]:::resource
        FLAV["flavours.md"]:::resource
        CTPL["conventions_template.md"]:::resource
        GTPL["glossary_template.md"]:::resource
        ATPL["adr_template.md"]:::resource
        SIB["structured_siblings.md"]:::resource
        OKF["adr_okf_yaml.md"]:::resource
    end

    subgraph OUT["Outputs"]
        PLAN["Shelving plan"]:::artifact
        MOV["git mv + link rewrites"]:::artifact
        CORE["CONVENTIONS, AGENTS + stub,<br/>GLOSSARY, CODING_STANDARDS,<br/>ADR surface"]:::artifact
        GEN["YAML index or<br/>okf-yaml bundle"]:::artifact
    end

    BARE --> AUD
    PATH --> AUD
    PATH --> APP
    FLV --> INI
    CONV --> IDX
    AUD --> BASE
    AUD --> SMELL
    AUD --> FLAV
    INI --> CTPL
    INI --> GTPL
    INI --> ATPL
    IDX --> SIB
    IDX --> OKF
    AUD --> PLAN
    APP --> MOV
    INI --> CORE
    IDX --> GEN

    classDef input    fill:#1e40af,stroke:#93c5fd,color:#fff,stroke-width:2px
    classDef step     fill:#047857,stroke:#6ee7b7,color:#fff,stroke-width:2px
    classDef resource fill:#334155,stroke:#cbd5e1,color:#fff,stroke-width:2px
    classDef artifact fill:#92400e,stroke:#fcd34d,color:#fff,stroke-width:2px
```

</details>

## 2. Dialect resolution

Every contested question is answered by the highest rung that has evidence, and the audit names the rung.

```mermaid
flowchart TB
    Q["Contested question"]:::input
    ADJ["User adjudication<br/>learned/"]:::rule
    DEC["Declared dialect<br/>docs/CONVENTIONS.md"]:::rule
    OBS["Observed dialect<br/>3+ instances"]:::rule
    BAS["Baseline"]:::resource
    V["Verdict + rung named"]:::artifact

    Q --> ADJ -- silent --> DEC -- silent --> OBS -- silent --> BAS
    ADJ -- rules --> V
    DEC -- rules --> V
    OBS -- rules --> V
    BAS --> V

    classDef input    fill:#1e40af,stroke:#93c5fd,color:#fff,stroke-width:2px
    classDef rule     fill:#6d28d9,stroke:#c4b5fd,color:#fff,stroke-width:2px
    classDef resource fill:#334155,stroke:#cbd5e1,color:#fff,stroke-width:2px
    classDef artifact fill:#92400e,stroke:#fcd34d,color:#fff,stroke-width:2px
```

*User beats declared, declared beats observed, observed beats baseline.*

<details>
<summary>Complete diagram: named conventions, majority rule and forbidden findings</summary>

```mermaid
flowchart TB
    Q["Contested question"]:::input
    ADJ["Adjudication exists?"]:::rule
    DEC["CONVENTIONS.md<br/>declares it?"]:::rule
    NAMED["Named convention<br/>e.g. okf-yaml"]:::rule
    OBS["3+ consistent<br/>instances?"]:::rule
    MIX["Inconsistent repo"]:::rule
    MAJ["Majority is dialect,<br/>minority are findings"]:::step
    BAS["Baseline + flavour"]:::resource
    REC["Baseline prefers otherwise"]:::step
    V["Verdict + rung named"]:::artifact
    REC2["Recommendation only"]:::artifact
    NO["Finding from baseline<br/>over a local choice"]:::forbidden

    Q --> ADJ
    ADJ -- yes --> V
    ADJ -- no --> DEC
    DEC -- yes --> V
    DEC -- names one --> NAMED --> V
    DEC -- no --> OBS
    OBS -- yes --> V
    OBS -- mixed --> MIX --> MAJ --> V
    OBS -- no --> BAS --> V
    BAS --> REC --> REC2
    REC -. never .-> NO

    classDef input     fill:#1e40af,stroke:#93c5fd,color:#fff,stroke-width:2px
    classDef rule      fill:#6d28d9,stroke:#c4b5fd,color:#fff,stroke-width:2px
    classDef step      fill:#047857,stroke:#6ee7b7,color:#fff,stroke-width:2px
    classDef resource  fill:#334155,stroke:#cbd5e1,color:#fff,stroke-width:2px
    classDef artifact  fill:#92400e,stroke:#fcd34d,color:#fff,stroke-width:2px
    classDef forbidden fill:#b91c1c,stroke:#fca5a5,color:#fff,stroke-width:2px
```

</details>

## 3. Audit pipeline

Read-only.
Charters come first, so every misplacement verdict cites one.

```mermaid
flowchart LR
    INV["Inventory"]:::step
    CH["Charter table"]:::rule
    EX["Existence +<br/>cross-links"]:::step
    MIS["Misplacement<br/>M + P smells"]:::step
    GR["Graduation check"]:::step
    PLAN["Shelving plan<br/>red, yellow, purple"]:::artifact
    OFFER["Offer: apply all,<br/>red only, report"]:::input

    INV --> CH --> EX --> MIS --> GR --> PLAN --> OFFER

    classDef input    fill:#1e40af,stroke:#93c5fd,color:#fff,stroke-width:2px
    classDef rule     fill:#6d28d9,stroke:#c4b5fd,color:#fff,stroke-width:2px
    classDef step     fill:#047857,stroke:#6ee7b7,color:#fff,stroke-width:2px
    classDef artifact fill:#92400e,stroke:#fcd34d,color:#fff,stroke-width:2px
```

*Seven stages, no writes.*

<details>
<summary>Complete diagram: every check feeding the plan</summary>

```mermaid
flowchart LR
    subgraph EXIST["Existence"]
        REQ["Required set:<br/>README, CONTRIBUTING,<br/>CODING_STANDARDS, AGENTS,<br/>ADRs, GLOSSARY"]:::step
        STUB["CLAUDE.md is<br/>exactly @AGENTS.md"]:::step
        ADRS["ADR records<br/>structurally complete"]:::step
        GLOS["GLOSSARY shape"]:::step
        LOC["Health-file locations"]:::step
    end

    subgraph LINKS["Cross-links"]
        L1["AGENTS to ADRs"]:::step
        L2["AGENTS to GLOSSARY"]:::step
        L3["AGENTS to CONVENTIONS"]:::step
        L4["CONTRIBUTING + AGENTS<br/>to CODING_STANDARDS"]:::step
        L5["README to CONTRIBUTING"]:::step
    end

    subgraph SMELLS["Misplacement"]
        M["M1-M10<br/>whole document"]:::step
        P["P1-P8<br/>within a file"]:::step
    end

    GR["Graduation<br/>triggers"]:::rule
    PLAN["Shelving plan"]:::artifact
    ADJ["learned/<br/>adjudications"]:::resource

    REQ --> PLAN
    STUB --> PLAN
    ADRS --> PLAN
    GLOS --> PLAN
    LOC --> PLAN
    L1 --> PLAN
    L2 --> PLAN
    L3 --> PLAN
    L4 --> PLAN
    L5 --> PLAN
    M --> PLAN
    P --> PLAN
    GR -- purple only --> PLAN
    PLAN -- rejected --> ADJ

    classDef rule     fill:#6d28d9,stroke:#c4b5fd,color:#fff,stroke-width:2px
    classDef step     fill:#047857,stroke:#6ee7b7,color:#fff,stroke-width:2px
    classDef resource fill:#334155,stroke:#cbd5e1,color:#fff,stroke-width:2px
    classDef artifact fill:#92400e,stroke:#fcd34d,color:#fff,stroke-width:2px
```

</details>

## 4. Apply operations

A closed set of seven operations, each loss-free.

```mermaid
flowchart LR
    PLAN["Shelving plan row"]:::input
    OPS["create-stub, move, rename,<br/>extract, merge, link, symlink"]:::step
    INVAR["Invariants:<br/>git mv, link rewrite,<br/>verbatim cargo"]:::rule
    VER["Verify: old paths<br/>resolve, renames only"]:::step
    DONE["Commit-sized change"]:::artifact
    DEL["Delete"]:::forbidden

    PLAN --> OPS --> INVAR --> VER --> DONE
    OPS -. never .-> DEL

    classDef input     fill:#1e40af,stroke:#93c5fd,color:#fff,stroke-width:2px
    classDef rule      fill:#6d28d9,stroke:#c4b5fd,color:#fff,stroke-width:2px
    classDef step      fill:#047857,stroke:#6ee7b7,color:#fff,stroke-width:2px
    classDef artifact  fill:#92400e,stroke:#fcd34d,color:#fff,stroke-width:2px
    classDef forbidden fill:#b91c1c,stroke:#fca5a5,color:#fff,stroke-width:2px
```

*Deletion is not in the vocabulary.*

<details>
<summary>Complete diagram: each operation and its guard</summary>

```mermaid
flowchart LR
    subgraph OPS["Operations"]
        CS["create-stub"]:::step
        MV["move / rename"]:::step
        EXT["extract"]:::step
        MRG["merge"]:::step
        LNK["link"]:::step
        SYM["symlink"]:::step
    end

    subgraph GUARDS["Guards"]
        G1["Stub marker +<br/>required links"]:::rule
        G2["git mv +<br/>repo-wide rewrite"]:::rule
        G3["Verbatim section,<br/>link left at source"]:::rule
        G4["Merged file<br/>leaves a link"]:::rule
        G5["ADR ids immutable"]:::rule
    end

    VER["Grep old paths<br/>and anchors"]:::step
    OK["Renames, not<br/>delete + add"]:::artifact
    REWORD["Reword cargo<br/>in transit"]:::forbidden
    RENUM["Renumber an ADR"]:::forbidden

    CS --> G1
    MV --> G2
    MV --> G5
    EXT --> G3
    MRG --> G4
    LNK --> VER
    SYM --> VER
    G1 --> VER
    G2 --> VER
    G3 --> VER
    G4 --> VER
    G5 --> VER
    VER --> OK
    EXT -. never .-> REWORD
    MV -. never .-> RENUM

    classDef rule      fill:#6d28d9,stroke:#c4b5fd,color:#fff,stroke-width:2px
    classDef step      fill:#047857,stroke:#6ee7b7,color:#fff,stroke-width:2px
    classDef artifact  fill:#92400e,stroke:#fcd34d,color:#fff,stroke-width:2px
    classDef forbidden fill:#b91c1c,stroke:#fca5a5,color:#fff,stroke-width:2px
```

</details>

## 5. Init

A flavour sets the starting shape; observed practice overrides it line by line.

```mermaid
flowchart LR
    ARG["init [flavour]"]:::input
    PICK["Pick flavour<br/>or infer one"]:::rule
    OBS["Observed practice<br/>overrides preset"]:::rule
    CONV["docs/CONVENTIONS.md"]:::artifact
    AG["AGENTS.md +<br/>CLAUDE.md stub"]:::artifact
    GL["GLOSSARY.md"]:::artifact
    CSD["CODING_STANDARDS.md"]:::artifact
    ADR["ADR surface +<br/>template"]:::artifact

    ARG --> PICK --> OBS
    OBS --> CONV
    OBS --> AG
    OBS --> GL
    OBS --> CSD
    OBS --> ADR

    classDef input    fill:#1e40af,stroke:#93c5fd,color:#fff,stroke-width:2px
    classDef rule     fill:#6d28d9,stroke:#c4b5fd,color:#fff,stroke-width:2px
    classDef artifact fill:#92400e,stroke:#fcd34d,color:#fff,stroke-width:2px
```

*Five core documents, each written only when missing.*

<details>
<summary>Complete diagram: flavours, templates and wiring</summary>

```mermaid
flowchart LR
    subgraph FLV["Flavour"]
        NONE["none: infer"]:::input
        MIN["minimal"]:::input
        STD["standard"]:::input
        RIG["rigorous"]:::input
    end

    PICK["Preset dialect"]:::rule
    OBS["Observed lines win,<br/>defaults marked"]:::rule

    subgraph TPL["Templates"]
        CT["conventions_template"]:::resource
        GT["glossary_template"]:::resource
        ST["coding_standards_template"]:::resource
        AT["adr_template"]:::resource
    end

    subgraph WRITE["Writes"]
        CONV["CONVENTIONS.md<br/>Flavour line + layout map"]:::artifact
        AG["AGENTS.md"]:::artifact
        CL["CLAUDE.md =<br/>@AGENTS.md"]:::artifact
        GL["GLOSSARY.md<br/>6 seed terms"]:::artifact
        CSD["CODING_STANDARDS.md<br/>per language"]:::artifact
        ADRS["ADR surface +<br/>layout template"]:::artifact
    end

    MVCL["Full CLAUDE.md<br/>git mv to AGENTS.md"]:::step

    NONE --> PICK
    MIN --> PICK
    STD --> PICK
    RIG --> PICK
    PICK --> OBS
    CT --> CONV
    GT --> GL
    ST --> CSD
    OBS --> CONV
    OBS --> CSD
    AT --> ADRS
    MVCL --> AG
    AG --> CL
    AG -- links --> CONV
    AG -- links --> GL
    AG -- links --> CSD
    AG -- links --> ADRS

    classDef input    fill:#1e40af,stroke:#93c5fd,color:#fff,stroke-width:2px
    classDef rule     fill:#6d28d9,stroke:#c4b5fd,color:#fff,stroke-width:2px
    classDef step     fill:#047857,stroke:#6ee7b7,color:#fff,stroke-width:2px
    classDef resource fill:#334155,stroke:#cbd5e1,color:#fff,stroke-width:2px
    classDef artifact fill:#92400e,stroke:#fcd34d,color:#fff,stroke-width:2px
```

</details>

## 6. Index

No consumer, no index.

```mermaid
flowchart LR
    ARG["index [convention] path"]:::input
    TRIG["Observable<br/>consumer?"]:::rule
    STOP["Report: plain<br/>markdown is correct"]:::artifact
    ARR["Pick arrangement"]:::rule
    MD["Indexed markdown<br/>md2yaml.ts"]:::resource
    OKF["okf-yaml bundle<br/>okf_render.py"]:::resource
    GATE["Round-trip gate<br/>whole corpus"]:::step

    ARG --> TRIG
    TRIG -- no --> STOP
    TRIG -- yes --> ARR
    ARR -- default --> MD --> GATE
    ARR -- named --> OKF --> GATE

    classDef input    fill:#1e40af,stroke:#93c5fd,color:#fff,stroke-width:2px
    classDef rule     fill:#6d28d9,stroke:#c4b5fd,color:#fff,stroke-width:2px
    classDef step     fill:#047857,stroke:#6ee7b7,color:#fff,stroke-width:2px
    classDef resource fill:#334155,stroke:#cbd5e1,color:#fff,stroke-width:2px
    classDef artifact fill:#92400e,stroke:#fcd34d,color:#fff,stroke-width:2px
```

*A named convention skips the arrangement choice.*

<details>
<summary>Complete diagram: both arrangements end to end</summary>

```mermaid
flowchart LR
    TRIG["Consumer exists"]:::rule

    subgraph IDXMD["Indexed markdown"]
        SRC["doc.md stays<br/>authoritative"]:::step
        M2Y["md2yaml.ts --out"]:::resource
        YML["doc.yml sibling"]:::artifact
        CHK["md2yaml.ts --check"]:::step
    end

    subgraph OKFB["okf-yaml"]
        REC["NNNN-slug.yml<br/>records"]:::step
        SCH["record.schema.json"]:::resource
        REN["okf_render.py"]:::resource
        OUTS["md + index +<br/>graph.json + graph.html"]:::artifact
    end

    MK["make target +<br/>generator banner"]:::step
    CONV["Dialect line in<br/>CONVENTIONS.md"]:::artifact
    FIXDOC["Edit source to<br/>suit the tool"]:::forbidden

    TRIG --> SRC --> M2Y --> YML --> CHK
    TRIG --> REC --> SCH --> REN --> OUTS
    CHK --> MK
    OUTS --> MK
    MK --> CONV
    CHK -. never .-> FIXDOC

    classDef rule      fill:#6d28d9,stroke:#c4b5fd,color:#fff,stroke-width:2px
    classDef step      fill:#047857,stroke:#6ee7b7,color:#fff,stroke-width:2px
    classDef resource  fill:#334155,stroke:#cbd5e1,color:#fff,stroke-width:2px
    classDef artifact  fill:#92400e,stroke:#fcd34d,color:#fff,stroke-width:2px
    classDef forbidden fill:#b91c1c,stroke:#fca5a5,color:#fff,stroke-width:2px
```

</details>

## 7. Permutations

The full product of mode, argument, dialect rung, repo state and index trigger is too large to run.
The evals cover every value of every axis at least once; the axis table and the scenario that covers each value live in [evals/README.md](evals/README.md#coverage).
