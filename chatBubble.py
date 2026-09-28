"""
chatBubble.py — A self-contained messaging-style chat widget for Moxie.

Public API (all on ChatView):
    view = ChatView(parent=None, greeting="...")
    view.set_send_handler(fn)              # fn(text) called on send
    view.set_system_prompt_provider(fn)    # fn() -> str, refreshed per send
    view.get_system_prompt()               # -> str
    view.on_reply(text)                    # call when the AI replies
    view.on_error(message)                 # call when the AI fails
    view.set_busy(bool)                    # lock/unlock the composer
    view.reset()                           # clear and greet again
    view.history                           # list[{role, content}, ...]

ChatView knows nothing about HTTP or Groq. The caller wires a backend
by passing a send handler that starts a worker and later calls
view.on_reply() / view.on_error().
"""

from datetime import datetime

from PyQt6.QtCore import Qt, QTimer
from PyQt6.QtWidgets import (
    QWidget, QVBoxLayout, QHBoxLayout, QLabel, QPushButton, QFrame,
    QScrollArea, QLineEdit, QSizePolicy,
)


class ChatView(QWidget):
    """A messaging-style chat panel with bubbles, grouping, typing dots,
    timestamps, a date separator, and a rounded composer. One class."""

    def __init__(self,
                 greeting="Hi! I'm Moxie. How can I help? 🌱",
                 parent=None):
        super().__init__(parent)

        self._greeting = greeting
        self._send_handler = None
        self._system_prompt_provider = None
        self._typing_bubble = None
        self._typing_timer = None
        self._typing_step = 0
        self._last_who = None
        self._is_busy = False
        self.history = []          # [{role, content}, ...]
        self._voice_worker = None

        self._build_ui()
        self.reset()

    # ── Public API ────────────────────────────────────────────────────
    def set_send_handler(self, fn):
        """fn(text: str) is called when the user sends a message."""
        self._send_handler = fn

    def set_system_prompt_provider(self, fn):
        """fn() -> str, called on every send to get a fresh prompt."""
        self._system_prompt_provider = fn

    def get_system_prompt(self):
        if self._system_prompt_provider:
            return self._system_prompt_provider()
        return "You are a helpful assistant."

    def on_reply(self, text):
        """Deliver the AI's reply to the chat view."""
        self._hide_typing()
        self.history.append({"role": "assistant", "content": text})
        self._append_bubble(text, who="assistant")
        self.set_busy(False)

    def on_error(self, message):
        """Deliver an error message to the chat view."""
        self._hide_typing()
        # Don't add errors to history — they aren't part of the
        # conversation the model should see.
        self._append_bubble(message, who="assistant")
        self.set_busy(False)

    def set_busy(self, busy):
        self._is_busy = busy
        self.input.setEnabled(not busy)
        self.send_btn.setEnabled(not busy)
        self.send_btn.setText("…" if busy else "➤")
        if not busy:
            self.input.setFocus()

    def reset(self):
        """Clear the transcript, reset history, and greet again."""
        # Remove every widget above the trailing stretch.
        while self.chat_layout.count() > 1:
            item = self.chat_layout.takeAt(0)
            w = item.widget()
            if w:
                w.setParent(None)
                w.deleteLater()

        self._hide_typing()
        self.history = []
        self._last_who = None
        self._append_date_separator("Today")
        self._append_bubble(self._greeting, who="assistant")

    # ── UI construction ───────────────────────────────────────────────
    def _build_ui(self):
        outer = QVBoxLayout(self)
        outer.setContentsMargins(0, 0, 0, 0)
        outer.setSpacing(8)

        self.scroll = QScrollArea()
        self.scroll.setWidgetResizable(True)
        self.scroll.setFrameShape(QFrame.Shape.NoFrame)
        self.scroll.setHorizontalScrollBarPolicy(
            Qt.ScrollBarPolicy.ScrollBarAlwaysOff
        )
        self.scroll.setStyleSheet(
            "QScrollArea { background: transparent; border: none; }"
        )

        self.content = QWidget()
        self.chat_layout = QVBoxLayout(self.content)
        self.chat_layout.setContentsMargins(8, 8, 8, 8)
        self.chat_layout.setSpacing(4)
        self.chat_layout.addStretch(1)   # keeps bubbles pushed to the top
        self.scroll.setWidget(self.content)
        outer.addWidget(self.scroll, 1)

        # ── Composer ─────────────────────────────────────────────────
        composer = QFrame()
        composer.setObjectName("ChatComposer")
        composer.setStyleSheet(
            "QFrame#ChatComposer {"
            "  background: rgba(127,127,127,20);"
            "  border-radius: 22px;"
            "  padding: 4px;"
            "}"
        )
        cl = QHBoxLayout(composer)
        cl.setContentsMargins(8, 4, 6, 4)
        cl.setSpacing(6)

        self.input = QLineEdit()
        self.input.setPlaceholderText("Message Moxie…")
        self.input.setStyleSheet(
            "QLineEdit { border: none; background: transparent;"
            " padding: 6px 4px; font-size: 13px; }"
        )
        self.input.returnPressed.connect(self._on_send_clicked)
        cl.addWidget(self.input, 1)

        self.send_btn = QPushButton("➤")
        self.send_btn.setFixedSize(34, 34)
        self.send_btn.setCursor(Qt.CursorShape.PointingHandCursor)
        self.send_btn.setStyleSheet(
            "QPushButton {"
            "  background: qlineargradient(x1:0, y1:0, x2:1, y2:1,"
            "    stop:0 #2E86DE, stop:1 #5B4BE0);"
            "  color: white;"
            "  border: none;"
            "  border-radius: 17px;"
            "  font-size: 14px;"
            "  font-weight: bold;"
            "}"
            "QPushButton:hover { background: #4A6CF7; }"
            "QPushButton:disabled { background: rgba(127,127,127,80); }"
        )
        self.send_btn.clicked.connect(self._on_send_clicked)
        cl.addWidget(self.send_btn, 0)
        # In _build_ui(), inside the composer layout, after the send button:
        self.mic_btn = QPushButton("🎤")
        self.mic_btn.setFixedSize(34, 34)
        self.mic_btn.setCursor(Qt.CursorShape.PointingHandCursor)
        self.mic_btn.setStyleSheet(
            "QPushButton { background: transparent; border: none;"
            " font-size: 16px; border-radius: 17px; }"
            "QPushButton:hover { background: rgba(127,127,127,40); }"
            "QPushButton:checked { background: rgba(46,134,222,60); }"
        )
        self.mic_btn.setCheckable(True)
        self.mic_btn.clicked.connect(self._on_mic_clicked)
        cl.addWidget(self.mic_btn, 0)

        # In __init__:
        clear = QPushButton("⟳")
        clear.setFixedSize(34, 34)
        clear.setCursor(Qt.CursorShape.PointingHandCursor)
        clear.setToolTip("New chat")
        clear.setStyleSheet(
            "QPushButton {"
            "  background: transparent;"
            "  border: none;"
            "  color: rgba(140,140,140,200);"
            "  font-size: 16px;"
            "  border-radius: 17px;"
            "}"
            "QPushButton:hover { background: rgba(127,127,127,40); }"
        )
        clear.clicked.connect(self._on_new_chat)
        cl.addWidget(clear, 0)

        outer.addWidget(composer)

    # ── Bubble rendering ──────────────────────────────────────────────
    def _append_bubble(self, text, who="assistant", timestamp=None):
        """Build a single message row inline (no helper class)."""
        is_user = who == "user"
        grouped = (self._last_who == who)
        self._last_who = who

        row = QWidget()
        outer = QHBoxLayout(row)
        outer.setContentsMargins(
            8, 1 if grouped else 4, 8, 1 if grouped else 4
        )
        outer.setSpacing(8)

        # Assistant avatar (first bubble of a group only).
        if not is_user:
            if grouped:
                spacer = QLabel()
                spacer.setFixedSize(28, 28)
                outer.addWidget(spacer, 0, Qt.AlignmentFlag.AlignTop)
            else:
                avatar = QLabel("✨")
                avatar.setFixedSize(28, 28)
                avatar.setAlignment(Qt.AlignmentFlag.AlignCenter)
                avatar.setStyleSheet(
                    "background: qlineargradient(x1:0, y1:0, x2:1, y2:1,"
                    " stop:0 #2E86DE, stop:1 #5B4BE0);"
                    " color: white;"
                    " border-radius: 14px;"
                    " font-size: 13px;"
                )
                outer.addWidget(avatar, 0, Qt.AlignmentFlag.AlignTop)

        col = QVBoxLayout()
        col.setSpacing(2)
        col.setContentsMargins(0, 0, 0, 0)

        bubble = QLabel(text)
        bubble.setWordWrap(True)
        bubble.setTextInteractionFlags(
            Qt.TextInteractionFlag.TextSelectableByMouse
        )
        bubble.setMaximumWidth(440)
        bubble.setSizePolicy(
            QSizePolicy.Policy.Maximum, QSizePolicy.Policy.Preferred
        )
        bubble.setStyleSheet(self._bubble_qss(is_user, grouped))
        col.addWidget(bubble)

        if not grouped:
            ts = QLabel(timestamp or datetime.now().strftime("%H:%M"))
            ts.setStyleSheet(
                "color: rgba(140,140,140,180);"
                "font-size: 10px;"
                "padding: 0 6px;"
            )
            ts.setAlignment(
                Qt.AlignmentFlag.AlignRight if is_user
                else Qt.AlignmentFlag.AlignLeft
            )
            col.addWidget(ts)

        if is_user:
            outer.addStretch(1)
            outer.addLayout(col)
        else:
            outer.addLayout(col)
            outer.addStretch(1)

        self.chat_layout.insertWidget(self.chat_layout.count() - 1, row)
        QTimer.singleShot(0, self._scroll_to_bottom)

    @staticmethod
    def _bubble_qss(is_user, grouped):
        if is_user:
            bg = ("qlineargradient(x1:0, y1:0, x2:1, y2:1,"
                  " stop:0 #2E86DE, stop:1 #4A6CF7)")
            fg = "white"
            radii = (16, 16, 16, 16) if grouped else (16, 16, 4, 16)
        else:
            bg = "rgba(127,127,127,32)"
            fg = "palette(text)"
            radii = (16, 16, 16, 16) if grouped else (4, 16, 16, 16)

        tl, tr, br, bl = radii
        return (
            f"background: {bg};"
            f"color: {fg};"
            f"border-top-left-radius: {tl}px;"
            f"border-top-right-radius: {tr}px;"
            f"border-bottom-right-radius: {br}px;"
            f"border-bottom-left-radius: {bl}px;"
            "padding: 8px 12px;"
            "font-size: 13px;"
        )

    def _append_date_separator(self, label="Today"):
        wrap = QWidget()
        lay = QHBoxLayout(wrap)
        lay.setContentsMargins(0, 8, 0, 8)
        lay.setSpacing(8)

        left = QFrame()
        left.setFrameShape(QFrame.Shape.HLine)
        left.setStyleSheet("color: rgba(127,127,127,60);")
        left.setFixedHeight(1)

        lbl = QLabel(label)
        lbl.setStyleSheet(
            "color: rgba(140,140,140,200);"
            "font-size: 11px;"
            "font-weight: 600;"
            "padding: 0 6px;"
        )

        right = QFrame()
        right.setFrameShape(QFrame.Shape.HLine)
        right.setStyleSheet("color: rgba(127,127,127,60);")
        right.setFixedHeight(1)

        lay.addWidget(left, 1)
        lay.addWidget(lbl, 0)
        lay.addWidget(right, 1)

        self.chat_layout.insertWidget(self.chat_layout.count() - 1, wrap)

    def _scroll_to_bottom(self):
        sb = self.scroll.verticalScrollBar()
        sb.setValue(sb.maximum())

    # ── Typing indicator ──────────────────────────────────────────────
    def _show_typing(self):
        if self._typing_bubble is not None:
            return
        self._typing_bubble = self._append_typing_bubble()
        self._typing_step = 0
        self._typing_timer = QTimer(self)
        self._typing_timer.setInterval(450)
        self._typing_timer.timeout.connect(self._tick_typing)
        self._typing_timer.start()

    def _append_typing_bubble(self):
        """A bare-bones assistant bubble used only for the dots."""
        row = QWidget()
        outer = QHBoxLayout(row)
        outer.setContentsMargins(8, 4, 8, 4)
        outer.setSpacing(8)

        avatar = QLabel("✨")
        avatar.setFixedSize(28, 28)
        avatar.setAlignment(Qt.AlignmentFlag.AlignCenter)
        avatar.setStyleSheet(
            "background: qlineargradient(x1:0, y1:0, x2:1, y2:1,"
            " stop:0 #2E86DE, stop:1 #5B4BE0);"
            " color: white;"
            " border-radius: 14px;"
            " font-size: 13px;"
        )
        outer.addWidget(avatar, 0, Qt.AlignmentFlag.AlignTop)

        dots = QLabel("●○○")
        dots.setStyleSheet(
            "background: rgba(127,127,127,32);"
            "color: rgba(140,140,140,200);"
            "border-top-left-radius: 4px;"
            "border-top-right-radius: 16px;"
            "border-bottom-right-radius: 16px;"
            "border-bottom-left-radius: 16px;"
            "padding: 8px 14px;"
            "font-size: 11px;"
            "letter-spacing: 2px;"
        )
        outer.addWidget(dots, 0, Qt.AlignmentFlag.AlignTop)
        outer.addStretch(1)

        self.chat_layout.insertWidget(self.chat_layout.count() - 1, row)
        QTimer.singleShot(0, self._scroll_to_bottom)
        self._last_who = "assistant"
        return row

    def _tick_typing(self):
        if self._typing_bubble is None:
            return
        self._typing_step = (self._typing_step + 1) % 3
        frames = ["●○○", "○●○", "○○●"]
        lbl = self._typing_bubble.findChild(QLabel)
        # The first QLabel in the row is the avatar; we want the second.
        labels = self._typing_bubble.findChildren(QLabel)
        if len(labels) >= 2:
            labels[1].setText(frames[self._typing_step])

    def _hide_typing(self):
        if self._typing_timer:
            self._typing_timer.stop()
            self._typing_timer = None
        if self._typing_bubble is None:
            return
        self.chat_layout.removeWidget(self._typing_bubble)
        self._typing_bubble.setParent(None)
        self._typing_bubble.deleteLater()
        self._typing_bubble = None
        # So the real reply starts a fresh group with its own avatar.
        self._last_who = None
    def _on_mic_clicked(self):
        """Start or stop voice input."""
        if self._voice_worker and self._voice_worker.isRunning():
            # Already listening — cancel
            self._voice_worker.stop()
            self._voice_worker = None
            self.mic_btn.setChecked(False)
            return

        self.mic_btn.setChecked(True)
        self.input.setPlaceholderText("Listening… speak now")

        from voiceWorker import VoiceWorker
        self._voice_worker = VoiceWorker()
        self._voice_worker.transcribed.connect(self._on_voice_result)
        self._voice_worker.failed.connect(self._on_voice_error)
        self._voice_worker.start()

    def _on_voice_result(self, text):
        """Fill the input with the recognized text."""
        self.input.setText(text)
        self.input.setPlaceholderText("Message Moxie…")
        self.mic_btn.setChecked(False)

    def _on_voice_error(self, message):
        self.input.setPlaceholderText("Message Moxie…")
        self.mic_btn.setChecked(False)
        # Optionally show a toast or status message
    # ── Event handlers ────────────────────────────────────────────────
    def _on_send_clicked(self):
        text = self.input.text().strip()
        if not text or self._is_busy:
            return
        self.input.clear()
        self.history.append({"role": "user", "content": text})
        self.history = self.history[-20:]
        while self.history and self.history[0]["role"] != "user":
            self.history.pop(0)

        self._append_bubble(text, who="user")
        self.set_busy(True)
        self._show_typing()

        if self._send_handler:
            self._send_handler(text)
        else:
            self.on_error("(No send handler configured.)")

    def _on_new_chat(self):
        if self._is_busy:
            return
        self.reset()