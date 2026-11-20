# Plugin publication workflow

[`tag-plugin-versions.yml`](tag-plugin-versions.yml) validates generated plugin packages on pull requests and publishes generated mirrors and version tags from `main`.
Canonical sources are `skills/`, `hooks/` and [`plugins/composition.yaml`](../../plugins/composition.yaml).
Generated mirrors live under `plugins/<plugin>/skills/` and `plugins/<plugin>/hooks/`.

## Triggers and routing

| Event | Validation job | Publication job |
|---|---|---|
| Pull request | Runs with read-only repository contents access | Skipped |
| Push to `main` | Skipped | Runs with repository contents write access |
| Manual dispatch on `main` | Skipped | Runs with repository contents write access |
| Manual dispatch on another ref | Skipped | Skipped |

The workflow grants `contents: read` by default. Only the publication job overrides this with `contents: write`.
Both jobs use `ubuntu-latest`.
Concurrency groups are `plugin-publication-<pull-request-number>` for pull requests and `plugin-publication-main` for publication.
`cancel-in-progress: false` keeps the running job active. GitHub can replace an older pending run in the same group, so not every queued run is retained.

## Workflow overview

Pull requests prove that canonical sources generate valid plugins.
Publication on `main` repeats those checks, commits generated mirrors, then creates missing version tags.

```mermaid
%%{init: {"themeVariables": {"actorBkg": "#dbeafe", "actorBorder": "#1e40af", "actorTextColor": "#1e293b", "noteBkgColor": "#fef3c7", "noteBorderColor": "#92400e", "noteTextColor": "#1e293b", "activationBkgColor": "#dbeafe", "activationBorderColor": "#1e40af", "labelBoxBkgColor": "#dbeafe", "labelBoxBorderColor": "#64748b", "labelTextColor": "#1e293b"}}}%%
sequenceDiagram
    autonumber
    participant E as GitHub event
    participant A as Actions
    participant C as Checks
    participant O as origin repository
    E->>A: Pull request, push to main, or manual dispatch
    alt Pull request
        A->>C: Build mirrors, validate packages and run tests
        C-->>A: Pass or fail with read-only repository access
    else Main publication
        A->>C: Check out current main, build, validate and test
        C-->>A: All checks must pass
        A->>O: Commit generated changes and push main
        O-->>A: Main push must succeed
        A->>O: Create and push missing immutable version tags
    else Manual dispatch on another ref
        A-->>E: Skip both jobs
    end
```

<details>
<summary>Complete validation and publication sequence</summary>

### Detailed workflow sequence

Blue participant boxes identify workflow components. Amber notes identify constraints and decisions.
Message colours follow the reader's GitHub theme.

```mermaid
%%{init: {"themeVariables": {"actorBkg": "#dbeafe", "actorBorder": "#1e40af", "actorTextColor": "#1e293b", "noteBkgColor": "#fef3c7", "noteBorderColor": "#92400e", "noteTextColor": "#1e293b", "activationBkgColor": "#dbeafe", "activationBorderColor": "#1e40af", "labelBoxBkgColor": "#dbeafe", "labelBoxBorderColor": "#64748b", "labelTextColor": "#1e293b"}}}%%
sequenceDiagram
    autonumber
    participant E as GitHub event
    participant A as Actions scheduler
    participant R as Ubuntu runner
    participant U as setup-uv and uv
    participant S as Mirror synchroniser
    participant V as Plugin validator
    participant T as Pytest
    participant G as Local Git checkout
    participant O as origin repository
    E->>A: Pull request, push to main, or manual dispatch
    A->>A: Select concurrency group from PR number or main
    Note over A: Do not cancel the running job
    A->>A: Evaluate job conditions
    alt Pull request event
        A->>R: Start validate job with contents read
        R->>G: actions/checkout@v7.0.1 with default checkout settings
        Note over R,G: Pull request checkout uses the action's default PR ref
        R->>U: astral-sh/setup-uv@v10.3.3
        U->>U: Make Python 3.12 available and enable dependency caching
        Note over U: Cache dependency globs include uv.lock and tools/plugin-ci/uv.lock
        R->>S: uv run --locked --project tools/plugin-ci plugin-ci sync
        S->>S: Read composition and canonical skill and hook sources
        S->>G: Rebuild generated mirrors and remove stale mirrored entries
        S-->>R: Generation status
        R->>V: uv run --locked --project tools/plugin-ci plugin-ci validate
        V->>G: Check mirror freshness and package contracts
        V-->>R: Exit status and findings
        R->>T: uv run --locked --project tools/plugin-ci pytest<br/>-c tools/plugin-ci/pyproject.toml tools/plugin-ci/tests
        T->>T: Run Plugin CI Tool and publication contract tests
        T-->>R: Tool test exit status
        R->>T: uv run --locked pytest
        T->>T: Run root hook tests with root configuration
        T-->>R: Root test exit status
        R-->>A: Job result
        Note over R,O: No generated commit or tag push occurs on pull requests
    else Non-PR event on refs/heads/main
        A->>R: Start tag job with contents write
        R->>O: actions/checkout@v7.0.1, ref main, full history and tags
        O-->>G: Current main checkout and existing tags
        Note over G,O: Checkout explicitly selects main, not a queued event's SHA
        R->>U: astral-sh/setup-uv@v10.3.3
        U->>U: Make Python 3.12 available and enable root and Tool lockfile caching
        R->>G: Set github-actions bot name and email
        R->>S: uv run --locked --project tools/plugin-ci plugin-ci sync
        S->>S: Load plugin composition
        S->>G: Synchronise generated skill and hook trees
        S-->>R: Generation status
        R->>V: uv run --locked --project tools/plugin-ci plugin-ci validate
        V->>G: Validate generated package contracts and freshness
        V-->>R: Validation exit status
        R->>T: uv run --locked --project tools/plugin-ci pytest<br/>-c tools/plugin-ci/pyproject.toml tools/plugin-ci/tests
        T->>T: Exercise Plugin CI Tool and publication contracts
        T-->>R: Tool test exit status
        R->>T: uv run --locked pytest
        T->>T: Run root hook tests with root configuration
        T-->>R: Root test exit status
        Note over R,T: Any failing step prevents subsequent publication steps
        R->>G: uv run --locked --project tools/plugin-ci plugin-ci commit --push
        G->>G: Require branch main and an empty staging index
        G->>G: Collect staged, unstaged and untracked paths
        G->>G: Reject changes outside generated skill and hook trees
        alt Generated paths changed
            G->>G: Stage generated paths including deletions
            G->>G: Commit chore: sync generated plugin mirrors
            Note over G: Commit uses --no-gpg-sign
        else Generated mirrors already match
            G-->>R: Report no generated changes to commit
        end
        G->>O: Push HEAD to refs/heads/main without force
        alt Push rejected or fails
            O-->>R: Failure stops job before tagging
        else Push succeeds
            O-->>G: main contains the generated snapshot
            R->>G: uv run --locked --project tools/plugin-ci plugin-ci tag --push
            G->>G: Read each plugins/*/.claude-plugin/plugin.json
            loop Each plugin manifest
                G->>G: Strip jpai- prefix and form plugin/vVERSION
                G->>G: Check whether refs/tags/plugin/vVERSION exists
                alt Tag already exists
                    G->>G: Preserve existing tag without moving it
                else Tag missing
                    G->>G: Queue release tag for current HEAD
                end
            end
            alt At least one tag missing
                G->>G: Create all missing annotated tags locally
                G->>O: Push explicit refs for the newly created tags
                O-->>R: Tag push result
            else All versions already tagged
                G-->>R: Report every plugin version already tagged
            end
        end
        R-->>A: Publication job result
    else Manual dispatch on another ref
        A-->>E: Both jobs skipped by their conditions
    end
```

</details>

## Generation and validation contracts

The synchroniser copies canonical skill trees according to composition and copies the configured hook files.
It excludes configured development artefacts and `evals/`, and removes stale generated entries.
It does not update plugin versions.

The validator checks symlink restrictions, exact mirror freshness, composition membership, hook wiring, Claude and Codex manifests, skill frontmatter and marketplace metadata.
The publication test step runs the Plugin CI Tool suite with its own explicit pytest configuration, then runs root hook tests.
Both invocations must pass before publication continues.
A successful synchronisation step alone does not establish package validity: validation and tests must also succeed.

## Commit and release boundaries

The generated-commit helper accepts changes only below `plugins/<plugin>/skills/` or `plugins/<plugin>/hooks/`.
Manifests, composition, plugin READMEs and canonical source changes are authored inputs and cannot enter this automatic commit.
It refuses another branch, a pre-populated index or unrelated dirty files.
The push also runs when no generated commit was necessary.
A concurrent update to remote `main` can reject the normal push; the helper does not force-push, rebase or retry.

Version tags derive from the Claude plugin manifests. For example, `jpai-essentials` version `1.2.3` produces `essentials/v1.2.3`.
Missing tags are annotated and target the checked-out HEAD after any generated commit.
Existing tags are immutable under this helper: it skips their names without retargeting them or comparing their commits.
Version numbers must therefore be updated explicitly in the authored manifest change when a new release tag is needed.

Publication is ordered but not transactional.
The generated commit can reach `main` before a later tag operation fails.
New tags are pushed together without `--atomic`, so a failed push requires inspecting the remote tag state before retrying.
A fresh run checks out remote `main` and fetches tags again, allowing it to skip tags already present remotely.

Pushes made with the workflow's repository token do not recursively trigger another ordinary push workflow run.
This workflow publishes Git commits and tags; it does not create GitHub Releases, publish registry packages or run live harness installation tests.

## Maintenance

Keep this sequence aligned with the workflow YAML and the invoked helpers when commands, guards, permissions or publication order change.
Use the root contribution checks for documentation. For this deliberately detailed diagram, run parsing and contrast validation with complexity disabled:

```sh
bunx @jpeakai/mermaidjs-lint .github/workflows/README.md --disable-category complexity
```
