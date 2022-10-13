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


from contextlib import AbstractAsyncContextManager
from types import TracebackType
from typing import Any, AsyncIterator, Dict, Iterable, Optional, Type

import httpx

from pontos.github.api.helper import (
    DEFAULT_GITHUB_API_URL,
    DEFAULT_TIMEOUT_CONFIG,
    JSON,
    JSON_OBJECT,
    _get_next_url,
)

Headers = Dict[str, str]
Params = Dict[str, str]


class GitHubAsyncRESTClient(AbstractAsyncContextManager):
    """
    A client for calling the GitHub REST API asynchronously

    Should be used as an async context manager

    Example:
        .. code-block:: python

        org = "foo"
        async with GitHubAsyncRESTClient(token) as client:
            response = await client.get(f"/orgs/{org}/repos")
    """

    def __init__(
        self,
        token: Optional[str] = None,
        url: Optional[str] = DEFAULT_GITHUB_API_URL,
        *,
        timeout: Optional[httpx.Timeout] = DEFAULT_TIMEOUT_CONFIG,
    ) -> None:
        self.token = token
        self.url = url
        self._client = httpx.AsyncClient(timeout=timeout)

    def _request_headers(
        self, *, content_type: Optional[str] = None
    ) -> Headers:
        """
        Get the default request headers
        """
        headers = {
            "Accept": "application/vnd.github.v3+json",
        }
        if self.token:
            headers["Authorization"] = f"token {self.token}"
        if content_type:
            headers["Content-Type"] = content_type

        return headers

    def _request_kwargs(
        self, *, json: Optional[JSON] = None, content: Optional[Any] = None
    ) -> Dict[str, str]:
        """
        Get the default request arguments
        """
        kwargs = {}
        if json is not None:
            kwargs["json"] = json
        if content is not None:
            kwargs["content"] = content
        return kwargs

    def _request_api_url(self, api) -> str:
        return f"{self.url}{api}"

    async def _get(
        self,
        url: str,
        *,
        params: Optional[Params] = None,
    ) -> httpx.Response:
        """
        Internal get request. Requires the full API URL.
        """
        headers = self._request_headers()
        kwargs = self._request_kwargs()
        return await self._client.get(
            url,
            headers=headers,
            params=params,
            follow_redirects=True,
            **kwargs,
        )

    async def get(
        self,
        api: str,
        *,
        params: Optional[Params] = None,
    ) -> httpx.Response:
        """
        Get request to a GitHub API

        Args:
            api: API path to use for the get request
            params: Optional params to use for the get request
        """
        url = self._request_api_url(api)
        return await self._get(url, params=params)

    async def get_all(
        self,
        api: str,
        *,
        params: Optional[Params] = None,
    ) -> AsyncIterator[httpx.Response]:
        """
        Get paginated content of a get GitHub API request

        Args:
            api: API path to use for the get request
            params: Optional params to use for the get request
        """
        response = await self.get(api, params=params)

        yield response

        next_url = _get_next_url(response)

        while next_url:
            response = await self._get(next_url, params=params)

            yield response

            next_url = _get_next_url(response)

    async def delete(
        self, api, *, params: Optional[Params] = None
    ) -> httpx.Response:
        """
        Delete request to a GitHub API

        Args:
            api: API path to use for the delete request
            params: Optional params to use for the delete request
        """
        headers = self._request_headers()
        url = self._request_api_url(api)
        return await self._client.delete(url, params=params, headers=headers)

    async def post(
        self, api, *, params: Optional[Params] = None, data: Optional[JSON]
    ) -> httpx.Response:
        """
        Post request to a GitHub API

        Args:
            api: API path to use for the post request
            params: Optional params to use for the post request
            data: Optional data to include in the post request
        """
        headers = self._request_headers()
        url = self._request_api_url(api)
        return await self._client.post(
            url, params=params, headers=headers, json=data
        )

    async def __aenter__(self) -> "GitHubAsyncRESTClient":
        await self._client.__aenter__()
        return self

    async def __aexit__(
        self,
        exc_type: Optional[Type[BaseException]],
        exc_value: Optional[BaseException],
        traceback: Optional[TracebackType],
    ) -> Optional[bool]:
        return await self._client.__aexit__(exc_type, exc_value, traceback)


class GitHubAsyncREST:
    """
    Base class for GitHub asynchronous REST classes
    """

    def __init__(self, client: GitHubAsyncRESTClient):
        self._client = client

    async def _get_paged_items(
        self, api: str, name: str, *, params: Optional[Params] = None
    ) -> Iterable[JSON_OBJECT]:
        """
        Internal method to get the paged items information from different REST
        URLs.
        """
        if not params:
            params = {}

        params["per_page"] = "100"  # max number

        items = []

        async for response in self._client.get_all(api, params=params):
            response.raise_for_status()
            data: JSON_OBJECT = response.json()
            items.extend(data.get(name, []))

        return items
