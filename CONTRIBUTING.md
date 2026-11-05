# Contributing

Thank you. A few things that keep this project trustworthy:

- **Every claim needs a test.** If you add a guarantee to the README, add
  the test that proves it.
- **Spec changes go through `SPEC.md` first**, as a pull request, with the
  reasoning in the description. Code follows the spec, not the other way
  round.
- **No network, ever**, in the core package. `tests/test_no_network.py`
  will catch it.
- **Plain language.** Documents in this repo are written so a compliance
  lead can read them. If a sentence needs a computer-science degree,
  rewrite it.
- **Decisions are recorded** in `ROADMAP.md`, including rejected ones.

Run the tests locally:

```bash
pip install -e ".[dev]"
pytest
```

By contributing you agree your contribution is licensed under Apache 2.0.
