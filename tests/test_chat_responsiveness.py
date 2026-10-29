"""Offline regression tests: no database or real OpenAI requests."""
import asyncio
import importlib
import json
import sys
from pathlib import Path
from types import ModuleType, SimpleNamespace
from unittest.mock import AsyncMock

import httpx
import pytest
import pytest_asyncio
from openai import AsyncOpenAI


@pytest.fixture
def chat_module(monkeypatch, tmp_path):
    # Do not load the developer's .env or use production credentials.
    monkeypatch.chdir(tmp_path)
    monkeypatch.setenv("SECRET_KEY", "offline-test-only")
    monkeypatch.setenv("OPENAI_API_KEY", "offline-test-only")
    return importlib.import_module("app.services.chat_service")


@pytest_asyncio.fixture
async def service(chat_module, monkeypatch):
    state = SimpleNamespace(delay=0, fail=False, cancelled=False, requests=[])

    async def respond(request):
        state.requests.append(json.loads(request.content))
        try:
            await asyncio.sleep(state.delay)
        except asyncio.CancelledError:
            state.cancelled = True
            raise
        if state.fail:
            raise httpx.ReadTimeout("offline test", request=request)
        return httpx.Response(200, json={
            "id": "resp_test", "object": "response", "created_at": 0,
            "model": "test", "status": "completed",
            "output": [{"type": "message", "id": "msg_test", "role": "assistant",
                        "content": [{"type": "output_text", "text": "기존 응답 그대로", "annotations": []}]}],
        })

    def client(**kwargs):
        return AsyncOpenAI(**kwargs, http_client=httpx.AsyncClient(transport=httpx.MockTransport(respond)))

    monkeypatch.setattr(chat_module, "AsyncOpenAI", client)
    instance = chat_module.ChatService()
    try:
        yield instance, state
    finally:
        await instance.openai_client.close()


@pytest.mark.asyncio
async def test_slow_ai_does_not_block_other_tasks(service):
    instance, state = service
    state.delay = 0.15
    task = asyncio.create_task(instance.call_openai_response("opening", "__INIT__", {}))
    while not state.requests:
        await asyncio.sleep(0)
    await asyncio.wait_for(asyncio.sleep(0.01), timeout=0.1)
    assert not task.done(), "Other work must run while the AI request is pending"
    assert await task == ("기존 응답 그대로", {})
    assert instance.openai_client.max_retries == 0


@pytest.mark.asyncio
@pytest.mark.parametrize("step", ["opening", "question", "flip", "roles", "ending"])
async def test_existing_prompt_and_variable_contract(service, chat_module, monkeypatch, step):
    instance, state = service
    monkeypatch.setattr(chat_module, "STEP_RESPONSE_MODELS", {})
    mapping = instance.step_variable_mapping[step]
    context = {key: f"saved-{key}" for key in mapping}
    manual = {"topic": "manual-topic"}
    result = await instance.call_openai_response(step, "기존 입력", context, manual)
    assert result == ("기존 응답 그대로", {})
    payload = state.requests[0]
    assert payload["input"] == "기존 입력"
    assert payload["prompt"]["id"] == chat_module.settings.CHATBOT_PROMPTS[step]["id"]
    assert payload["prompt"]["version"] == chat_module.settings.CHATBOT_PROMPTS[step]["version"]
    assert payload["prompt"]["variables"] == {**{dest: context[key] for key, dest in mapping.items()}, **manual}


@pytest.mark.asyncio
@pytest.mark.parametrize("sdk_timeout", [False, True])
async def test_timeout_does_not_advance_or_overwrite_session(service, chat_module, monkeypatch, sdk_timeout):
    instance, state = service
    state.delay = 0 if sdk_timeout else 10
    state.fail = sdk_timeout
    monkeypatch.setattr(chat_module, "RESPONSE_TIMEOUT_SECONDS", 0.03)
    original_context = {"opening_topic": "보존할 주제"}
    instance.get_or_create_session = AsyncMock(return_value=SimpleNamespace(current_step="opening", context=original_context))
    instance.update_session = AsyncMock()
    request = chat_module.MultiStepChatRequest(session_id="same-session", step="opening", user_input="__INIT__")
    with pytest.raises(TimeoutError):
        await instance.process_multi_step_chat(None, request)
    instance.update_session.assert_not_awaited()
    assert original_context == {"opening_topic": "보존할 주제"}
    assert len(state.requests) == 1, "SDK must not silently retry a stalled request"
    if not sdk_timeout:
        assert state.cancelled


@pytest.mark.asyncio
@pytest.mark.parametrize("slow_extraction", [False, True])
async def test_extraction_preserves_response_and_existing_fallback(service, chat_module, monkeypatch, slow_extraction):
    from langchain_core.runnables import RunnableLambda
    import langchain_openai

    instance, _ = service
    settings_seen = []
    async def extract(_prompt):
        if slow_extraction:
            await asyncio.sleep(10)
        return json.dumps({"response_text": "must not replace raw response", "topic": "AI 윤리"})
    def extractor(**kwargs):
        settings_seen.append(kwargs)
        return RunnableLambda(extract)
    monkeypatch.setattr(langchain_openai, "ChatOpenAI", extractor)
    monkeypatch.setattr(chat_module, "EXTRACTION_TIMEOUT_SECONDS", 0.03)
    text, variables = await instance.call_openai_response("opening", "AI 윤리", {})
    assert text == "기존 응답 그대로"
    assert variables == ({} if slow_extraction else {"topic": "AI 윤리"})
    assert settings_seen[0]["max_retries"] == 0
    assert settings_seen[0]["timeout"] == 0.03


@pytest.mark.asyncio
async def test_http_deadline_returns_retryable_504(chat_module, monkeypatch):
    from fastapi import FastAPI
    # Isolate the DB dependency before importing the router (no DB driver needed).
    deps = ModuleType("app.core.deps")
    deps.get_db = lambda: None
    monkeypatch.setitem(sys.modules, "app.core.deps", deps)
    # Load separately so the mocked dependency cannot leak into other tests.
    source = Path(chat_module.__file__).parents[1] / "api/endpoints/chat.py"
    spec = importlib.util.spec_from_file_location("chat_endpoint_under_test", source)
    endpoints = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(endpoints)
    async def stalled(*_args):
        await asyncio.sleep(10)
    monkeypatch.setattr(endpoints.chat_service, "process_multi_step_chat", stalled)
    monkeypatch.setattr(endpoints, "CHAT_TIMEOUT_SECONDS", 0.03)
    app = FastAPI()
    app.include_router(endpoints.router)
    app.dependency_overrides[endpoints.get_db] = lambda: None
    async with httpx.AsyncClient(transport=httpx.ASGITransport(app=app), base_url="http://test") as client:
        response = await client.post("/chat/multi-step", json={"session_id": "same-session", "user_input": "__INIT__", "step": "opening"})
    assert response.status_code == 504
    assert "다시 시도" in response.json()["detail"]


@pytest.mark.asyncio
@pytest.mark.parametrize("route", ["/chat/with-prompt", "/chat/image"])
async def test_other_http_requests_run_during_legacy_ai_calls(chat_module, monkeypatch, route):
    from fastapi import FastAPI
    from langchain_core.runnables import RunnableLambda
    import langchain_openai
    import openai
    import time

    deps = ModuleType("app.core.deps")
    deps.get_db = lambda: None
    monkeypatch.setitem(sys.modules, "app.core.deps", deps)
    source = Path(chat_module.__file__).parents[1] / "api/endpoints/chat.py"
    spec = importlib.util.spec_from_file_location("legacy_chat_endpoint_under_test", source)
    endpoints = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(endpoints)
    started = asyncio.Event()
    answer = SimpleNamespace(output=[], data=[SimpleNamespace(url="https://offline.invalid/image.png")])

    async def respond(**_kwargs):
        started.set()
        await asyncio.sleep(0.15)
        return answer

    def blocking_response(**_kwargs):
        started.set()
        time.sleep(0.15)
        return answer

    class AsyncClient:
        responses = SimpleNamespace(create=respond)
        images = SimpleNamespace(generate=respond)

        async def __aenter__(self):
            return self

        async def __aexit__(self, *_args):
            pass

    # Both SDKs are offline, so the pre-fix synchronous version fails safely.
    monkeypatch.setattr(openai, "AsyncOpenAI", lambda **_kwargs: AsyncClient())
    monkeypatch.setattr(openai, "OpenAI", lambda **_kwargs: SimpleNamespace(
        responses=SimpleNamespace(create=blocking_response),
        images=SimpleNamespace(generate=blocking_response)))
    monkeypatch.setattr(langchain_openai, "ChatOpenAI", lambda **_kwargs: RunnableLambda(lambda _: '{}'))
    monkeypatch.setattr(httpx.AsyncClient, "get", AsyncMock(return_value=httpx.Response(
        200, content=b"offline image", request=httpx.Request("GET", "https://offline.invalid/image.png"))))

    app = FastAPI()
    app.include_router(endpoints.router)
    app.dependency_overrides[endpoints.get_db] = lambda: None

    @app.get("/health")
    async def health():
        return {"ok": True}

    async with httpx.AsyncClient(transport=httpx.ASGITransport(app=app), base_url="http://test") as client:
        request = asyncio.create_task(client.post(route, json={"input": "offline", "step": "opening"}))
        await asyncio.wait_for(started.wait(), timeout=2)
        health_response = await client.request("GET", "/health")
        assert health_response.status_code == 200
        assert not request.done(), "One AI call must not hold all other HTTP requests"
        assert (await request).status_code == 200
