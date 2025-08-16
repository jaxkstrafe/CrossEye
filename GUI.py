import sys
import os
import json
from PyQt5.QtWidgets import (
    QApplication, QWidget, QPushButton, QVBoxLayout, QHBoxLayout,
    QLabel, QSlider, QColorDialog, QComboBox, QCheckBox,
    QGroupBox, QGridLayout, QDialog, QFrame, QTextBrowser, QFileDialog
)
from PyQt5.QtCore import Qt, QSize, QRectF, QPropertyAnimation, pyqtProperty
from PyQt5.QtGui import QColor, QMovie, QIcon, QPainter
from ShapePreviewSelector import ShapePreviewSelector

# -----------------------------
# Helpers
# -----------------------------
SETTINGS_FILE = "settings.json"

def resource_path(relative_path):
    if hasattr(sys, '_MEIPASS'):
        return os.path.join(sys._MEIPASS, relative_path)
    return os.path.join(os.path.abspath("."), relative_path)


# -----------------------------
# Animated Toggle Switch
# -----------------------------
class ToggleSwitch(QCheckBox):
    def __init__(self, accent=QColor("#33B5E5"), parent=None):
        super().__init__(parent)
        self.setCursor(Qt.PointingHandCursor)
        self.setFocusPolicy(Qt.StrongFocus)  # allow Space/Enter toggle
        self._offset = 1.0 if self.isChecked() else 0.0
        self._anim = QPropertyAnimation(self, b"offset", self)
        self._anim.setDuration(140)
        self._anim.valueChanged.connect(self.update)
        self.accent = accent
        self.setFixedSize(46, 26)
        self.toggled.connect(self._start_anim)

    def _start_anim(self, checked):
        self._anim.stop()
        self._anim.setStartValue(self._offset)
        self._anim.setEndValue(1.0 if checked else 0.0)
        self._anim.start()

    def getOffset(self):
        return self._offset

    def setOffset(self, v):
        self._offset = float(v)
        self.update()

    offset = pyqtProperty(float, fget=getOffset, fset=setOffset)

    # --- Make the whole control clickable ---
    def mouseReleaseEvent(self, e):
        if e.button() == Qt.LeftButton and self.rect().contains(e.pos()):
            self.toggle()           # flips checked state, emits toggled()
            e.accept()
            return
        super().mouseReleaseEvent(e)

    # Keyboard accessibility: Space/Enter toggles
    def keyPressEvent(self, e):
        if e.key() in (Qt.Key_Space, Qt.Key_Return, Qt.Key_Enter):
            self.toggle()
            e.accept()
            return
        super().keyPressEvent(e)

    def paintEvent(self, event):
        p = QPainter(self)
        p.setRenderHint(QPainter.Antialiasing)
        r = self.rect().adjusted(1, 1, -1, -1)
        radius = r.height() / 2

        # Track
        track = QColor(self.accent)
        track.setAlpha(180 if self.isChecked() else 70)
        p.setPen(Qt.NoPen)
        p.setBrush(track)
        p.drawRoundedRect(r, radius, radius)

        # Thumb
        margin = 3
        d = r.height() - 2 * margin
        x = r.left() + margin + (r.width() - 2 * margin - d) * self._offset
        p.setBrush(Qt.white)
        p.drawEllipse(QRectF(x, r.top() + margin, d, d))


# -----------------------------
# Advanced Options dialog (⚙️)
# -----------------------------
class AdvancedOptionsDialog(QDialog):
    def __init__(self, current_theme: str, themes: dict, on_theme_change, parent=None):
        super().__init__(parent)
        self.setWindowTitle("Advanced Options")
        self.setMinimumSize(420, 500)
        self.on_theme_change = on_theme_change
        self.themes = themes

        layout = QVBoxLayout(self)
        layout.setContentsMargins(18, 18, 18, 18)
        layout.setSpacing(16)

        # Card wrapper helper
        def make_card(title: str, inner: QWidget):
            card = QFrame()
            card.setObjectName("card")
            v = QVBoxLayout(card); v.setSpacing(10); v.setContentsMargins(16, 16, 16, 16)
            h = QHBoxLayout(); h.setContentsMargins(0, 0, 0, 0)
            t = QLabel(title); t.setObjectName("cardTitle")
            h.addWidget(t); h.addStretch()
            v.addLayout(h); v.addWidget(inner)
            return card

        # Theme picker
        theme_inner = QWidget()
        tl = QVBoxLayout(theme_inner)
        self.theme_combo = QComboBox()
        self.theme_combo.addItems(list(self.themes.keys()))
        self.theme_combo.setCurrentText(current_theme)
        self.theme_combo.currentTextChanged.connect(self.on_theme_change)
        tl.addWidget(self.theme_combo)

        layout.addWidget(make_card("🖌️ GUI Theme", theme_inner))

        # Help content
        help_inner = QWidget()
        hl = QVBoxLayout(help_inner)
        tb = QTextBrowser(self)
        tb.setOpenExternalLinks(True)
        tb.setHtml("""
            <h3>How to Use</h3>
            <ul>
              <li><b>🎨 Colors:</b> Change Crosshair & Center Dot colors.</li>
              <li><b>📏 Size & Thickness:</b> Use sliders for crosshair size and line width.</li>
              <li><b>🎯 Center Dot:</b> Toggle and size the center dot.</li>
              <li><b>🖼️ Custom:</b> “Upload Custom Crosshair” (PNG/JPG). Size slider scales it.</li>
              <li><b>🔲 Shape:</b> “Select Crosshair Shape” for visual options.</li>
              <li><b>⚙️ Advanced:</b> This menu for Theme + Help.</li>
              <li><b>🔄 Reset:</b> Restores defaults.</li>
            </ul>
            <h3>Hotkeys</h3>
            <ul>
              <li><b>Ctrl + Alt + H</b> — Toggle the settings window</li>
              <li><b>Ctrl + Alt + X</b> — Quit the app</li>
            </ul>
            <h3>Notes</h3>
            <ul>
              <li>Overlay is always-on-top and click-through.</li>
              <li>Settings are saved to <code>settings.json</code>.</li>
              <li>Prefer PNG with transparency for custom images.</li>
            </ul>
        """)
        hl.addWidget(tb)

        layout.addWidget(make_card("❓ Help & Shortcuts", help_inner))

        btn_close = QPushButton("Close")
        btn_close.clicked.connect(self.accept)
        layout.addWidget(btn_close, alignment=Qt.AlignRight)


# -----------------------------
# Main GUI (Modern look)
# -----------------------------
class CrosshairGUI(QWidget):
    def __init__(self, overlay):
        super().__init__()
        self.setWindowIcon(QIcon(resource_path("Crosshair.ico")))
        self.setWindowTitle("Crosshair Settings")
        self.setGeometry(100, 100, 420, 640)
        self.setObjectName("root")  # used by stylesheet

        self.overlay = overlay
        self.settings = self.load_settings()

        # ---- Load initial settings ----
        self.current_theme = self.settings.get("theme", "Light Orange")
        initial_size = self.settings.get("size", 5)
        initial_shape = self.settings.get("shape", "Dot")
        initial_color = self.settings.get("color", "#FF0000")
        initial_center_color = self.settings.get("center_dot_color", "#333333")
        initial_thickness = self.settings.get("thickness", 2)
        initial_center_dot_size = self.settings.get("center_dot_size", max(1, initial_size // 3))
        initial_show_dot = self.settings.get("show_center_dot", True)
        initial_custom_image = self.settings.get("custom_image_path", None)
        initial_custom_opacity = float(self.settings.get("custom_opacity", 1.0))

        # ---- Themes (same palette; modern skin) ----
        self.themes = {
            "Light Pink": {"bg": "#FFE6F0", "button": "#FF80B3", "hover": "#FF4D94", "label": "#C71585", "text": "black"},
            "Light Blue": {"bg": "#E0F7FF", "button": "#33B5E5", "hover": "#0099CC", "label": "#007BA7", "text": "black"},
            "Dark Gray": {"bg": "#2E2E2E", "button": "#555555", "hover": "#777777", "label": "#CCCCCC", "text": "white"},
            "Light Orange": {"bg": "#FFE6CC", "button": "#FF7F27", "hover": "#E65C00", "label": "#FF6600", "text": "black"}
        }

        # ---- Header bar ----
        header = QFrame(); header.setObjectName("header")
        hbar = QHBoxLayout(header); hbar.setContentsMargins(12, 12, 12, 12)
        title = QLabel("Crosshair Settings"); title.setObjectName("title")
        hbar.addWidget(title); hbar.addStretch()
        self.btn_advanced = QPushButton("⚙"); self.btn_advanced.setObjectName("iconBtn")
        self.btn_advanced.setToolTip("Advanced Options")
        self.btn_advanced.clicked.connect(self.open_advanced_options)
        hbar.addWidget(self.btn_advanced)

        # ---- Theme GIF (kept) ----
        self.theme_gif = QLabel()
        self.theme_movie = QMovie()
        self.theme_gif.setMovie(self.theme_movie)
        gif_row = QHBoxLayout(); gif_row.addStretch(); gif_row.addWidget(self.theme_gif); gif_row.addStretch()

        # ---- Card helper ----
        def make_card(title_text: str):
            card = QFrame(); card.setObjectName("card")
            v = QVBoxLayout(card); v.setContentsMargins(16, 16, 16, 16); v.setSpacing(12)
            ht = QHBoxLayout(); ht.setContentsMargins(0, 0, 0, 0)
            t = QLabel(title_text); t.setObjectName("cardTitle")
            ht.addWidget(t); ht.addStretch(); v.addLayout(ht)
            return card, v

        # ---- Appearance card ----
        appearance_card, appearance_layout = make_card("🎯 Crosshair Appearance")

        self.btn_color = QPushButton("Change Crosshair Color")
        self.btn_color.clicked.connect(self.open_color_picker)

        self.btn_center_color = QPushButton("Change Center Dot Color")
        self.btn_center_color.clicked.connect(self.open_center_dot_color_picker)

        # Size row with value chip
        size_row = QHBoxLayout()
        size_lbl = QLabel("Size")
        self.size_value = QLabel(str(initial_size)); self.size_value.setObjectName("chip")
        self.slider = QSlider(Qt.Horizontal); self.slider.setRange(2, 50); self.slider.setValue(initial_size)
        self.slider.valueChanged.connect(lambda v: self._on_slider(self.size_value, v, self.update_dot_size))
        size_row.addWidget(size_lbl); size_row.addWidget(self.slider); size_row.addWidget(self.size_value)

        # Thickness row with value chip
        thick_row = QHBoxLayout()
        thick_lbl = QLabel("Thickness")
        self.thickness_value = QLabel(str(initial_thickness)); self.thickness_value.setObjectName("chip")
        self.thickness_slider = QSlider(Qt.Horizontal); self.thickness_slider.setRange(1, 10); self.thickness_slider.setValue(initial_thickness)
        self.thickness_slider.valueChanged.connect(lambda v: self._on_slider(self.thickness_value, v, self.update_thickness))
        thick_row.addWidget(thick_lbl); thick_row.addWidget(self.thickness_slider); thick_row.addWidget(self.thickness_value)

        # Opacity row (0–100%)
        opacity_row = QHBoxLayout()
        opacity_lbl = QLabel("Opacity")
        self.opacity_value = QLabel(str(int(initial_custom_opacity * 100))); self.opacity_value.setObjectName("chip")
        self.opacity_slider = QSlider(Qt.Horizontal); self.opacity_slider.setRange(0, 100)
        self.opacity_slider.setValue(int(initial_custom_opacity * 100))
        self.opacity_slider.valueChanged.connect(lambda v: self._on_slider(self.opacity_value, v, self.update_opacity))
        opacity_row.addWidget(opacity_lbl); opacity_row.addWidget(self.opacity_slider); opacity_row.addWidget(self.opacity_value)

        # Center dot size row
        cd_row = QHBoxLayout()
        cd_lbl = QLabel("Center Dot Size")
        self.center_dot_value = QLabel(f"{initial_center_dot_size:.2f}"); self.center_dot_value.setObjectName("chip")
        self.center_dot_slider = QSlider(Qt.Horizontal); self.center_dot_slider.setRange(1, 40)
        self.center_dot_slider.setValue(int(initial_center_dot_size * 4))
        self.center_dot_slider.valueChanged.connect(lambda v: self._on_slider(self.center_dot_value, v/4.0, self.update_center_dot_size))
        cd_row.addWidget(cd_lbl); cd_row.addWidget(self.center_dot_slider); cd_row.addWidget(self.center_dot_value)

        # Pill toggle for Center Dot (animated)
        toggle_row = QHBoxLayout()
        t_label = QLabel("Show Center Dot")
        self.center_dot_checkbox = ToggleSwitch(accent=QColor(self.themes[self.current_theme]["button"]))
        self.center_dot_checkbox.setChecked(initial_show_dot)
        self.center_dot_checkbox.stateChanged.connect(self.toggle_center_dot)
        toggle_row.addWidget(t_label); toggle_row.addStretch(); toggle_row.addWidget(self.center_dot_checkbox)

        # Add to appearance card
        appearance_layout.addWidget(self.btn_color)
        appearance_layout.addWidget(self.btn_center_color)
        appearance_layout.addLayout(size_row)
        appearance_layout.addLayout(thick_row)
        appearance_layout.addLayout(opacity_row)
        appearance_layout.addLayout(cd_row)
        appearance_layout.addLayout(toggle_row)

        # ---- Shape card ----
        shape_card, shape_layout = make_card("🔲 Crosshair Shape")

        self.shape_combo = QComboBox()
        self.shape_combo.addItems(["Dot","Cross","V Cross","Arrow Up","Shaped Crosshair",
                                   "Vertical Line","Arrow Sides","T-Hair","Circle Dot","Custom"])
        self.shape_combo.setCurrentText(initial_shape)
        self.shape_combo.currentTextChanged.connect(self.update_shape)
        self.shape_combo.hide()

        self.btn_select_shape = QPushButton("Select Crosshair Shape")
        self.btn_select_shape.clicked.connect(self.open_shape_selector)

        self.btn_upload_custom = QPushButton("Upload Custom Crosshair (PNG/JPG)")
        self.btn_upload_custom.clicked.connect(self.upload_custom_crosshair)

        self.btn_clear_custom = QPushButton("Clear Custom Crosshair")
        self.btn_clear_custom.clicked.connect(self.clear_custom_crosshair)

        shape_layout.addWidget(self.btn_select_shape)
        shape_layout.addWidget(self.btn_upload_custom)
        shape_layout.addWidget(self.btn_clear_custom)

        # ---- Reset card ----
        reset_card, reset_layout = make_card("Reset")
        self.btn_reset = QPushButton("Reset to Defaults")
        self.btn_reset.clicked.connect(self.reset_defaults)
        reset_layout.addWidget(self.btn_reset)

        # ---- Main layout ----
        root = QVBoxLayout(self)
        root.setContentsMargins(14, 14, 14, 14)
        root.setSpacing(12)
        root.addWidget(header)
        root.addLayout(gif_row)
        root.addWidget(appearance_card)
        root.addWidget(shape_card)
        root.addWidget(reset_card)

        # ---- Apply theme + initial values into overlay ----
        self.apply_theme_styles()   # base modern stylesheet
        self.update_theme(self.current_theme)

        self.overlay.set_show_center_dot(initial_show_dot)
        self.overlay.set_center_dot_size(initial_center_dot_size)
        self.overlay.set_dot_size(initial_size)
        self.overlay.set_shape(initial_shape)
        self.overlay.set_dot_color(QColor(initial_color))
        self.overlay.set_center_dot_color(QColor(initial_center_color))
        self.overlay.set_thickness(initial_thickness)
        # These require your overlay to implement set_custom_opacity/set_custom_image
        if hasattr(self.overlay, "set_custom_opacity"):
            self.overlay.set_custom_opacity(initial_custom_opacity)
        if initial_custom_image and hasattr(self.overlay, "set_custom_image"):
            self.overlay.set_custom_image(initial_custom_image)

    # -------- Modern style (QSS) --------
    def apply_theme_styles(self):
        # Base stylesheet used for all themes. We always rebuild from this.
        self._base_qss = """
            QWidget { font-family: 'Segoe UI', 'Inter', system-ui; font-size: 13px; }
            #header { background: transparent; }
            #title { font-size: 16px; font-weight: 700; }
            #iconBtn {
                min-width: 32px; max-width: 32px; min-height: 32px; max-height: 32px;
                border-radius: 8px; background: rgba(0,0,0,0.06);
            }
            #iconBtn:hover { background: rgba(0,0,0,0.12); }
            #card {
                background: rgba(0,0,0,0.08);
                border: 1px solid rgba(0,0,0,0.12);
                border-radius: 14px;
            }
            #cardTitle { font-weight: 700; opacity: 0.9; }
            QPushButton {
                border: none; border-radius: 10px; padding: 10px 12px; font-weight: 600;
            }
            QPushButton:disabled { opacity: 0.5; }
            QSlider::groove:horizontal {
                height: 8px; border-radius: 4px; background: rgba(0,0,0,0.12);
            }
            QSlider::handle:horizontal {
                width: 18px; height: 18px; margin: -6px 0;
                border-radius: 9px; background: white;
            }
            QLabel#chip {
                padding: 2px 8px; border-radius: 999px; font-weight: 700;
                background: rgba(0,0,0,0.12);
            }
        """
        # Clear any per-widget styles so only the global sheet controls colors
        for b in getattr(self, "__dict__", {}).values():
            if hasattr(b, "setStyleSheet") and b is not self:
                try:
                    b.setStyleSheet("")
                except Exception:
                    pass

        # Apply an initial base stylesheet globally (theme layer is added in update_theme)
        app = QApplication.instance()
        if app:
            app.setStyleSheet(self._base_qss)
        else:
            self.setStyleSheet(self._base_qss)


    # ---------- Slots / handlers ----------
    def open_advanced_options(self):
        dlg = AdvancedOptionsDialog(
            current_theme=self.current_theme,
            themes=self.themes,
            on_theme_change=self.update_theme,
            parent=self
        )
        dlg.exec_()

    def _on_slider(self, chip_label: QLabel, val, apply_fn):
        chip_label.setText(f"{val:.2f}" if isinstance(val, float) else str(int(val)))
        apply_fn(val)

    def open_color_picker(self):
        color = QColorDialog.getColor()
        if color.isValid():
            self.overlay.set_dot_color(color)
            self.settings["color"] = color.name()
            self.save_settings()

    def open_center_dot_color_picker(self):
        color = QColorDialog.getColor()
        if color.isValid():
            self.overlay.set_center_dot_color(color)
            self.settings["center_dot_color"] = color.name()
            self.save_settings()

    def update_dot_size(self, value):
        self.overlay.set_dot_size(int(value))
        self.settings["size"] = int(value)
        self.save_settings()

    def update_thickness(self, value):
        self.overlay.set_thickness(int(value))
        self.settings["thickness"] = int(value)
        self.save_settings()

    def open_shape_selector(self):
        dialog = ShapePreviewSelector()
        if dialog.exec_() == QDialog.Accepted and dialog.selected_shape:
            self.overlay.set_shape(dialog.selected_shape)
            self.shape_combo.setCurrentText(dialog.selected_shape)
            self.settings["shape"] = dialog.selected_shape
            self.save_settings()

    def update_shape(self, shape):
        self.overlay.set_shape(shape)
        self.settings["shape"] = shape
        self.save_settings()

    def update_opacity(self, value):
        # value is 0–100 from the slider -> convert to 0.0–1.0
        opacity = max(0, min(100, int(value))) / 100.0
        if hasattr(self.overlay, "set_custom_opacity"):
            self.overlay.set_custom_opacity(opacity)
        else:
            try:
                self.overlay.setWindowOpacity(opacity)
            except Exception:
                pass
        self.settings["custom_opacity"] = opacity
        self.save_settings()

    def update_center_dot_size(self, value):
        scaled_value = float(value)
        self.overlay.set_center_dot_size(scaled_value)
        self.settings["center_dot_size"] = scaled_value
        self.save_settings()

    def toggle_center_dot(self, state):
        show = state == Qt.Checked
        self.overlay.set_show_center_dot(show)
        self.settings["show_center_dot"] = show
        self.save_settings()

    def upload_custom_crosshair(self):
        path, _ = QFileDialog.getOpenFileName(self, "Select Crosshair Image", "", "Images (*.png *.jpg *.jpeg)")
        if path:
            if hasattr(self.overlay, "set_custom_image"):
                self.overlay.set_custom_image(path)
            self.overlay.set_shape("Custom")
            self.shape_combo.setCurrentText("Custom")
            self.settings["shape"] = "Custom"
            self.settings["custom_image_path"] = path
            self.save_settings()

    def clear_custom_crosshair(self):
        if hasattr(self.overlay, "set_custom_image"):
            self.overlay.set_custom_image(None)
        self.overlay.set_shape("Dot")
        self.shape_combo.setCurrentText("Dot")
        self.settings["shape"] = "Dot"
        self.settings.pop("custom_image_path", None)
        self.save_settings()

    def update_theme(self, theme_name):
        self.current_theme = theme_name
        self.settings["theme"] = theme_name
        self.save_settings()

        theme = self.themes[theme_name]
        bg, btn, hover, label = theme["bg"], theme["button"], theme["hover"], theme["label"]
        text_color = "black" if theme_name in ["Light Pink", "Light Blue", "Light Orange"] else "white"

        # Page background
        self.setStyleSheet(self.styleSheet() + f"""
            QWidget#root {{ background: {bg}; }}
        """)

        # Buttons (big)
        button_style = f"""
            QPushButton {{
                background-color: {btn};
                color: white;
                border: none; border-radius: 10px; padding: 10px 12px; font-weight: 600;
            }}
            QPushButton:hover {{ background-color: {hover}; }}
        """
        for b in (self.btn_color, self.btn_center_color, self.btn_reset,
                  self.btn_select_shape, self.btn_upload_custom, self.btn_clear_custom):
            b.setStyleSheet(button_style)

        # Card titles / labels
        for w in self.findChildren(QLabel, "cardTitle"):
            w.setStyleSheet(f"color: {label};")
        for w in self.findChildren(QLabel):
            if w.objectName() not in ("cardTitle", "chip", "title"):
                w.setStyleSheet(f"color: {text_color};")
        for w in self.findChildren(QLabel, "chip"):
            w.setStyleSheet(w.styleSheet() + f"; color: {text_color};")

        # Toggle accent follows theme button color
        if hasattr(self, "center_dot_checkbox") and isinstance(self.center_dot_checkbox, ToggleSwitch):
            self.center_dot_checkbox.accent = QColor(btn)
            self.center_dot_checkbox.update()

        # Theme GIFs (kept)
        if theme_name == "Dark Gray":
            gif_path = resource_path("berserk.gif"); gif_size = QSize(200, 128)
        elif theme_name == "Light Orange":
            gif_path = resource_path("cat.gif"); gif_size = QSize(128, 128)
        else:
            gif_path = resource_path("cat.gif"); gif_size = QSize(128, 128)

        if gif_path:
            self.theme_gif.setVisible(True)
            self.theme_movie.stop()
            self.theme_movie.setFileName(gif_path)
            self.theme_movie.setScaledSize(gif_size)
            self.theme_movie.start()
        else:
            self.theme_gif.setVisible(False)
            self.theme_movie.stop()

    def reset_defaults(self):
        defaults = {
            "theme": "Light Orange",
            "size": 5,
            "shape": "Dot",
            "color": "#FF0000",
            "thickness": 2,
            "center_dot_color": "#333333",
            "center_dot_size": 2,
            "show_center_dot": True,
            "custom_opacity": 1.0,
        }

        # Update settings first
        self.settings.update(defaults)
        self.save_settings()

        # Overlay
        self.overlay.set_dot_color(QColor(defaults["color"]))
        self.overlay.set_center_dot_color(QColor(defaults["center_dot_color"]))
        self.overlay.set_show_center_dot(defaults["show_center_dot"])
        self.overlay.set_center_dot_size(defaults["center_dot_size"])
        self.overlay.set_dot_size(defaults["size"])
        self.overlay.set_thickness(defaults["thickness"])
        if hasattr(self.overlay, "set_custom_opacity"):
            self.overlay.set_custom_opacity(defaults["custom_opacity"])
        else:
            try:
                self.overlay.setWindowOpacity(defaults["custom_opacity"])
            except Exception:
                pass

        # UI controls (use your actual widget names)
        self.slider.setValue(defaults["size"])
        self.size_value.setText(str(defaults["size"]))

        self.thickness_slider.setValue(defaults["thickness"])
        self.thickness_value.setText(str(defaults["thickness"]))

        self.center_dot_slider.setValue(int(defaults["center_dot_size"] * 4))
        self.center_dot_value.setText(f"{defaults['center_dot_size']:.2f}")

        self.opacity_slider.setValue(int(defaults["custom_opacity"] * 100))
        self.opacity_value.setText(str(int(defaults["custom_opacity"] * 100)))

        self.center_dot_checkbox.setChecked(defaults["show_center_dot"])

        self.shape_combo.setCurrentText(defaults["shape"])

        # Theme (last so colors refresh)
        self.update_theme(defaults["theme"])



    # settings I/O
    def load_settings(self):
        if os.path.exists(SETTINGS_FILE):
            try:
                with open(SETTINGS_FILE, 'r') as f:
                    return json.load(f)
            except Exception as e:
                print(f"[Settings Load Error] {e}")
        return {}

    def save_settings(self):
        try:
            with open(SETTINGS_FILE, 'w') as f:
                json.dump(self.settings, f)
        except Exception as e:
            print(f"[Settings Save Error] {e}")
