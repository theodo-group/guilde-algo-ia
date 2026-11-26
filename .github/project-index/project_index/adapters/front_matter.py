"""Reads the YAML metadata block at the top of a README."""

import yaml

from project_index.constants import BYTE_ORDER_MARK, FRONT_MATTER_FENCE
from project_index.metadata import Block, FrontMatter, MalformedBlock, NoBlock


def read_front_matter(text: str) -> FrontMatter:
    """Read the metadata block of a README text.

    Returns NoBlock when the first line is not `---`, MalformedBlock when the block is
    never closed, is not a YAML mapping or has keys that are not text, and Block with its fields otherwise. An empty
    block gives a Block with no fields, which validation then reports.
    """
    lines = text.removeprefix(BYTE_ORDER_MARK).splitlines()
    if not lines or lines[0].strip() != FRONT_MATTER_FENCE:
        return NoBlock()
    closing = next((i for i, line in enumerate(lines[1:], start=1) if line.strip() == FRONT_MATTER_FENCE), None)
    if closing is None:
        return MalformedBlock(f"metadata block opened with '{FRONT_MATTER_FENCE}' but never closed")
    return parse_block("\n".join(lines[1:closing]))


def parse_block(yaml_text: str) -> FrontMatter:
    """Parse the YAML between the fences into a Block, or a MalformedBlock that says why it cannot be used."""
    try:
        fields = yaml.safe_load(yaml_text)
    except (yaml.YAMLError, ValueError) as error:  # PyYAML raises ValueError for an impossible date
        first_line = str(error).splitlines()[0]
        return MalformedBlock(f"metadata block is not valid YAML: {first_line}")
    if fields is None:
        return Block({})
    if not isinstance(fields, dict):
        return MalformedBlock("metadata block is not a YAML mapping")
    non_text_keys = [repr(key) for key in fields if not isinstance(key, str)]
    if non_text_keys:
        return MalformedBlock(f"metadata keys must be text, quote them: {', '.join(non_text_keys)}")
    return Block(fields)
