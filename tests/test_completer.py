from prompt_toolkit.document import Document

from veni.completer import VeniCompleter
from veni.core import TerminalChatbot


class _FakeClient:
    def __init__(self):
        self.model = "fake"

    def chat(self, messages, stream=True):
        yield ""


def test_completer_path_suggestions():
    bot = TerminalChatbot(_FakeClient())
    completer = VeniCompleter(bot)

    # Simulate typing "/read RE"
    doc = Document("/read RE", cursor_position=len("/read RE"))
    completions = list(completer.get_completions(doc, None))

    # Should suggest "README.md"
    assert any("README.md" in c.text for c in completions)

    # Simulate typing "/model "
    doc = Document("/model ", cursor_position=len("/model "))
    completions = list(completer.get_completions(doc, None))
    # Should suggest presets if config has them (default config does)
    # Since we use a real ConfigManager, it should load default_config.yaml
    assert len(completions) > 0


if __name__ == "__main__":
    test_completer_path_suggestions()
    print("Completer test passed!")
