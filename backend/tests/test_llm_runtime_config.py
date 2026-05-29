from app.services.llm import DeepSeekClient


def test_deepseek_client_uses_runtime_config(monkeypatch):
    import app.services.llm as llm

    monkeypatch.setattr(
        llm,
        "get_deepseek_runtime_config",
        lambda settings=None: type(
            "RuntimeConfig",
            (),
            {
                "api_key": "sk-runtime-page-key",
                "base_url": "https://runtime.deepseek.example",
                "model": "deepseek-chat",
            },
        )(),
    )

    client = DeepSeekClient()

    assert client.api_key == "sk-runtime-page-key"
    assert client.base_url == "https://runtime.deepseek.example"
    assert client.model == "deepseek-chat"
