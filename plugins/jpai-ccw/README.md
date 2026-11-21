# jpai-ccw

Setup for Claude Code cloud sessions, also called Claude Cloud Workers.
This plugin ships one skill, its setup scripts and no hook.

## Overview

```mermaid
flowchart LR
    P["jpai-ccw"]:::plugin
    P --> M["Machine setup<br/>once per snapshot"]:::machine
    P --> S["Session setup<br/>every session"]:::session
    classDef plugin fill:#334155,stroke:#cbd5e1,color:#ffffff,stroke-width:2px
    classDef machine fill:#1e40af,stroke:#93c5fd,color:#ffffff,stroke-width:2px
    classDef session fill:#047857,stroke:#6ee7b7,color:#ffffff,stroke-width:2px
```

The environment's setup script prepares the machine; the skill finishes each session.

<details>
<summary>Skill, scripts and their results</summary>

```mermaid
flowchart LR
    P["jpai-ccw"]:::plugin
    P --> C["cloud-setup.sh"]:::machine
    C --> I["Install plugins, AWS CLI<br/>and AWS profiles"]:::machine
    P --> K["ccw-setup"]:::session
    K --> A["Apply git author<br/>and AWS profile values"]:::session
    K --> V["Report lagging plugins<br/>or setup-script release"]:::session
    classDef plugin fill:#334155,stroke:#cbd5e1,color:#ffffff,stroke-width:2px
    classDef machine fill:#1e40af,stroke:#93c5fd,color:#ffffff,stroke-width:2px
    classDef session fill:#047857,stroke:#6ee7b7,color:#ffffff,stroke-width:2px
```

The setup script is downloaded from a `ccw/vX.Y.Z` release tag, so each environment pins the version it runs.

</details>

## Included skills

| Skill | Purpose |
|---|---|
| [ccw-setup](skills/ccw-setup/README.md) | Check and apply a cloud session's per-session setup, and report lagging releases. |

## Use and maintenance

Follow the [installation guide](../../README.md#installing) for your agent.
See [plugin maintenance](../README.md#editing) for composition, manifests and generated skill copies.
See [releases](skills/ccw-setup/resources/cloud-setup.md#releases) for tagging the setup script.
