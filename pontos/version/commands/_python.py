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

import importlib.util
from pathlib import Path
from typing import Literal, Union

import tomlkit

from ..errors import VersionError
from ..schemes import PEP440VersioningScheme
from ..version import Version, VersionUpdate
from ._command import VersionCommand

TEMPLATE = """# pylint: disable=invalid-name

# THIS IS AN AUTOGENERATED FILE. DO NOT TOUCH!

__version__ = "{}"\n"""


# This class is used for Python Version command(s)
class PythonVersionCommand(VersionCommand):
    project_file_name = "pyproject.toml"
    _version_file_path = None
    _pyproject_toml = None

    def _get_version_from_pyproject_toml(self) -> Version:
        """
        Return the version information from the [tool.poetry] section of the
        pyproject.toml file. The version may be in non standardized form.
        """

        if (
            "tool" in self.pyproject_toml
            and "poetry" in self.pyproject_toml["tool"]  # type: ignore
            and "version" in self.pyproject_toml["tool"]["poetry"]  # type: ignore # pylint: disable=line-too-long
        ):
            return PEP440VersioningScheme.parse_version(
                self.pyproject_toml["tool"]["poetry"]["version"]
            )  # type: ignore

        raise VersionError(
            "Version information not found in "
            f"{self.project_file_path} file."
        )

    def _update_version_file(self, new_version: Version) -> None:
        """
        Update the version file with the new version
        """
        self.version_file_path.write_text(
            TEMPLATE.format(str(new_version)), encoding="utf-8"
        )

    def _update_pyproject_version(
        self,
        new_version: Version,
    ) -> None:
        """
        Update the version in the pyproject.toml file
        """
        pyproject_toml = tomlkit.parse(
            self.project_file_path.read_text(encoding="utf-8")
        )

        if "tool" not in pyproject_toml:
            tool_table = tomlkit.table()
            pyproject_toml["tool"] = tool_table

        if "poetry" not in pyproject_toml["tool"]:  # type: ignore
            poetry_table = tomlkit.table()
            # pylint: disable=line-too-long, no-member # ignore pylint (2.13.9) error: pontos/version/python.py:128:12: E1101: Instance of 'OutOfOrderTableProxy' has no 'add' member (no-member)
            pyproject_toml["tool"].add("poetry", poetry_table)  # type: ignore

        pyproject_toml["tool"]["poetry"]["version"] = str(new_version)  # type: ignore # pylint: disable=line-too-long

        self.project_file_path.write_text(
            tomlkit.dumps(pyproject_toml), encoding="utf-8"
        )

    @property
    def pyproject_toml(self) -> tomlkit.TOMLDocument:
        if self._pyproject_toml:
            return self._pyproject_toml

        if not self.project_file_path.exists():
            raise VersionError("pyproject.toml file not found.")

        self._pyproject_toml = tomlkit.parse(
            self.project_file_path.read_text(encoding="utf-8")
        )

        return self._pyproject_toml

    @property
    def version_file_path(self) -> Path:
        if self._version_file_path:
            return self._version_file_path

        if (
            "tool" not in self.pyproject_toml
            or "pontos" not in self.pyproject_toml["tool"]  # type: ignore
            or "version" not in self.pyproject_toml["tool"]["pontos"]  # type: ignore # pylint: disable=line-too-long
        ):
            raise VersionError(
                "[tool.pontos.version] section missing "
                f"in {self.project_file_path}."
            )

        pontos_version_settings = self.pyproject_toml["tool"]["pontos"][  # type: ignore # pylint: disable=line-too-long
            "version"
        ]

        try:
            self._version_file_path = Path(
                pontos_version_settings["version-module-file"]  # type: ignore
            )
            return self._version_file_path
        except tomlkit.exceptions.NonExistentKey:
            raise VersionError(
                "version-module-file key not set in [tool.pontos.version] "
                f"section of {str(self.project_file_path)}."
            ) from None

    def get_current_version(self) -> Version:
        version_module_name = self.version_file_path.stem
        module_parts = list(self.version_file_path.parts[:-1]) + [
            version_module_name
        ]
        module_name = ".".join(module_parts)
        try:
            spec = importlib.util.spec_from_file_location(
                module_name, self.version_file_path
            )
            version_module = importlib.util.module_from_spec(spec)
            spec.loader.exec_module(version_module)
            return PEP440VersioningScheme.parse_version(
                version_module.__version__
            )
        except FileNotFoundError:
            raise VersionError(
                f"Could not load version from '{module_name}'. "
                f"{self.version_file_path} not found."
            ) from None
        except ModuleNotFoundError:
            raise VersionError(
                f"Could not load version from '{module_name}'. Import failed."
            ) from None

    def verify_version(
        self, version: Union[Literal["current"], Version, None]
    ) -> None:
        current_version = self.get_current_version()
        pyproject_version = self._get_version_from_pyproject_toml()

        if pyproject_version != current_version:
            raise VersionError(
                f"The version {pyproject_version} in "
                f"{str(self.project_file_path)} doesn't match the current "
                f"version {current_version}."
            )

        if version and version != "current":
            if version != current_version:
                raise VersionError(
                    f"Provided version {version} does not match the "
                    f"current version {current_version}."
                )

    def update_version(
        self, new_version: Version, *, force: bool = False
    ) -> VersionUpdate:
        try:
            current_version = self.get_current_version()
        except VersionError:
            # maybe no version module exists yet. fallback to version from
            # pyproject.toml
            current_version = self._get_version_from_pyproject_toml()

        new_pep440_version = PEP440VersioningScheme.from_version(new_version)
        current_converted_version = self.versioning_scheme.from_version(
            current_version
        )

        if not force and new_pep440_version == current_version:
            return VersionUpdate(
                previous=current_converted_version, new=new_version
            )

        self._update_pyproject_version(new_version=new_pep440_version)

        self._update_version_file(new_version=new_pep440_version)

        return VersionUpdate(
            previous=current_converted_version,
            new=new_version,
            changed_files=[self.version_file_path, self.project_file_path],
        )
