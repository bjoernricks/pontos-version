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

# pylint: disable=too-many-lines, redefined-builtin

import unittest
from pathlib import Path
from unittest.mock import MagicMock, patch

import httpx

from pontos.github.api import GitHubRESTApi, RepositoryType
from pontos.github.api.errors import GitHubApiError
from pontos.github.api.organizations import (
    GitHubAsyncRESTOrganizations,
    InvitationRole,
    MemberFilter,
    MemberRole,
)
from tests import AsyncIteratorMock, aiter, anext
from tests.github.api import (
    GitHubAsyncRESTTestCase,
    create_response,
    default_request,
)

here = Path(__file__).parent


class GitHubAsyncRESTOrganizationsTestCase(GitHubAsyncRESTTestCase):
    api_cls = GitHubAsyncRESTOrganizations

    async def test_exists(self):
        response = create_response(is_success=True)
        self.client.get.return_value = response

        self.assertTrue(await self.api.exists("foo"))

        self.client.get.assert_awaited_once_with("/orgs/foo")

    async def test_not_exists(self):
        response = create_response(is_success=False)
        self.client.get.return_value = response

        self.assertFalse(await self.api.exists("foo"))

        self.client.get.assert_awaited_once_with("/orgs/foo")

    async def test_get_repositories(self):
        response1 = create_response()
        response1.json.return_value = [{"id": 1}]
        response2 = create_response()
        response2.json.return_value = [{"id": 2}, {"id": 3}]

        self.client.get_all.return_value = AsyncIteratorMock(
            [response1, response2]
        )

        async_it = aiter(self.api.get_repositories("foo"))
        repo = await anext(async_it)
        self.assertEqual(repo["id"], 1)
        repo = await anext(async_it)
        self.assertEqual(repo["id"], 2)
        repo = await anext(async_it)
        self.assertEqual(repo["id"], 3)

        with self.assertRaises(StopAsyncIteration):
            await anext(async_it)

        self.client.get_all.assert_called_once_with(
            "/orgs/foo/repos",
            params={"per_page": "100", "type": "all"},
        )

    async def test_get_private_repositories(self):
        response1 = create_response()
        response1.json.return_value = [{"id": 1}]
        response2 = create_response()
        response2.json.return_value = [{"id": 2}, {"id": 3}]

        self.client.get_all.return_value = AsyncIteratorMock(
            [response1, response2]
        )

        async_it = aiter(
            self.api.get_repositories(
                "foo", repository_type=RepositoryType.PRIVATE
            )
        )
        repo = await anext(async_it)
        self.assertEqual(repo["id"], 1)
        repo = await anext(async_it)
        self.assertEqual(repo["id"], 2)
        repo = await anext(async_it)
        self.assertEqual(repo["id"], 3)

        with self.assertRaises(StopAsyncIteration):
            await anext(async_it)

        self.client.get_all.assert_called_once_with(
            "/orgs/foo/repos",
            params={"per_page": "100", "type": "private"},
        )

    async def test_members(self):
        response1 = create_response()
        response1.json.return_value = [{"id": 1}]
        response2 = create_response()
        response2.json.return_value = [{"id": 2}, {"id": 3}]

        self.client.get_all.return_value = AsyncIteratorMock(
            [response1, response2]
        )

        async_it = aiter(self.api.members("foo"))
        member = await anext(async_it)
        self.assertEqual(member["id"], 1)
        member = await anext(async_it)
        self.assertEqual(member["id"], 2)
        member = await anext(async_it)
        self.assertEqual(member["id"], 3)

        with self.assertRaises(StopAsyncIteration):
            await anext(async_it)

        self.client.get_all.assert_called_once_with(
            "/orgs/foo/members",
            params={"per_page": "100", "filter": "all", "role": "all"},
        )

    async def test_members_admins(self):
        response1 = create_response()
        response1.json.return_value = [{"id": 1}]
        response2 = create_response()
        response2.json.return_value = [{"id": 2}, {"id": 3}]

        self.client.get_all.return_value = AsyncIteratorMock(
            [response1, response2]
        )

        async_it = aiter(self.api.members("foo", role=MemberRole.ADMIN))
        member = await anext(async_it)
        self.assertEqual(member["id"], 1)
        member = await anext(async_it)
        self.assertEqual(member["id"], 2)
        member = await anext(async_it)
        self.assertEqual(member["id"], 3)

        with self.assertRaises(StopAsyncIteration):
            await anext(async_it)

        self.client.get_all.assert_called_once_with(
            "/orgs/foo/members",
            params={"per_page": "100", "filter": "all", "role": "admin"},
        )

    async def test_members_filter(self):
        response1 = create_response()
        response1.json.return_value = [{"id": 1}]
        response2 = create_response()
        response2.json.return_value = [{"id": 2}, {"id": 3}]

        self.client.get_all.return_value = AsyncIteratorMock(
            [response1, response2]
        )

        async_it = aiter(
            self.api.members("foo", member_filter=MemberFilter.TWO_FA_DISABLED)
        )
        member = await anext(async_it)
        self.assertEqual(member["id"], 1)
        member = await anext(async_it)
        self.assertEqual(member["id"], 2)
        member = await anext(async_it)
        self.assertEqual(member["id"], 3)

        with self.assertRaises(StopAsyncIteration):
            await anext(async_it)

        self.client.get_all.assert_called_once_with(
            "/orgs/foo/members",
            params={"per_page": "100", "filter": "2fa_disabled", "role": "all"},
        )

    async def test_invite_email(self):
        response = create_response(is_success=False)
        self.client.post.return_value = response

        await self.api.invite(
            "foo",
            email="foo@bar.com",
        )

        self.client.post.assert_awaited_once_with(
            "/orgs/foo/invitations",
            data={"role": "direct_member", "email": "foo@bar.com"},
        )

    async def test_invite_invitee(self):
        response = create_response(is_success=False)
        self.client.post.return_value = response

        await self.api.invite(
            "foo",
            invitee_id="foo",
        )

        self.client.post.assert_awaited_once_with(
            "/orgs/foo/invitations",
            data={"role": "direct_member", "invitee_id": "foo"},
        )

    async def test_invite_missing_user(self):
        response = create_response(is_success=False)
        self.client.post.return_value = response

        with self.assertRaises(GitHubApiError):
            await self.api.invite("foo")

    async def test_invite_with_teams(self):
        response = create_response(is_success=False)
        self.client.post.return_value = response

        await self.api.invite("foo", email="foo@bar.com", team_ids=("1", "2"))

        self.client.post.assert_awaited_once_with(
            "/orgs/foo/invitations",
            data={
                "role": "direct_member",
                "email": "foo@bar.com",
                "team_ids": ["1", "2"],
            },
        )

    async def test_invite_with_role(self):
        response = create_response(is_success=False)
        self.client.post.return_value = response

        await self.api.invite(
            "foo", email="foo@bar.com", role=InvitationRole.ADMIN
        )

        self.client.post.assert_awaited_once_with(
            "/orgs/foo/invitations",
            data={
                "role": "admin",
                "email": "foo@bar.com",
            },
        )

    async def test_remove_member(self):
        response = create_response(is_success=False)
        self.client.delete.return_value = response

        await self.api.remove_member("foo", "bar")

        self.client.delete.assert_awaited_once_with(
            "/orgs/foo/memberships/bar",
        )

    async def test_remove_member_failure(self):
        response = create_response()
        self.client.delete.side_effect = httpx.HTTPStatusError(
            "404", request=MagicMock(), response=response
        )

        with self.assertRaises(httpx.HTTPStatusError):
            await self.api.remove_member("foo", "bar")

        self.client.delete.assert_awaited_once_with(
            "/orgs/foo/memberships/bar",
        )

    async def test_outside_collaborators(self):
        response1 = create_response()
        response1.json.return_value = [{"id": 1}]
        response2 = create_response()
        response2.json.return_value = [{"id": 2}, {"id": 3}]

        self.client.get_all.return_value = AsyncIteratorMock(
            [response1, response2]
        )

        async_it = aiter(self.api.outside_collaborators("foo"))
        member = await anext(async_it)
        self.assertEqual(member["id"], 1)
        member = await anext(async_it)
        self.assertEqual(member["id"], 2)
        member = await anext(async_it)
        self.assertEqual(member["id"], 3)

        with self.assertRaises(StopAsyncIteration):
            await anext(async_it)

        self.client.get_all.assert_called_once_with(
            "/orgs/foo/outside_collaborators",
            params={"per_page": "100", "filter": "all"},
        )

    async def test_outside_collaborators_filter(self):
        response1 = create_response()
        response1.json.return_value = [{"id": 1}]
        response2 = create_response()
        response2.json.return_value = [{"id": 2}, {"id": 3}]

        self.client.get_all.return_value = AsyncIteratorMock(
            [response1, response2]
        )

        async_it = aiter(
            self.api.outside_collaborators(
                "foo", member_filter=MemberFilter.TWO_FA_DISABLED
            )
        )
        member = await anext(async_it)
        self.assertEqual(member["id"], 1)
        member = await anext(async_it)
        self.assertEqual(member["id"], 2)
        member = await anext(async_it)
        self.assertEqual(member["id"], 3)

        with self.assertRaises(StopAsyncIteration):
            await anext(async_it)

        self.client.get_all.assert_called_once_with(
            "/orgs/foo/outside_collaborators",
            params={"per_page": "100", "filter": "2fa_disabled"},
        )

    async def test_remove_outside_collaborator(self):
        response = create_response(is_success=False)
        self.client.delete.return_value = response

        await self.api.remove_outside_collaborator("foo", "bar")

        self.client.delete.assert_awaited_once_with(
            "/orgs/foo/outside_collaborators/bar",
        )

    async def test_remove_outside_collaborator_failure(self):
        response = create_response()
        self.client.delete.side_effect = httpx.HTTPStatusError(
            "404", request=MagicMock(), response=response
        )

        with self.assertRaises(httpx.HTTPStatusError):
            await self.api.remove_outside_collaborator("foo", "bar")

        self.client.delete.assert_awaited_once_with(
            "/orgs/foo/outside_collaborators/bar",
        )


class GitHubOrganizationsTestCase(unittest.TestCase):
    @patch("pontos.github.api.api.httpx.get")
    def test_organization_exists(self, requests_mock: MagicMock):
        response = MagicMock()
        response.ok = True
        requests_mock.return_value = response

        api = GitHubRESTApi("12345")
        exists = api.organisation_exists("foo")

        args, kwargs = default_request(
            "https://api.github.com/orgs/foo",
        )
        requests_mock.assert_called_once_with(*args, **kwargs)
        self.assertTrue(exists)

    @patch("pontos.github.api.api.httpx.get")
    def test_organization_not_exists(self, requests_mock: MagicMock):
        response = MagicMock()
        response.is_success = False
        requests_mock.return_value = response

        api = GitHubRESTApi("12345")
        exists = api.organisation_exists("foo")

        args, kwargs = default_request(
            "https://api.github.com/orgs/foo",
        )
        requests_mock.assert_called_once_with(*args, **kwargs)
        self.assertFalse(exists)

    @patch("pontos.github.api.api.httpx.get")
    def test_get_repositories(self, requests_mock: MagicMock):
        api = GitHubRESTApi("12345")
        response1 = httpx.Response(
            status_code=200,
            json={"public_repos": 1, "total_private_repos": 1},
            request=MagicMock(),
        )
        response2 = httpx.Response(
            status_code=200,
            json=[{"foo": "bar"}, {"foo": "baz"}],
            request=MagicMock(),
        )
        requests_mock.side_effect = [response1, response2]
        ret = api.get_repositories(
            orga="foo", repository_type=RepositoryType.ALL
        )

        args, kwargs = default_request(
            "https://api.github.com/orgs/foo",
        )
        requests_mock.assert_any_call(*args, **kwargs)
        args2, kwargs2 = default_request(
            "https://api.github.com/orgs/foo/repos",
            params={"per_page": 100, "page": 1, "type": "all"},
        )
        requests_mock.assert_any_call(*args2, **kwargs2)
        self.assertEqual(ret, [{"foo": "bar"}, {"foo": "baz"}])

    @patch("pontos.github.api.api.httpx.get")
    def test_get_organization_repository_number_all(
        self, requests_mock: MagicMock
    ):
        api = GitHubRESTApi("12345")
        response = httpx.Response(
            status_code=200,
            json={"public_repos": 10, "total_private_repos": 10},
            request=MagicMock(),
        )

        requests_mock.return_value = response
        ret = api.get_organization_repository_number(
            orga="foo", repository_type=RepositoryType.ALL
        )

        args, kwargs = default_request(
            "https://api.github.com/orgs/foo",
        )
        requests_mock.assert_any_call(*args, **kwargs)

        self.assertEqual(ret, 20)

    @patch("pontos.github.api.api.httpx.get")
    def test_get_organization_repository_number_private(
        self, requests_mock: MagicMock
    ):
        api = GitHubRESTApi("12345")
        response = httpx.Response(
            status_code=200,
            json={"public_repos": 10, "total_private_repos": 10},
            request=MagicMock(),
        )

        requests_mock.return_value = response
        ret = api.get_organization_repository_number(
            orga="foo", repository_type=RepositoryType.PRIVATE
        )

        args, kwargs = default_request(
            "https://api.github.com/orgs/foo",
        )
        requests_mock.assert_any_call(*args, **kwargs)

        self.assertEqual(ret, 10)

    @patch("pontos.github.api.api.httpx.get")
    def test_get_organization_repository_number_public(
        self, requests_mock: MagicMock
    ):
        api = GitHubRESTApi("12345")
        response = httpx.Response(
            status_code=200,
            json={"public_repos": 10, "total_private_repos": 10},
            request=MagicMock(),
        )

        requests_mock.return_value = response
        ret = api.get_organization_repository_number(
            orga="foo", repository_type=RepositoryType.PUBLIC
        )

        args, kwargs = default_request(
            "https://api.github.com/orgs/foo",
        )
        requests_mock.assert_any_call(*args, **kwargs)

        self.assertEqual(ret, 10)
