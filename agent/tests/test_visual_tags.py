"""Unit tests for the streaming visual-tag parser."""

from __future__ import annotations

import pytest

from agent.src.visual_tags import VisualTag, VisualTagFilter, parse_and_strip_tags


def test_text_without_tags_passes_through_unchanged():
    text = "Great answer. What happens when the readiness probe starts failing?"
    clean, tags = parse_and_strip_tags(text)
    assert clean == text
    assert tags == []


def test_nested_brackets_inside_a_diagram_are_kept_in_the_tag():
    clean, tags = parse_and_strip_tags(
        "Here it is. [DIAGRAM: graph TD; A[Ingress] --> B[Service] --> C[Pod]]"
    )
    assert clean == "Here it is."
    assert tags == [VisualTag("diagram", "graph TD; A[Ingress] --> B[Service] --> C[Pod]")]


def test_yaml_list_content_survives_intact():
    manifest = (
        "apiVersion: v1\nkind: Pod\nspec:\n"
        "  containers:\n    - name: app\n    - name: sidecar"
    )
    clean, tags = parse_and_strip_tags(f"Like this. [YAML: {manifest}]")
    assert clean == "Like this."
    assert tags == [VisualTag("yaml", manifest)]


def test_card_tag_splits_into_title_and_message():
    _, tags = parse_and_strip_tags("[CARD: Probes | Liveness restarts, readiness gates traffic]")
    assert tags[0].to_payload() == {
        "type": "card",
        "title": "Probes",
        "message": "Liveness restarts, readiness gates traffic",
    }


def test_unclosed_tag_is_dropped_rather_than_spoken():
    # The regression this guards: a truncated response used to fall through the
    # parser and get read aloud as "Here DIAGRAM: graph TD; A x --> B".
    clean, tags = parse_and_strip_tags("Here [DIAGRAM: graph TD; A[x] --> B")
    assert clean == "Here"
    assert tags == []


def test_brackets_that_are_not_tags_are_left_alone():
    clean, tags = parse_and_strip_tags("Index into args[0] and env[HOME].")
    assert clean == "Index into args[0] and env[HOME]."
    assert tags == []


def test_text_streams_before_the_tag_closes():
    """The latency regression: prose must not wait for the whole response."""
    parser = VisualTagFilter()
    spoken, tags = parser.feed("Rolling updates replace pods gradually. ")
    assert spoken == "Rolling updates replace pods gradually. "
    assert tags == []

    spoken, tags = parser.feed("[DIAGRAM: graph TD; A[Old] --> B[New]")
    assert spoken == ""
    assert tags == []

    spoken, tags = parser.feed("]")
    assert spoken == ""
    assert tags == [VisualTag("diagram", "graph TD; A[Old] --> B[New]")]


@pytest.mark.parametrize("chunk_size", [1, 2, 3, 5, 8, 13])
def test_streaming_matches_single_shot_for_any_chunking(chunk_size):
    source = (
        "First, traffic hits the ingress. [CARD: Ingress | The edge of the cluster] "
        "Then it fans out. [DIAGRAM: graph TD; A[Ingress] --> B[Svc]]"
    )
    parser = VisualTagFilter()
    spoken, tags = [], []
    for i in range(0, len(source), chunk_size):
        text, found = parser.feed(source[i : i + chunk_size])
        spoken.append(text)
        tags.extend(found)
    spoken.append(parser.flush())

    assert ("".join(spoken).strip(), tags) == parse_and_strip_tags(source)


def test_opener_split_across_chunk_boundary_is_still_recognised():
    parser = VisualTagFilter()
    assert parser.feed("Look at this [DIA")[0] == "Look at this "
    spoken, tags = parser.feed("GRAM: graph TD; A --> B]")
    assert spoken == ""
    assert tags == [VisualTag("diagram", "graph TD; A --> B")]
