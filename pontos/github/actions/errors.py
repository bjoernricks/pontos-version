# SPDX-FileCopyrightText: 2022-2023 Greenbone AG
#
# SPDX-License-Identifier: GPL-3.0-or-later
#


from pontos.errors import PontosError


class GitHubActionsError(PontosError):
    """
    A GitHub Actions related error has occurred
    """
