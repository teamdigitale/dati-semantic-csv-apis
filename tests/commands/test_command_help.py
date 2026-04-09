"""
Tests for help commands.
"""

import logging

import pytest
from click.testing import CliRunner

from tests.commands.utils import harness_step, make_fixtures

HELP_FIXTURES = make_fixtures(__file__)


@pytest.mark.parametrize("params", argvalues=HELP_FIXTURES)
def test_help(params, runner: CliRunner, caplog: pytest.LogCaptureFixture):
    """
    Execute the test suite defined in the associated YAML file.
    """
    caplog.set_level(logging.DEBUG)

    for step in params["steps"]:
        harness_step(step, runner, caplog)
