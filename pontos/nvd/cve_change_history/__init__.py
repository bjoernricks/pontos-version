# SPDX-FileCopyrightText: 2023 Greenbone AG
#
# SPDX-License-Identifier: GPL-3.0-or-later

import asyncio
from argparse import ArgumentParser, Namespace
from typing import Callable

from pontos.nvd.cve_change_history.api import CVEChangeHistoryApi

__all__ = ("CVEChangeHistoryApi",)


async def query_changes(args: Namespace) -> None:
    async with CVEChangeHistoryApi(token=args.token) as api:
        async for cve in api.cve_changes(
            cve_id=args.cve_id, event_name=args.event_name
        ):
            print(cve)


def cve_changes() -> None:
    parser = ArgumentParser()
    parser.add_argument("--token", help="API key to use for querying.")
    parser.add_argument("--cve-id", help="Get history for a specific CVE")
    parser.add_argument(
        "--event-name", help="Get all CVE associated with a specific event name"
    )

    main(parser, query_changes)


def main(parser: ArgumentParser, func: Callable) -> None:
    try:
        args = parser.parse_args()
        asyncio.run(func(args))
    except KeyboardInterrupt:
        pass
