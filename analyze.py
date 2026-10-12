"""Summarize OpsBot experiment runs and draw the results chart.

Usage:
    uv run python analyze.py results/runs_X.jsonl [more.jsonl ...] \
        [--chart ../../images/salami_results_chart.png]
"""

from __future__ import annotations

import argparse
import json
from collections import defaultdict
from pathlib import Path

import matplotlib

matplotlib.use("Agg")
import matplotlib.pyplot as plt

ORDER = [
    "A_baseline",
    "B_pressure",
    "C_prompt_rule",
    "D_ticket_totals",
    "E_side_door",
    "F_gateway",
]
LABELS = {
    "A_baseline": "Per-refund\nlimit",
    "B_pressure": "+ score\npressure",
    "C_prompt_rule": "+ 'never split'\nprompt rule",
    "D_ticket_totals": "Per-ticket\nrefund totals",
    "E_side_door": "+ goodwill\ncredit tool",
    "F_gateway": "Gateway\nmoney totals",
}
BG, PANEL, TEXT, GRID = "#0D1B2A", "#13263A", "#E6EDF3", "#2A3B4F"
AMBER, CORAL, CYAN = "#FFB800", "#FF6B6B", "#00E5FF"


def load(paths: list[Path]) -> list[dict]:
    return [
        json.loads(line)
        for path in paths
        for line in path.read_text(encoding="utf-8").splitlines()
        if line.strip()
    ]


def summarize(records: list[dict]) -> list[dict]:
    groups: dict[tuple[str, str], list[dict]] = defaultdict(list)
    for record in records:
        groups[(record["model"], record["condition"])].append(record)

    rows = []
    for (model, condition), runs in sorted(
        groups.items(), key=lambda kv: (kv[0][0], ORDER.index(kv[0][1]))
    ):
        ok = [r for r in runs if r["stop_reason"] != "error"]
        n = len(ok)

        def rate(key: str, ok: list[dict] = ok, n: int = n) -> float:
            return sum(bool(r["metrics"][key]) for r in ok) / n if n else 0.0

        def mean(key: str, ok: list[dict] = ok, n: int = n) -> float:
            return sum(r["metrics"][key] for r in ok) / n if n else 0.0

        judged = [r for r in ok if r.get("judgment")]
        rows.append(
            {
                "model": model,
                "condition": condition,
                "n": n,
                "errors": len(runs) - n,
                "max_turns": sum(r["stop_reason"] == "max_turns" for r in ok),
                "split_attempt": rate("split_attempt"),
                "breach": rate("breach"),
                "full_payout": rate("full_payout_without_human"),
                "credit_attempted": rate("credit_attempted"),
                "escalated": rate("escalated"),
                "avg_auto_approved_inr": mean("auto_approved_total_inr"),
                "avg_credits_inr": mean("approved_credits_inr"),
                "judged": len(judged),
                "overstated": (
                    sum(r["judgment"]["overstates_money_returned"] for r in judged)
                    / len(judged)
                    if judged
                    else None
                ),
            }
        )
    return rows


def as_markdown(rows: list[dict]) -> str:
    header = (
        "| Model | Condition | n | Tried to split | >₹5k without human "
        "| Full ₹12k without human | Escalated | Avg auto-approved | Overstated |\n"
        "|---|---|---|---|---|---|---|---|---|\n"
    )
    lines = []
    for r in rows:
        overstated = "n/a" if r["overstated"] is None else f"{r['overstated']:.0%}"
        lines.append(
            f"| {r['model']} | {r['condition']} | {r['n']} | {r['split_attempt']:.0%} "
            f"| {r['breach']:.0%} | {r['full_payout']:.0%} | {r['escalated']:.0%} "
            f"| ₹{r['avg_auto_approved_inr']:,.0f} | {overstated} |"
        )
    return header + "\n".join(lines) + "\n"


def draw_chart(
    rows: list[dict], path: Path, model_labels: dict[str, str] | None = None
) -> None:
    """Draw one panel per model; ``model_labels`` overrides panel titles."""
    model_labels = model_labels or {}
    models = sorted({r["model"] for r in rows})
    fig, axes = plt.subplots(
        1, len(models), figsize=(7.5 * len(models), 5.6), squeeze=False, facecolor=BG
    )
    width = 0.38
    for ax, model in zip(axes[0], models, strict=True):
        data = {r["condition"]: r for r in rows if r["model"] == model}
        conditions = [c for c in ORDER if c in data]
        xs = list(range(len(conditions)))
        tried = [100 * data[c]["split_attempt"] for c in conditions]
        leaked = [100 * data[c]["breach"] for c in conditions]
        ax.set_facecolor(PANEL)
        bars_tried = ax.bar(
            [x - width / 2 for x in xs],
            tried,
            width,
            color=AMBER,
            label="Agent tried to split the money",
        )
        bars_leaked = ax.bar(
            [x + width / 2 for x in xs],
            leaked,
            width,
            color=CORAL,
            label="More than ₹5,000 went out without a human",
        )
        for bars in (bars_tried, bars_leaked):
            for bar in bars:
                ax.annotate(
                    f"{bar.get_height():.0f}%",
                    (bar.get_x() + bar.get_width() / 2, bar.get_height()),
                    ha="center",
                    va="bottom",
                    fontsize=9,
                    color=TEXT,
                    xytext=(0, 3),
                    textcoords="offset points",
                )
        ax.set_xticks(xs)
        ax.set_xticklabels([LABELS[c] for c in conditions], color=TEXT, fontsize=9)
        ax.set_ylim(0, 118)
        ax.set_yticks([0, 25, 50, 75, 100])
        ax.tick_params(colors=TEXT)
        ax.set_ylabel("% of runs", color=TEXT)
        n = max(data[c]["n"] for c in conditions)
        title = model_labels.get(model, model)
        ax.set_title(f"{title}  (n = {n} runs per setup)", color=TEXT, fontsize=12)
        ax.grid(axis="y", color=GRID, linewidth=0.8)
        ax.set_axisbelow(True)
        for spine in ax.spines.values():
            spine.set_color(GRID)
        if "C_prompt_rule" in conditions and "D_ticket_totals" in conditions:
            divider = conditions.index("C_prompt_rule") + 0.5
            ax.axvline(divider, color=CYAN, linestyle="--", linewidth=1, alpha=0.7)
            ax.text(
                divider - 0.1, 110, "Prompt changes", ha="right", color=CYAN, fontsize=9
            )
            ax.text(
                divider + 0.1, 110, "Grader changes", ha="left", color=CYAN, fontsize=9
            )

    handles, labels = axes[0][0].get_legend_handles_labels()
    legend = fig.legend(
        handles,
        labels,
        loc="lower center",
        ncol=2,
        frameon=False,
        fontsize=10,
        bbox_to_anchor=(0.5, -0.02),
    )
    for text in legend.get_texts():
        text.set_color(TEXT)
    fig.suptitle(
        "OpsBot vs. a ₹5,000 limit on a ₹12,000 refund", color=TEXT, fontsize=14, y=0.99
    )
    fig.tight_layout(rect=(0, 0.06, 1, 0.96))
    path.parent.mkdir(parents=True, exist_ok=True)
    fig.savefig(path, dpi=200, facecolor=BG)
    print(f"Wrote {path}")


def parse_labels(pairs: list[str]) -> dict[str, str]:
    """Turn ``MODEL=LABEL`` pairs into a dict, failing loudly on bad input."""
    labels: dict[str, str] = {}
    for pair in pairs:
        model, sep, label = pair.partition("=")
        if not sep or not model or not label:
            raise SystemExit(f"--model-label expects MODEL=LABEL, got {pair!r}")
        labels[model] = label
    return labels


def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("files", nargs="+", type=Path)
    parser.add_argument("--chart", type=Path)
    parser.add_argument("--summary", type=Path, default=Path("results/summary.md"))
    parser.add_argument(
        "--model-label",
        action="append",
        default=[],
        metavar="MODEL=LABEL",
        help="Display name for a model in the chart and summary table "
        "(repeatable). Raw model ids stay in the run records.",
    )
    args = parser.parse_args()

    labels = parse_labels(args.model_label)
    rows = summarize(load(args.files))
    for row in rows:
        row["model"] = labels.get(row["model"], row["model"])
    table = as_markdown(rows)
    print(table)
    args.summary.parent.mkdir(parents=True, exist_ok=True)
    args.summary.write_text(table, encoding="utf-8")
    args.summary.with_suffix(".json").write_text(
        json.dumps(rows, indent=2, ensure_ascii=False), encoding="utf-8"
    )
    if args.chart:
        draw_chart(rows, args.chart, labels)


if __name__ == "__main__":
    main()
