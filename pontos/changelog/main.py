# Copyright (C) 2020-2022 Greenbone AG
#
# SPDX-License-Identifier: GPL-3.0-or-later
#
# This program is free software: you can redistribute it and/or modify
# it under the terms of the GNU General Public License as published by
# the Free Software Foundation, either version 3 of the License, or
# (at your option) any later version.
#
# This program is distributed in the hope that it will be useful,
# but WITHOUT ANY WARRANTY; without even the implied warranty of
# MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
# GNU General Public License for more details.
#
# You should have received a copy of the GNU General Public License
# along with this program.  If not, see <http://www.gnu.org/licenses/>.

import sys
from argparse import ArgumentParser, Namespace
from pathlib import Path
from typing import NoReturn, Optional, Sequence

from pontos.changelog.conventional_commits import ChangelogBuilder
from pontos.errors import PontosError
from pontos.terminal.null import NullTerminal
from pontos.terminal.rich import RichTerminal
from pontos.terminal.terminal import Terminal
from pontos.version.helper import get_last_release_version
from pontos.version.schemes import (
    VERSIONING_SCHEMES,
    VersioningScheme,
    versioning_scheme_argument_type,
)


def parse_args(args: Optional[Sequence[str]] = None) -> Namespace:
    parser = ArgumentParser(
        description="Conventional commits utility.",
        prog="pontos-changelog",
    )

    parser.add_argument(
        "--config",
        "-C",
        default="changelog.toml",
        type=Path,
        help="Conventional commits config file (toml), including conventions.",
    )

    parser.add_argument(
        "--project",
        required=True,
        help="The github project",
    )

    parser.add_argument(
        "--space",
        default="greenbone",
        help="User/Team name in github",
    )

    parser.add_argument(
        "--versioning-scheme",
        help="Versioning scheme to use for parsing and handling version "
        f"information. Choices are {', '.join(VERSIONING_SCHEMES.keys())}. "
        "Default: %(default)s",
        default="pep440",
        type=versioning_scheme_argument_type,
    )

    parser.add_argument(
        "--current-version",
        help="Current version before these changes",
    )

    parser.add_argument(
        "--next-version",
        help="The planned release version",
    )

    parser.add_argument(
        "--git-tag-prefix",
        default="v",
        help="Prefix for git tag versions. Default: %(default)s",
    )

    parser.add_argument(
        "--output",
        "-o",
        type=Path,
        help="Write changelog to this file.",
    )

    parser.add_argument(
        "--quiet",
        "-q",
        action="store_true",
        help="Don't print messages to the terminal",
    )

    parsed_args = parser.parse_args(args=args)

    scheme: VersioningScheme = parsed_args.versioning_scheme
    current_version = getattr(parsed_args, "current_version", None)
    if current_version:
        parsed_args.current_version = scheme.parse_version(current_version)

    next_version = getattr(parsed_args, "next_version", None)
    if next_version:
        parsed_args.next_version = scheme.parse_version(next_version)

    return parsed_args


def main(args: Optional[Sequence[str]] = None) -> NoReturn:
    parsed_args = parse_args(args)

    term: Terminal = NullTerminal if parsed_args.quiet else RichTerminal()  # type: ignore # pylint: disable=line-too-long

    if parsed_args.current_version:
        last_version = parsed_args.current_version
    else:
        last_version = get_last_release_version(
            parsed_args.versioning_scheme.parse_version,
            git_tag_prefix=parsed_args.git_tag_prefix,
        )

    try:
        changelog_builder = ChangelogBuilder(
            config=parsed_args.config,
            project=parsed_args.project,
            space=parsed_args.space,
        )
        if parsed_args.output:
            changelog_builder.create_changelog_file(
                parsed_args.output,
                last_version=last_version,
                next_version=parsed_args.next_version,
            )
        else:
            changelog = changelog_builder.create_changelog(
                last_version=last_version,
                next_version=parsed_args.next_version,
            )
            print(changelog)
    except PontosError as e:
        term.error(str(e))
        sys.exit(1)

    sys.exit(0)


if __name__ == "__main__":
    main()
