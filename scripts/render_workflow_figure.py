from __future__ import annotations

import argparse
import json
from pathlib import Path
import textwrap

import matplotlib

matplotlib.use("Agg")

import matplotlib.pyplot as plt
from matplotlib.patches import FancyArrowPatch, FancyBboxPatch


PROJECT_ROOT = Path(__file__).resolve().parents[1]
DEFAULT_SOURCE = (
    PROJECT_ROOT / "figures" / "concept_src" / "fig_1_overall_research_workflow.json"
)
DEFAULT_PNG = (
    PROJECT_ROOT / "figures" / "concept" / "fig_1_overall_research_workflow.png"
)
DEFAULT_SVG = (
    PROJECT_ROOT / "figures" / "concept_src" / "fig_1_overall_research_workflow.svg"
)

CANVAS_WIDTH = 120
CANVAS_HEIGHT = 60
STAGE_Y = 44.0
NODE_TOP_Y = 30.7
NODE_BOTTOM_Y = 17.0
NODE_W = 18.5
NODE_H = 10.1


def _wrap(text: str, width: int) -> str:
    return "\n".join(textwrap.wrap(text, width=width, break_long_words=False))


def _stage_positions(stages: list[dict[str, str]]) -> dict[str, float]:
    left_margin = 12.0
    step = (CANVAS_WIDTH - 2 * left_margin) / max(len(stages) - 1, 1)
    return {stage["id"]: left_margin + index * step for index, stage in enumerate(stages)}


def _node_position(
    node: dict[str, object],
    stage_x: dict[str, float],
) -> tuple[float, float]:
    x = stage_x[str(node["stage"])] - NODE_W / 2
    y = NODE_TOP_Y if int(node["row"]) == 0 else NODE_BOTTOM_Y
    return x, y


def _draw_stage_header(ax, stage: dict[str, str], x_center: float) -> None:
    color = stage["color"]
    ax.add_patch(
        FancyBboxPatch(
            (x_center - NODE_W / 2, STAGE_Y),
            NODE_W,
            3.9,
            boxstyle="round,pad=0.35,rounding_size=1.0",
            linewidth=0,
            facecolor=color,
            alpha=0.96,
        )
    )
    ax.text(
        x_center,
        STAGE_Y + 1.95,
        stage["label"],
        ha="center",
        va="center",
        fontsize=10.6,
        color="white",
        fontweight="bold",
    )


def _draw_node(
    ax,
    node: dict[str, object],
    stage: dict[str, str],
    position: tuple[float, float],
) -> None:
    x, y = position
    color = stage["color"]
    ax.add_patch(
        FancyBboxPatch(
            (x + 0.25, y - 0.25),
            NODE_W,
            NODE_H,
            boxstyle="round,pad=0.45,rounding_size=1.2",
            linewidth=0,
            facecolor="#000000",
            alpha=0.08,
        )
    )
    ax.add_patch(
        FancyBboxPatch(
            (x, y),
            NODE_W,
            NODE_H,
            boxstyle="round,pad=0.45,rounding_size=1.2",
            linewidth=1.4,
            edgecolor=color,
            facecolor="#FFFFFF",
        )
    )
    ax.add_patch(
        FancyBboxPatch(
            (x + 1.0, y + NODE_H - 2.1),
            5.4,
            1.4,
            boxstyle="round,pad=0.16,rounding_size=0.45",
            linewidth=0,
            facecolor=color,
            alpha=0.95,
        )
    )
    ax.text(
        x + 3.7,
        y + NODE_H - 1.4,
        str(node.get("badge", str(node["artifact"]).split("/")[0])),
        ha="center",
        va="center",
        fontsize=6.3,
        color="white",
        fontweight="bold",
    )
    ax.text(
        x + 1.0,
        y + NODE_H - 3.3,
        _wrap(str(node["title"]), 19),
        ha="left",
        va="top",
        fontsize=9.8,
        color="#14212B",
        fontweight="bold",
    )
    ax.text(
        x + 1.0,
        y + 4.8,
        _wrap(str(node["body"]), 28),
        ha="left",
        va="top",
        fontsize=6.5,
        color="#3C4650",
        linespacing=1.15,
    )
    ax.text(
        x + 1.0,
        y + 1.15,
        _wrap(str(node["artifact"]), 31),
        ha="left",
        va="bottom",
        fontsize=5.6,
        color=color,
        fontweight="bold",
    )


def _draw_edge(
    ax,
    edge: dict[str, str],
    node_positions: dict[str, tuple[float, float]],
) -> None:
    source_x, source_y = node_positions[edge["from"]]
    target_x, target_y = node_positions[edge["to"]]
    if edge.get("kind") == "feedback":
        start = (source_x + NODE_W * 0.12, source_y)
        end = (target_x + NODE_W * 0.12, target_y + NODE_H)
        connection = "arc3,rad=-0.46"
        color = "#7A8793"
        alpha = 0.7
        y_label = min(start[1], end[1]) - 1.2
    else:
        start = (source_x + NODE_W, source_y + NODE_H / 2)
        end = (target_x, target_y + NODE_H / 2)
        connection = "arc3,rad=0.0"
        color = "#59636E"
        alpha = 0.72
        y_label = (start[1] + end[1]) / 2 + 1.4

    ax.add_patch(
        FancyArrowPatch(
            start,
            end,
            connectionstyle=connection,
            arrowstyle="-|>",
            mutation_scale=12,
            linewidth=1.2,
            color=color,
            alpha=alpha,
            shrinkA=5,
            shrinkB=5,
        )
    )
    ax.text(
        (start[0] + end[0]) / 2,
        y_label,
        edge["label"],
        ha="center",
        va="center",
        fontsize=6.8,
        color="#5E6872",
        bbox={
            "boxstyle": "round,pad=0.18,rounding_size=0.25",
            "facecolor": "#F7F4EE",
            "edgecolor": "none",
            "alpha": 0.92,
        },
    )


def render_workflow_figure(
    source_path: str | Path = DEFAULT_SOURCE,
    png_path: str | Path = DEFAULT_PNG,
    svg_path: str | Path = DEFAULT_SVG,
) -> None:
    source = json.loads(Path(source_path).read_text(encoding="utf-8"))
    stages = source["stages"]
    stage_by_id = {stage["id"]: stage for stage in stages}
    stage_x = _stage_positions(stages)

    fig, ax = plt.subplots(figsize=(14.4, 6.4), dpi=180)
    fig.patch.set_facecolor("#F7F4EE")
    ax.set_facecolor("#F7F4EE")
    ax.set_xlim(0, CANVAS_WIDTH)
    ax.set_ylim(0, CANVAS_HEIGHT)
    ax.axis("off")

    ax.text(
        5.0,
        56.4,
        source["title"],
        ha="left",
        va="top",
        fontsize=18.0,
        color="#14212B",
        fontweight="bold",
    )
    ax.text(
        5.0,
        52.6,
        source["subtitle"],
        ha="left",
        va="top",
        fontsize=9.2,
        color="#52606D",
    )

    ax.plot([5.0, 115.0], [42.1, 42.1], color="#D7D0C4", linewidth=1.2)

    for stage in stages:
        _draw_stage_header(ax, stage, stage_x[stage["id"]])

    node_positions: dict[str, tuple[float, float]] = {}
    for node in source["nodes"]:
        position = _node_position(node, stage_x)
        node_positions[node["id"]] = position

    for edge in source["edges"]:
        _draw_edge(ax, edge, node_positions)

    for node in source["nodes"]:
        _draw_node(ax, node, stage_by_id[str(node["stage"])], node_positions[node["id"]])

    ax.add_patch(
        FancyBboxPatch(
            (5.0, 3.3),
            110.0,
            4.4,
            boxstyle="round,pad=0.35,rounding_size=0.75",
            linewidth=1.0,
            edgecolor="#D7D0C4",
            facecolor="#FFFDF8",
        )
    )
    ax.text(
        7.0,
        5.5,
        source["footer"],
        ha="left",
        va="center",
        fontsize=8.4,
        color="#39434D",
        fontweight="bold",
    )

    Path(png_path).parent.mkdir(parents=True, exist_ok=True)
    Path(svg_path).parent.mkdir(parents=True, exist_ok=True)
    fig.savefig(png_path, dpi=180, bbox_inches="tight", pad_inches=0.08)
    fig.savefig(svg_path, format="svg", bbox_inches="tight", pad_inches=0.08)
    plt.close(fig)


def main() -> int:
    parser = argparse.ArgumentParser(description="Render the paper workflow figure.")
    parser.add_argument("--source", default=str(DEFAULT_SOURCE), help="Source JSON path.")
    parser.add_argument("--png", default=str(DEFAULT_PNG), help="Output PNG path.")
    parser.add_argument("--svg", default=str(DEFAULT_SVG), help="Output SVG path.")
    args = parser.parse_args()
    render_workflow_figure(args.source, args.png, args.svg)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
