from veni.history import ChatHistory


def test_pinned_messages_are_kept():
    history = ChatHistory()
    history.add_message("user", "A" * 40)
    history.add_message("assistant", "B" * 40)
    history.pin_message(2)  # pin the first message (from end)

    context, _, _ = history.get_context_state(max_tokens=5)
    contents = [m.get("content", "") for m in context]
    assert any("A" in c for c in contents)
    assert not any("B" in c for c in contents)


def test_get_context_messages_accepts_legacy_ai_client_argument():
    history = ChatHistory()
    history.add_message("user", "hello")

    context = history.get_context_messages(ai_client=object())

    assert context[0]["role"] == "system"
    assert context[-1]["content"] == "hello"


def test_load_preserves_message_timestamps(tmp_path):
    storage_dir = tmp_path / "history"
    history = ChatHistory(storage_dir=storage_dir)
    history.add_message("user", "hello")
    history.messages[0].timestamp = 123.456
    history.save("session")

    loaded = ChatHistory(storage_dir=storage_dir)
    assert loaded.load("session") is True
    assert loaded.messages[0].timestamp == 123.456
