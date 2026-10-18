"""Citation integrity reads every command in its declared vocabulary (#81).

Both readers of `\\cite` keys -- `paper_bib.cited_keys` (refs.bib coupling)
and `paper_verify._cite_keys` (block verification) -- matched only
`\\cite{...}`, so a key cited through `\\citep` or `\\citet` was invisible and
a missing bibliography entry passed. The declared vocabulary is `\\cite`,
`\\citep` and `\\citet`, each optionally starred and with up to two optional
`[...]` arguments, with the whitespace TeX skips between them. Other natbib
commands (`\\citeauthor`, `\\citealp`, ...) are deliberately outside it.
"""

import sys
import unittest
from pathlib import Path

FORGE_ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(FORGE_ROOT / "skills" / "paper-writing" / "scripts"))
import paper_bib  # noqa: E402
import paper_verify  # noqa: E402

TEX = (
    r"Plain \cite{alpha}. Parenthetical \citep{beta, gamma}. "
    r"Textual \citet{delta}. Starred \citep*{epsilon}. "
    r"Optional \citep[see][p.~4]{zeta}. One optional \citet[ch.~2]{eta}. "
    r"Spaced \citep {theta}. Spaced options \citet* [p.~2] {iota}. "
    "Broken line \\citep\n  {kappa}. "
    r"Out of vocabulary \citeauthor{omega} and \citealp{psi}."
)
EXPECTED = {"alpha", "beta", "gamma", "delta", "epsilon", "zeta", "eta",
            "theta", "iota", "kappa"}


class CiteVocabularyTest(unittest.TestCase):
    def test_bib_reader_sees_every_declared_command(self):
        self.assertEqual(paper_bib.cited_keys(TEX.encode()), EXPECTED)

    def test_verify_reader_sees_every_declared_command(self):
        self.assertEqual(paper_verify._cite_keys(TEX.encode()), EXPECTED)

    def test_a_missing_entry_cited_through_citep_or_citet_is_reported(self):
        main_tex = rb"\citep{present} and \citet{absent_t} and \citep[p.~1]{absent_p}"
        refs_bib = b"@article{present,\n  title={T}\n}\n"
        missing = paper_bib.cited_keys(main_tex) - paper_bib.entry_keys(refs_bib)
        self.assertEqual(missing, {"absent_t", "absent_p"})


if __name__ == "__main__":
    unittest.main()
