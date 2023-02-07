# -*- coding: utf-8 -*-
# Copyright (C) 2021-2022 Greenbone Networks GmbH
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

import unittest
from dataclasses import dataclass
from pathlib import Path
from unittest.mock import MagicMock, patch

from pontos.testing import temp_directory, temp_file
from pontos.version.go import GoVersionCommand
from pontos.version.helper import VersionError


@dataclass
class StdOutput:
    stdout: bytes


TEMPLATE = """package main

// THIS IS AN AUTOGENERATED FILE. DO NOT TOUCH!

var version = "0.0.1"
\n"""


class GetCurrentGoVersionCommandTestCase(unittest.TestCase):
    def test_getting_last_git_tag(self):
        with temp_file(
            "",
            name="go.mod",
            change_into=True,
        ):
            version_file_path = Path("version.go")
            version_file_path.write_text(TEMPLATE, encoding="utf-8")
            cmd = GoVersionCommand()
            version = cmd.get_current_version()

            self.assertEqual(version, "0.0.1")

            version_file_path.unlink()

    def test_no_version_tag(self):
        with temp_file(
            "",
            name="go.mod",
            change_into=True,
        ), self.assertRaisesRegex(
            VersionError,
            "No version found in the version.go file.",
        ):
            Path("version.go").touch()
            cmd = GoVersionCommand()
            cmd.get_current_version()

    def test_no_version_file(self):
        with temp_file(
            "",
            name="go.mod",
            change_into=True,
        ), self.assertRaisesRegex(
            VersionError,
            "No version.go file found. This file is required for pontos",
        ):
            cmd = GoVersionCommand()
            cmd.get_current_version()


class VerifyGoVersionCommandTestCase(unittest.TestCase):
    def test_verify_version(self):
        with temp_file(
            "",
            name="go.mod",
            change_into=True,
        ), patch.object(
            GoVersionCommand,
            "get_current_version",
            MagicMock(return_value="21.0.1"),
        ):
            cmd = GoVersionCommand()
            cmd.verify_version("21.0.1")

    def test_verify_branch_not_pep(self):
        with temp_file(
            "",
            name="go.mod",
            change_into=True,
        ), patch.object(
            GoVersionCommand,
            "get_current_version",
            MagicMock(return_value="021.02a"),
        ), self.assertRaisesRegex(
            VersionError, "The version 021.02a is not PEP 440 compliant."
        ):
            cmd = GoVersionCommand()
            cmd.verify_version("21.0.1")

    def test_verify_branch_not_equal(self):
        with temp_file(
            "",
            name="go.mod",
            change_into=True,
        ), patch.object(
            GoVersionCommand,
            "get_current_version",
            MagicMock(return_value="21.0.1"),
        ), self.assertRaisesRegex(
            VersionError,
            "Provided version 21.2 does not match the current version 21.0.1.",
        ):
            cmd = GoVersionCommand()
            cmd.verify_version("21.2")


class UpdateGoVersionCommandTestCase(unittest.TestCase):
    def test_no_update_version(self):
        cmd = GoVersionCommand()

        with self.assertRaisesRegex(
            VersionError,
            "No version.go file found. This file is required for pontos",
        ):
            cmd.update_version("22.2.2")


class ProjectFileGoVersionCommandTestCase(unittest.TestCase):
    def test_project_file_not_found(self):
        with temp_directory() as temp:
            go_mod = temp / "go.mod"
            cmd = GoVersionCommand(project_file_path=go_mod)

            self.assertIsNone(cmd.project_file_found())
            self.assertFalse(cmd.project_found())

    def test_project_file_found(self):
        with temp_file(name="go.mod") as go_mod:
            cmd = GoVersionCommand(project_file_path=go_mod)

            self.assertEqual(cmd.project_file_found(), go_mod)
            self.assertTrue(cmd.project_found())
