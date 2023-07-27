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

import logging
import re
from pathlib import Path
from typing import Literal, Optional, Union

from lxml import etree

from ..errors import VersionError
from ..schemes import PEP440VersioningScheme
from ..version import Version, VersionUpdate
from ._command import VersionCommand

TEMPLATE = """# pylint: disable=invalid-name

# THIS IS AN AUTOGENERATED FILE. DO NOT TOUCH!

__version__ = "{}"\n"""


def find_file(
    filename: Path, search_path: str, search_glob: str
) -> Optional[Path]:
    """Find a file somewhere within an directory tree

    Arg:
        filename: The file to look up
        search_path: The path to look for the file
        search_glob: The glob search pattern

    Returns:
        The file as Path object, if existing
    """
    search_path = Path(search_path).resolve()
    for file_path in search_path.glob(search_glob):
        if file_path.is_file() and file_path.name == filename.name:
            return file_path
    logging.warning("File %s not found in %s.", filename.name, search_path)
    return None


def replace_string_in_file(
    file_path: Path, pattern: str, replacement: str
) -> None:
    # Read the content of the file
    content = file_path.read_text(encoding="utf-8")

    # Search for the pattern in the content
    match = re.search(pattern, content)

    # Replace the matched group (Group 1) with the replacement
    if match:
        # Write the updated content back to the file
        file_path.write_text(
            content.replace(match.group(1), replacement), encoding="utf-8"
        )
    logging.warning(
        "Couldn't match the pattern %s in the content of %s.",
        pattern,
        file_path,
    )


# This class is used for Java Version command(s)
class JavaVersionCommand(VersionCommand):
    project_file_name = "pom.xml"
    _properties_file_path = Path("src/main/resources/application.properties")
    _pom_xml: Optional[etree.Element] = None

    def _get_version_from_pom_xml(self) -> Version:
        """
        Return the version information from the <version> tag of the
        pom.xml file. The version may be in non standardized form.
        """

        pom_xml: etree.Element = self.pom_xml

        version_element = pom_xml.find("{*}version")
        if version_element is None:
            raise VersionError("Version tag missing in pom.xml")

        return PEP440VersioningScheme.parse_version(version_element.text)

    def _update_pom_version(
        self,
        new_version: Version,
    ) -> None:
        """
        Update the version in the pom.xml file
        """
        pom_xml: etree.Element = self.pom_xml

        version_element = pom_xml.find("{*}version")
        if version_element is None:
            raise VersionError("Version tag missing in pom.xml")
        version_element.text = str(new_version)

        etree.ElementTree(pom_xml).write(
            self.project_file_path, pretty_print=True, encoding="utf-8"
        )

    def _update_properties_file(
        self,
        new_version: Version,
    ) -> None:
        # update the java properties file version
        if not self._properties_file_path.exists():
            # skip if not existing
            return
        pattern = r"sentry\.release=([0-9]+\.[0-9]+\.[0-9]+)"
        replace_string_in_file(
            self._properties_file_path,
            pattern=pattern,
            replacement=str(new_version),
        )

    def _update_swagger_config(
        self,
        new_version: Version,
    ) -> None:
        # update swagger config file version
        swagger_config_file = find_file(
            filename=Path("SwaggerConfig.java"),
            search_path="src",
            search_glob="**/config/swagger/*",
        )
        if not swagger_config_file:
            # skip if not existing
            return
        pattern = r'\.version\("([0-9]+\.[0-9]+\.[0-9]+)"\)'
        replace_string_in_file(
            swagger_config_file, pattern=pattern, replacement=str(new_version)
        )

    @property
    def pom_xml(self) -> etree.Element:
        if self._pom_xml is not None:
            return self._pom_xml

        if not self.project_file_path.exists():
            raise VersionError("pom.xml file not found.")

        try:
            pom_xml: etree.ElementTree = etree.parse(self.project_file_path)
        except etree.XMLSyntaxError as e:
            raise VersionError(e) from e

        self._pom_xml = pom_xml.getroot()

        return self._pom_xml

    def get_current_version(self) -> Version:
        """Get the current version of this project
        In go the version is only defined within the repository
        tags, thus we need to check git, what tag is the latest"""
        return self._get_version_from_pom_xml()

    def verify_version(
        self, version: Union[Literal["current"], Version, None]
    ) -> None:
        """Verify the current version of this project"""
        current_version = self.get_current_version()

        if current_version != version:
            raise VersionError(
                f"Provided version {version} does not match the "
                f"current version {current_version} in "
                f"{self.project_file_path}."
            )

    def update_version(
        self, new_version: Version, *, force: bool = False
    ) -> VersionUpdate:
        try:
            package_version = self.get_current_version()
            if not force and new_version == package_version:
                return VersionUpdate(previous=package_version, new=new_version)
        except VersionError:
            # just ignore current version and override it
            package_version = None

        changed_files = [self.project_file_path]
        self._update_pom_version(new_version=new_version)
        self._update_properties_file(new_version=new_version)
        self._update_swagger_config(new_version=new_version)

        return VersionUpdate(
            previous=package_version,
            new=new_version,
            changed_files=changed_files,
        )
