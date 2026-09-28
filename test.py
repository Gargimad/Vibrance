# test_chat.py
import sys
from PyQt6.QtCore import QTimer
from PyQt6.QtWidgets import QApplication, QMainWindow
from chatBubble import ChatView

app = QApplication(sys.argv)
w = QMainWindow()
w.resize(600, 700)

view = ChatView()

def fake_send(text):
    QTimer.singleShot(1200, lambda: view.on_reply(
        f"You said: \"{text}\"! 🎉"
    ))

view.set_send_handler(fake_send)
view.set_system_prompt_provider(lambda: "test")
w.setCentralWidget(view)
w.show()
sys.exit(app.exec())