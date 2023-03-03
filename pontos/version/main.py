# Copyright (C) 2020-2022 Greenbone Networks GmbH
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
from enum import IntEnum, auto
from typing import List, NoReturn, Optional

from pontos.errors import PontosError

from .__version__ import __version__
from .parser import initialize_default_parser
from .project import Project


class VersionExitCode(IntEnum):
    SUCCESS = 0
    NO_PROJECT = auto()
    UPDATE_ERROR = auto()
    CURRENT_VERSION_ERROR = auto()
    VERIFY_ERROR = auto()


def main(args: Optional[List[str]] = None) -> NoReturn:
    parser = initialize_default_parser()

    parsed_args = parser.parse_args(args)

    try:
        project = Project.gather_project()
    except PontosError:
        print("No project found.", file=sys.stderr)
        sys.exit(VersionExitCode.NO_PROJECT)

    if parsed_args.command == "update":
        try:
            update = project.update_version(
                parsed_args.version, force=parsed_args.force
            )
        except PontosError as e:
            print(str(e), file=sys.stderr)
            sys.exit(VersionExitCode.UPDATE_ERROR)

        if update.new == update.previous:
            print("Version is already up-to-date.")
        else:
            print(f"Updated version from {update.previous} to {update.new}.")
    elif parsed_args.command == "show":
        try:
            print(str(project.get_current_version()))
        except PontosError as e:
            print(str(e), file=sys.stderr)
            sys.exit(VersionExitCode.CURRENT_VERSION_ERROR)
    elif parsed_args.command == "verify":
        try:
            project.verify_version(parsed_args.version)
        except PontosError as e:
            print(str(e), file=sys.stderr)
            sys.exit(VersionExitCode.VERIFY_ERROR)

    sys.exit(VersionExitCode.SUCCESS)
