# 路径: src/services/codex_protocol.py
# 作用: OpenAI Responses API 与 Chat Completions API 的协议转换

from __future__ import annotations

import json
import time
import uuid
from typing import Any, Iterable


def _text_from_content(content: Any) -> str:
    if isinstance(content, str):
        return content
    if not isinstance(content, list):
        return ""
    chunks: list[str] = []
    for part in content:
        if isinstance(part, str):
            chunks.append(part)
        elif isinstance(part, dict):
            text = part.get("text")
            if isinstance(text, str):
                chunks.append(text)
    return "\n".join(chunk for chunk in chunks if chunk)


def _chat_tool(tool: dict[str, Any]) -> dict[str, Any] | None:
    tool_type = tool.get("type")
    if tool_type == "tool_search":
        return {
            "type": "function",
            "function": {
                "name": "tool_search",
                "description": "Search and load tools for the current task.",
                "parameters": {
                    "type": "object",
                    "properties": {
                        "query": {"type": "string"},
                        "limit": {"type": "integer"},
                    },
                    "required": ["query"],
                },
            },
        }
    name = tool.get("name")
    if not isinstance(name, str) or not name:
        return None
    if tool_type == "custom":
        return {
            "type": "function",
            "function": {
                "name": name,
                "description": tool.get("description", ""),
                "parameters": {
                    "type": "object",
                    "properties": {"input": {"type": "string"}},
                    "required": ["input"],
                },
            },
        }
    if tool_type != "function":
        return None
    return {
        "type": "function",
        "function": {
            "name": name,
            "description": tool.get("description", ""),
            "parameters": tool.get("parameters") or {},
        },
    }


def responses_to_chat(body: dict[str, Any], model: str) -> dict[str, Any]:
    messages: list[dict[str, Any]] = []
    instructions = _text_from_content(body.get("instructions"))
    if instructions:
        messages.append({"role": "system", "content": instructions})

    input_value = body.get("input", [])
    if isinstance(input_value, str):
        messages.append({"role": "user", "content": input_value})
    elif isinstance(input_value, list):
        pending_calls: list[dict[str, Any]] = []
        for item in input_value:
            if not isinstance(item, dict):
                continue
            item_type = item.get("type")
            if item_type == "message":
                role = item.get("role", "user")
                if role == "developer":
                    role = "system"
                messages.append(
                    {"role": role, "content": _text_from_content(item.get("content"))}
                )
            elif item_type == "function_call":
                pending_calls.append(
                    {
                        "id": item.get("call_id") or item.get("id") or f"call_{uuid.uuid4().hex}",
                        "type": "function",
                        "function": {
                            "name": item.get("name", ""),
                            "arguments": item.get("arguments", "{}"),
                        },
                    }
                )
            elif item_type == "custom_tool_call":
                pending_calls.append(
                    {
                        "id": item.get("call_id") or item.get("id") or f"call_{uuid.uuid4().hex}",
                        "type": "function",
                        "function": {
                            "name": item.get("name", ""),
                            "arguments": json.dumps(
                                {"input": item.get("input", "")},
                                ensure_ascii=False,
                                separators=(",", ":"),
                            ),
                        },
                    }
                )
            elif item_type in {
                "function_call_output",
                "custom_tool_call_output",
                "tool_search_output",
            }:
                if pending_calls:
                    messages.append(
                        {"role": "assistant", "content": None, "tool_calls": pending_calls}
                    )
                    pending_calls = []
                messages.append(
                    {
                        "role": "tool",
                        "tool_call_id": item.get("call_id", ""),
                        "content": _text_from_content(item.get("output")),
                    }
                )
        if pending_calls:
            messages.append(
                {"role": "assistant", "content": None, "tool_calls": pending_calls}
            )

    result: dict[str, Any] = {
        "model": model,
        "messages": _collapse_system_messages(messages),
        "stream": bool(body.get("stream", False)),
    }
    if result["stream"]:
        result["stream_options"] = {"include_usage": True}

    tools = [
        converted
        for tool in body.get("tools", [])
        if isinstance(tool, dict)
        for converted in [_chat_tool(tool)]
        if converted is not None
    ]
    if tools:
        result["tools"] = tools
        if "tool_choice" in body:
            choice = body["tool_choice"]
            if isinstance(choice, dict) and choice.get("type") in {
                "function",
                "custom",
                "tool_search",
            }:
                result["tool_choice"] = {
                    "type": "function",
                    "function": {
                        "name": choice.get("name")
                        or ("tool_search" if choice.get("type") == "tool_search" else "")
                    },
                }
            else:
                result["tool_choice"] = choice

    if "temperature" in body:
        result["temperature"] = body["temperature"]
    if "top_p" in body:
        result["top_p"] = body["top_p"]
    if "max_output_tokens" in body:
        result["max_tokens"] = body["max_output_tokens"]

    reasoning = body.get("reasoning")
    if isinstance(reasoning, dict):
        effort = reasoning.get("effort")
        enabled = effort not in {"none", "off", "disabled"}
        if effort and model.lower().startswith("deepseek-"):
            result["reasoning_effort"] = "high" if effort in {"max", "xhigh"} else effort
        result["thinking"] = {"type": "enabled" if enabled else "disabled"}
    return result


def _collapse_system_messages(messages: list[dict[str, Any]]) -> list[dict[str, Any]]:
    system: list[str] = []
    rest: list[dict[str, Any]] = []
    for message in messages:
        if message.get("role") == "system":
            content = message.get("content")
            if isinstance(content, str) and content:
                system.append(content)
        else:
            rest.append(message)
    if system:
        return [{"role": "system", "content": "\n\n".join(system)}, *rest]
    return rest


def chat_to_response(
    body: dict[str, Any],
    model: str,
    custom_tools: set[str] | None = None,
) -> dict[str, Any]:
    response_id = body.get("id") or f"resp_{uuid.uuid4().hex}"
    choice = (body.get("choices") or [{}])[0]
    message = choice.get("message") or {}
    output: list[dict[str, Any]] = []

    reasoning = message.get("reasoning_content") or message.get("reasoning")
    if isinstance(reasoning, str) and reasoning:
        output.append(
            {
                "id": f"rs_{uuid.uuid4().hex}",
                "type": "reasoning",
                "summary": [{"type": "summary_text", "text": reasoning}],
            }
        )

    content = message.get("content")
    if isinstance(content, str) and content:
        output.append(
            {
                "id": f"msg_{uuid.uuid4().hex}",
                "type": "message",
                "status": "completed",
                "role": "assistant",
                "content": [
                    {
                        "type": "output_text",
                        "text": content,
                        "annotations": [],
                    }
                ],
            }
        )

    for call in message.get("tool_calls") or []:
        function = call.get("function") or {}
        name = function.get("name", "")
        arguments = function.get("arguments", "{}")
        if custom_tools and name in custom_tools:
            try:
                input_value = json.loads(arguments).get("input", "")
            except (json.JSONDecodeError, AttributeError):
                input_value = arguments
            item = {
                "id": f"ctc_{uuid.uuid4().hex}",
                "type": "custom_tool_call",
                "status": "completed",
                "call_id": call.get("id") or f"call_{uuid.uuid4().hex}",
                "name": name,
                "input": input_value,
            }
        elif name == "tool_search":
            try:
                parsed_arguments = json.loads(arguments)
            except json.JSONDecodeError:
                parsed_arguments = {"query": arguments}
            item = {
                "type": "tool_search_call",
                "status": "completed",
                "execution": "client",
                "call_id": call.get("id") or f"call_{uuid.uuid4().hex}",
                "arguments": parsed_arguments,
            }
        else:
            item = {
                "id": f"fc_{uuid.uuid4().hex}",
                "type": "function_call",
                "status": "completed",
                "call_id": call.get("id") or f"call_{uuid.uuid4().hex}",
                "name": name,
                "arguments": arguments,
            }
        output.append(item)

    usage = body.get("usage") or {}
    return {
        "id": response_id,
        "object": "response",
        "created_at": body.get("created") or int(time.time()),
        "status": "completed",
        "model": body.get("model") or model,
        "output": output,
        "usage": {
            "input_tokens": usage.get("prompt_tokens", 0),
            "output_tokens": usage.get("completion_tokens", 0),
            "total_tokens": usage.get("total_tokens", 0),
        },
    }


class ChatStreamToResponses:
    def __init__(self, model: str, custom_tools: set[str] | None = None) -> None:
        self.model = model
        self.response_id = f"resp_{uuid.uuid4().hex}"
        self.message_id = f"msg_{uuid.uuid4().hex}"
        self.reasoning_id = f"rs_{uuid.uuid4().hex}"
        self.message_started = False
        self.reasoning_started = False
        self.message_text = ""
        self.reasoning_text = ""
        self.output_index = 0
        self.tool_calls: dict[int, dict[str, str]] = {}
        self.usage: dict[str, Any] = {}
        self.custom_tools = custom_tools or set()

    @staticmethod
    def _event(event_type: str, **payload: Any) -> bytes:
        data = {"type": event_type, **payload}
        return (
            f"event: {event_type}\ndata: {json.dumps(data, ensure_ascii=False)}\n\n"
        ).encode("utf-8")

    def start_events(self) -> list[bytes]:
        response = {
            "id": self.response_id,
            "object": "response",
            "created_at": int(time.time()),
            "status": "in_progress",
            "model": self.model,
            "output": [],
        }
        return [self._event("response.created", response=response)]

    def feed(self, chunk: dict[str, Any]) -> list[bytes]:
        events: list[bytes] = []
        if chunk.get("usage"):
            self.usage = chunk["usage"]
        choices = chunk.get("choices") or []
        if not choices:
            return events
        delta = choices[0].get("delta") or {}

        reasoning = delta.get("reasoning_content") or delta.get("reasoning")
        if isinstance(reasoning, str) and reasoning:
            self.reasoning_text += reasoning
            if not self.reasoning_started:
                self.reasoning_started = True
                item = {
                    "id": self.reasoning_id,
                    "type": "reasoning",
                    "summary": [],
                }
                events.append(
                    self._event(
                        "response.output_item.added",
                        output_index=self.output_index,
                        item=item,
                    )
                )
                events.append(
                    self._event(
                        "response.reasoning_summary_part.added",
                        item_id=self.reasoning_id,
                        output_index=self.output_index,
                        summary_index=0,
                        part={"type": "summary_text", "text": ""},
                    )
                )
            events.append(
                self._event(
                    "response.reasoning_summary_text.delta",
                    item_id=self.reasoning_id,
                    output_index=self.output_index,
                    summary_index=0,
                    delta=reasoning,
                )
            )

        content = delta.get("content")
        if isinstance(content, str) and content:
            self.message_text += content
            if self.reasoning_started and not self.message_started:
                self.output_index += 1
            if not self.message_started:
                self.message_started = True
                item = {
                    "id": self.message_id,
                    "type": "message",
                    "status": "in_progress",
                    "role": "assistant",
                    "content": [],
                }
                events.append(
                    self._event(
                        "response.output_item.added",
                        output_index=self.output_index,
                        item=item,
                    )
                )
                events.append(
                    self._event(
                        "response.content_part.added",
                        item_id=self.message_id,
                        output_index=self.output_index,
                        content_index=0,
                        part={"type": "output_text", "text": "", "annotations": []},
                    )
                )
            events.append(
                self._event(
                    "response.output_text.delta",
                    item_id=self.message_id,
                    output_index=self.output_index,
                    content_index=0,
                    delta=content,
                )
            )

        for tool_delta in delta.get("tool_calls") or []:
            index = int(tool_delta.get("index", 0))
            state = self.tool_calls.setdefault(
                index,
                {"id": "", "name": "", "arguments": ""},
            )
            if tool_delta.get("id"):
                state["id"] = tool_delta["id"]
            function = tool_delta.get("function") or {}
            if function.get("name"):
                state["name"] += function["name"]
            if function.get("arguments"):
                state["arguments"] += function["arguments"]
        return events

    def finish_events(self) -> list[bytes]:
        events: list[bytes] = []
        completed_output: list[dict[str, Any]] = []
        if self.reasoning_started:
            reasoning_item = {
                "id": self.reasoning_id,
                "type": "reasoning",
                "summary": [
                    {"type": "summary_text", "text": self.reasoning_text}
                ],
            }
            events.extend(
                [
                    self._event(
                        "response.reasoning_summary_text.done",
                        item_id=self.reasoning_id,
                        output_index=0,
                        summary_index=0,
                        text=self.reasoning_text,
                    ),
                    self._event(
                        "response.reasoning_summary_part.done",
                        item_id=self.reasoning_id,
                        output_index=0,
                        summary_index=0,
                        part=reasoning_item["summary"][0],
                    ),
                    self._event(
                        "response.output_item.done",
                        output_index=0,
                        item=reasoning_item,
                    ),
                ]
            )
            completed_output.append(reasoning_item)
        if self.message_started:
            message_index = 1 if self.reasoning_started else 0
            content_part = {
                "type": "output_text",
                "text": self.message_text,
                "annotations": [],
            }
            message_item = {
                "id": self.message_id,
                "type": "message",
                "status": "completed",
                "role": "assistant",
                "content": [content_part],
            }
            events.extend(
                [
                    self._event(
                        "response.output_text.done",
                        item_id=self.message_id,
                        output_index=message_index,
                        content_index=0,
                        text=self.message_text,
                    ),
                    self._event(
                        "response.content_part.done",
                        item_id=self.message_id,
                        output_index=message_index,
                        content_index=0,
                        part=content_part,
                    ),
                    self._event(
                        "response.output_item.done",
                        output_index=message_index,
                        item=message_item,
                    ),
                ]
            )
            completed_output.append(message_item)
        next_index = self.output_index + int(self.message_started or self.reasoning_started)
        for index in sorted(self.tool_calls):
            call = self.tool_calls[index]
            item_id = f"fc_{uuid.uuid4().hex}"
            if call["name"] in self.custom_tools:
                try:
                    input_value = json.loads(call["arguments"]).get("input", "")
                except (json.JSONDecodeError, AttributeError):
                    input_value = call["arguments"]
                item = {
                    "id": item_id,
                    "type": "custom_tool_call",
                    "status": "completed",
                    "call_id": call["id"] or f"call_{uuid.uuid4().hex}",
                    "name": call["name"],
                    "input": input_value,
                }
            else:
                item = {
                    "id": item_id,
                    "type": "function_call",
                    "status": "completed",
                    "call_id": call["id"] or f"call_{uuid.uuid4().hex}",
                    "name": call["name"],
                    "arguments": call["arguments"],
                }
            events.append(
                self._event(
                    "response.output_item.added",
                    output_index=next_index,
                    item=item,
                )
            )
            if call["name"] in self.custom_tools:
                events.append(
                    self._event(
                        "response.custom_tool_call_input.done",
                        item_id=item_id,
                        output_index=next_index,
                        input=item["input"],
                    )
                )
            else:
                events.append(
                    self._event(
                        "response.function_call_arguments.done",
                        item_id=item_id,
                        output_index=next_index,
                        arguments=call["arguments"],
                    )
                )
            events.append(
                self._event(
                    "response.output_item.done",
                    output_index=next_index,
                    item=item,
                )
            )
            completed_output.append(item)
            next_index += 1

        usage = {
            "input_tokens": self.usage.get("prompt_tokens", 0),
            "output_tokens": self.usage.get("completion_tokens", 0),
            "total_tokens": self.usage.get("total_tokens", 0),
        }
        response = {
            "id": self.response_id,
            "object": "response",
            "created_at": int(time.time()),
            "status": "completed",
            "model": self.model,
            "output": completed_output,
            "usage": usage,
        }
        events.append(self._event("response.completed", response=response))
        events.append(b"data: [DONE]\n\n")
        return events


def iter_sse_json(lines: Iterable[bytes | str]) -> Iterable[dict[str, Any]]:
    for raw in lines:
        line = (
            raw.decode("utf-8", errors="replace")
            if isinstance(raw, bytes)
            else raw
        ).strip()
        if not line.startswith("data:"):
            continue
        data = line[5:].strip()
        if not data or data == "[DONE]":
            continue
        try:
            value = json.loads(data)
        except json.JSONDecodeError:
            continue
        if isinstance(value, dict):
            yield value
