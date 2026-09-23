from PyQt6.QtCore import Qt, QDate
from PyQt6.QtGui import QCursor
from PyQt6.QtWidgets import (
    QWidget, QVBoxLayout, QHBoxLayout, QLabel, QLineEdit, QTextEdit,
    QPushButton, QComboBox, QDateEdit, QCheckBox, QSpinBox, QListWidget,
    QListWidgetItem, QMessageBox, QFrame, QScrollArea, QGridLayout,
    QStackedWidget
)


class OrgDashboard(QWidget):
    """
    Org-side: a list of the org's opportunities plus a create/edit form.
    Two pages in a small internal stack: 'list' and 'form'.
    """

    def __init__(self, db, on_logout_click=None, on_back_click=None, parent=None):
        super().__init__(parent)
        self.setObjectName("OrgDashboard")
        self.db = db
        self.on_logout_click = on_logout_click
        self.org = None
        self.editing_id = None

        outer = QVBoxLayout(self)
        outer.setContentsMargins(0, 0, 0, 0)
        outer.setSpacing(0)

        # Header
        header = QWidget()
        header.setObjectName("VolunteerHeader")
        h = QHBoxLayout(header)
        h.setContentsMargins(20, 14, 20, 14)

        self.title_lbl = QLabel("Organization Dashboard")
        self.title_lbl.setObjectName("VolunteerTitle")

        self.new_btn = QPushButton("+ New Opportunity")
        self.new_btn.setObjectName("PrimaryBtn")
        self.new_btn.setCursor(QCursor(Qt.CursorShape.PointingHandCursor))
        self.new_btn.clicked.connect(self._start_new)

        logout_btn = QPushButton("Log out")
        logout_btn.setObjectName("SecondaryBtn")
        logout_btn.setCursor(QCursor(Qt.CursorShape.PointingHandCursor))
        if on_logout_click:
            logout_btn.clicked.connect(on_logout_click)

        h.addWidget(self.title_lbl)
        h.addStretch()
        h.addWidget(self.new_btn)
        h.addWidget(logout_btn)

        # Internal stack: list page + form page
        self.stack = QStackedWidget()
        self.stack.addWidget(self._build_list_page())
        self.stack.addWidget(self._build_form_page())

        outer.addWidget(header)
        outer.addWidget(self.stack, 1)

    # ------------------------------------------------------------------
    def _build_list_page(self):
        page = QWidget()
        lay = QVBoxLayout(page)
        lay.setContentsMargins(20, 12, 20, 20)

        self.list_widget = QListWidget()
        self.list_widget.setObjectName("OrgOppList")
        self.list_widget.itemDoubleClicked.connect(self._edit_selected)
        lay.addWidget(self.list_widget)

        row = QHBoxLayout()
        edit_btn = QPushButton("Edit selected")
        edit_btn.clicked.connect(self._edit_selected)
        del_btn = QPushButton("Delete selected")
        del_btn.clicked.connect(self._delete_selected)
        row.addStretch()
        row.addWidget(edit_btn)
        row.addWidget(del_btn)
        lay.addLayout(row)
        return page

    def _build_form_page(self):
        page = QWidget()
        outer = QVBoxLayout(page)
        outer.setContentsMargins(20, 12, 20, 20)
        outer.setSpacing(10)

        self.form_title = QLabel("New Opportunity")
        self.form_title.setObjectName("VolunteerTitle")
        outer.addWidget(self.form_title)

        form = QGridLayout()
        form.setHorizontalSpacing(14)
        form.setVerticalSpacing(10)

        self.f_title = QLineEdit(); self.f_title.setPlaceholderText("Title *")
        self.f_description = QTextEdit(); self.f_description.setPlaceholderText("Description")
        self.f_description.setFixedHeight(90)
        self.f_category = QLineEdit(); self.f_category.setPlaceholderText("Category (e.g. Environment)")
        self.f_location = QLineEdit(); self.f_location.setPlaceholderText("Location (free text)")
        self.f_address = QLineEdit(); self.f_address.setPlaceholderText("Address (optional, structured)")
        self.f_remote = QCheckBox("Remote")
        self.f_date = QDateEdit(); self.f_date.setCalendarPopup(True)
        self.f_date.setDate(QDate.currentDate())
        self.f_date.setDisplayFormat("yyyy-MM-dd")
        self.f_start = QLineEdit(); self.f_start.setPlaceholderText("Start time (e.g. 15:00)")
        self.f_end = QLineEdit(); self.f_end.setPlaceholderText("End time (e.g. 18:00)")
        self.f_capacity = QSpinBox(); self.f_capacity.setRange(0, 9999)
        self.f_capacity.setSpecialValueText("Unlimited")
        self.f_status = QComboBox(); self.f_status.addItems(["open", "full", "cancelled", "completed"])
        self.f_skills = QLineEdit(); self.f_skills.setPlaceholderText("Required skills (comma-separated)")
        self.f_contact_name = QLineEdit(); self.f_contact_name.setPlaceholderText("Contact name")
        self.f_contact_email = QLineEdit(); self.f_contact_email.setPlaceholderText("Contact email")

        r = 0
        form.addWidget(QLabel("Title"), r, 0); form.addWidget(self.f_title, r, 1, 1, 3); r += 1
        form.addWidget(QLabel("Description"), r, 0); form.addWidget(self.f_description, r, 1, 1, 3); r += 1
        form.addWidget(QLabel("Category"), r, 0); form.addWidget(self.f_category, r, 1)
        form.addWidget(QLabel("Status"), r, 2); form.addWidget(self.f_status, r, 3); r += 1
        form.addWidget(QLabel("Location"), r, 0); form.addWidget(self.f_location, r, 1)
        form.addWidget(QLabel("Address"), r, 2); form.addWidget(self.f_address, r, 3); r += 1
        form.addWidget(QLabel("Date"), r, 0); form.addWidget(self.f_date, r, 1)
        form.addWidget(self.f_remote, r, 2)
        form.addWidget(QLabel("Capacity"), r, 3); r += 1
        form.addWidget(QLabel("Start"), r, 0); form.addWidget(self.f_start, r, 1)
        form.addWidget(QLabel("End"), r, 2); form.addWidget(self.f_end, r, 3)
        form.addWidget(self.f_capacity, r, 3, 1, 1)
        r += 1
        form.addWidget(QLabel("Skills"), r, 0); form.addWidget(self.f_skills, r, 1, 1, 3); r += 1
        form.addWidget(QLabel("Contact name"), r, 0); form.addWidget(self.f_contact_name, r, 1)
        form.addWidget(QLabel("Contact email"), r, 2); form.addWidget(self.f_contact_email, r, 3)

        outer.addLayout(form)
        outer.addStretch()

        row = QHBoxLayout()
        cancel_btn = QPushButton("Cancel")
        cancel_btn.clicked.connect(lambda: self.stack.setCurrentIndex(0))
        save_btn = QPushButton("Save")
        save_btn.setObjectName("PrimaryBtn")
        save_btn.clicked.connect(self._save)
        row.addStretch()
        row.addWidget(cancel_btn)
        row.addWidget(save_btn)
        outer.addLayout(row)
        return page

    # ------------------------------------------------------------------
    def set_org_data(self, org_data: dict):
        self.org = org_data
        self.title_lbl.setText(f"Dashboard — {org_data.get('org_name', '')}")
        self.refresh()

    def refresh(self):
        self.list_widget.clear()
        if not self.org:
            return
        rows = self.db.getOpportunitiesByOrg(self.org["orgID"])
        for r in rows:
            label = (f"{r['title']}  •  {r['event_date'] or 'TBD'}  "
                     f"•  {r['status'] or 'open'}  •  {r['category'] or ''}")
            item = QListWidgetItem(label)
            item.setData(Qt.ItemDataRole.UserRole, r["opportunityID"])
            self.list_widget.addItem(item)

    # ------------------------------------------------------------------
    def _start_new(self):
        self.editing_id = None
        self.form_title.setText("New Opportunity")
        self.f_title.clear(); self.f_description.clear(); self.f_category.clear()
        self.f_location.clear(); self.f_address.clear(); self.f_skills.clear()
        self.f_contact_name.clear(); self.f_contact_email.clear()
        self.f_start.clear(); self.f_end.clear()
        self.f_remote.setChecked(False)
        self.f_date.setDate(QDate.currentDate())
        self.f_capacity.setValue(0)
        self.f_status.setCurrentText("open")
        self.stack.setCurrentIndex(1)

    def _edit_selected(self, *_):
        item = self.list_widget.currentItem()
        if not item:
            return
        oid = item.data(Qt.ItemDataRole.UserRole)
        # Load the row via existing helper and pick this one out
        rows = [r for r in self.db.getOpportunitiesByOrg(self.org["orgID"])
                if r["opportunityID"] == oid]
        if not rows:
            return
        r = rows[0]
        self.editing_id = oid
        self.form_title.setText("Edit Opportunity")
        self.f_title.setText(r["title"] or "")
        self.f_description.setPlainText(r["description"] or "")
        self.f_category.setText(r["category"] or "")
        self.f_location.setText(r["location"] or "")
        self.f_address.setText(r["address"] or "")
        self.f_remote.setChecked(bool(r["is_remote"]))
        if r["event_date"]:
            d = QDate.fromString(r["event_date"], "yyyy-MM-dd")
            if d.isValid():
                self.f_date.setDate(d)
        self.f_start.setText(r["start_time"] or "")
        self.f_end.setText(r["end_time"] or "")
        self.f_capacity.setValue(r["capacity"] or 0)
        self.f_status.setCurrentText(r["status"] or "open")
        self.f_skills.setText(r["required_skills"] or "")
        self.f_contact_name.setText(r["contact_name"] or "")
        self.f_contact_email.setText(r["contact_email"] or "")
        self.stack.setCurrentIndex(1)

    def _delete_selected(self):
        item = self.list_widget.currentItem()
        if not item:
            return
        oid = item.data(Qt.ItemDataRole.UserRole)
        if QMessageBox.question(self, "Delete", "Delete this opportunity?") \
                != QMessageBox.StandardButton.Yes:
            return
        # Soft-delete via status update — safer than hard delete
        self.db.updateOpportunity(oid, status="cancelled")
        self.refresh()

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
        )

        if self.editing_id:
            ok = self.db.updateOpportunity(self.editing_id, **payload)
        else:
            ok = self.db.addOpportunity(
                self.org["orgID"],
                payload["title"], payload["description"], payload["category"],
                payload["location"], payload["is_remote"], payload["event_date"],
                start_time=payload["start_time"], end_time=payload["end_time"],
                capacity=payload["capacity"], status=payload["status"],
                required_skills=payload["required_skills"],
                contact_name=payload["contact_name"],
                contact_email=payload["contact_email"],
                address=payload["address"],
            )

        if not ok:
            QMessageBox.warning(self, "Save failed", "Could not save opportunity.")
            return

        self.refresh()
        self.stack.setCurrentIndex(0)