# Contributing

See [CONTRIBUTING.md](https://github.com/neoastra303/Veni-AI/blob/main/CONTRIBUTING.md) for full details.

## Quick Start

```bash
git clone https://github.com/neoastra303/Veni-AI.git
cd Veni-AI
pip install -e ".[dev]"
pre-commit install
```

## Code Quality

```bash
make format     # black
make lint       # ruff
make typecheck  # mypy
make test       # pytest with coverage
make security   # bandit
make check      # all of the above
```
