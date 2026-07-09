# Native settings dialog: pickers for note types and fields instead of raw
# JSON. The JSON config remains the power-user path ("Edit raw JSON…").

from __future__ import annotations

import json
from typing import Any, Dict, List, Optional

from aqt import mw
from aqt.qt import (
    QCheckBox,
    QComboBox,
    QDialog,
    QDialogButtonBox,
    QFormLayout,
    QFrame,
    QGroupBox,
    QHBoxLayout,
    QLabel,
    QLineEdit,
    QListWidget,
    QListWidgetItem,
    QMessageBox,
    QPlainTextEdit,
    QPushButton,
    QScrollArea,
    QSplitter,
    Qt,
    QVBoxLayout,
    QWidget,
)

ADDON = __name__.split(".")[0]

PROVIDER_ITEMS = [
    ("Claude (Anthropic)", "anthropic"),
    ("OpenAI-compatible (OpenAI / OpenRouter / Groq / Ollama / LM Studio)", "openai_compatible"),
]
OVERRIDE_PROVIDER_ITEMS = [("(use global setting)", "")] + PROVIDER_ITEMS

MODEL_PLACEHOLDER = {
    "anthropic": "claude-opus-4-8",
    "openai_compatible": "e.g. gpt-5, llama3.1, mistral",
}


def _cfg() -> Dict[str, Any]:
    return mw.addonManager.getConfig(ADDON) or {}


def open_dialog() -> None:
    SettingsDialog(mw).exec()


class SettingsDialog(QDialog):
    def __init__(self, parent) -> None:
        super().__init__(parent)
        self.setWindowTitle("LLM Answer Grader Settings")
        self.setMinimumSize(880, 640)
        self.config = _cfg()
        self.profiles: List[Dict[str, Any]] = [
            dict(p) for p in self.config.get("profiles") or []
        ]
        self._current_row: Optional[int] = None
        self._loading = False
        self._build_ui()
        self._load_connection()
        self._reload_profile_list(select=0 if self.profiles else None)

    # -- UI scaffolding ------------------------------------------------------

    def _build_ui(self) -> None:
        outer = QVBoxLayout(self)

        conn = QGroupBox("Connection")
        form = QFormLayout(conn)
        self.provider_box = QComboBox()
        for label, _ in PROVIDER_ITEMS:
            self.provider_box.addItem(label)
        self.provider_box.currentIndexChanged.connect(self._provider_changed)
        form.addRow("Provider:", self.provider_box)
        self.key_edit = QLineEdit()
        self.key_edit.setEchoMode(QLineEdit.EchoMode.Password)
        self.key_edit.setPlaceholderText(
            "API key (leave empty for local servers or env vars)"
        )
        form.addRow("API key:", self.key_edit)
        self.model_edit = QLineEdit()
        form.addRow("Model:", self.model_edit)
        self.base_url_edit = QLineEdit()
        self.base_url_edit.setPlaceholderText(
            "https://api.openai.com/v1 · Ollama: http://localhost:11434/v1"
        )
        self.base_url_label = QLabel("Base URL:")
        form.addRow(self.base_url_label, self.base_url_edit)
        outer.addWidget(conn)

        prof_group = QGroupBox("Grading profiles — which cards get the grader")
        prof_layout = QHBoxLayout(prof_group)
        splitter = QSplitter(Qt.Orientation.Horizontal)

        left = QWidget()
        left_l = QVBoxLayout(left)
        left_l.setContentsMargins(0, 0, 0, 0)
        self.profile_list = QListWidget()
        self.profile_list.currentRowChanged.connect(self._profile_selected)
        left_l.addWidget(self.profile_list)
        btn_row = QHBoxLayout()
        add_btn = QPushButton("Add")
        add_btn.clicked.connect(self._add_profile)
        rm_btn = QPushButton("Remove")
        rm_btn.clicked.connect(self._remove_profile)
        btn_row.addWidget(add_btn)
        btn_row.addWidget(rm_btn)
        left_l.addLayout(btn_row)
        splitter.addWidget(left)

        right = QWidget()
        right_l = QVBoxLayout(right)
        right_l.setContentsMargins(8, 0, 8, 0)
        right_l.setSpacing(8)

        name_row = QFormLayout()
        self.name_edit = QLineEdit()
        name_row.addRow("Profile name:", self.name_edit)
        right_l.addLayout(name_row)

        right_l.addWidget(QLabel("Show the grader on these note types:"))
        self.notetype_list = QListWidget()
        self.notetype_list.setMinimumHeight(110)
        self.notetype_list.setMaximumHeight(150)
        self.notetype_list.itemChanged.connect(self._notetypes_changed)
        right_l.addWidget(self.notetype_list)
        pre_row = QFormLayout()
        self.prefix_edit = QLineEdit()
        self.prefix_edit.setPlaceholderText(
            'Optional name prefixes, comma-separated ("*" = every note type)'
        )
        self.prefix_edit.editingFinished.connect(self._notetypes_changed)
        pre_row.addRow("Also match prefixes:", self.prefix_edit)
        right_l.addLayout(pre_row)

        right_l.addWidget(QLabel(
            "Card fields to send as context (none checked = all fields):"
        ))
        self.field_list = QListWidget()
        self.field_list.setMinimumHeight(90)
        self.field_list.setMaximumHeight(120)
        right_l.addWidget(self.field_list)

        right_l.addWidget(QLabel(
            "Grading instructions — describe the task in plain English "
            "(what the card shows, what the learner should produce, what matters):"
        ))
        self.instructions_edit = QPlainTextEdit()
        self.instructions_edit.setPlaceholderText(
            "Example: The card shows an English sentence (field 'Front') that "
            "the learner translates into Spanish. Grade meaning first, then "
            "grammar and naturalness at the level in the 'Level' field."
        )
        self.instructions_edit.setMinimumHeight(90)
        self.instructions_edit.setMaximumHeight(140)
        right_l.addWidget(self.instructions_edit)

        self.override_group = QGroupBox(
            "Override model for this profile (e.g. a cheaper/local model)"
        )
        self.override_group.setCheckable(True)
        self.override_group.setChecked(False)
        ov_form = QFormLayout(self.override_group)
        self.ov_provider_box = QComboBox()
        for label, _ in OVERRIDE_PROVIDER_ITEMS:
            self.ov_provider_box.addItem(label)
        ov_form.addRow("Provider:", self.ov_provider_box)
        self.ov_model_edit = QLineEdit()
        ov_form.addRow("Model:", self.ov_model_edit)
        self.ov_base_url_edit = QLineEdit()
        ov_form.addRow("Base URL:", self.ov_base_url_edit)
        right_l.addWidget(self.override_group)
        right_l.addStretch(1)

        # Scroll area so the editor never squeezes widgets into each other
        # when the stacked content is taller than the window.
        scroll = QScrollArea()
        scroll.setWidgetResizable(True)
        scroll.setFrameShape(QFrame.Shape.NoFrame)
        scroll.setWidget(right)
        splitter.addWidget(scroll)
        splitter.setStretchFactor(0, 1)
        splitter.setStretchFactor(1, 3)
        prof_layout.addWidget(splitter)
        outer.addWidget(prof_group, stretch=1)

        buttons = QDialogButtonBox(
            QDialogButtonBox.StandardButton.Save
            | QDialogButtonBox.StandardButton.Cancel
        )
        raw_btn = QPushButton("Edit raw JSON…")
        raw_btn.clicked.connect(self._edit_raw)
        buttons.addButton(raw_btn, QDialogButtonBox.ButtonRole.ActionRole)
        buttons.accepted.connect(self._save)
        buttons.rejected.connect(self.reject)
        outer.addWidget(buttons)

    # -- Connection section --------------------------------------------------

    def _load_connection(self) -> None:
        provider = (self.config.get("provider") or "anthropic").lower()
        idx = next(
            (i for i, (_, v) in enumerate(PROVIDER_ITEMS) if v == provider), 0
        )
        self.provider_box.setCurrentIndex(idx)
        self.key_edit.setText(self.config.get("api_key") or "")
        self.model_edit.setText(self.config.get("model") or "")
        self.base_url_edit.setText(self.config.get("openai_base_url") or "")
        self._provider_changed()

    def _provider_changed(self) -> None:
        provider = PROVIDER_ITEMS[self.provider_box.currentIndex()][1]
        is_openai = provider == "openai_compatible"
        self.base_url_edit.setVisible(is_openai)
        self.base_url_label.setVisible(is_openai)
        self.model_edit.setPlaceholderText(MODEL_PLACEHOLDER[provider])

    # -- Profile list --------------------------------------------------------

    def _reload_profile_list(self, select: Optional[int]) -> None:
        self._loading = True
        self.profile_list.clear()
        for p in self.profiles:
            self.profile_list.addItem(p.get("name") or "(unnamed)")
        self._loading = False
        self._current_row = None
        if select is not None and 0 <= select < len(self.profiles):
            self.profile_list.setCurrentRow(select)

    def _profile_selected(self, row: int) -> None:
        if self._loading:
            return
        self._store_editor()
        self._current_row = row if 0 <= row < len(self.profiles) else None
        self._load_editor()

    def _add_profile(self) -> None:
        self._store_editor()
        self.profiles.append({
            "name": f"Profile {len(self.profiles) + 1}",
            "note_type_prefixes": [],
            "card_fields": [],
            "grading_instructions": "",
        })
        self._reload_profile_list(select=len(self.profiles) - 1)

    def _remove_profile(self) -> None:
        row = self.profile_list.currentRow()
        if not (0 <= row < len(self.profiles)):
            return
        self._current_row = None  # don't store the editor into a removed row
        del self.profiles[row]
        self._reload_profile_list(select=min(row, len(self.profiles) - 1))

    # -- Profile editor ------------------------------------------------------

    def _note_type_names(self) -> List[str]:
        try:
            return [nt.name for nt in mw.col.models.all_names_and_ids()]
        except Exception:
            return []

    def _load_editor(self) -> None:
        self._loading = True
        p = (
            self.profiles[self._current_row]
            if self._current_row is not None
            else {}
        )
        enabled = self._current_row is not None
        for w in (self.name_edit, self.notetype_list, self.prefix_edit,
                  self.field_list, self.instructions_edit, self.override_group):
            w.setEnabled(enabled)

        self.name_edit.setText(p.get("name") or "")
        prefixes = list(p.get("note_type_prefixes") or [])
        names = self._note_type_names()
        self.notetype_list.clear()
        for name in names:
            item = QListWidgetItem(name)
            item.setFlags(item.flags() | Qt.ItemFlag.ItemIsUserCheckable)
            item.setCheckState(
                Qt.CheckState.Checked if name in prefixes
                else Qt.CheckState.Unchecked
            )
            self.notetype_list.addItem(item)
        custom = [x for x in prefixes if x not in names]
        self.prefix_edit.setText(", ".join(custom))

        self.instructions_edit.setPlainText(p.get("grading_instructions") or "")

        has_override = any(
            p.get(k) for k in ("provider", "model", "openai_base_url")
        )
        self.override_group.setChecked(bool(has_override))
        ov_provider = (p.get("provider") or "").lower()
        ov_idx = next(
            (i for i, (_, v) in enumerate(OVERRIDE_PROVIDER_ITEMS) if v == ov_provider),
            0,
        )
        self.ov_provider_box.setCurrentIndex(ov_idx)
        self.ov_model_edit.setText(p.get("model") or "")
        self.ov_base_url_edit.setText(p.get("openai_base_url") or "")

        self._loading = False
        self._refresh_fields(p.get("card_fields") or [])

    def _selected_prefixes(self) -> List[str]:
        prefixes: List[str] = []
        for i in range(self.notetype_list.count()):
            item = self.notetype_list.item(i)
            if item.checkState() == Qt.CheckState.Checked:
                prefixes.append(item.text())
        for part in self.prefix_edit.text().split(","):
            part = part.strip()
            if part and part not in prefixes:
                prefixes.append(part)
        return prefixes

    def _matched_note_types(self) -> List[str]:
        prefixes = self._selected_prefixes()
        return [
            name for name in self._note_type_names()
            if any(pre == "*" or name.startswith(pre) for pre in prefixes)
        ]

    def _notetypes_changed(self, *_args) -> None:
        if self._loading:
            return
        checked = [
            self.field_list.item(i).text()
            for i in range(self.field_list.count())
            if self.field_list.item(i).checkState() == Qt.CheckState.Checked
        ]
        self._refresh_fields(checked)

    def _refresh_fields(self, checked: List[str]) -> None:
        names: List[str] = []
        try:
            for nt_name in self._matched_note_types():
                nt = mw.col.models.by_name(nt_name)
                if nt:
                    for f in mw.col.models.field_names(nt):
                        if f not in names:
                            names.append(f)
        except Exception:
            pass
        self.field_list.clear()
        for name in names:
            item = QListWidgetItem(name)
            item.setFlags(item.flags() | Qt.ItemFlag.ItemIsUserCheckable)
            item.setCheckState(
                Qt.CheckState.Checked if name in checked
                else Qt.CheckState.Unchecked
            )
            self.field_list.addItem(item)

    def _store_editor(self) -> None:
        if self._current_row is None or self._current_row >= len(self.profiles):
            return
        p = self.profiles[self._current_row]
        p["name"] = self.name_edit.text().strip() or "(unnamed)"
        p["note_type_prefixes"] = self._selected_prefixes()
        p["card_fields"] = [
            self.field_list.item(i).text()
            for i in range(self.field_list.count())
            if self.field_list.item(i).checkState() == Qt.CheckState.Checked
        ]
        p["grading_instructions"] = self.instructions_edit.toPlainText().strip()
        for key in ("provider", "model", "openai_base_url"):
            p.pop(key, None)
        if self.override_group.isChecked():
            ov_provider = OVERRIDE_PROVIDER_ITEMS[self.ov_provider_box.currentIndex()][1]
            if ov_provider:
                p["provider"] = ov_provider
            if self.ov_model_edit.text().strip():
                p["model"] = self.ov_model_edit.text().strip()
            if self.ov_base_url_edit.text().strip():
                p["openai_base_url"] = self.ov_base_url_edit.text().strip()

    # -- Persistence ---------------------------------------------------------

    def _save(self) -> None:
        self._store_editor()
        cfg = _cfg()  # keep keys the dialog doesn't manage (prompts, labels…)
        cfg["provider"] = PROVIDER_ITEMS[self.provider_box.currentIndex()][1]
        cfg["api_key"] = self.key_edit.text().strip()
        cfg["model"] = self.model_edit.text().strip() or cfg.get("model") or ""
        if self.base_url_edit.text().strip():
            cfg["openai_base_url"] = self.base_url_edit.text().strip()
        cfg["profiles"] = self.profiles
        mw.addonManager.writeConfig(ADDON, cfg)
        self.accept()

    def _edit_raw(self) -> None:
        dlg = QDialog(self)
        dlg.setWindowTitle("LLM Answer Grader — raw config (JSON)")
        dlg.setMinimumSize(640, 480)
        lay = QVBoxLayout(dlg)
        editor = QPlainTextEdit()
        editor.setPlainText(json.dumps(_cfg(), ensure_ascii=False, indent=2))
        lay.addWidget(editor)
        bb = QDialogButtonBox(
            QDialogButtonBox.StandardButton.Save
            | QDialogButtonBox.StandardButton.Cancel
        )
        lay.addWidget(bb)

        def save_raw() -> None:
            try:
                new_cfg = json.loads(editor.toPlainText())
                assert isinstance(new_cfg, dict)
            except (ValueError, AssertionError):
                QMessageBox.warning(dlg, "Invalid JSON",
                                    "That isn't a valid JSON object.")
                return
            mw.addonManager.writeConfig(ADDON, new_cfg)
            dlg.accept()
            self.reject()  # close main dialog so it reloads fresh next open

        bb.accepted.connect(save_raw)
        bb.rejected.connect(dlg.reject)
        dlg.exec()
