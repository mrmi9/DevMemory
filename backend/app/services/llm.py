from typing import Any

import httpx

from app.config import get_settings


class DeepSeekClient:
    def __init__(self, api_key: str | None = None, base_url: str | None = None, model: str | None = None) -> None:
        settings = get_settings()
        self.api_key = api_key if api_key is not None else settings.deepseek_api_key
        self.base_url = (base_url or settings.deepseek_base_url).rstrip("/")
        self.model = model or settings.deepseek_model

    async def complete(self, prompt: str, temperature: float = 0.2) -> str:
        if not self.api_key:
            return self._offline_response(prompt)

        payload: dict[str, Any] = {
            "model": self.model,
            "messages": [{"role": "user", "content": prompt}],
            "temperature": temperature,
        }
        headers = {"Authorization": f"Bearer {self.api_key}", "Content-Type": "application/json"}
        async with httpx.AsyncClient(timeout=60) as client:
            response = await client.post(f"{self.base_url}/chat/completions", json=payload, headers=headers)
            response.raise_for_status()
            data = response.json()
        return data["choices"][0]["message"]["content"]

    def _offline_response(self, prompt: str) -> str:
        return (
            "当前未配置 DeepSeek API Key，系统返回离线占位结果。\n\n"
            "你可以先完成资料上传、解析、分块和检索；配置 STUDY_DEEPSEEK_API_KEY 后，"
            "这里会替换为真实 AI 生成内容。\n\n"
            f"请求摘要：{prompt[:500]}"
        )
