import sys
import os
import json
from PyQt5.QtWidgets import (
    QWidget, QPushButton, QSlider, QLabel, QComboBox, QColorDialog,
    QVBoxLayout, QHBoxLayout, QGroupBox, QDialog, QCheckBox
)
from PyQt5.QtCore import Qt, QSize, QPoint
from PyQt5.QtGui import QColor, QMovie, QIcon, QPainter, QPen
from ShapePreviewSelector import ShapePreviewSelector

# Helper function for PyInstaller compatibility
def resource_path(relative_path):
    # Gets the correct path whether running as script or from PyInstaller .exe
    if hasattr(sys, '_MEIPASS'):
        return os.path.join(sys._MEIPASS, relative_path)
    return os.path.join(os.path.abspath("."), relative_path)


SETTINGS_FILE = "settings.json"

class CrosshairPreview(QWidget):
    def __init__(self):
        super().__init__()
        self.dot_color = QColor("#FF0000")
        self.center_dot_color = QColor("#333333")
        self.shape = "Dot"
        self.radius = 5
        self.thickness = 2
        self.setFixedSize(100, 100)
        self.show_center_dot = True

    def set_dot_color(self, color): self.dot_color = color; self.update()
    def set_center_dot_color(self, color): self.center_dot_color = color; self.update()
    def set_shape(self, shape): self.shape = shape; self.update()
    def set_radius(self, radius): self.radius = radius; self.update()
    def set_thickness(self, thickness): self.thickness = thickness; self.update()
    def set_center_dot_size(self, size): 
        self.center_dot_size = size
        self.update()
    def set_show_center_dot(self, show):
        self.show_center_dot = show
        self.update()

    def paintEvent(self, event):
        qp = QPainter(self)
        qp.setRenderHint(QPainter.Antialiasing)
        cx, cy = self.width() // 2, self.height() // 2
        qp.setPen(QPen(self.dot_color, self.thickness))
        qp.setBrush(self.dot_color)

        if self.shape == "Dot":
            qp.drawEllipse(QPoint(cx, cy), self.radius, self.radius)
            if self.show_center_dot:
                qp.setBrush(self.center_dot_color)
                qp.setPen(Qt.NoPen)
                qp.drawEllipse(QPoint(cx, cy), max(1, self.radius // 3), max(1, self.radius // 3))
        elif self.shape == "Cross":
            length = self.radius * 2
            qp.drawLine(cx - length, cy, cx + length, cy)
            qp.drawLine(cx, cy - length, cx, cy + length)
            if self.show_center_dot:
                qp.setBrush(self.center_dot_color)
                qp.setPen(Qt.NoPen)
                qp.drawEllipse(QPoint(cx, cy), max(1, self.radius // 3), max(1, self.radius // 3))
        elif self.shape == "V Cross":
            length = self.radius * 2
            qp.drawLine(cx - length, cy - length, cx + length, cy + length)
            qp.drawLine(cx + length, cy - length, cx - length, cy + length)
            if self.show_center_dot:
                qp.setBrush(self.center_dot_color)
                qp.setPen(Qt.NoPen)
                qp.drawEllipse(QPoint(cx, cy), max(1, self.radius // 3), max(1, self.radius // 3))
        elif self.shape == "Arrow Up":
            length = self.radius * 2
            pen = QPen(self.dot_color, self.thickness, Qt.SolidLine, Qt.RoundCap)
            if self.show_center_dot:
                qp.setBrush(self.center_dot_color)
                qp.setPen(Qt.NoPen)
                qp.drawEllipse(QPoint(cx, cy), max(1, self.radius // 3), max(1, self.radius // 3))
        elif self.shape == "Shaped Crosshair":
            l, gap = self.radius * 2, self.radius
            qp.drawLine(cx - l, cy - l, cx - gap, cy - l)
            qp.drawLine(cx - l, cy - l, cx - l, cy - gap)
            qp.drawLine(cx + gap, cy - l, cx + l, cy - l)
            qp.drawLine(cx + l, cy - l, cx + l, cy - gap)
            qp.drawLine(cx - l, cy + l, cx - gap, cy + l)
            qp.drawLine(cx - l, cy + l, cx - l, cy + gap)
            qp.drawLine(cx + gap, cy + l, cx + l, cy + l)
            qp.drawLine(cx + l, cy + l, cx + l, cy + gap)
            if self.show_center_dot:
                qp.setBrush(self.center_dot_color)
                qp.setPen(Qt.NoPen)
                qp.drawEllipse(QPoint(cx, cy), max(1, self.radius // 3), max(1, self.radius // 3))
        elif self.shape == "Vertical Line":
            length = self.radius * 3
            qp.setPen(QPen(self.dot_color, self.thickness, Qt.SolidLine, Qt.RoundCap))
            qp.drawLine(cx, cy + 1, cx, cy + length)

class CrosshairGUI(QWidget):
    def __init__(self, overlay):
        super().__init__()
        self.setWindowIcon(QIcon("Crosshair.ico"))
        self.setWindowTitle("Crosshair Settings")
        self.setGeometry(100, 100, 340, 550)
        
        self.theme_gif = QLabel()
        self.theme_movie = QMovie()
        self.theme_gif.setMovie(self.theme_movie)

        cat_layout = QHBoxLayout()
        cat_layout.addStretch()
        cat_layout.addWidget(self.theme_gif)
        cat_layout.addStretch()

        self.overlay = overlay
        self.settings = self.load_settings()
        self.current_theme = self.settings.get("theme", "Light Orange")
        initial_size = self.settings.get("size", 5)
        initial_shape = self.settings.get("shape", "Dot")
        initial_color = self.settings.get("color", "#FF0000")
        initial_center_color = self.settings.get("center_dot_color", "#333333")
        initial_thickness = self.settings.get("thickness", 2)
        initial_center_dot_size = self.settings.get("center_dot_size", max(1, initial_size // 3))
        initial_show_dot = self.settings.get("show_center_dot", True)
        self.overlay.set_show_center_dot(initial_show_dot)
        
        self.overlay.set_center_dot_size(initial_center_dot_size)
        self.overlay.set_dot_size(initial_size)
        self.overlay.set_shape(initial_shape)
        self.overlay.set_dot_color(QColor(initial_color))
        self.overlay.set_center_dot_color(QColor(initial_center_color))
        self.overlay.set_thickness(initial_thickness)

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

        # Appearance
        # self.orange_banner = QLabel()
        # self.orange_banner.setVisible(False)
        # self.orange_banner.setAlignment(Qt.AlignCenter)
        # self.orange_banner_movie = QMovie("Thorfinn.gif") 
        # self.orange_banner_movie.setScaledSize(QSize(498, 281))
        # self.orange_banner.setMovie(self.orange_banner_movie)
        # self.orange_banner_movie.start()
        
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

        appearance_layout = QVBoxLayout()
        appearance_layout.addWidget(self.btn_color)
        appearance_layout.addWidget(self.btn_center_color)
        appearance_layout.addWidget(self.size_label)
        appearance_layout.addWidget(self.slider)
        appearance_layout.addWidget(self.thickness_label)
        appearance_layout.addWidget(self.thickness_slider)
        appearance_group.setLayout(appearance_layout)

        
        self.center_dot_label = QLabel(f"Center Dot Size: {initial_center_dot_size:.2f}")
        self.center_dot_slider = QSlider(Qt.Horizontal)
        self.center_dot_slider.setRange(1, 40)  # 0.25 * 1 = 0.25, 0.25 * 40 = 10
        self.center_dot_slider.setValue(int(initial_center_dot_size * 4))
        self.center_dot_slider.valueChanged.connect(self.update_center_dot_size)
        appearance_layout.addWidget(self.center_dot_label)
        appearance_layout.addWidget(self.center_dot_slider)

        # Shape group
        shape_group = QGroupBox("🔲 Crosshair Shape")
        shape_layout = QVBoxLayout()

        self.shape_combo = QComboBox()  # Needed for settings sync but hidden from user
        self.shape_combo.addItems([
            "Dot", "Cross", "V Cross", "Arrow Up", "Shaped Crosshair", "Vertical Line",
            "Arrow Sides", "T-Hair", "Circle Dot"
        ])
        self.shape_combo.setCurrentText(initial_shape)
        self.shape_combo.currentTextChanged.connect(self.update_shape)
        self.shape_combo.hide()  # Hide dropdown since we use custom selector

        self.btn_select_shape = QPushButton("🖼️ Select Crosshair Shape")
        self.btn_select_shape.clicked.connect(self.open_shape_selector)

        shape_layout.addWidget(self.btn_select_shape)
        shape_group.setLayout(shape_layout)

        # Theme group
        theme_group = QGroupBox("🖌️ GUI Theme")
        self.theme_combo = QComboBox()
        self.theme_combo.addItems(list(self.themes.keys()))
        self.theme_combo.setCurrentText(self.current_theme)
        self.theme_combo.currentTextChanged.connect(self.update_theme)
        self.theme_combo.setMinimumHeight(40)
        theme_layout = QVBoxLayout()
        theme_layout.addWidget(self.theme_combo)
        theme_group.setLayout(theme_layout)

        # Reset button
        self.btn_reset = QPushButton("🔄 Reset to Defaults")
        self.btn_reset.clicked.connect(self.reset_defaults)

        # Main layout
        layout = QVBoxLayout()
        layout.setSpacing(14)
        layout.setContentsMargins(15, 15, 15, 15)
        layout.addLayout(cat_layout)
        # layout.addWidget(self.orange_banner)  # Thorfinn banner (shown only for Light Orange)
        layout.addWidget(appearance_group)
        layout.addWidget(shape_group)
        layout.addWidget(theme_group)
        layout.addWidget(self.btn_reset)
        self.setLayout(layout)
        self.update_theme(self.current_theme)

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
                self.shape_combo.setCurrentText(selected_shape)  # optional: sync combo
                self.settings["shape"] = selected_shape
                self.save_settings()


    def update_shape(self, shape):
        self.overlay.set_shape(shape)
        self.settings["shape"] = shape
        self.save_settings()
    
    def update_center_dot_size(self, value):
        scaled_value = value / 4
        self.center_dot_label.setText(f"Center Dot Size: {scaled_value:.2f}")
        self.overlay.set_center_dot_size(scaled_value)
        self.settings["center_dot_size"] = scaled_value
        self.save_settings()
        
    def toggle_center_dot(self, state):
        show = state == Qt.Checked
        self.overlay.set_show_center_dot(show)
        self.settings["show_center_dot"] = show
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
        self.btn_color.setStyleSheet(button_style)
        self.btn_center_color.setStyleSheet(button_style)
        self.btn_reset.setStyleSheet(button_style)

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
        self.slider.setStyleSheet(slider_style)
        self.thickness_slider.setStyleSheet(slider_style)

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
            
        if theme_name == "Dark Gray":
            gif_path = resource_path("berserk.gif")
            gif_size = QSize(200, 128)
        elif theme_name == "Light Orange":
            gif_path = resource_path("cat.gif")
            gif_size = QSize(128, 128)
        else:
            gif_path = resource_path("cat.gif")
            gif_size = QSize(128, 128)

        # Apply GIF logic
        if gif_path:
            self.theme_gif.setVisible(True)
            self.theme_movie.stop()
            self.theme_movie.setFileName(gif_path)
            self.theme_movie.setScaledSize(gif_size)
            self.theme_movie.start()
        else:
            self.theme_gif.setVisible(False)
            self.theme_movie.stop()
            
        # self.orange_banner.setVisible(theme_name == "Light Orange")


    def reset_defaults(self):
        defaults = {
            "theme": "Light Orange", "size": 5, "shape": "Dot",
            "color": "#FF0000", "thickness": 2, "center_dot_color": "#333333",
            "center_dot_size": 2,
            "show_center_dot": True
            
        }
        self.settings = defaults
        self.theme_combo.setCurrentText(defaults["theme"])
        self.slider.setValue(defaults["size"])
        self.shape_combo.setCurrentText(defaults["shape"])
        self.thickness_slider.setValue(defaults["thickness"])
        self.overlay.set_dot_color(QColor(defaults["color"]))
        self.center_dot_slider.setValue(defaults["center_dot_size"])
        self.center_dot_checkbox.setChecked(defaults["show_center_dot"])
        self.overlay.set_show_center_dot(defaults["show_center_dot"])
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
