# Chart legend contract

Always place every chart's legend on the right-hand side, vertically stacked outside the plotting area.
Apply this rule to all chart formats and all output modes, including static charts authored outside Plotly.
Do not place legends above, below, inside or to the left of a chart.
Keep legend labels readable and reserve enough right-side space to avoid clipping.
For formats the script cannot inspect, verify the rendered chart manually.

For every Plotly fence, explicitly set `layout.showlegend` to `true` and define `layout.legend` using the settings in [the rich block contract](../rich-blocks.md).
Required legend fields:

| Field | Required value |
|---|---|
| `orientation` | `"v"` |
| `xref` | `"paper"` |
| `x` | From `1.02` to `3` |
| `xanchor` | `"left"` |
| `y` | From `0` to `1` |
| `yanchor` | `"top"` |

Apply the same positioning to named legends such as `legend2`.
Never set a legend's `visible` field to `false`.
Do not rely on Plotly defaults or hide the legend to bypass the rule.
Run the deterministic check on the Markdown source before rendering or delivery:

```sh
uv run --no-project {SKILLS_ROOT}/richdocs/scripts/legends.py DOC.md
```

A non-zero exit blocks delivery.
Correct every reported file-and-line diagnostic and rerun the check.
The helper parses Plotly fenced JSON; it does not inspect rendered images or other chart languages and never rewrites source.

