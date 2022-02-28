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


class Autoflake(PythonToolBase):
    options_scope = "autoflake"
    help = "The Autoflake Python code formatter (https://github.com/myint/autoflake)."

    default_version = "autoflake==1.4"
    default_main = ConsoleScript("autoflake")

    register_interpreter_constraints = True
    default_interpreter_constraints = ["CPython>=3.7,<4"]

    register_lockfile = True
    default_lockfile_resource = ("pants.backend.python.lint.autoflake", "lockfile.txt")
    default_lockfile_path = "src/python/pants/backend/python/lint/autoflake/lockfile.txt"
    default_lockfile_url = git_url(default_lockfile_path)

    skip = BoolOption(
        "--skip",
        default=False,
        help=f"Don't use Autoflake when running `{bin_name()} fmt` and `{bin_name()} lint`",
    )
    args = ArgsListOption(
        help=lambda cls: (
            "Arguments to pass directly to Autoflake, e.g. "
            f'`--{cls.options_scope}-args="--target-version=py37 --quiet"`'
        ),
    )


class AutoflakeLockfileSentinel(GenerateToolLockfileSentinel):
    resolve_name = Autoflake.options_scope


@rule()
async def setup_autoflake_lockfile(
    _: AutoflakeLockfileSentinel, autoflake: Autoflake
) -> GeneratePythonLockfile:
    return GeneratePythonLockfile.from_tool(autoflake)


def rules():
    return (
        *collect_rules(),
        *lockfile.rules(),
        UnionRule(GenerateToolLockfileSentinel, AutoflakeLockfileSentinel),
    )
