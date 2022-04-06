# Copyright (C) 2022 Greenbone Networks GmbH
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

# pylint: disable=no-member

from argparse import Namespace
import io
from pathlib import Path
import unittest
from unittest.mock import Mock
from pontos.github.api import FileStatus

from pontos.github.argparser import parse_args
from pontos.github.cmds import (
    file_status,
    create_pull_request,
    update_pull_request,
)


class TestArgparsing(unittest.TestCase):
    def setUp(self):
        self.term = Mock()

    def test_create_pr_parse_args(self):
        argv = [
            "pr",
            "create",
            "foo/bar",
            "baz",
            "main",
            "baz in main",
        ]

        parsed_args = parse_args(argv)

        template = Path().cwd() / 'pontos/github/pr_template.md'

        self.assertEqual(parsed_args.command, "pr")
        self.assertEqual(parsed_args.token, "GITHUB_TOKEN")
        self.assertEqual(parsed_args.body, template.read_text(encoding='utf-8'))
        self.assertEqual(parsed_args.pr_func, create_pull_request)
        self.assertEqual(parsed_args.repo, "foo/bar")
        self.assertEqual(parsed_args.target, "main")
        self.assertEqual(parsed_args.title, "baz in main")

    def test_create_pr_parse_args_fail(self):
        argv = ["pr", "create", "foo/bar"]

        with self.assertRaises(SystemExit):
            parse_args(argv)

    def test_update_pr_parse_args(self):
        argv = [
            "pr",
            "update",
            "foo/bar",
            "123",
            "--body",
            "foo",
            "--target",
            "main",
            "--title",
            "baz in main",
        ]

        parsed_args = parse_args(argv)

        self.assertEqual(parsed_args.command, "pr")
        self.assertEqual(parsed_args.token, "GITHUB_TOKEN")
        self.assertEqual(parsed_args.body, "foo")
        self.assertEqual(parsed_args.pr_func, update_pull_request)
        self.assertEqual(parsed_args.repo, "foo/bar")
        self.assertEqual(parsed_args.pull_request, 123)
        self.assertEqual(parsed_args.target, "main")
        self.assertEqual(parsed_args.title, "baz in main")

    def test_update_pr_parse_args_fail(self):
        argv = ["pr", "update", "foo/bar"]

        with self.assertRaises(SystemExit):
            parse_args(argv)

    def test_fs_parse_args(self):
        argv = [
            "FS",
            "foo/bar",
            "8",
            "-o",
            "some.file",
        ]

        parsed_args = parse_args(argv)
        output = io.open(Path("some.file"), mode='w', encoding='utf-8')

        expected_args = Namespace(
            command='FS',
            func=file_status,
            repo='foo/bar',
            pull_request=8,
            output=output,
            status=[FileStatus.ADDED, FileStatus.MODIFIED],
            token='GITHUB_TOKEN',
            pages=30,
        )

        self.assertEqual(type(parsed_args.output), type(expected_args.output))
        self.assertEqual(parsed_args.command, expected_args.command)
        self.assertEqual(parsed_args.func, expected_args.func)
        self.assertEqual(parsed_args.repo, expected_args.repo)
        self.assertEqual(parsed_args.pull_request, expected_args.pull_request)
        self.assertEqual(parsed_args.status, expected_args.status)
        self.assertEqual(parsed_args.token, expected_args.token)
        self.assertEqual(parsed_args.pages, expected_args.pages)

        output.close()
        parsed_args.output.close()
