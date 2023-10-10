# SPDX-FileCopyrightText: 2021-2023 Greenbone AG
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

from pontos.github.actions.argparser import parse_args
from pontos.terminal.null import NullTerminal
from pontos.terminal.rich import RichTerminal


def main(args=None):
    parsed_args = parse_args(args)

    if parsed_args.quiet:
        term = NullTerminal()
    else:
        term = RichTerminal()

    parsed_args.func(term, parsed_args)


if __name__ == "__main__":
    main()
