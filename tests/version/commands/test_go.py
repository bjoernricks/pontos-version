# -*- coding: utf-8 -*-
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

import unittest
from dataclasses import dataclass
from pathlib import Path
from unittest.mock import MagicMock, patch

from pontos.testing import temp_directory, temp_file
from pontos.version import VersionError
from pontos.version.commands._go import GoVersionCommand
from pontos.version.schemes import SemanticVersioningScheme


@dataclass
class StdOutput:
    stdout: bytes


VERSION_FILE_PATH = "version.go"
TEMPLATE = """package {}

// THIS IS AN AUTOGENERATED FILE. DO NOT TOUCH!

var version = "{}"
\n"""


class GetCurrentGoVersionCommandTestCase(unittest.TestCase):
    def test_getting_version(self):
        with temp_file(
            name="go.mod",
            change_into=True,
        ):
            version = "0.0.1"
            version_file_path = Path(VERSION_FILE_PATH)
            version_file_path.write_text(
                TEMPLATE.format("main", version), encoding="utf-8"
            )
            result_version = GoVersionCommand(
                SemanticVersioningScheme
            ).get_current_version()

            self.assertEqual(
                result_version, SemanticVersioningScheme.parse_version(version)
            )
            version_file_path.unlink()

    def test_no_version_found(self):
        exp_err_msg = "No version found in the version.go file."
        with temp_file(
            name="go.mod",
            change_into=True,
        ), self.assertRaisesRegex(
            VersionError,
            exp_err_msg,
        ):
            version_file_path = Path(VERSION_FILE_PATH)
            version_file_path.touch()
            GoVersionCommand(SemanticVersioningScheme).get_current_version()

    def test_no_version_file(self):
        exp_err_msg = (
            "No version.go file found. This file is required for pontos"
        )
        with temp_file(
            name="go.mod",
            change_into=True,
        ), self.assertRaisesRegex(
            VersionError,
            exp_err_msg,
        ):
            GoVersionCommand(SemanticVersioningScheme).get_current_version()

    def test_invalid_version(self):
        with temp_file(
            name="go.mod",
            change_into=True,
        ), self.assertRaisesRegex(
            VersionError, "abc is not valid SemVer string"
        ):
            version_file_path = Path(VERSION_FILE_PATH)
            version_file_path.write_text(
                TEMPLATE.format("main", "abc"), encoding="utf-8"
            )
            GoVersionCommand(SemanticVersioningScheme).get_current_version()


class VerifyGoVersionCommandTestCase(unittest.TestCase):
    def test_verify_version(self):
        with temp_file(
            name="go.mod",
            change_into=True,
        ), patch.object(
            GoVersionCommand,
            "get_current_version",
            MagicMock(
                return_value=SemanticVersioningScheme.parse_version("21.0.1")
            ),
        ):
            cmd = GoVersionCommand(SemanticVersioningScheme)
            cmd.verify_version(SemanticVersioningScheme.parse_version("21.0.1"))

    def test_verify_branch_not_equal(self):
        with temp_file(
            name="go.mod",
            change_into=True,
        ), patch.object(
            GoVersionCommand,
            "get_current_version",
            MagicMock(
                return_value=SemanticVersioningScheme.parse_version("21.0.1")
            ),
        ), self.assertRaisesRegex(
            VersionError,
            "Provided version 21.2.0 does not match the current version "
            "21.0.1.",
        ):
            cmd = GoVersionCommand(SemanticVersioningScheme)
            cmd.verify_version(SemanticVersioningScheme.parse_version("21.2.0"))

    def test_verify_current(self):
        with temp_file(
            name="go.mod",
            change_into=True,
        ), patch.object(
            GoVersionCommand,
            "get_current_version",
            MagicMock(
                return_value=SemanticVersioningScheme.parse_version("21.0.1")
            ),
        ):
            cmd = GoVersionCommand(SemanticVersioningScheme)
            cmd.verify_version("current")
            cmd.verify_version(version=None)

    def test_verify_current_failure(self):
        with temp_file(
            name="go.mod",
            change_into=True,
        ):
            cmd = GoVersionCommand(SemanticVersioningScheme)

            with self.assertRaisesRegex(
                VersionError,
                "^No version.go file found. This file is required for pontos",
            ):
                cmd.verify_version("current")

            with self.assertRaisesRegex(
                VersionError,
                "^No version.go file found. This file is required for pontos",
            ):
                cmd.verify_version(version=None)


class UpdateGoVersionCommandTestCase(unittest.TestCase):
    def test_no_file_update_version(self):
        with temp_directory(change_into=True) as temp:
            go_mod = temp / "go.mod"
            go_mod.touch()

            version = SemanticVersioningScheme.parse_version("22.2.2")
            updated_version_obj = GoVersionCommand(
                SemanticVersioningScheme
            ).update_version(version)
            version_file_path = Path(VERSION_FILE_PATH)
            content = version_file_path.read_text(encoding="utf-8")

            self.assertIn(str(version), content)

            self.assertIsNone(updated_version_obj.previous)
            self.assertEqual(updated_version_obj.new, version)
            self.assertEqual(
                updated_version_obj.changed_files, [version_file_path]
            )

    def test_update_version(self):
        with temp_file(name="go.mod", change_into=True):
            cmd = GoVersionCommand(SemanticVersioningScheme)
            version = SemanticVersioningScheme.parse_version("22.2.2")
            version_file_path = Path(VERSION_FILE_PATH)
            version_file_path.write_text(
                TEMPLATE.format("foo", "0.0.1"), encoding="utf-8"
            )
            updated = cmd.update_version(version)

            content = version_file_path.read_text(encoding="utf-8")
            self.assertIn(str(version), content)
            self.assertIn("foo", content)
            version_file_path.unlink()

            self.assertEqual(updated.new, version)
            self.assertEqual(
                updated.previous,
                SemanticVersioningScheme.parse_version("0.0.1"),
            )
            self.assertEqual(updated.changed_files, [version_file_path])

    def test_create_file_update_version(self):
        with temp_file(name="go.mod", change_into=True):
            with patch.object(
                GoVersionCommand,
                "get_current_version",
                MagicMock(
                    return_value=SemanticVersioningScheme.parse_version(
                        "21.0.1"
                    )
                ),
            ):
                version = SemanticVersioningScheme.parse_version("22.2.2")
                cmd = GoVersionCommand(SemanticVersioningScheme)
                updated = cmd.update_version(version)

                version_file_path = Path(VERSION_FILE_PATH)
                content = version_file_path.read_text(encoding="utf-8")

                self.assertIn(str(version), content)
                version_file_path.unlink()

                self.assertEqual(updated.new, version)
                self.assertEqual(
                    updated.previous,
                    SemanticVersioningScheme.parse_version("21.0.1"),
                )
                self.assertEqual(updated.changed_files, [version_file_path])

    def test_no_update(self):
        with temp_file(name="go.mod", change_into=True):
            cmd = GoVersionCommand(SemanticVersioningScheme)
            version = SemanticVersioningScheme.parse_version("22.2.2")
            version_file_path = Path(VERSION_FILE_PATH)
            version_file_path.write_text(
                TEMPLATE.format("main", "22.2.2"), encoding="utf-8"
            )
            updated = cmd.update_version(version)

            content = version_file_path.read_text(encoding="utf-8")
            self.assertIn(str(version), content)

            self.assertEqual(updated.new, version)
            self.assertEqual(updated.previous, version)
            self.assertEqual(updated.changed_files, [])

    def test_forced_update(self):
        with temp_file(name="go.mod", change_into=True):
            cmd = GoVersionCommand(SemanticVersioningScheme)
            version = SemanticVersioningScheme.parse_version("22.2.2")
            version_file_path = Path(VERSION_FILE_PATH)
            version_file_path.write_text(
                TEMPLATE.format("main", "22.2.2"), encoding="utf-8"
            )
            updated = cmd.update_version(version, force=True)

            content = version_file_path.read_text(encoding="utf-8")
            self.assertIn(str(version), content)

            self.assertEqual(updated.new, version)
            self.assertEqual(updated.previous, version)
            self.assertEqual(updated.changed_files, [version_file_path])


class ProjectFileGoVersionCommandTestCase(unittest.TestCase):
    def test_project_file_not_found(self):
        with temp_directory(change_into=True):
            cmd = GoVersionCommand(SemanticVersioningScheme)

            self.assertFalse(cmd.project_found())

    def test_project_file_found(self):
        with temp_file(name="go.mod", change_into=True):
            cmd = GoVersionCommand(SemanticVersioningScheme)

            self.assertTrue(cmd.project_found())
