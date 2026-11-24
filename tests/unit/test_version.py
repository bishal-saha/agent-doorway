import re

from agent_doorway import __version__


def test_version_is_semver() -> None:
    assert re.fullmatch(r"\d+\.\d+\.\d+", __version__)
    assert __version__ == "0.1.0"
