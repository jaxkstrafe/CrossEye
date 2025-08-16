import sys
import os
import json
from PyQt5.QtWidgets import (
    QWidget, QPushButton, QSlider, QLabel, QComboBox, QColorDialog, QFileDialog,
    QVBoxLayout, QHBoxLayout, QGroupBox, QDialog, QCheckBox, QTextBrowser, QShortcut
)
from PyQt5.QtCore import Qt, QSize, QPoint
from PyQt5.QtGui import QColor, QMovie, QIcon, QPainter, QPen, QKeySequence
from ShapePreviewSelector import ShapePreviewSelector

# Helper function for PyInstaller compatibility
def resource_path(relative_path):
    if hasattr(sys, '_MEIPASS'):
        return os.path.join(sys._MEIPASS, relative_path)
    return os.path.join(os.path.abspath("."), relative_path)

SETTINGS_FILE = "settings.json"

# -----------------------------
# Help dialog
# -----------------------------
class HelpDialog(QDialog):
    def __init__(self, parent=None):
        super().__init__(parent)
        self.setWindowTitle("Crosshair — Help & Shortcuts")
        self.setMinimumSize(460, 540)
        layout = QVBoxLayout(self)

        tb = QTextBrowser(self)
        tb.setOpenExternalLinks(True)
        tb.setHtml("""
            <h2>How to Use</h2>
            <ul>
              <li><b>🎨 Colors:</b> Use “Change Crosshair Color” and “Change Center Dot Color”.</li>
              <li><b>📏 Size & Thickness:</b> Adjust the sliders for crosshair size and line thickness.</li>
              <li><b>🎯 Center Dot:</b> Use “Center Dot Size” slider and toggle “Show Center Dot”.</li>
              <li><b>🖼️ Custom:</b> Click “Upload Custom Crosshair” to pick a PNG/JPG. The <i>Size</i> slider scales it.</li>
              <li><b>🔲 Shape:</b> Click “Select Crosshair Shape” to pick from visual previews.</li>
              <li><b>🖌️ Theme:</b> Pick a GUI theme from the dropdown.</li>
              <li><b>🔄 Reset:</b> “Reset to Defaults” restores factory settings.</li>
            </ul>
            <h2>Hotkeys</h2>
            <ul>
              <li><b>Ctrl + Alt + H</b> — Toggle the settings window</li>
              <li><b>Ctrl + Alt + X</b> — Quit the app</li>
              <li><b>F1</b> — Open this Help</li>
            </ul>
            <h2>Notes</h2>
            <ul>
              <li>The overlay is <b>always on top</b> and click-through (it won’t block game input).</li>
              <li>Settings are saved to <code>settings.json</code> next to the app.</li>
              <li>Custom crosshair supports PNG/JPG (PNG with transparency recommended).</li>
            </ul>
        """)
        layout.addWidget(tb)

        ok = QPushButton("Close", self)
        ok.clicked.connect(self.accept)
        layout.addWidget(ok, alignment=Qt.AlignRight)

# -----------------------------
# Main GUI
# -----------------------------
class CrosshairGUI(QWidget):
    def __init__(self, overlay):
        super().__init__()
        self.setWindowIcon(QIcon(resource_path("Crosshair.ico")))
        self.setWindowTitle("Crosshair Settings")
        self.setGeometry(100, 100, 360, 600)

        self.overlay = overlay
        self.settings = self.load_settings()

        # Theme GIF
        from PyQt5.QtWidgets import QLabel
        self.theme_gif = QLabel()
        self.theme_movie = QMovie()
        self.theme_gif.setMovie(self.theme_movie)

        # ---- Help button ----
        self.btn_help = QPushButton("?")
        self.btn_help.setCursor(Qt.PointingHandCursor)
        self.btn_help.setFixedSize(32, 32)
        self.btn_help.setStyleSheet("""
            QPushButton {
                font-weight: bold;
                font-size: 18px;
                border-radius: 4px;
                padding: 0;
            }
        """)
        self.btn_help.clicked.connect(self.open_help)

        self.help_shortcut = QShortcut(QKeySequence("F1"), self)
        self.help_shortcut.activated.connect(self.open_help)

        help_layout = QHBoxLayout()
        help_layout.setContentsMargins(0, 0, 0, 0)
        help_layout.addWidget(self.btn_help, alignment=Qt.AlignLeft)

        gif_layout = QHBoxLayout()
        gif_layout.addStretch()
        gif_layout.addWidget(self.theme_gif, alignment=Qt.AlignCenter)
        gif_layout.addStretch()

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

        # Push into overlay
        self.overlay.set_show_center_dot(initial_show_dot)
        self.overlay.set_center_dot_size(initial_center_dot_size)
        self.overlay.set_dot_size(initial_size)
        self.overlay.set_shape(initial_shape)
        self.overlay.set_dot_color(QColor(initial_color))
        self.overlay.set_center_dot_color(QColor(initial_center_color))
        self.overlay.set_thickness(initial_thickness)
        self.overlay.set_custom_opacity(initial_custom_opacity)
        if initial_custom_image:
            self.overlay.set_custom_image(initial_custom_image)

        # ---- Themes ----
        self.themes = {
            "Light Pink": {
                "bg": "#FFE6F0", "button": "#FF80B3", "hover": "#FF4D94",
                "label": "#C71585", "text": "black"
            },
            "Light Blue": {
                "bg": "#E0F7FF", "button": "#33B5E5", "hover": "#0099CC",
                "label": "#007BA7", "text": "black"
            },
            "Dark Gray": {
                "bg": "#2E2E2E", "button": "#555555", "hover": "#777777",
                "label": "#CCCCCC", "text": "white"
            },
            "Light Orange": {
                "bg": "#FFE6CC", "button": "#FF7F27", "hover": "#E65C00",
                "label": "#FF6600", "text": "black"
            }
        }

        # ---- Appearance group ----
        appearance_group = QGroupBox("🎯 Crosshair Appearance")

        self.btn_color = QPushButton("🎨 Change Crosshair Color")
        self.btn_color.clicked.connect(self.open_color_picker)

        self.btn_center_color = QPushButton("🎯 Change Center Dot Color")
        self.btn_center_color.clicked.connect(self.open_center_dot_color_picker)

        self.size_label = QLabel(f"Size: {initial_size}")
        self.slider = QSlider(Qt.Horizontal)
        self.slider.setRange(2, 50)
        self.slider.setValue(initial_size)
        self.slider.valueChanged.connect(self.update_dot_size)

        self.thickness_label = QLabel(f"Thickness: {initial_thickness}")
        self.thickness_slider = QSlider(Qt.Horizontal)
        self.thickness_slider.setRange(1, 10)
        self.thickness_slider.setValue(initial_thickness)
        self.thickness_slider.valueChanged.connect(self.update_thickness)

        # Center dot controls
        self.center_dot_label = QLabel(f"Center Dot Size: {initial_center_dot_size:.2f}")
        self.center_dot_slider = QSlider(Qt.Horizontal)
        self.center_dot_slider.setRange(1, 40)  # UI scale; value/4.0 sent to overlay
        self.center_dot_slider.setValue(int(initial_center_dot_size * 4))
        self.center_dot_slider.valueChanged.connect(self.update_center_dot_size)

        self.center_dot_checkbox = QCheckBox("Show Center Dot")
        self.center_dot_checkbox.setChecked(initial_show_dot)
        self.center_dot_checkbox.stateChanged.connect(self.toggle_center_dot)

        # --- Custom image controls ---
        self.btn_upload_custom = QPushButton("🖼️ Upload Custom Crosshair (PNG/JPG)")
        self.btn_upload_custom.clicked.connect(self.upload_custom_crosshair)

        self.btn_clear_custom = QPushButton("🧹 Clear Custom Crosshair")
        self.btn_clear_custom.clicked.connect(self.clear_custom_crosshair)

        appearance_layout = QVBoxLayout()
        appearance_layout.addWidget(self.btn_color)
        appearance_layout.addWidget(self.btn_center_color)
        appearance_layout.addWidget(self.size_label)
        appearance_layout.addWidget(self.slider)
        appearance_layout.addWidget(self.thickness_label)
        appearance_layout.addWidget(self.thickness_slider)
        appearance_layout.addWidget(self.center_dot_label)
        appearance_layout.addWidget(self.center_dot_slider)
        appearance_layout.addWidget(self.center_dot_checkbox)
        appearance_layout.addWidget(self.btn_upload_custom)
        appearance_layout.addWidget(self.btn_clear_custom)
        appearance_group.setLayout(appearance_layout)

        # ---- Shape group ----
        shape_group = QGroupBox("🔲 Crosshair Shape")
        shape_layout = QVBoxLayout()

        # Hidden combo to keep settings sync if needed elsewhere
        self.shape_combo = QComboBox()
        self.shape_combo.addItems([
            "Dot", "Cross", "V Cross", "Arrow Up", "Shaped Crosshair", "Vertical Line",
            "Arrow Sides", "T-Hair", "Circle Dot", "Custom"
        ])
        self.shape_combo.setCurrentText(initial_shape)
        self.shape_combo.currentTextChanged.connect(self.update_shape)
        self.shape_combo.hide()

        self.btn_select_shape = QPushButton("🖼️ Select Crosshair Shape")
        self.btn_select_shape.clicked.connect(self.open_shape_selector)

        shape_layout.addWidget(self.btn_select_shape)
        shape_group.setLayout(shape_layout)

        # ---- Theme group ----
        theme_group = QGroupBox("🖌️ GUI Theme")
        self.theme_combo = QComboBox()
        self.theme_combo.addItems(list(self.themes.keys()))
        self.theme_combo.setCurrentText(self.current_theme)
        self.theme_combo.currentTextChanged.connect(self.update_theme)
        self.theme_combo.setMinimumHeight(40)

        theme_layout = QVBoxLayout()
        theme_layout.addWidget(self.theme_combo)
        theme_group.setLayout(theme_layout)

        # ---- Reset button ----
        self.btn_reset = QPushButton("🔄 Reset to Defaults")
        self.btn_reset.clicked.connect(self.reset_defaults)

        # ---- Main layout ----
        layout = QVBoxLayout()
        layout.setSpacing(14)
        layout.setContentsMargins(15, 15, 15, 15)
        layout.addLayout(help_layout)
        layout.addLayout(gif_layout)
        layout.addWidget(appearance_group)
        layout.addWidget(shape_group)
        layout.addWidget(theme_group)
        layout.addWidget(self.btn_reset)
        self.setLayout(layout)

        # Apply theme once at startup
        self.update_theme(self.current_theme)

    # ---------- Slots / handlers ----------
    def open_help(self):
        dlg = HelpDialog(self)
        dlg.exec_()

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
        self.size_label.setText(f"Size: {value}")
        self.overlay.set_dot_size(value)
        self.settings["size"] = value
        self.save_settings()

    def update_thickness(self, value):
        self.thickness_label.setText(f"Thickness: {value}")
        self.overlay.set_thickness(value)
        self.settings["thickness"] = value
        self.save_settings()

    def open_shape_selector(self):
        dialog = ShapePreviewSelector()
        if dialog.exec_() == QDialog.Accepted:
            selected_shape = dialog.selected_shape
            if selected_shape:
                self.overlay.set_shape(selected_shape)
                self.shape_combo.setCurrentText(selected_shape)
                self.settings["shape"] = selected_shape
                self.save_settings()

    def update_shape(self, shape):
        self.overlay.set_shape(shape)
        self.settings["shape"] = shape
        self.save_settings()

    def update_center_dot_size(self, value):
        scaled_value = value / 4.0
        self.center_dot_label.setText(f"Center Dot Size: {scaled_value:.2f}")
        self.overlay.set_center_dot_size(scaled_value)
        self.settings["center_dot_size"] = scaled_value
        self.save_settings()

    def toggle_center_dot(self, state):
        show = state == Qt.Checked
        self.overlay.set_show_center_dot(show)
        self.settings["show_center_dot"] = show
        self.save_settings()

    # --- Custom image handlers ---
    def upload_custom_crosshair(self):
        path, _ = QFileDialog.getOpenFileName(
            self,
            "Select Crosshair Image",
            "",
            "Images (*.png *.jpg *.jpeg)"
        )
        if path:
            self.overlay.set_custom_image(path)
            self.overlay.set_shape("Custom")
            self.shape_combo.setCurrentText("Custom")
            self.settings["shape"] = "Custom"
            self.settings["custom_image_path"] = path
            self.save_settings()

    def clear_custom_crosshair(self):
        self.overlay.set_custom_image(None)
        # Revert to a normal default shape
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

        self.setStyleSheet(f"background-color: {bg};")

        button_style = f"""
            QPushButton {{
                background-color: {btn};
                color: white;
                font-weight: bold;
                font-size: 14px;
                border-radius: 8px;
                padding: 10px;
            }}
            QPushButton:hover {{
                background-color: {hover};
            }}
        """
        for b in (self.btn_color, self.btn_center_color, self.btn_reset, self.btn_select_shape, self.btn_help,
                  self.btn_upload_custom, self.btn_clear_custom):
            b.setStyleSheet(button_style)

        slider_style = f"""
            QSlider::groove:horizontal {{
                height: 6px;
                background: {btn};
                border-radius: 3px;
            }}
            QSlider::handle:horizontal {{
                background: {hover};
                width: 16px;
                border-radius: 8px;
                margin: -5px 0;
            }}
        """
        for s in (self.slider, self.thickness_slider, self.center_dot_slider):
            s.setStyleSheet(slider_style)

        combo_style = f"""
            QComboBox {{
                background-color: {btn};
                color: {text_color};
                border-radius: 6px;
                padding: 6px;
                font-weight: bold;
                font-size: 14px;
                min-height: 40px;
            }}
            QComboBox QAbstractItemView {{
                background-color: {btn};
                color: {text_color};
                selection-background-color: {hover};
            }}
        """
        self.shape_combo.setStyleSheet(combo_style)
        self.theme_combo.setStyleSheet(combo_style)

        label_style = f"color: {label}; font-weight: bold;"
        self.size_label.setStyleSheet(label_style)
        self.thickness_label.setStyleSheet(label_style)
        for box in self.findChildren(QGroupBox):
            box.setStyleSheet(f"color: {text_color}; font-size: 16px; font-weight: bold;")

        # Theme GIFs (kept as your version)
        if theme_name == "Dark Gray":
            gif_path = resource_path("berserk.gif")
            gif_size = QSize(200, 128)
        elif theme_name == "Light Orange":
            gif_path = resource_path("cat.gif")
            gif_size = QSize(128, 128)
        else:
            gif_path = resource_path("cat.gif")
            gif_size = QSize(128, 128)

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
            "theme": "Light Orange", "size": 5, "shape": "Dot",
            "color": "#FF0000", "thickness": 2, "center_dot_color": "#333333",
            "center_dot_size": 2, "show_center_dot": True,
        }
        self.settings = defaults
        self.theme_combo.setCurrentText(defaults["theme"])
        self.slider.setValue(defaults["size"])
        self.shape_combo.setCurrentText(defaults["shape"])
        self.thickness_slider.setValue(defaults["thickness"])
        self.overlay.set_dot_color(QColor(defaults["color"]))
        self.center_dot_slider.setValue(int(defaults["center_dot_size"] * 4))
        self.center_dot_checkbox.setChecked(defaults["show_center_dot"])
        self.overlay.set_show_center_dot(defaults["show_center_dot"])
        # Clear custom image
        self.overlay.set_custom_image(None)
        self.settings.pop("custom_image_path", None)
        self.save_settings()

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
        except:
            pass
