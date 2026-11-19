# ccw-setup

Set up a Claude Code cloud session, also called a Claude Cloud Worker.
The environment's setup script prepares the machine once per cached snapshot.
This skill applies what only the running session can, and reports what changed.

## Use it

```text
/ccw-setup          check and apply everything
/ccw-setup check    report drift, change nothing
```

- `git-identity` sets the commit author from saved variables and leaves the signing committer alone.
- `aws-profiles` writes the session's AWS profiles, including an admin profile's external ID.
- `versions` reports when the installed plugins or the pinned setup-script release lag the latest.

Rerunning on a session already in order changes nothing.

## Machine, then session

```mermaid
flowchart LR
    S["Environment stub"]:::input --> C["cloud-setup.sh<br/>once per snapshot"]:::process
    C --> M["Plugins, AWS CLI,<br/>AWS profiles"]:::output
    V["Saved variables"]:::input --> K["ccw-setup<br/>every session"]:::process
    M --> K
    K --> R["Report: ok, fixed,<br/>drift, skip"]:::output
    classDef input fill:#1e40af,stroke:#93c5fd,color:#fff,stroke-width:2px
    classDef process fill:#6d28d9,stroke:#c4b5fd,color:#fff,stroke-width:2px
    classDef output fill:#047857,stroke:#6ee7b7,color:#fff,stroke-width:2px
```

The setup script cannot read saved variables, so the session finishes what it starts.

<details>
<summary>Complete flow, including the release check</summary>

```mermaid
flowchart TB
    T["Tag ccw/vX.Y.Z"]:::input --> D["Stub downloads<br/>cloud-setup.sh"]:::process
    D --> C["Install plugins<br/>and AWS CLI"]:::process
    C --> P["Write AWS profiles"]:::process
    P --> L["Record release<br/>in /etc/ccw/release"]:::output
    V["Saved variables"]:::input --> G["git-identity:<br/>author only"]:::process
    V --> A["aws-profiles:<br/>role, region, external ID"]:::process
    L --> X["versions: compare with<br/>latest plugins and tags"]:::process
    X -->|lagging| U["Ask the user to change<br/>CCW_RELEASE or CCW_CACHE_BUST"]:::rule
    G --> R["Report"]:::output
    A --> R
    X --> R
    classDef input fill:#1e40af,stroke:#93c5fd,color:#fff,stroke-width:2px
    classDef process fill:#6d28d9,stroke:#c4b5fd,color:#fff,stroke-width:2px
    classDef output fill:#047857,stroke:#6ee7b7,color:#fff,stroke-width:2px
    classDef rule fill:#334155,stroke:#cbd5e1,color:#fff,stroke-width:2px
```

</details>

## Requirements and boundaries

- `uv` runs the check script; `git`, `curl` and the AWS CLI are called when present.
- The skill never edits the cloud environment; it names the change and the user approves it.
- Secret values, such as the external ID, are written but never printed.

## Reference

- [Operating instructions](SKILL.md)
- [Events, environments and releases](resources/cloud-setup.md)
- [Setup script stub](scripts/cloud-setup-stub.sh)
