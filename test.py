"""
test_chat.py — Debug helper for chatBubble.py chat history.

Put this file in the same folder as chatBubble.py.

    python test_chat.py             # opens a small chat window with a fake
                                    # "echo" AI, using the real history file
    python test_chat.py --headless  # runs automated checks (no window) using
                                    # a temporary history file

GUI mode: send a few messages, click the 🆕 button to start a new chat,
send more, then click the 🕘 button to see your past chats. Close and
reopen the window: your chats should still be there.
"""

import os
import sys
import tempfile
from pathlib import Path

HEADLESS = "--headless" in sys.argv
if HEADLESS:
    os.environ.setdefault("QT_QPA_PLATFORM", "offscreen")

sys.path.insert(0, str(Path(__file__).resolve().parent))

from PyQt6.QtCore import QTimer
from PyQt6.QtWidgets import QApplication, QMainWindow

import Chatbot.chatBubble as chatBubble
from Chatbot.chatBubble import ChatView, DEFAULT_HISTORY_PATH


def make_echo_view(path):
    """A ChatView wired to a fake backend that just echoes."""
    view = ChatView(history_path=path)
    view.set_send_handler(lambda text: view.on_reply(f"Echo: {text}"))
    return view


def send(view, text):
    view.input.setText(text)
    view._on_send_clicked()


def bubble_rows(view):
    # Everything in the layout except the trailing stretch.
    return view.chat_layout.count() - 1


results = []


def check(name, condition, detail=""):
    results.append(condition)
    print(f"  [{'PASS' if condition else 'FAIL'}] {name}"
          + (f"  ({detail})" if detail and not condition else ""))


def run_headless():
    print(f"chatBubble loaded from: {chatBubble.__file__}")
    tmp = Path(tempfile.mkdtemp()) / "chat_history.json"
    print(f"Using temp history file: {tmp}\n")

    print("1. Fresh start")
    v1 = make_echo_view(tmp)
    check("greeting shown (separator + greeting = 2 rows)",
          bubble_rows(v1) == 2, f"rows={bubble_rows(v1)}")
    check("no history file yet", not tmp.exists())

    print("\n2. First chat: two messages")
    send(v1, "hello")
    send(v1, "how are you?")
    check("file was written", tmp.exists())
    check("1 saved chat", len(v1._sessions) == 1,
          f"sessions={len(v1._sessions)}")
    check("chat has 4 messages", len(v1._current["messages"]) == 4)
    check("chat title is the first message",
          v1._current["title"] == "hello", v1._current["title"])

    print("\n3. New chat keeps the old one")
    first_id = v1._current["id"]
    v1.reset()
    check("file still exists after reset()", tmp.exists())
    check("old chat still saved", len(v1._sessions) == 1)
    check("screen cleared to greeting", bubble_rows(v1) == 2)
    check("model history cleared", v1.history == [])
    send(v1, "second chat")
    check("now 2 saved chats", len(v1._sessions) == 2,
          f"sessions={len(v1._sessions)}")

    print("\n4. Reopen the app")
    v2 = make_echo_view(tmp)
    check("both chats loaded", len(v2._sessions) == 2,
          f"sessions={len(v2._sessions)}")
    check("last chat restored on screen (separator + 2 bubbles = 3 rows)",
          bubble_rows(v2) == 3, f"rows={bubble_rows(v2)}")

    print("\n5. Open the older chat from history")
    v2.open_session(first_id)
    check("older chat shown (separator + 4 bubbles = 5 rows)",
          bubble_rows(v2) == 5, f"rows={bubble_rows(v2)}")
    check("model history has the older chat (4 entries)",
          len(v2.history) == 4, f"history={len(v2.history)}")
    check("history entries have only role/content (safe for the API)",
          all(set(h) == {"role", "content"} for h in v2.history))
    send(v2, "continuing the first chat")
    check("continuing adds to the older chat, not a new one",
          len(v2._sessions) == 2 and len(v2._current["messages"]) == 6,
          f"sessions={len(v2._sessions)}")

    print("\n6. History window")
    QTimer.singleShot(
        300, lambda: QApplication.activeModalWidget().reject()
    )
    try:
        v2.show_history()
        ok = True
    except Exception as e:
        ok = False
        print(f"     error: {e}")
    check("history window opens and closes without error", ok)

    print("\n7. reset() right after startup no longer deletes anything")
    v3 = make_echo_view(tmp)
    v3.reset()
    v4 = make_echo_view(tmp)
    check("chats survive a reset() on startup",
          len(v4._sessions) == 2, f"sessions={len(v4._sessions)}")

    print("\n8. Delete a chat")
    v4.delete_session(first_id)
    check("one chat left", len(v4._sessions) == 1)
    v5 = make_echo_view(tmp)
    check("deletion persisted", len(v5._sessions) == 1)

    print(f"\n{sum(results)}/{len(results)} checks passed")
    return 0 if all(results) else 1


def run_gui():
    app = QApplication(sys.argv)

    path = DEFAULT_HISTORY_PATH
    print(f"chatBubble loaded from: {chatBubble.__file__}")
    print(f"History file: {path}")
    print(f"Exists before launch: {Path(path).exists()}"
          + (f" ({Path(path).stat().st_size} bytes)"
             if Path(path).exists() else ""))

    win = QMainWindow()
    win.setWindowTitle("Chat history test")
    win.resize(560, 640)

    view = ChatView(history_path=path)

    def fake_ai(text):
        # Simulate network delay so the typing dots show.
        QTimer.singleShot(800, lambda: view.on_reply(f"Echo: {text}"))

    view.set_send_handler(fake_ai)
    win.setCentralWidget(view)
    win.show()
    sys.exit(app.exec())


if __name__ == "__main__":
    if HEADLESS:
        app = QApplication(sys.argv)
        sys.exit(run_headless())
    run_gui()