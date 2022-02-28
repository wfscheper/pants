# Copyright 2021 Pants project contributors (see CONTRIBUTORS.md).
# Licensed under the Apache License, Version 2.0 (see LICENSE).

from __future__ import annotations

from pants.backend.python.goals import lockfile
from pants.backend.python.goals.lockfile import GeneratePythonLockfile
from pants.backend.python.subsystems.python_tool_base import PythonToolBase
from pants.backend.python.target_types import ConsoleScript
from pants.core.goals.generate_lockfiles import GenerateToolLockfileSentinel
from pants.engine.rules import collect_rules, rule
from pants.engine.unions import UnionRule
from pants.option.option_types import ArgsListOption, BoolOption
from pants.util.docutil import bin_name, git_url


class PyUpgrade(PythonToolBase):
    options_scope = "pyupgrade"
    help = (
        "Upgrade syntax for newer versions of the language (https://github.com/asottile/pyupgrade)."
    )

    default_version = "pyupgrade>=2.31.0,<2.32"
    default_main = ConsoleScript("pyupgrade")

    register_interpreter_constraints = True
    default_interpreter_constraints = ["CPython>=3.7"]

    register_lockfile = True
    default_lockfile_resource = ("pants.backend.python.lint.pyupgrade", "lockfile.txt")
    default_lockfile_path = "src/python/pants/backend/python/lint/pyupgrade/lockfile.txt"
    default_lockfile_url = git_url(default_lockfile_path)

    skip = BoolOption(
        "--skip",
        default=False,
        help=f"Don't use pyupgrade when running `{bin_name()} fmt` and `{bin_name()} lint`.",
    )
    args = ArgsListOption(
        help=lambda cls: (
            f"Arguments to pass directly to pyupgrade, e.g. "
            f'`--{cls.options_scope}-args="--py39-plus --keep-runtime-typing"`'
        ),
    )


class PyUpgradeLockfileSentinel(GenerateToolLockfileSentinel):
    resolve_name = PyUpgrade.options_scope


@rule
def setup_pyupgrade_lockfile(
    _: PyUpgradeLockfileSentinel, pyupgrade: PyUpgrade
) -> GeneratePythonLockfile:
    return GeneratePythonLockfile.from_tool(pyupgrade)


def rules():
    return (
        *collect_rules(),
        *lockfile.rules(),
        UnionRule(GenerateToolLockfileSentinel, PyUpgradeLockfileSentinel),
    )
