# Providers

Veni AI supports 12 AI providers:

| Provider | Privacy | Tool Use | Cost |
|----------|:-------:|:--------:|:----:|
| Ollama | 100% Local | ✅ | Free |
| OpenAI | Cloud | Native | Paid |
| Gemini | Cloud | Native | Tiered |
| Anthropic | Cloud | Native | Paid |
| Groq | Cloud | ✅ | Free |
| DeepSeek | Cloud | ✅ | Paid |
| Qwen | Cloud | ✅ | Paid |
| OpenRouter | Cloud | ✅ | Paid |
| Mistral | Cloud | ✅ | Paid |
| Perplexity | Cloud | ❌ | Paid |
| DuckDuckGo | Cloud | ❌ | Free |
| Free | Cloud | Limited | Free |

## Configuration

Set API keys in your `.env` file or through `veni init`:

```bash
OPENAI_API_KEY=sk-...
GEMINI_API_KEY=...
ANTHROPIC_API_KEY=...
```

## Usage

```bash
veni chat --provider openai --model gpt-4o
veni chat --provider ollama --model llama3.2
veni chat --provider free
```
