"""Streaming parser for the tutor's inline visual tags.

The tutor appends structured tags to its spoken answer so the browser can
render a diagram, a manifest or a summary card alongside the audio:

    [DIAGRAM: graph TD; A[Ingress] --> B[Pod]]
    [YAML: apiVersion: v1 ...]
    [CARD: Title | takeaway]

The parser is incremental on purpose. Buffering the whole LLM response before
handing anything to TTS costs the entire generation time in added latency, so
text streams straight through and only the inside of an open tag is held back.
A tag that never closes (a truncated response) is dropped rather than spoken.
"""

from __future__ import annotations

from dataclasses import dataclass

#: Openers include the colon, so `[Ingress]` inside a diagram is never mistaken
#: for one. Longest first is not required -- no opener is a prefix of another.
_OPENERS: tuple[tuple[str, str], ...] = (
    ("[DIAGRAM:", "diagram"),
    ("[YAML:", "yaml"),
    ("[CARD:", "card"),
)
_MAX_OPENER_LEN = max(len(opener) for opener, _ in _OPENERS)


@dataclass(frozen=True)
class VisualTag:
    """One complete tag lifted out of the response."""

    type: str
    content: str

    def to_payload(self) -> dict[str, str]:
        """The JSON shape published to the browser over the data channel."""
        if self.type == "card":
            title, _, message = self.content.partition("|")
            return {
                "type": "card",
                "title": title.strip() or "Key Concept",
                "message": message.strip() or self.content.strip(),
            }
        return {"type": self.type, "content": self.content}


class VisualTagFilter:
    """Incrementally strips visual tags out of a text stream.

    Feed it chunks as they arrive; each call returns the text that is safe to
    speak now plus any tags that completed in this chunk. Call `flush()` once
    the stream ends.
    """

    def __init__(self) -> None:
        self._pending = ""
        self._tag_type: str | None = None
        self._tag_buf = ""
        self._depth = 0

    @property
    def inside_tag(self) -> bool:
        return self._tag_type is not None

    def feed(self, chunk: str) -> tuple[str, list[VisualTag]]:
        self._pending += chunk
        out: list[str] = []
        tags: list[VisualTag] = []

        while self._pending:
            if self.inside_tag:
                if not self._consume_tag_body(tags):
                    break
                continue

            start = self._pending.find("[")
            if start == -1:
                out.append(self._pending)
                self._pending = ""
                break

            out.append(self._pending[:start])
            self._pending = self._pending[start:]

            opener = self._match_opener()
            if opener is not None:
                text, self._tag_type = opener
                self._pending = self._pending[len(text) :]
                self._tag_buf = ""
                self._depth = 1
                continue

            if self._could_still_become_opener():
                # A boundary landed mid-opener ("Here [DIA" | "GRAM: ...").
                # Hold the fragment back until the next chunk decides it.
                break

            # A plain bracket, e.g. prose or markdown. Emit and keep scanning.
            out.append("[")
            self._pending = self._pending[1:]

        return "".join(out), tags

    def flush(self) -> str:
        """End of stream: return any held-back text, dropping an unclosed tag."""
        if self.inside_tag:
            self._tag_type = None
            self._tag_buf = ""
            self._depth = 0
            self._pending = ""
            return ""

        text, self._pending = self._pending, ""
        return text

    def _match_opener(self) -> tuple[str, str] | None:
        for text, tag_type in _OPENERS:
            if self._pending.startswith(text):
                return text, tag_type
        return None

    def _could_still_become_opener(self) -> bool:
        if len(self._pending) >= _MAX_OPENER_LEN:
            return False
        return any(opener.startswith(self._pending) for opener, _ in _OPENERS)

    def _consume_tag_body(self, tags: list[VisualTag]) -> bool:
        """Scan for the tag's matching `]`. Returns False if it needs more input."""
        for idx, char in enumerate(self._pending):
            if char == "[":
                self._depth += 1
            elif char == "]":
                self._depth -= 1
                if self._depth == 0:
                    assert self._tag_type is not None
                    content = (self._tag_buf + self._pending[:idx]).strip()
                    tags.append(VisualTag(self._tag_type, content))
                    self._pending = self._pending[idx + 1 :]
                    self._tag_type = None
                    self._tag_buf = ""
                    return True

        self._tag_buf += self._pending
        self._pending = ""
        return False


def parse_and_strip_tags(text: str) -> tuple[str, list[VisualTag]]:
    """Non-streaming convenience wrapper, used by the tests."""
    parser = VisualTagFilter()
    clean, tags = parser.feed(text)
    return (clean + parser.flush()).strip(), tags
