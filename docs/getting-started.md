# Getting Started

## Installation

### From PyPI

```bash
pip install veni-ai
```

### With extras

```bash
pip install "veni-ai[voice,web,scheduler,dashboard,telegram,memory,browser]"
```

### From source

```bash
git clone https://github.com/neoastra303/Veni-AI.git
cd Veni-AI
pip install -e .
```

## Initialize

```bash
veni init
```

This interactive wizard will guide you through setting up your preferred provider and API keys.

## Usage

```bash
# Chat with your local Ollama model
veni chat --provider ollama --model llama3.2

# Chat with OpenAI
veni chat --provider openai --model gpt-4o

# Pipe mode for CI/CD
veni pipe "explain the architecture of this project"

# One-shot query
veni pipe "find all TODO comments" --provider gemini
```
