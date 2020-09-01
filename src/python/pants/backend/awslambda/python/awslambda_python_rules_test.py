# Copyright 2019 Pants project contributors (see CONTRIBUTORS.md).
# Licensed under the Apache License, Version 2.0 (see LICENSE).

import textwrap
from io import BytesIO
from typing import Tuple
from zipfile import ZipFile

import pytest

from pants.backend.awslambda.common.awslambda_common_rules import CreatedAWSLambda
from pants.backend.awslambda.python.awslambda_python_rules import PythonAwsLambdaFieldSet
from pants.backend.awslambda.python.awslambda_python_rules import rules as awslambda_python_rules
from pants.backend.awslambda.python.target_types import PythonAWSLambda
from pants.backend.python.target_types import PythonLibrary
from pants.engine.addresses import Address
from pants.engine.fs import DigestContents
from pants.engine.rules import QueryRule
from pants.engine.target import WrappedTarget
from pants.option.options_bootstrapper import OptionsBootstrapper
from pants.testutil.option_util import create_options_bootstrapper
from pants.testutil.rule_runner import RuleRunner


@pytest.fixture
def rule_runner() -> RuleRunner:
    return RuleRunner(
        rules=[
            *awslambda_python_rules(),
            QueryRule(CreatedAWSLambda, (PythonAwsLambdaFieldSet, OptionsBootstrapper)),
        ],
        target_types=[PythonAWSLambda, PythonLibrary],
    )


def create_python_awslambda(rule_runner: RuleRunner, addr: str) -> Tuple[str, bytes]:
    bootstrapper = create_options_bootstrapper(
        args=[
            "--backend-packages=pants.backend.awslambda.python",
            "--source-root-patterns=src/python",
        ]
    )
    target = rule_runner.request_product(WrappedTarget, [Address.parse(addr), bootstrapper]).target
    created_awslambda = rule_runner.request_product(
        CreatedAWSLambda, [PythonAwsLambdaFieldSet.create(target), bootstrapper]
    )
    created_awslambda_digest_contents = rule_runner.request_product(
        DigestContents, [created_awslambda.digest]
    )
    assert len(created_awslambda_digest_contents) == 1
    return created_awslambda.zip_file_relpath, created_awslambda_digest_contents[0].content


def test_create_hello_world_lambda(rule_runner: RuleRunner) -> None:
    rule_runner.create_file(
        "src/python/foo/bar/hello_world.py",
        textwrap.dedent(
            """
            def handler(event, context):
                print('Hello, World!')
            """
        ),
    )

    rule_runner.add_to_build_file(
        "src/python/foo/bar",
        textwrap.dedent(
            """
            python_library(
              name='hello_world',
              sources=['hello_world.py']
            )

            python_awslambda(
              name='hello_world_lambda',
              dependencies=[':hello_world'],
              handler='foo.bar.hello_world',
              runtime='python3.7'
            )
            """
        ),
    )

    zip_file_relpath, content = create_python_awslambda(
        rule_runner, "src/python/foo/bar:hello_world_lambda"
    )
    assert "hello_world_lambda.zip" == zip_file_relpath
    zipfile = ZipFile(BytesIO(content))
    names = set(zipfile.namelist())
    assert "lambdex_handler.py" in names
    assert "foo/bar/hello_world.py" in names
