# Contributing to Veni AI

Thank you for your interest in contributing to Veni AI! This document provides guidelines and instructions for contributors.

## 🚀 Quick Start

### Setting Up Development Environment

```bash
# Clone the repository
git clone https://github.com/yourusername/veni-ai.git
cd veni-ai

# Create virtual environment
python -m venv venv
venv\Scripts\activate  # Windows
# or: source venv/bin/activate  # Linux/Mac

# Install dependencies
pip install -r requirements.txt

# Install dev dependencies
pip install -r requirements.txt  # Includes pytest, black, ruff, mypy
```

### Running Tests

```bash
# Run all tests
pytest

# Run with coverage
pytest --cov=veni

# Run specific test file
pytest tests/test_tool_calling.py -v
```

## 📐 Code Style

Veni AI uses the following tools for code quality:

```bash
# Format code
black veni/ tests/

# Lint code
ruff check veni/ tests/

# Type checking
mypy veni/
```

### Style Guidelines

- **Line length**: 88 characters (Black default)
- **Imports**: Sorted automatically by Black
- **Type hints**: Use for all function signatures
- **Docstrings**: Google style for public APIs

## 🏗️ Architecture Overview

### Key Components

| Component | Location | Description |
|-----------|----------|-------------|
| Core | `veni/core.py` | Main chatbot orchestrator |
| CLI | `veni/cli.py` | Command-line interface |
| Providers | `veni/providers/` | AI provider implementations |
| Commands | `veni/commands/` | User command handlers |
| Tools | `veni/tools/` | AI-accessible tools |
| Config | `veni/config.py` | Configuration management |

### Adding a New Provider

1. Create `veni/providers/your_provider.py`
2. Inherit from `AIClient` base class
3. Implement the `chat()` method
4. Register in `veni/providers/factory.py`

```python
from veni.providers.base import AIClient, ProviderCapabilities

class YourProviderClient(AIClient):
    capabilities = ProviderCapabilities(
        supports_streaming=True,
        supports_multimodal=False,
        supports_tool_calls=False,
    )
    
    def __init__(self, api_key: str, model: str = "default-model"):
        self.api_key = api_key
        self.model = model
        
    def chat(self, messages, stream=True, tools=None, **kwargs):
        # Your implementation here
        yield "response chunk"
```

### Adding a New Command

1. Create `veni/commands/your_command.py`
2. Inherit from `BaseCommand`
3. Register in `veni/core.py`

```python
from veni.commands.base import BaseCommand

class YourCommand(BaseCommand):
    @property
    def name(self) -> str: return "/yourcmd"
    
    @property
    def description(self) -> str: return "Description of your command"
    
    def execute(self, args: list) -> str | None:
        # Your implementation
        self.show_success("Command executed!")
        return None
```

### Adding a New Tool

1. Create `veni/tools/your_tool.py`
2. Inherit from `AITool`
3. Register in `veni/core.py`

```python
from veni.tools.base import AITool

class YourTool(AITool):
    @property
    def name(self) -> str: return "your_tool"
    
    @property
    def description(self) -> str: return "What your tool does"
    
    @property
    def parameters(self) -> dict:
        return {
            "type": "object",
            "properties": {
                "arg_name": {"type": "string", "description": "Argument description"}
            },
            "required": ["arg_name"]
        }
    
    def execute(self, arg_name: str) -> str:
        # Your implementation
        return f"Result: {arg_name}"
```

## 🧪 Testing Guidelines

### Writing Tests

- Place tests in `tests/` directory
- Name test files `test_*.py`
- Use pytest fixtures for common setup
- Mock external API calls

```python
import pytest
from unittest.mock import Mock, patch

def test_your_feature():
    with patch('module.function') as mock_fn:
        mock_fn.return_value = "mocked result"
        # Your test code
        assert result == "expected"
```

### Test Coverage Goals

- Core functionality: 80%+
- Provider implementations: 70%+
- Commands and tools: 60%+

## 🔒 Security Guidelines

- **Never commit API keys** - Use `.env` file (gitignored)
- **Redact sensitive data** - Use `veni/security.py` redactor
- **Validate user input** - Especially for file operations
- **Rate limiting** - Implement for external API calls

## 📝 Pull Request Process

1. **Fork** the repository
2. **Create a branch** for your feature
   ```bash
   git checkout -b feature/your-feature-name
   ```
3. **Make changes** and write tests
4. **Run tests** and ensure they pass
   ```bash
   pytest tests/
   ```
5. **Run linters** and fix issues
   ```bash
   black veni/ tests/
   ruff check veni/ tests/
   ```
6. **Commit** with clear messages
   ```bash
   git commit -m "feat: add your feature description"
   ```
7. **Push** and create Pull Request

### Commit Message Format

```
feat: Add new feature
fix: Fix bug in component
docs: Update documentation
test: Add or update tests
refactor: Code refactoring
chore: Maintenance tasks
```

## 🐛 Reporting Issues

When reporting bugs, please include:

- **Veni AI version**
- **Python version**
- **Operating system**
- **Steps to reproduce**
- **Expected vs actual behavior**
- **Error messages/logs**

## 💡 Feature Requests

Feature requests are welcome! Please include:

- **Use case**: Why is this feature needed?
- **Proposed solution**: How should it work?
- **Alternatives considered**: What other approaches?

## 📚 Resources

- [Technical Guide](TECHNICAL_GUIDE.md) - Architecture deep dive
- [README](README.md) - User documentation
- [Python Style Guide](https://peps.python.org/pep-0008/)
- [pytest Documentation](https://docs.pytest.org/)

## 🤝 Community

- Be respectful and inclusive
- Help other contributors
- Share knowledge and best practices

---

Thank you for contributing to Veni AI! 🚀
