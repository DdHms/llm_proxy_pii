import os
import sys

import pytest

sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))

from src.proxy import scrub_llm_payload


@pytest.mark.asyncio
async def test_openai_chat_completion_scrubs_message_content():
    secret = "KEY" + "123" + "AAA"
    data = {
        "model": "gpt-5-codex",
        "messages": [
            {"role": "system", "content": f"System context {secret}"},
            {"role": "user", "content": [{"type": "text", "text": f"User prompt {secret}"}]},
        ],
    }
    mapping = {}

    await scrub_llm_payload(data, "v1/chat/completions", {"counts": {}, "seen_texts": {}}, mapping)

    assert secret not in data["messages"][0]["content"]
    assert secret not in data["messages"][1]["content"][0]["text"]
    assert mapping


@pytest.mark.asyncio
async def test_openai_responses_scrubs_input_and_instructions():
    input_secret = "KEY" + "456" + "BBB"
    instruction_secret = "KEY" + "789" + "CCC"
    data = {
        "model": "gpt-5-codex",
        "instructions": f"Follow project context {instruction_secret}",
        "input": [
            {
                "role": "user",
                "content": [{"type": "input_text", "text": f"Review this {input_secret}"}],
            }
        ],
    }
    mapping = {}

    await scrub_llm_payload(data, "v1/responses", {"counts": {}, "seen_texts": {}}, mapping)

    assert instruction_secret not in data["instructions"]
    assert input_secret not in data["input"][0]["content"][0]["text"]
    assert mapping


@pytest.mark.asyncio
async def test_openai_responses_scrubs_tool_outputs_without_scrubbing_metadata():
    output_secret = "KEY" + "121" + "OUTPUT"
    stdout_secret = "KEY" + "122" + "STDOUT"
    stderr_secret = "KEY" + "123" + "STDERR"
    block_secret = "KEY" + "124" + "BLOCK"
    data = {
        "model": "gpt-5-codex",
        "input": [
            {
                "type": "function_call_output",
                "call_id": "call_KEY121OUTPUT",
                "name": "tool_KEY122STDOUT",
                "output": f"Tool returned {output_secret}",
            },
            {
                "type": "shell_call_output",
                "id": "item_KEY123STDERR",
                "stdout": f"stdout had {stdout_secret}",
                "stderr": f"stderr had {stderr_secret}",
            },
            {
                "type": "custom_tool_call_output",
                "output": [{"type": "output_text", "text": f"block had {block_secret}"}],
            },
        ],
    }
    mapping = {}

    await scrub_llm_payload(data, "v1/responses", {"counts": {}, "seen_texts": {}}, mapping)

    assert output_secret not in data["input"][0]["output"]
    assert stdout_secret not in data["input"][1]["stdout"]
    assert stderr_secret not in data["input"][1]["stderr"]
    assert block_secret not in data["input"][2]["output"][0]["text"]
    assert data["input"][0]["call_id"] == "call_KEY121OUTPUT"
    assert data["input"][0]["name"] == "tool_KEY122STDOUT"
    assert data["input"][1]["id"] == "item_KEY123STDERR"
    assert mapping


@pytest.mark.asyncio
async def test_gemini_scrubbing_does_not_treat_content_or_input_as_text_fields():
    text_secret = "KEY" + "111" + "TEXT"
    content_secret = "KEY" + "222" + "CONTENT"
    input_secret = "KEY" + "333" + "INPUT"
    data = {
        "contents": [{"parts": [{"text": f"Scrub me {text_secret}"}]}],
        "content": f"Do not scrub this container value {content_secret}",
        "input": f"Do not scrub this container value {input_secret}",
    }
    mapping = {}

    await scrub_llm_payload(data, "v1beta/models/gemini-pro:generateContent", {"counts": {}, "seen_texts": {}}, mapping)

    assert text_secret not in data["contents"][0]["parts"][0]["text"]
    assert content_secret in data["content"]
    assert input_secret in data["input"]


@pytest.mark.asyncio
async def test_gemini_scrubs_session_context_without_scrubbing_generic_content():
    context_secret = "KEY" + "888" + "SESSION"
    nested_secret = "KEY" + "999" + "NESTED"
    content_secret = "KEY" + "000" + "CONTENT"
    data = {
        "session_context": f"Context includes {context_secret}",
        "sessionContext": {
            "notes": [f"Nested context includes {nested_secret}"],
        },
        "content": f"Generic content should remain {content_secret}",
    }
    mapping = {}

    await scrub_llm_payload(data, "v1beta/models/gemini-pro:generateContent", {"counts": {}, "seen_texts": {}}, mapping)

    assert context_secret not in data["session_context"]
    assert nested_secret not in data["sessionContext"]["notes"][0]
    assert content_secret in data["content"]
    assert mapping


@pytest.mark.asyncio
async def test_unknown_post_json_path_still_uses_conservative_text_scrubbing():
    name = "Jane Example"
    data = {
        "contents": [{"parts": [{"text": f"My name is {name}."}]}],
        "content": f"Container string should remain {name}",
    }
    mapping = {}

    from src import constants

    constants.DEFAULT_EXCLUSIONS = [name]
    await scrub_llm_payload(data, "unrecognized/gemini/path", {"counts": {}, "seen_texts": {}}, mapping)

    assert name not in data["contents"][0]["parts"][0]["text"]
    assert name in data["content"]
    assert mapping


@pytest.mark.asyncio
async def test_anthropic_messages_scrubs_system_and_message_content():
    system_secret = "KEY" + "444" + "SYSTEM"
    user_secret = "KEY" + "555" + "USER"
    assistant_secret = "KEY" + "666" + "ASSISTANT"
    data = {
        "model": "claude-sonnet-4-5",
        "system": f"Project context {system_secret}",
        "messages": [
            {"role": "user", "content": f"Plain content {user_secret}"},
            {
                "role": "assistant",
                "content": [{"type": "text", "text": f"Typed content {assistant_secret}"}],
            },
        ],
    }
    mapping = {}

    await scrub_llm_payload(data, "v1/messages", {"counts": {}, "seen_texts": {}}, mapping)

    assert system_secret not in data["system"]
    assert user_secret not in data["messages"][0]["content"]
    assert assistant_secret not in data["messages"][1]["content"][0]["text"]
    assert mapping


@pytest.mark.asyncio
async def test_anthropic_complete_scrubs_prompt():
    secret = "KEY" + "777" + "PROMPT"
    data = {
        "model": "claude-2.1",
        "prompt": f"\n\nHuman: Review this {secret}\n\nAssistant:",
    }
    mapping = {}

    await scrub_llm_payload(data, "v1/complete", {"counts": {}, "seen_texts": {}}, mapping)

    assert secret not in data["prompt"]
    assert mapping


@pytest.mark.asyncio
async def test_anthropic_messages_scrubs_tool_result_outputs_without_scrubbing_metadata():
    output_secret = "KEY" + "778" + "OUTPUT"
    block_secret = "KEY" + "779" + "BLOCK"
    data = {
        "model": "claude-sonnet-4-5",
        "messages": [
            {
                "role": "user",
                "content": [
                    {
                        "type": "tool_result",
                        "tool_use_id": "toolu_KEY778OUTPUT",
                        "name": "lookup_KEY779BLOCK",
                        "output": f"Tool result {output_secret}",
                    },
                    {
                        "type": "tool_result",
                        "content": [{"type": "text", "text": f"Nested result {block_secret}"}],
                    },
                ],
            }
        ],
    }
    mapping = {}

    await scrub_llm_payload(data, "v1/messages", {"counts": {}, "seen_texts": {}}, mapping)

    assert output_secret not in data["messages"][0]["content"][0]["output"]
    assert block_secret not in data["messages"][0]["content"][1]["content"][0]["text"]
    assert data["messages"][0]["content"][0]["tool_use_id"] == "toolu_KEY778OUTPUT"
    assert data["messages"][0]["content"][0]["name"] == "lookup_KEY779BLOCK"
    assert mapping
