from veni.history import ChatMessage


def test_tool_role_maps_to_user():
    msg = ChatMessage("tool", "Tool output here")
    chat = msg.to_chat_dict()
    assert chat["role"] == "user"
    assert "Tool output" in chat["content"]
