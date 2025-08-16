# main.py 
import sys
import threading
import ctypes
import keyboard
from PyQt5.QtWidgets import QApplication, QWidget
from PyQt5.QtCore import Qt, QTimer, QPoint, QRect
from PyQt5.QtGui import QPainter, QColor, QPen, QIcon, QPolygon, QPixmap

from GUI import CrosshairGUI

class CrosshairOverlay(QWidget):
    def __init__(self):
        super().__init__()
        self.dot_color = QColor(255, 0, 0)
        self.dot_radius = 5           # used as the main "size" control
        self.thickness = 2
        self.shape = "Dot"

        # Center-dot controls
        self.center_dot_color = QColor("#333333")
        self.center_dot_size = 2
        self.show_center_dot = True

        # --- Custom crosshair image state ---
        self.custom_pixmap: QPixmap | None = None
        self.custom_opacity = 1.0      # 0.0 - 1.0

        self.setWindowFlags(Qt.FramelessWindowHint | Qt.WindowStaysOnTopHint | Qt.Tool)
        self.setAttribute(Qt.WA_TranslucentBackground)
        self.setAttribute(Qt.WA_TransparentForMouseEvents)
        # self.setCursor(Qt.BlankCursor)
        self.showFullScreen()

        # ✅ Windows-level click-through
        hwnd = self.winId().__int__()
        style = ctypes.windll.user32.GetWindowLongW(hwnd, -20)
        ctypes.windll.user32.SetWindowLongW(hwnd, -20, style | 0x80000 | 0x20)  # WS_EX_LAYERED | WS_EX_TRANSPARENT

        self.timer = QTimer()
        self.timer.timeout.connect(self.update)
        self.timer.start(100)

    # ----- setters -----
    def set_dot_color(self, color: QColor):
        self.dot_color = color
        self.update()

    def set_show_center_dot(self, show):
        self.show_center_dot = show
        self.update()

    def set_dot_size(self, radius: int):
        self.dot_radius = radius
        self.update()

    def set_thickness(self, thickness: int):
        self.thickness = thickness
        self.update()

    def set_shape(self, shape: str):
        self.shape = shape
        self.update()

    def set_center_dot_size(self, size: int | float):
        self.center_dot_size = size
        self.update()

    def set_center_dot_color(self, color: QColor):
        self.center_dot_color = color
        self.update()

    # --- custom image controls ---
    def set_custom_image(self, path: str | None):
        """Load a custom image (PNG/JPG with alpha). Set None to clear."""
        if path:
            pm = QPixmap(path)
            if not pm.isNull():
                self.custom_pixmap = pm
                self.set_shape("Custom")
            else:
                self.custom_pixmap = None
        else:
            self.custom_pixmap = None
        self.update()

    def set_custom_opacity(self, opacity: float):
        """Set overall overlay opacity (0.0–1.0) for ALL shapes/images."""
        try:
            val = float(opacity)
        except Exception:
            val = 1.0
        self.custom_opacity = max(0.0, min(1.0, val))
        # Try window-level opacity (smoothest on Windows); keep value for painter fallback
        try:
            self.setWindowOpacity(self.custom_opacity)
        except Exception:
            pass
        self.update()

    # ----- helpers -----
    def _paint_center_dot(self, qp, cx, cy):
        if not self.show_center_dot:
            return
        r = max(1, int(self.center_dot_size))
        qp.setBrush(self.center_dot_color)
        qp.setPen(Qt.NoPen)
        qp.drawEllipse(QPoint(cx, cy), r, r)

    def _paint_custom(self, qp, cx, cy):
        if not self.custom_pixmap:
            return
        # Use Size slider as "target width" for the image (in pixels * a factor).
        target_width = max(8, int(self.dot_radius * 10))
        pm = self.custom_pixmap

        # Preserve aspect ratio
        scaled = pm.scaledToWidth(target_width, Qt.SmoothTransformation)
        w, h = scaled.width(), scaled.height()
        x = cx - w // 2
        y = cy - h // 2

        # qp opacity is already set globally in paintEvent
        qp.drawPixmap(QRect(x, y, w, h), scaled)

    def paintEvent(self, event):
        qp = QPainter(self)
        qp.setRenderHint(QPainter.Antialiasing)

        # Apply opacity to ALL painting (fallback if setWindowOpacity isn't used)
        qp.setOpacity(self.custom_opacity)

        cx = self.width() // 2
        cy = self.height() // 2

        # Custom image path
        if self.shape == "Custom" and self.custom_pixmap:
            self._paint_custom(qp, cx, cy)
            return

        qp.setPen(QPen(self.dot_color, self.thickness))
        qp.setBrush(self.dot_color)

        if self.shape == "Dot":
            qp.drawEllipse(QPoint(cx, cy), self.dot_radius, self.dot_radius)
            self._paint_center_dot(qp, cx, cy)

        elif self.shape == "Cross":
            length = self.dot_radius * 2
            qp.drawLine(cx - length, cy, cx + length, cy)
            qp.drawLine(cx, cy - length, cx, cy + length)
            self._paint_center_dot(qp, cx, cy)

        elif self.shape == "V Cross":
            length = self.dot_radius * 2
            qp.drawLine(cx - length, cy - length, cx + length, cy + length)
            qp.drawLine(cx + length, cy - length, cx - length, cy + length)
            self._paint_center_dot(qp, cx, cy)

        elif self.shape == "Arrow Up":
            length = self.dot_radius * 2
            pen = QPen(self.dot_color, self.thickness, Qt.SolidLine, Qt.RoundCap)
            qp.setPen(pen)
            qp.setBrush(Qt.NoBrush)
            arrow = [QPoint(cx - length, cy + length), QPoint(cx, cy), QPoint(cx + length, cy + length)]
            qp.drawPolyline(QPolygon(arrow))
            self._paint_center_dot(qp, cx, cy)

        elif self.shape == "Shaped Crosshair":
            l = self.dot_radius * 2
            gap = self.dot_radius
            qp.drawLine(cx - l, cy - l, cx - gap, cy - l)
            qp.drawLine(cx - l, cy - l, cx - l, cy - gap)
            qp.drawLine(cx + gap, cy - l, cx + l, cy - l)
            qp.drawLine(cx + l, cy - l, cx + l, cy - gap)
            qp.drawLine(cx - l, cy + l, cx - gap, cy + l)
            qp.drawLine(cx - l, cy + l, cx - l, cy + gap)
            qp.drawLine(cx + gap, cy + l, cx + l, cy + l)
            qp.drawLine(cx + l, cy + l, cx + l, cy + gap)
            self._paint_center_dot(qp, cx, cy)

        elif self.shape == "Vertical Line":
            length = self.dot_radius * 3
            pen = QPen(self.dot_color, self.thickness, Qt.SolidLine, Qt.RoundCap)
            qp.setPen(pen)
            qp.setBrush(Qt.NoBrush)
            qp.drawLine(cx, cy + 1, cx, cy + length)

        elif self.shape == "Arrow Sides":
            length = self.dot_radius * 2
            offset = self.dot_radius
            self._paint_center_dot(qp, cx, cy)
            qp.setPen(QPen(self.dot_color, self.thickness, Qt.SolidLine, Qt.RoundCap))
            qp.setBrush(Qt.NoBrush)
            qp.drawLine(cx - offset, cy - offset, cx - length, cy)
            qp.drawLine(cx - offset, cy + offset, cx - length, cy)
            qp.drawLine(cx + offset, cy - offset, cx + length, cy)
            qp.drawLine(cx + offset, cy + offset, cx + length, cy)

        elif self.shape == "T-Hair":
            length = self.dot_radius * 2
            spacing = self.dot_radius // 2
            vertical_length = self.dot_radius * 3
            pen = QPen(self.dot_color, self.thickness, Qt.SolidLine, Qt.RoundCap)
            qp.setPen(pen)
            qp.setBrush(Qt.NoBrush)
            qp.drawLine(cx, cy + 1, cx, cy + vertical_length - 8)
            qp.drawLine(cx - length, cy - spacing, cx - spacing, cy - spacing)
            qp.drawLine(cx + spacing, cy - spacing, cx + length, cy - spacing)

        elif self.shape == "Circle Dot":
            radius = self.dot_radius * 2
            qp.setPen(QPen(self.dot_color, self.thickness))
            qp.setBrush(Qt.NoBrush)
            qp.drawEllipse(QPoint(cx, cy), radius, radius)
            self._paint_center_dot(qp, cx, cy)


def start_hotkey_listener(gui: CrosshairGUI, overlay: CrosshairOverlay):
    def toggle_gui():
        gui.setVisible(not gui.isVisible())

    def exit_app():
        gui.close()
        overlay.close()
        sys.exit(0)

    keyboard.add_hotkey("ctrl+alt+h", toggle_gui)
    keyboard.add_hotkey("ctrl+alt+x", exit_app)
    keyboard.wait()

if __name__ == '__main__':
    app = QApplication(sys.argv)
    app.setWindowIcon(QIcon("Crosshair.ico"))

    overlay = CrosshairOverlay()
    gui = CrosshairGUI(overlay)
    gui.show()

    threading.Thread(target=start_hotkey_listener, args=(gui, overlay), daemon=True).start()
    sys.exit(app.exec_())
