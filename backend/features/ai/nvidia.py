import asyncio
import json

from collections.abc import AsyncIterator

import aiohttp

from shared.exceptions import AiUnavailableError
from utils.logger import logger

_TIMEOUT = aiohttp.ClientTimeout(total=45)

def _payload(model: str, system: str, user: str, stream: bool) -> dict:
    return {
        "model": model,
        "messages": [
            {"role": "system", "content": system},
            {"role": "user", "content": user}
        ],
        "temperature": 0.15,
        "top_p": 0.7,
        "frequency_penalty": 0.3,
        "max_tokens": 700,
        "response_format": {"type": "json_object"},
        "stream": stream
    }

async def stream_complete(http: aiohttp.ClientSession, base_url: str, api_key: str, model: str,
                          system: str, user: str) -> AsyncIterator[str]:
    headers = {"Authorization": f"Bearer {api_key}", "Accept": "text/event-stream"}
    try:
        async with http.post(f"{base_url}/chat/completions", json=_payload(model, system, user, True),
                             headers=headers, timeout=_TIMEOUT) as resp:
            if resp.status != 200:
                logger.warning(f"[ai] nvidia stream {resp.status}: {(await resp.text())[:300]}")
                raise AiUnavailableError("The AI provider is busy — try again shortly")
            async for raw in resp.content:
                line = raw.decode("utf-8", "ignore").strip()
                if not line.startswith("data:"):
                    continue
                data = line[5:].strip()
                if data == "[DONE]":
                    break
                try:
                    delta = json.loads(data)["choices"][0]["delta"].get("content")
                except (KeyError, IndexError, ValueError, TypeError):
                    continue
                if delta:
                    yield delta
    except AiUnavailableError:
        raise
    except (aiohttp.ClientError, asyncio.TimeoutError) as e:
        logger.warning(f"[ai] nvidia stream failed: {e}")
        raise AiUnavailableError("Could not reach the AI provider — try again shortly")

async def complete(http: aiohttp.ClientSession, base_url: str, api_key: str, model: str, system: str, user: str) -> str:
    payload = _payload(model, system, user, False)
    headers = {"Authorization": f"Bearer {api_key}", "Accept": "application/json"}
    try:
        async with http.post(f"{base_url}/chat/completions", json=payload, headers=headers, timeout=_TIMEOUT) as resp:
            status = resp.status
            body = await resp.text()
        if status != 200:
            logger.warning(f"[ai] nvidia {status}: {body[:300]}")
            raise AiUnavailableError("The AI provider is busy — try again shortly")
        content = json.loads(body)["choices"][0]["message"]["content"]
        if not isinstance(content, str) or not content.strip():
            raise AiUnavailableError("The AI provider returned an empty insight — try again")
        return content.strip()
    except AiUnavailableError:
        raise
    except (aiohttp.ClientError, asyncio.TimeoutError) as e:
        logger.warning(f"[ai] nvidia request failed: {e}")
        raise AiUnavailableError("Could not reach the AI provider — try again shortly")
    except (KeyError, IndexError, TypeError, ValueError) as e:
        logger.warning(f"[ai] nvidia malformed response: {e}")
        raise AiUnavailableError("The AI provider returned an unexpected response")
