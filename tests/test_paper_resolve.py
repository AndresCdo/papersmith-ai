"""paper-writing resolve: arXiv normalization and clean refusals.

Stdlib-only `unittest`. The transport is stubbed, so no test touches the
network: the prefix defect was measured live (`id_list=arXiv:1512.03385`
-> 706-byte entry-less feed; the bare id -> 2814 bytes with `<entry>`),
and these pin the corrected behavior.
"""
from __future__ import annotations

import sys
import unittest
import urllib.parse
from pathlib import Path

FORGE_ROOT = Path(__file__).resolve().parents[1]
SKILL_SCRIPTS = FORGE_ROOT / "skills" / "paper-writing" / "scripts"
sys.path.insert(0, str(SKILL_SCRIPTS))
sys.path.insert(0, str(FORGE_ROOT / "skills" / "_core" / "implementation"))
import paper_resolve  # noqa: E402
from impl_refusals import Refused  # noqa: E402

CONFIG = {
    "paper_writing": {
        "roles": {"resolution": ["arxiv"], "full-text": [], "discovery": []},
        "contact": "",
    }
}

EMPTY_FEED = (
    b"<?xml version='1.0' encoding='UTF-8'?>\n"
    b'<feed xmlns="http://www.w3.org/2005/Atom"><id>x</id><title>empty</title></feed>'
)

ENTRY_FEED = (
    b"<?xml version='1.0' encoding='UTF-8'?>\n"
    b'<feed xmlns="http://www.w3.org/2005/Atom">\n'
    b"<entry><title>Deep Residual Learning</title>"
    b"<summary>We present a residual  learning framework.</summary>"
    b'<link href="https://arxiv.org/pdf/1512.03385" type="application/pdf"/>'
    b"<author><name>Kaiming He</name></author></entry>\n"
    b"</feed>"
)


def id_list_of(url: str) -> str:
    return urllib.parse.parse_qs(urllib.parse.urlparse(url).query)["id_list"][0]


class ArxivIdentifierTests(unittest.TestCase):
    """The `arXiv:` prefix users paste is not part of the API's id."""

    def stub_get(self, payload: bytes) -> list[str]:
        seen: list[str] = []
        original = paper_resolve._get

        def fake(url: str, *, config: dict) -> bytes:
            seen.append(url)
            return payload

        paper_resolve._get = fake
        self.addCleanup(setattr, paper_resolve, "_get", original)
        return seen

    def test_prefix_variants_query_the_bare_id(self) -> None:
        for identifier in ("arXiv:1512.03385", "arxiv:1512.03385", "  1512.03385  "):
            with self.subTest(identifier=identifier):
                assert id_list_of(paper_resolve._arxiv_url(identifier)) == "1512.03385"

    def test_empty_feed_refuses_identifier_unresolved(self) -> None:
        seen = self.stub_get(EMPTY_FEED)
        with self.assertRaises(Refused) as ctx:
            paper_resolve.resolve_identifier(
                "arXiv:1512.03385", resolver="arxiv", role="resolution", config=CONFIG
            )
        assert ctx.exception.code == "IDENTIFIER_UNRESOLVED", ctx.exception.code
        assert len(seen) == 1 and id_list_of(seen[0]) == "1512.03385", seen

    def test_entry_feed_resolves_with_measured_fields(self) -> None:
        seen = self.stub_get(ENTRY_FEED)
        result = paper_resolve.resolve_identifier(
            "arXiv:1512.03385", resolver="arxiv", role="resolution", config=CONFIG
        )
        assert id_list_of(seen[0]) == "1512.03385", seen
        assert result["title"] == "Deep Residual Learning", result
        assert result["abstract"] == "We present a residual learning framework.", result
        assert result["venue"] == "arXiv", result
        assert result["full_text_url"] == "https://arxiv.org/pdf/1512.03385", result
        assert result["authors"] == ["Kaiming He"], result


if __name__ == "__main__":
    unittest.main()
