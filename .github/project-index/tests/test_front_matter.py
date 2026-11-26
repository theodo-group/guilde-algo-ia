import pytest

from project_index.adapters.front_matter import read_front_matter
from project_index.metadata import Block, MalformedBlock, NoBlock


@pytest.mark.parametrize(
    ("text", "expected"),
    [
        ("# Title\n", NoBlock()),
        ("", NoBlock()),
        ("\n---\ntitre: x\n---\n", NoBlock()),
        ("---\ntitre: x\nstack: [a]\n---\n# T\n", Block({"titre": "x", "stack": ["a"]})),
        ("﻿---\ntitre: x\n---\n", Block({"titre": "x"})),
        ("---\r\ntitre: x\r\n---\r\n", Block({"titre": "x"})),
        ("---\n---\n", Block({})),
        ("---\n# a comment\n---\n", Block({})),
        ("---\ntitre: x\n", MalformedBlock("metadata block opened with '---' but never closed")),
        ("---\ntitre: x\n----\n", MalformedBlock("metadata block opened with '---' but never closed")),
        ("---\n- a\n- b\n---\n", MalformedBlock("metadata block is not a YAML mapping")),
        ("---\n1: x\nnull: y\n---\n", MalformedBlock("metadata keys must be text, quote them: 1, None")),
    ],
)
def test_read_front_matter(text, expected):
    assert read_front_matter(text) == expected


@pytest.mark.parametrize("block", ["titre: [", "date: 2026-13-45"])
def test_invalid_yaml_gives_a_one_line_reason(block):
    outcome = read_front_matter(f"---\n{block}\n---\n")
    assert isinstance(outcome, MalformedBlock)
    assert outcome.reason.startswith("metadata block is not valid YAML: ")
    assert "\n" not in outcome.reason
