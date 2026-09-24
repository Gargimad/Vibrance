"""
orgDashboard.py — Organization dashboard.

Two views in a QStackedWidget:
    0. List page  — the org's own opportunities, with Edit / Delete actions
    1. Form page  — create or edit an opportunity

set_org_data(org) is called by landing.py after login. org is the dict
from Database.authenticate() and must include 'orgID' and 'org_name'.

After save, calls eventCard.clear_thumbnail_cache() so newly attached
images render on the next listing refresh.
"""

from PyQt6.QtCore import Qt, QDate
from PyQt6.QtGui import QCursor
from PyQt6.QtWidgets import (
    QWidget, QVBoxLayout, QHBoxLayout, QLabel, QLineEdit, QTextEdit,
    QPushButton, QComboBox, QDateEdit, QCheckBox, QSpinBox, QListWidget,
    QListWidgetItem, QMessageBox, QFrame, QScrollArea, QGridLayout,
    QStackedWidget, QFileDialog, QSizePolicy,
)

import theme
from eventCard import clear_thumbnail_cache


class OrgDashboard(QWidget):
    def __init__(self, db, on_logout_click=None, on_back_click=None,
                 parent=None):
        super().__init__(parent)
        self.setObjectName(theme.ORG_DASHBOARD)
        self.db = db
        self.on_logout_click = on_logout_click
        self.on_back_click = on_back_click
        self.org = None
        self.editing_id = None
        self._pending_thumbnail = None  # path string set via file dialog

        outer = QVBoxLayout(self)
        outer.setContentsMargins(0, 0, 0, 0)
        outer.setSpacing(0)

        outer.addWidget(self._build_header(), 0)

        self.stack = QStackedWidget()
        self.stack.addWidget(self._build_list_page())
        self.stack.addWidget(self._build_form_page())
        outer.addWidget(self.stack, 1)

    # ── Header ────────────────────────────────────────────────────────────
    def _build_header(self):
        header = QWidget()
        header.setObjectName(theme.VOLUNTEER_HEADER)
        h = QHBoxLayout(header)
        h.setContentsMargins(20, 14, 20, 14)
        h.setSpacing(8)

        self.title_lbl = QLabel("Organization Dashboard")
        self.title_lbl.setObjectName(theme.VOLUNTEER_TITLE)

        self.new_btn = QPushButton("+ New Opportunity")
        self.new_btn.setObjectName(theme.PRIMARY_BTN)
        self.new_btn.setCursor(QCursor(Qt.CursorShape.PointingHandCursor))
        self.new_btn.clicked.connect(self._start_new)

        logout_btn = QPushButton("Log Out")
        logout_btn.setObjectName(theme.SECONDARY_BTN)
        logout_btn.setCursor(QCursor(Qt.CursorShape.PointingHandCursor))
        if self.on_logout_click:
            logout_btn.clicked.connect(self.on_logout_click)

        h.addWidget(self.title_lbl)
        h.addStretch()
        h.addWidget(self.new_btn)
        h.addWidget(logout_btn)
        return header

    # ── List page ─────────────────────────────────────────────────────────
    def _build_list_page(self):
        page = QWidget()
        lay = QVBoxLayout(page)
        lay.setContentsMargins(20, 12, 20, 20)
        lay.setSpacing(10)

        self.list_widget = QListWidget()
        self.list_widget.setObjectName(theme.ORG_OPP_LIST)
        self.list_widget.itemDoubleClicked.connect(self._edit_selected)
        lay.addWidget(self.list_widget, 1)

        row = QHBoxLayout()
        row.addStretch()

        edit_btn = QPushButton("Edit selected")
        edit_btn.setObjectName(theme.SECONDARY_BTN)
        edit_btn.setCursor(QCursor(Qt.CursorShape.PointingHandCursor))
        edit_btn.clicked.connect(self._edit_selected)

        del_btn = QPushButton("Cancel selected")
        del_btn.setObjectName(theme.SECONDARY_BTN)
        del_btn.setCursor(QCursor(Qt.CursorShape.PointingHandCursor))
        del_btn.clicked.connect(self._cancel_selected)

        row.addWidget(edit_btn)
        row.addWidget(del_btn)
        lay.addLayout(row)
        return page

    # ── Form page ─────────────────────────────────────────────────────────
    def _build_form_page(self):
        page = QWidget()
        outer = QVBoxLayout(page)
        outer.setContentsMargins(20, 12, 20, 20)
        outer.setSpacing(10)

        self.form_title = QLabel("New Opportunity")
        self.form_title.setObjectName(theme.VOLUNTEER_TITLE)
        outer.addWidget(self.form_title)

        # Scrollable so the form fits on short windows
        scroll = QScrollArea()
        scroll.setWidgetResizable(True)
        scroll.setFrameShape(QScrollArea.Shape.NoFrame)
        scroll.setObjectName(theme.HOME_SCROLL)

        scroll_content = QWidget()
        form = QGridLayout(scroll_content)
        form.setContentsMargins(0, 0, 0, 0)
        form.setHorizontalSpacing(14)
        form.setVerticalSpacing(10)

        # ── Controls ──────────────────────────────────────────────────────
        self.f_title = QLineEdit()
        self.f_title.setPlaceholderText("e.g. Saturday park cleanup")

        self.f_description = QTextEdit()
        self.f_description.setPlaceholderText(
            "What will volunteers be doing?"
        )
        self.f_description.setFixedHeight(90)

        self.f_category = QLineEdit()
        self.f_category.setPlaceholderText("e.g. Environment")

        self.f_location = QLineEdit()
        self.f_location.setPlaceholderText("Where (free text)")

        self.f_address = QLineEdit()
        self.f_address.setPlaceholderText("Street address (optional)")

        self.f_remote = QCheckBox("Remote")

        self.f_date = QDateEdit()
        self.f_date.setCalendarPopup(True)
        self.f_date.setDate(QDate.currentDate())
        self.f_date.setDisplayFormat("yyyy-MM-dd")

        self.f_start = QLineEdit()
        self.f_start.setPlaceholderText("HH:MM (e.g. 09:00)")

        self.f_end = QLineEdit()
        self.f_end.setPlaceholderText("HH:MM (e.g. 12:00)")

        self.f_capacity = QSpinBox()
        self.f_capacity.setRange(0, 9999)
        self.f_capacity.setSpecialValueText("Unlimited")

        self.f_status = QComboBox()
        self.f_status.addItems(["open", "full", "cancelled", "completed"])

        self.f_skills = QLineEdit()
        self.f_skills.setPlaceholderText("Comma-separated (optional)")

        self.f_contact_name = QLineEdit()
        self.f_contact_name.setPlaceholderText("Contact name")

        self.f_contact_email = QLineEdit()
        self.f_contact_email.setPlaceholderText("Contact email")

        # ── Layout ────────────────────────────────────────────────────────
        r = 0
        form.addWidget(QLabel("Title *"), r, 0)
        form.addWidget(self.f_title, r, 1, 1, 3); r += 1

        form.addWidget(QLabel("Description"), r, 0)
        form.addWidget(self.f_description, r, 1, 1, 3); r += 1

        form.addWidget(QLabel("Category"), r, 0)
        form.addWidget(self.f_category, r, 1)
        form.addWidget(QLabel("Status"), r, 2)
        form.addWidget(self.f_status, r, 3); r += 1

        form.addWidget(QLabel("Location"), r, 0)
        form.addWidget(self.f_location, r, 1)
        form.addWidget(QLabel("Address"), r, 2)
        form.addWidget(self.f_address, r, 3); r += 1

        form.addWidget(QLabel("Date"), r, 0)
        form.addWidget(self.f_date, r, 1)
        form.addWidget(self.f_remote, r, 2)
        form.addWidget(QLabel("Capacity"), r, 3)
        form.addWidget(self.f_capacity, r, 4); r += 1

        form.addWidget(QLabel("Start time"), r, 0)
        form.addWidget(self.f_start, r, 1)
        form.addWidget(QLabel("End time"), r, 2)
        form.addWidget(self.f_end, r, 3); r += 1

        form.addWidget(QLabel("Required skills"), r, 0)
        form.addWidget(self.f_skills, r, 1, 1, 3); r += 1

        form.addWidget(QLabel("Contact name"), r, 0)
        form.addWidget(self.f_contact_name, r, 1)
        form.addWidget(QLabel("Contact email"), r, 2)
        form.addWidget(self.f_contact_email, r, 3); r += 1

        # ── Thumbnail ─────────────────────────────────────────────────────
        self.thumb_lbl = QLabel("No image attached")
        self.thumb_lbl.setObjectName(theme.EVENT_META_VALUE)

        pick_btn = QPushButton("Choose image…")
        pick_btn.setObjectName(theme.SECONDARY_BTN)
        pick_btn.setCursor(QCursor(Qt.CursorShape.PointingHandCursor))
        pick_btn.clicked.connect(self._pick_thumbnail)

        clear_btn = QPushButton("Remove image")
        clear_btn.setObjectName(theme.SECONDARY_BTN)
        clear_btn.setCursor(QCursor(Qt.CursorShape.PointingHandCursor))
        clear_btn.clicked.connect(self._clear_thumbnail)

        thumb_row = QHBoxLayout()
        thumb_row.addWidget(pick_btn)
        thumb_row.addWidget(clear_btn)
        thumb_row.addWidget(self.thumb_lbl, 1)

        form.addWidget(QLabel("Thumbnail"), r, 0)
        form.addLayout(thumb_row, r, 1, 1, 4); r += 1

        scroll.setWidget(scroll_content)
        outer.addWidget(scroll, 1)

        # ── Actions ───────────────────────────────────────────────────────
        row = QHBoxLayout()
        cancel_btn = QPushButton("Cancel")
        cancel_btn.setObjectName(theme.SECONDARY_BTN)
        cancel_btn.setCursor(QCursor(Qt.CursorShape.PointingHandCursor))
        cancel_btn.clicked.connect(lambda: self.stack.setCurrentIndex(0))

        save_btn = QPushButton("Save")
        save_btn.setObjectName(theme.PRIMARY_BTN)
        save_btn.setCursor(QCursor(Qt.CursorShape.PointingHandCursor))
        save_btn.clicked.connect(self._save)

        row.addStretch()
        row.addWidget(cancel_btn)
        row.addWidget(save_btn)
        outer.addLayout(row)
        return page

    # ── Lifecycle ─────────────────────────────────────────────────────────
    def set_org_data(self, org_data):
        self.org = org_data
        name = org_data.get("org_name", "")
        self.title_lbl.setText(f"Dashboard — {name}")
        self.refresh()

    # ── List refresh ──────────────────────────────────────────────────────
    def refresh(self):
        self.list_widget.clear()
        if not self.org:
            return
        try:
            rows = self.db.getOpportunitiesByOrg(self.org["orgID"])
        except Exception as e:
            print("Org opportunities query failed:", e)
            return

        if not rows:
            item = QListWidgetItem("No opportunities yet — click “+ New” to create one.")
            item.setFlags(Qt.ItemFlag.NoItemFlags)
            self.list_widget.addItem(item)
            return

        for r in rows:
            cap = r["capacity"]
            reg = r["registered_count"] or 0
            spots = f" · {reg}/{cap}" if cap else f" · {reg} signed up"
            label = (
                f"{r['title']}  ·  {r['event_date'] or 'TBD'}"
                f"  ·  {r['status'] or 'open'}  ·  "
                f"{r['category'] or 'uncategorized'}{spots}"
            )
            item = QListWidgetItem(label)
            item.setData(Qt.ItemDataRole.UserRole, r["opportunityID"])
            self.list_widget.addItem(item)

    # ── Form start / edit ─────────────────────────────────────────────────
    def _start_new(self):
        self.editing_id = None
        self._pending_thumbnail = None
        self.form_title.setText("New Opportunity")
        self.f_title.clear()
        self.f_description.clear()
        self.f_category.clear()
        self.f_location.clear()
        self.f_address.clear()
        self.f_skills.clear()
        self.f_contact_name.clear()
        self.f_contact_email.clear()
        self.f_start.clear()
        self.f_end.clear()
        self.f_remote.setChecked(False)
        self.f_date.setDate(QDate.currentDate())
        self.f_capacity.setValue(0)
        self.f_status.setCurrentText("open")
        self.thumb_lbl.setText("No image attached")
        self.stack.setCurrentIndex(1)

    def _edit_selected(self, *_):
        item = self.list_widget.currentItem()
        if not item:
            return
        oid = item.data(Qt.ItemDataRole.UserRole)
        if not oid:
            return
        row = self.db.getOpportunityByID(oid)
        if not row:
            QMessageBox.warning(self, "Not found",
                                "That opportunity no longer exists.")
            self.refresh()
            return

        self.editing_id = oid
        self._pending_thumbnail = row["thumbnail"]
        self.form_title.setText("Edit Opportunity")
        self.f_title.setText(row["title"] or "")
        self.f_description.setPlainText(row["description"] or "")
        self.f_category.setText(row["category"] or "")
        self.f_location.setText(row["location"] or "")
        self.f_address.setText(row["address"] or "")
        self.f_remote.setChecked(bool(row["is_remote"]))
        if row["event_date"]:
            d = QDate.fromString(row["event_date"], "yyyy-MM-dd")
            if d.isValid():
                self.f_date.setDate(d)
        self.f_start.setText(row["start_time"] or "")
        self.f_end.setText(row["end_time"] or "")
        self.f_capacity.setValue(row["capacity"] or 0)
        self.f_status.setCurrentText(row["status"] or "open")
        self.f_skills.setText(row["required_skills"] or "")
        self.f_contact_name.setText(row["contact_name"] or "")
        self.f_contact_email.setText(row["contact_email"] or "")
        self.thumb_lbl.setText(
            self._pending_thumbnail or "No image attached"
        )
        self.stack.setCurrentIndex(1)

    # ── Thumbnail ─────────────────────────────────────────────────────────
    def _pick_thumbnail(self):
        path, _ = QFileDialog.getOpenFileName(
            self, "Choose thumbnail",
            "", "Images (*.png *.jpg *.jpeg *.webp *.bmp)"
        )
        if path:
            self._pending_thumbnail = path
            self.thumb_lbl.setText(path)

    def _clear_thumbnail(self):
        self._pending_thumbnail = None
        self.thumb_lbl.setText("No image attached")

    # ── Cancel / soft delete ──────────────────────────────────────────────
    def _cancel_selected(self):
        item = self.list_widget.currentItem()
        if not item:
            return
        oid = item.data(Qt.ItemDataRole.UserRole)
        if not oid:
            return
        if QMessageBox.question(
            self, "Cancel opportunity",
            "Mark this opportunity as cancelled? Volunteers will still see "
            "it in their history but it won't appear in listings."
        ) != QMessageBox.StandardButton.Yes:
            return
        self.db.updateOpportunity(oid, status="cancelled")
        self.refresh()

    # ── Save ──────────────────────────────────────────────────────────────
    def _save(self):
        if not self.org:
            return

        title = self.f_title.text().strip()
        if not title:
            QMessageBox.warning(self, "Missing title", "Title is required.")
            return

        payload = dict(
            title=title,
            description=self.f_description.toPlainText().strip(),
            category=self.f_category.text().strip(),
            location=self.f_location.text().strip(),
            address=self.f_address.text().strip(),
            is_remote=self.f_remote.isChecked(),
            event_date=self.f_date.date().toString("yyyy-MM-dd"),
            start_time=self.f_start.text().strip() or None,
            end_time=self.f_end.text().strip() or None,
            capacity=self.f_capacity.value() or None,
            status=self.f_status.currentText(),
            required_skills=self.f_skills.text().strip() or None,
            contact_name=self.f_contact_name.text().strip() or None,
            contact_email=self.f_contact_email.text().strip() or None,
            thumbnail=self._pending_thumbnail,
        )

        if self.editing_id:
            ok = self.db.updateOpportunity(self.editing_id, **payload)
            if not ok:
                QMessageBox.warning(self, "Save failed",
                                    "Could not update opportunity.")
                return
        else:
            new_id = self.db.addOpportunity(
                orgID=self.org["orgID"],
                title=payload["title"],
                description=payload["description"],
                category=payload["category"],
                location=payload["location"],
                address=payload["address"],
                is_remote=payload["is_remote"],
                event_date=payload["event_date"],
                thumbnail=payload["thumbnail"],
                start_time=payload["start_time"],
                end_time=payload["end_time"],
                capacity=payload["capacity"],
                status=payload["status"],
                required_skills=payload["required_skills"],
                contact_name=payload["contact_name"],
                contact_email=payload["contact_email"],
            )
            if not new_id:
                QMessageBox.warning(self, "Save failed",
                                    "Could not create opportunity.")
                return

        clear_thumbnail_cache()
        self.refresh()
        self.stack.setCurrentIndex(0)