from PyQt5.QtWidgets import QDialog, QLabel, QGridLayout
from PyQt5.QtGui import QPainter, QPixmap, QColor, QPen, QPolygon
from PyQt5.QtCore import Qt, QPoint, QSize


class CrosshairPreviewWidget(QLabel):
    def __init__(self, shape, callback):
        super().__init__()
        self.shape = shape
        self.callback = callback
        self.radius = 6
        self.thickness = 2
        self.setFixedSize(80, 80)
        self.setCursor(Qt.PointingHandCursor)
        self.update_preview()

    def update_preview(self):
        pixmap = QPixmap(self.size())
        pixmap.fill(Qt.transparent)

        qp = QPainter(pixmap)
        qp.setRenderHint(QPainter.Antialiasing)
        pen = QPen(QColor("#FF0000"), self.thickness)
        qp.setPen(pen)
        qp.setBrush(QColor("#FF0000"))
        cx, cy = self.width() // 2, self.height() // 2

        if self.shape == "Dot":
            qp.drawEllipse(cx - self.radius, cy - self.radius, self.radius * 2, self.radius * 2)

        elif self.shape == "Cross":
            length = self.radius * 2
            qp.drawLine(cx - length, cy, cx + length, cy)
            qp.drawLine(cx, cy - length, cx, cy + length)

        elif self.shape == "V Cross":
            length = self.radius * 2
            qp.drawLine(cx - length, cy - length, cx + length, cy + length)
            qp.drawLine(cx + length, cy - length, cx - length, cy + length)

        elif self.shape == "Arrow Up":
            length = self.radius * 2
            pen = QPen(QColor("#FF0000"), self.thickness, Qt.SolidLine, Qt.RoundCap)
            qp.setPen(pen)
            qp.setBrush(Qt.NoBrush)
            left = QPoint(cx - length, cy + length)
            top = QPoint(cx, cy)
            right = QPoint(cx + length, cy + length)
            qp.drawLine(left, top)
            qp.drawLine(top, right)

        elif self.shape == "Shaped Crosshair":
            l, g = self.radius * 2, self.radius
            qp.drawLine(cx - l, cy - l, cx - g, cy - l)
            qp.drawLine(cx - l, cy - l, cx - l, cy - g)
            qp.drawLine(cx + g, cy - l, cx + l, cy - l)
            qp.drawLine(cx + l, cy - l, cx + l, cy - g)
            qp.drawLine(cx - l, cy + l, cx - g, cy + l)
            qp.drawLine(cx - l, cy + l, cx - l, cy + g)
            qp.drawLine(cx + g, cy + l, cx + l, cy + l)
            qp.drawLine(cx + l, cy + l, cx + l, cy + g)

        elif self.shape == "Vertical Line":
            length = self.radius * 3
            qp.drawLine(cx, cy + 1, cx, cy + length)

        elif self.shape == "Arrow Sides":
            length = self.radius
            offset = self.radius * 2

            # Left arrow (chevron)
            qp.drawLine(cx - offset + length, cy - length, cx - offset, cy)
            qp.drawLine(cx - offset + length, cy + length, cx - offset, cy)

            # Right arrow (chevron)
            qp.drawLine(cx + offset - length, cy - length, cx + offset, cy)
            qp.drawLine(cx + offset - length, cy + length, cx + offset, cy)

            # Center dot
            dot_radius = 2
            qp.setBrush(QColor("#FF0000"))
            qp.setPen(Qt.NoPen)
            qp.drawEllipse(QPoint(cx, cy), dot_radius, dot_radius)

        elif self.shape == "T-Hair":
            length = self.radius * 2
            spacing = self.radius // 2

            # Vertical line (centered, stops at center)
            qp.drawLine(cx, cy - length, cx, cy)

            # Horizontal left & right (above center line)
            y_offset = cy - length - spacing
            qp.drawLine(cx - length, y_offset, cx - spacing, y_offset)
            qp.drawLine(cx + spacing, y_offset, cx + length, y_offset)


        elif self.shape == "Circle Dot":
            qp.setBrush(Qt.NoBrush)
            qp.drawEllipse(cx - 12, cy - 12, 24, 24)  # Circle
            qp.setBrush(QColor("#FF0000"))
            qp.drawEllipse(cx - 2, cy - 2, 4, 4)       # Center dot

        qp.end()
        self.setPixmap(pixmap)

    def mousePressEvent(self, event):
        if event.button() == Qt.LeftButton:
            self.callback(self.shape)


class ShapePreviewSelector(QDialog):
    def __init__(self):
        super().__init__()
        self.setWindowTitle("Select Crosshair Shape")
        self.setFixedSize(300, 340)
        self.layout = QGridLayout()
        self.setLayout(self.layout)

        self.selected_shape = None

        shapes = [
            "Dot", "Cross", "V Cross",
            "Arrow Up", "Shaped Crosshair", "Vertical Line",
            "Arrow Sides", "T-Hair", "Circle Dot"
        ]

        for i, shape in enumerate(shapes):
            preview = CrosshairPreviewWidget(shape, self.shape_selected)
            self.layout.addWidget(preview, i // 3, i % 3)

    def shape_selected(self, shape):
        self.selected_shape = shape
        self.accept()
