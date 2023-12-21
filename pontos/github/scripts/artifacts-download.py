# SPDX-FileCopyrightText: 2022-2023 Greenbone AG
#
# SPDX-License-Identifier: GPL-3.0-or-later
#

"""
This script downloads a single artifacts of a given repository
"""

from argparse import ArgumentParser, Namespace
from pathlib import Path

from rich.progress import Progress

from pontos.github.api import GitHubAsyncRESTApi


def add_script_arguments(parser: ArgumentParser) -> None:
    parser.add_argument("repository")
    parser.add_argument("artifact", help="ID of the artifact to download")
    parser.add_argument(
        "--file",
        help="File to write the artifact to. Default: %(default)s",
        default="out.file",
        type=Path,
    )


async def github_script(api: GitHubAsyncRESTApi, args: Namespace) -> int:
    with args.file.open("wb") as f, Progress() as rich_progress:
        task_id = rich_progress.add_task(
            f"[red]Downloading Artifact {args.artifact}... ", total=None
        )
        async with api.artifacts.download(
            args.repository, args.artifact
        ) as download:
            async for content, progress in download:
                rich_progress.advance(task_id, progress or 1)
                f.write(content)

            rich_progress.update(task_id, total=1, completed=1)

    return 0
