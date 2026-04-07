# OpenAI Plugin / AutoGPT / Tool-Based Agents

Chutes.ai already publishes standard machine-readable interfaces that tool-based agent frameworks can consume directly. You don't need to build anything custom — just point your framework at these URLs.

## Plugin Manifest (ai-plugin.json)

```
https://chutes.ai/.well-known/ai-plugin.json
```

Compatible with AutoGPT, LangChain tool loaders, and the ChatGPT plugin format. Contains the tool name, auth type, and API schema URL.

## OpenAPI Specification

```
https://api.chutes.ai/openapi.json
```

Full REST API spec. Swagger UI available at `https://api.chutes.ai/docs`.

## Models List (Structured JSON)

```
https://llm.chutes.ai/v1/models
```

Structured JSON of all available models with pricing, context length, TEE status, supported features, and per-token cost in USD and TAO.

## Docs Index (Machine-Readable)

```
https://chutes.ai/docs.json
```

Structured index of all documentation pages.

## Usage with Common Frameworks

### LangChain

```python
from langchain_openai import ChatOpenAI

llm = ChatOpenAI(
    base_url="https://llm.chutes.ai/v1",
    api_key="cpk_...",
    model="deepseek-ai/DeepSeek-V3-0324"
)
```

### LiteLLM

```python
import litellm

response = litellm.completion(
    model="chutes_ai/deepseek-ai/DeepSeek-V3-0324",
    messages=[{"role": "user", "content": "Hello"}],
    api_key="cpk_..."
)
```

See [LiteLLM Chutes docs](https://docs.litellm.ai/docs/providers/chutes) for full configuration.

### Vercel AI SDK

```bash
npm install @chutes-ai/ai-sdk-provider
```

```javascript
import { createChutes } from '@chutes-ai/ai-sdk-provider';
const chutes = createChutes({ apiKey: 'cpk_...' });
```

### Any OpenAI-Compatible Client

Chutes is a drop-in replacement for the OpenAI API. Change the base URL to `https://llm.chutes.ai/v1` and use a `cpk_` API key. That's it.
