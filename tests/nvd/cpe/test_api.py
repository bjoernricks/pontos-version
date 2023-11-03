# Copyright (C) 2022 Greenbone AG
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

# pylint: disable=line-too-long, arguments-differ, redefined-builtin
# ruff: noqa: E501

from datetime import datetime
from typing import Any, Dict, List, Optional
from unittest.mock import MagicMock, patch

from httpx import AsyncClient, Response

from pontos.errors import PontosError
from pontos.nvd.api import now
from pontos.nvd.cpe.api import MAX_CPES_PER_PAGE, CPEApi
from tests import AsyncMock, IsolatedAsyncioTestCase, aiter, anext
from tests.nvd import get_cpe_data


def create_cpe_response(
    cpe_name_id: str,
    *,
    update: Optional[Dict[str, Any]] = None,
    results: int = 1,
) -> MagicMock:
    data = {
        "products": [
            {"cpe": get_cpe_data({"cpe_name_id": f"{cpe_name_id}-{i}"})}
            for i in range(1, results + 1)
        ],
        "results_per_page": results,
    }
    if update:
        data.update(update)

    response = MagicMock(spec=Response)
    response.json.return_value = data
    return response


def create_cpes_responses(
    responses: int = 2, results_per_response: int = 1
) -> List[MagicMock]:
    return [
        create_cpe_response(
            cpe_name_id=f"CPE-{i}",
            update={"total_results": responses * results_per_response},
            results=results_per_response,
        )
        for i in range(1, responses + 1)
    ]


class CPEApiTestCase(IsolatedAsyncioTestCase):
    @patch("pontos.nvd.api.time.monotonic", autospec=True)
    @patch("pontos.nvd.api.AsyncClient", spec=AsyncClient)
    def setUp(self, async_client: MagicMock, monotonic_mock: MagicMock) -> None:
        self.http_client = AsyncMock()
        async_client.return_value = self.http_client
        monotonic_mock.return_value = 0
        self.api = CPEApi()

    async def test_no_cpe_name_id(self):
        with self.assertRaises(PontosError):
            await self.api.cpe(None)

    async def test_no_cpe(self):
        data = {
            "products": [],
            "results_per_page": 1,
        }
        response = MagicMock(spec=Response)
        response.json.return_value = data
        self.http_client.get.return_value = response

        with self.assertRaises(PontosError):
            await self.api.cpe("CPE-1")

    async def test_cpe(self):
        self.http_client.get.return_value = create_cpe_response("CPE-1")

        cpe = await self.api.cpe("CPE-1-1")

        self.http_client.get.assert_awaited_once_with(
            "https://services.nvd.nist.gov/rest/json/cpes/2.0",
            headers={},
            params={"cpeNameId": "CPE-1-1"},
        )

        self.assertEqual(
            cpe.cpe_name,
            "cpe:2.3:o:microsoft:windows_10_22h2:-:*:*:*:*:*:arm64:*",
        )
        self.assertEqual(cpe.cpe_name_id, "CPE-1-1")
        self.assertFalse(cpe.deprecated)
        self.assertEqual(
            cpe.last_modified, datetime(2022, 12, 9, 18, 15, 16, 973000)
        )
        self.assertEqual(cpe.created, datetime(2022, 12, 9, 16, 20, 6, 943000))

        self.assertEqual(cpe.refs, [])
        self.assertEqual(cpe.titles, [])
        self.assertEqual(cpe.deprecated_by, [])

    @patch("pontos.nvd.api.time.monotonic", autospec=True)
    @patch("pontos.nvd.api.asyncio.sleep", autospec=True)
    async def test_rate_limit(
        self,
        sleep_mock: MagicMock,
        monotonic_mock: MagicMock,
    ):
        self.http_client.get.side_effect = create_cpes_responses(8)
        monotonic_mock.side_effect = [10, 11]

        it = aiter(self.api.cpes())
        await anext(it)
        await anext(it)
        await anext(it)
        await anext(it)
        await anext(it)

        sleep_mock.assert_not_called()

        await anext(it)

        sleep_mock.assert_called_once_with(20.0)

    @patch("pontos.nvd.cpe.api.now", spec=now)
    async def test_cves_last_modified_start_date(self, now_mock: MagicMock):
        now_mock.return_value = datetime(2022, 12, 31)
        self.http_client.get.side_effect = create_cpes_responses()

        it = aiter(
            self.api.cpes(last_modified_start_date=datetime(2022, 12, 1))
        )
        cve = await anext(it)

        self.assertEqual(cve.cpe_name_id, "CPE-1-1")
        self.http_client.get.assert_awaited_once_with(
            "https://services.nvd.nist.gov/rest/json/cpes/2.0",
            headers={},
            params={
                "startIndex": 0,
                "lastModStartDate": "2022-12-01T00:00:00",
                "lastModEndDate": "2022-12-31T00:00:00",
                "resultsPerPage": MAX_CPES_PER_PAGE,
            },
        )

        self.http_client.get.reset_mock()

        cve = await anext(it)

        self.assertEqual(cve.cpe_name_id, "CPE-2-1")
        self.http_client.get.assert_awaited_once_with(
            "https://services.nvd.nist.gov/rest/json/cpes/2.0",
            headers={},
            params={
                "startIndex": 1,
                "lastModStartDate": "2022-12-01T00:00:00",
                "lastModEndDate": "2022-12-31T00:00:00",
                "resultsPerPage": 1,
            },
        )

        with self.assertRaises(StopAsyncIteration):
            cve = await anext(it)

    async def test_cves_last_modified_end_date(self):
        self.http_client.get.side_effect = create_cpes_responses()

        it = aiter(
            self.api.cpes(
                last_modified_start_date=datetime(2022, 12, 1),
                last_modified_end_date=datetime(2022, 12, 31),
            )
        )
        cve = await anext(it)

        self.assertEqual(cve.cpe_name_id, "CPE-1-1")
        self.http_client.get.assert_awaited_once_with(
            "https://services.nvd.nist.gov/rest/json/cpes/2.0",
            headers={},
            params={
                "startIndex": 0,
                "lastModStartDate": "2022-12-01T00:00:00",
                "lastModEndDate": "2022-12-31T00:00:00",
                "resultsPerPage": MAX_CPES_PER_PAGE,
            },
        )

        self.http_client.get.reset_mock()

        cve = await anext(it)

        self.assertEqual(cve.cpe_name_id, "CPE-2-1")
        self.http_client.get.assert_awaited_once_with(
            "https://services.nvd.nist.gov/rest/json/cpes/2.0",
            headers={},
            params={
                "startIndex": 1,
                "lastModStartDate": "2022-12-01T00:00:00",
                "lastModEndDate": "2022-12-31T00:00:00",
                "resultsPerPage": 1,
            },
        )

        with self.assertRaises(StopAsyncIteration):
            cve = await anext(it)

    async def test_cpes_keywords(self):
        self.http_client.get.side_effect = create_cpes_responses()

        it = aiter(self.api.cpes(keywords=["Mac OS X", "kernel"]))
        cve = await anext(it)

        self.assertEqual(cve.cpe_name_id, "CPE-1-1")
        self.http_client.get.assert_awaited_once_with(
            "https://services.nvd.nist.gov/rest/json/cpes/2.0",
            headers={},
            params={
                "startIndex": 0,
                "keywordSearch": "Mac OS X kernel",
                "keywordExactMatch": "",
                "resultsPerPage": MAX_CPES_PER_PAGE,
            },
        )

        self.http_client.get.reset_mock()

        cve = await anext(it)

        self.assertEqual(cve.cpe_name_id, "CPE-2-1")
        self.http_client.get.assert_awaited_once_with(
            "https://services.nvd.nist.gov/rest/json/cpes/2.0",
            headers={},
            params={
                "startIndex": 1,
                "resultsPerPage": 1,
                "keywordSearch": "Mac OS X kernel",
                "keywordExactMatch": "",
            },
        )

        with self.assertRaises(StopAsyncIteration):
            cve = await anext(it)

    async def test_cpes_keyword(self):
        self.http_client.get.side_effect = create_cpes_responses()

        it = aiter(self.api.cpes(keywords="macOS"))
        cve = await anext(it)

        self.assertEqual(cve.cpe_name_id, "CPE-1-1")
        self.http_client.get.assert_awaited_once_with(
            "https://services.nvd.nist.gov/rest/json/cpes/2.0",
            headers={},
            params={
                "startIndex": 0,
                "keywordSearch": "macOS",
                "resultsPerPage": MAX_CPES_PER_PAGE,
            },
        )

        self.http_client.get.reset_mock()

        cve = await anext(it)

        self.assertEqual(cve.cpe_name_id, "CPE-2-1")
        self.http_client.get.assert_awaited_once_with(
            "https://services.nvd.nist.gov/rest/json/cpes/2.0",
            headers={},
            params={
                "startIndex": 1,
                "resultsPerPage": 1,
                "keywordSearch": "macOS",
            },
        )

        with self.assertRaises(StopAsyncIteration):
            cve = await anext(it)

    async def test_cpes_cpe_match_string(self):
        self.http_client.get.side_effect = create_cpes_responses()

        it = aiter(
            self.api.cpes(
                cpe_match_string="cpe:2.3:o:microsoft:windows_10:20h2:*:*:*:*:*:*:*"
            )
        )
        cve = await anext(it)

        self.assertEqual(cve.cpe_name_id, "CPE-1-1")
        self.http_client.get.assert_awaited_once_with(
            "https://services.nvd.nist.gov/rest/json/cpes/2.0",
            headers={},
            params={
                "startIndex": 0,
                "resultsPerPage": MAX_CPES_PER_PAGE,
                "cpeMatchString": "cpe:2.3:o:microsoft:windows_10:20h2:*:*:*:*:*:*:*",
            },
        )

        self.http_client.get.reset_mock()

        cve = await anext(it)

        self.assertEqual(cve.cpe_name_id, "CPE-2-1")
        self.http_client.get.assert_awaited_once_with(
            "https://services.nvd.nist.gov/rest/json/cpes/2.0",
            headers={},
            params={
                "startIndex": 1,
                "resultsPerPage": 1,
                "cpeMatchString": "cpe:2.3:o:microsoft:windows_10:20h2:*:*:*:*:*:*:*",
            },
        )

        with self.assertRaises(StopAsyncIteration):
            cve = await anext(it)

    async def test_cpes_match_criteria_id(self):
        self.http_client.get.side_effect = create_cpes_responses()

        it = aiter(
            self.api.cpes(
                match_criteria_id="36FBCF0F-8CEE-474C-8A04-5075AF53FAF4"
            )
        )
        cve = await anext(it)

        self.assertEqual(cve.cpe_name_id, "CPE-1-1")
        self.http_client.get.assert_awaited_once_with(
            "https://services.nvd.nist.gov/rest/json/cpes/2.0",
            headers={},
            params={
                "startIndex": 0,
                "matchCriteriaId": "36FBCF0F-8CEE-474C-8A04-5075AF53FAF4",
                "resultsPerPage": MAX_CPES_PER_PAGE,
            },
        )

        self.http_client.get.reset_mock()

        cve = await anext(it)

        self.assertEqual(cve.cpe_name_id, "CPE-2-1")
        self.http_client.get.assert_awaited_once_with(
            "https://services.nvd.nist.gov/rest/json/cpes/2.0",
            headers={},
            params={
                "startIndex": 1,
                "resultsPerPage": 1,
                "matchCriteriaId": "36FBCF0F-8CEE-474C-8A04-5075AF53FAF4",
            },
        )

        with self.assertRaises(StopAsyncIteration):
            cve = await anext(it)

    async def test_cpes_request_results(self):
        self.http_client.get.side_effect = create_cpes_responses(
            results_per_response=2
        )

        it = aiter(self.api.cpes(request_results=10))
        cve = await anext(it)

        self.http_client.get.assert_awaited_once_with(
            "https://services.nvd.nist.gov/rest/json/cpes/2.0",
            headers={},
            params={
                "startIndex": 0,
                "resultsPerPage": 10,
            },
        )
        self.assertEqual(cve.cpe_name_id, "CPE-1-1")

        self.http_client.get.reset_mock()
        cve = await anext(it)
        self.assertEqual(cve.cpe_name_id, "CPE-1-2")
        self.http_client.get.assert_not_called()

        self.http_client.get.reset_mock()
        cve = await anext(it)
        self.http_client.get.assert_awaited_once_with(
            "https://services.nvd.nist.gov/rest/json/cpes/2.0",
            headers={},
            params={
                "startIndex": 2,
                "resultsPerPage": 2,
            },
        )
        self.assertEqual(cve.cpe_name_id, "CPE-2-1")

        self.http_client.get.reset_mock()
        cve = await anext(it)
        self.assertEqual(cve.cpe_name_id, "CPE-2-2")
        self.http_client.get.assert_not_called()

        self.http_client.get.reset_mock()

        with self.assertRaises(Exception):
            cve = await anext(it)

    async def test_context_manager(self):
        async with self.api:
            pass

        self.http_client.__aenter__.assert_awaited_once()
        self.http_client.__aexit__.assert_awaited_once()
