from __future__ import annotations

import json
import unittest

from src.services.codex_protocol import (
    ChatStreamToResponses,
    chat_to_response,
    responses_to_chat,
)


class CodexProtocolTests(unittest.TestCase):
    def test_responses_request_maps_messages_reasoning_and_custom_tool(self) -> None:
        body = {
            "model": "ignored",
            "instructions": "Be precise.",
            "reasoning": {"effort": "xhigh"},
            "tools": [
                {
                    "type": "custom",
                    "name": "apply_patch",
                    "description": "Apply a patch.",
                }
            ],
            "tool_choice": {"type": "custom", "name": "apply_patch"},
            "input": [
                {"type": "message", "role": "user", "content": "Fix it"},
                {
                    "type": "custom_tool_call",
                    "call_id": "call_1",
                    "name": "apply_patch",
                    "input": "*** Begin Patch\n*** End Patch",
                },
            ],
        }
        result = responses_to_chat(body, "deepseek-v4-pro")
        self.assertEqual(result["model"], "deepseek-v4-pro")
        self.assertEqual(result["messages"][0]["role"], "system")
        self.assertEqual(
            result["tools"][0]["function"]["parameters"]["required"],
            ["input"],
        )
        arguments = result["messages"][-1]["tool_calls"][0]["function"]["arguments"]
        self.assertEqual(json.loads(arguments)["input"], "*** Begin Patch\n*** End Patch")
        self.assertEqual(result["reasoning_effort"], "high")

    def test_chat_response_restores_custom_tool(self) -> None:
        chat = {
            "id": "chat_1",
            "model": "kimi-k2.6",
            "choices": [
                {
                    "message": {
                        "role": "assistant",
                        "content": None,
                        "tool_calls": [
                            {
                                "id": "call_1",
                                "type": "function",
                                "function": {
                                    "name": "apply_patch",
                                    "arguments": '{"input":"patch text"}',
                                },
                            }
                        ],
                    }
                }
            ],
        }
        result = chat_to_response(chat, "kimi-k2.6", {"apply_patch"})
        self.assertEqual(result["output"][0]["type"], "custom_tool_call")
        self.assertEqual(result["output"][0]["input"], "patch text")

    def test_kimi_uses_thinking_without_deepseek_effort_field(self) -> None:
        result = responses_to_chat(
            {
                "input": "hello",
                "reasoning": {"effort": "high"},
            },
            "kimi-k2.6",
        )
        self.assertEqual(result["thinking"], {"type": "enabled"})
        self.assertNotIn("reasoning_effort", result)

    def test_stream_emits_text_reasoning_usage_and_custom_tool_events(self) -> None:
        converter = ChatStreamToResponses("glm-5.1", {"apply_patch"})
        output = b"".join(
            [
                *converter.start_events(),
                *converter.feed(
                    {
                        "choices": [
                            {"delta": {"reasoning_content": "thinking"}}
                        ]
                    }
                ),
                *converter.feed(
                    {"choices": [{"delta": {"content": "answer"}}]}
                ),
                *converter.feed(
                    {
                        "choices": [
                            {
                                "delta": {
                                    "tool_calls": [
                                        {
                                            "index": 0,
                                            "id": "call_1",
                                            "function": {
                                                "name": "apply_patch",
                                                "arguments": '{"input":"patch"}',
                                            },
                                        }
                                    ]
                                }
                            }
                        ],
                        "usage": {
                            "prompt_tokens": 2,
                            "completion_tokens": 3,
                            "total_tokens": 5,
                        },
                    }
                ),
                *converter.finish_events(),
            ]
        ).decode("utf-8")
        self.assertIn("response.reasoning_summary_text.delta", output)
        self.assertIn("response.output_text.delta", output)
        self.assertIn("response.custom_tool_call_input.done", output)
        self.assertIn('"total_tokens": 5', output)


if __name__ == "__main__":
    unittest.main()
