"""The terminal adapter -- thin on purpose, same rule as the other two.

    resume-screener rubric   docs/job_description.md
    resume-screener screen   path/to/resume.md  docs/job_description.md
    resume-screener rank     data/synthetic_resumes  docs/job_description.md

Every command takes the job description as a FILE, not a string. Postings
are long and full of newlines and quotes; making the caller paste one
through a shell is a worse interface than reading a path.

`--generate-rubric/-g` opts into a rubric written from the posting. It is
off by default so the CLI's default behaviour matches scripts/evaluate.py
and stays reproducible; pass it to see the dynamic path.

Needs ANTHROPIC_API_KEY.
"""

from __future__ import annotations

import asyncio
import json
from pathlib import Path
from typing import Annotated

import typer

from resume_screener.core.models import Verdict
from resume_screener.core.pipeline import rank_all, rubric_for, screen_one
from resume_screener.core.rubric_gen import GeneratedRubric, RubricGenerationError

app = typer.Typer(
    add_completion=False,
    help="Screen resumes against a job posting. Advisory only -- never a hiring decision.",
)

JobDescription = Annotated[
    Path,
    typer.Argument(exists=True, dir_okay=False, readable=True, help="Path to the job posting."),
]


def _read(path: Path) -> str:
    return path.read_text(encoding="utf-8")


def _fail(message: str) -> None:
    typer.secho(message, fg=typer.colors.RED, err=True)
    raise typer.Exit(code=1)


async def _resolve_rubric(job_description: str, generate: bool) -> GeneratedRubric | None:
    """None means the hand-written rubric in prompts/rubric.md."""
    if not generate:
        return None
    typer.secho("Writing a rubric for this posting...", fg=typer.colors.BLUE, err=True)
    rubric = await rubric_for(job_description)
    typer.secho(
        f"  {rubric.role_title}: {', '.join(d.name for d in rubric.dimensions)}\n",
        fg=typer.colors.BLUE,
        err=True,
    )
    return rubric


def _print_verdict(verdict: Verdict, *, show_panel: bool) -> None:
    colour = {
        "advance": typer.colors.GREEN,
        "hold": typer.colors.YELLOW,
        "reject": typer.colors.RED,
    }[verdict.recommendation.value]

    typer.secho(
        f"{verdict.candidate.name}  {verdict.score:.1f}/10  "
        f"{verdict.recommendation.value.upper()}",
        fg=colour,
        bold=True,
    )
    if show_panel:
        for panel in verdict.panel_scores:
            flag = "  (unreadable response)" if panel.parse_failed else ""
            typer.echo(f"    {panel.agent_name:<38} {panel.score:>4.1f}{flag}")
    if verdict.review_reason:
        typer.secho(f"    needs review: {verdict.review_reason}", fg=typer.colors.YELLOW)


@app.command()
def rubric(
    job_description: JobDescription,
    as_json: Annotated[bool, typer.Option("--json", help="Emit the rubric as JSON.")] = False,
) -> None:
    """Write the scoring rubric for a posting, without screening anyone."""
    try:
        generated = asyncio.run(rubric_for(_read(job_description)))
    except (RubricGenerationError, RuntimeError) as exc:
        _fail(str(exc))

    if as_json:
        typer.echo(json.dumps(generated.to_dict(), indent=2))
        return

    typer.secho(generated.role_title, bold=True)
    typer.echo(f"{generated.summary}\n")
    for i, dim in enumerate(generated.dimensions, start=1):
        typer.secho(f"{i}. {dim.title}  [{dim.name}]", bold=True)
        typer.echo(f"   {dim.criteria}\n")
        typer.echo(f"   agent brief: {dim.lens}\n")


@app.command()
def screen(
    resume: Annotated[Path, typer.Argument(exists=True, dir_okay=False, readable=True)],
    job_description: JobDescription,
    generate_rubric: Annotated[
        bool, typer.Option("--generate-rubric", "-g", help="Write a rubric from the posting.")
    ] = False,
) -> None:
    """Score one resume."""

    async def run() -> None:
        jd = _read(job_description)
        chosen = await _resolve_rubric(jd, generate_rubric)
        verdict = await screen_one(str(resume), jd, rubric=chosen)
        _print_verdict(verdict, show_panel=True)
        typer.echo(f"\n{verdict.rationale}")

    try:
        asyncio.run(run())
    except (RubricGenerationError, RuntimeError) as exc:
        _fail(str(exc))


@app.command()
def rank(
    resume_dir: Annotated[Path, typer.Argument(exists=True, file_okay=False, readable=True)],
    job_description: JobDescription,
    top: Annotated[int, typer.Option(help="How many to display. All are still screened.")] = 10,
    generate_rubric: Annotated[
        bool, typer.Option("--generate-rubric", "-g", help="Write a rubric from the posting.")
    ] = False,
) -> None:
    """Screen a folder of resumes and show the top N, best first."""

    async def run() -> None:
        jd = _read(job_description)
        chosen = await _resolve_rubric(jd, generate_rubric)
        verdicts = await rank_all(str(resume_dir), jd, rubric=chosen)
        if not verdicts:
            _fail(f"No readable resumes in {resume_dir}.")

        for verdict in verdicts[:top]:
            _print_verdict(verdict, show_panel=False)

        flagged = sum(1 for v in verdicts if v.review_reason)
        typer.echo(
            f"\n{len(verdicts)} screened, showing {min(top, len(verdicts))}. "
            f"{flagged} flagged for human review."
        )
        typer.secho(
            "Advisory only. Confirm every one of these yourself before acting.",
            fg=typer.colors.YELLOW,
        )

    try:
        asyncio.run(run())
    except (RubricGenerationError, RuntimeError) as exc:
        _fail(str(exc))


if __name__ == "__main__":
    app()
