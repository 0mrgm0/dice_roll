"""A minimal three-panel desktop interface for the Dice backend."""

import sys
import random
from math import ceil, isqrt
from pathlib import Path

from PySide6.QtCore import QRectF, Qt
from PySide6.QtGui import QColor, QFont, QFontDatabase, QPainter
from PySide6.QtSvg import QSvgRenderer
from PySide6.QtWidgets import (
    QApplication, QHBoxLayout, QLabel, QPlainTextEdit,
    QPushButton, QScrollArea, QSpinBox, QVBoxLayout, QWidget, QMessageBox,
)

from .dice import Dice


IMG_DIR = Path(__file__).resolve().parent / "img"
MIN_DIE_SIZE = 68
MAX_DIE_SIZE = 340
GRID_MARGIN = 4
GRID_SPACING = 4


def grid_geometry(count, width, height, scrollbar_width=0):
    """Return (columns, die size, rows) for the available viewport.

    Use a nearly square grid when it fits; otherwise keep the minimum
    icon size and fill the available width, allowing vertical scrolling.
    Width and height refer to the viewport before a scrollbar appears.
    """
    if count < 1:
        return 0, MIN_DIE_SIZE, 0

    columns = isqrt(count - 1) + 1  # ceil(sqrt(count)), exactly
    rows = ceil(count / columns)
    usable_w = width - 2 * GRID_MARGIN
    usable_h = height - 2 * GRID_MARGIN

    size = min(
        MAX_DIE_SIZE,
        (usable_w - (columns - 1) * GRID_SPACING) // columns,
        (usable_h - (rows - 1) * GRID_SPACING) // rows,
    )
    if size >= MIN_DIE_SIZE:
        return columns, size, rows

    # Reserve the vertical scrollbar's width before choosing columns.
    # One additional pixel allows for style-specific rounding.
    usable_w -= scrollbar_width + 1
    columns = max(1, (usable_w + GRID_SPACING) //
                  (MIN_DIE_SIZE + GRID_SPACING))
    columns = min(count, columns)
    rows = ceil(count / columns)
    return columns, MIN_DIE_SIZE, rows

# Centers of the large white faces, in normalized SVG coordinates.
# These correspond to the supplied SVG files, including the revised d10.
FACE_CENTERS = {
    4: (0.4335, 0.6353),
    6: (0.4134, 0.5936),
    8: (0.5000, 0.5000),
    10: (0.4984, 0.4431),
    12: (0.5000, 0.5000),
    20: (0.5000, 0.5000),
}


class DieIcon(QWidget):
    """Draw a supplied SVG and overlay a number on its main face."""

    def __init__(self, sides, value=None, size=MIN_DIE_SIZE, parent=None):
        super().__init__(parent)
        self.sides = sides
        self.value = sides if value is None else value
        self.setFixedSize(size, size)
        self.setAccessibleName(f"d{sides}, value {self.value}")

        path = IMG_DIR / f"d{sides}_face.svg"
        # Also accept the filenames from the uploaded copies.
        if not path.exists():
            path = IMG_DIR / f"d{sides}_face(1).svg"
        self.renderer = QSvgRenderer(str(path), self)
        if not self.renderer.isValid():
            raise ValueError(f"Cannot load dice SVG: {path}")

    def set_value(self, value):
        self.value = value
        self.setAccessibleName(f"d{self.sides}, value {value}")
        self.update()

    def paintEvent(self, event):
        painter = QPainter(self)
        painter.setRenderHint(QPainter.RenderHint.Antialiasing)
        painter.setRenderHint(QPainter.RenderHint.TextAntialiasing)

        side = min(self.width(), self.height())
        bounds = QRectF((self.width() - side) / 2,
                        (self.height() - side) / 2, side, side)
        self.renderer.render(painter, bounds)

        # Text is drawn separately: the SVG source stays unmodified.
        x, y = FACE_CENTERS[self.sides]
        cx = bounds.left() + x * side
        cy = bounds.top() + y * side
        font = QFont("Sans Serif")
        font.setBold(True)
        font.setPixelSize(round(side * (0.28 if len(str(self.value)) == 1 else 0.25)))
        painter.setFont(font)
        painter.setPen(QColor("black"))
        text_rect = QRectF(cx - side / 2, cy - side / 2, side, side)
        painter.drawText(text_rect, Qt.AlignmentFlag.AlignCenter, str(self.value))
        painter.end()


class DiceWindow(QWidget):
    def __init__(self, seed=None):
        super().__init__()
        self.engine = Dice(seed=seed)
        self.inputs = {}
        # Separate RNG: visual shuffling cannot change Dice.rng.
        self.display_rng = random.Random()
        self.setWindowTitle("Dice Roller")

        # Three zones in a single horizontal layout.
        layout = QHBoxLayout(self)
        layout.setContentsMargins(16, 16, 16, 16)
        layout.setSpacing(18)
        layout.addWidget(self.create_controls())
        layout.addWidget(self.create_roll_area())
        layout.addWidget(self.create_history(), 1)
        self.resize(1080, 520)

    def create_controls(self):
        """Zone 1: dice icons, quantities, and Roll button."""
        panel = QWidget()
        panel.setFixedWidth(160)
        layout = QVBoxLayout(panel)
        layout.setContentsMargins(0, 0, 0, 0)
        layout.setSpacing(3)
        layout.addWidget(QLabel("Dice"))

        for sides in self.engine.dice:
            row = QHBoxLayout()
            row.setSpacing(10)
            row.addWidget(DieIcon(sides))

            quantity = QSpinBox()
            quantity.setRange(0, 99)
            quantity.setValue(1 if sides == 6 else 0)
            quantity.setFixedWidth(65)
            quantity.setAccessibleName(f"Number of d{sides} dice")
            self.inputs[sides] = quantity
            row.addWidget(quantity)
            layout.addLayout(row)

        self.roll_button = QPushButton("Roll")
        self.roll_button.setFixedHeight(34)
        self.roll_button.clicked.connect(self.roll_dice)
        layout.addStretch()
        layout.addWidget(self.roll_button)
        return panel

    def create_roll_area(self):
        """Zone 2: expandable roll display, aligned with the other panels."""
        panel = QWidget()
        layout = QVBoxLayout(panel)
        layout.setContentsMargins(0, 0, 0, 0)
        layout.setSpacing(3)
        layout.addWidget(QLabel("Roll area"))

        self.roll_area = QScrollArea()
        self.roll_area.setObjectName("rollArea")
        self.roll_area.setFixedWidth(440)
        self.roll_area.setMinimumHeight(440)
        self.roll_area.setWidgetResizable(True)
        self.roll_area.setHorizontalScrollBarPolicy(
            Qt.ScrollBarPolicy.ScrollBarAlwaysOff
        )
        self.roll_area.setVerticalScrollBarPolicy(
            Qt.ScrollBarPolicy.ScrollBarAsNeeded
        )
        self.roll_area.setStyleSheet(
            "QScrollArea#rollArea { background-color: white; "
            "border: 1px solid #999; }"
        )

        # A fresh content widget will be created for each roll.
        self.roll_content = QWidget()
        self.roll_content.setStyleSheet("background-color: white;")
        self.roll_area.setWidget(self.roll_content)

        # Fill the entire middle zone down to the buttons' bottom edge.
        layout.addWidget(self.roll_area, 1)
        return panel

    def create_history(self):
        """Zone 3: show the backend log verbatim in a read-only editor."""
        panel = QWidget()
        panel.setMinimumWidth(320)
        layout = QVBoxLayout(panel)
        layout.setContentsMargins(0, 0, 0, 0)
        layout.setSpacing(3)
        layout.addWidget(QLabel("History"))

        self.history = QPlainTextEdit()
        self.history.setReadOnly(True)
        self.history.setLineWrapMode(QPlainTextEdit.LineWrapMode.NoWrap)
        self.history.setFont(QFontDatabase.systemFont(QFontDatabase.SystemFont.FixedFont))
        layout.addWidget(self.history, 1)

        self.save_button = QPushButton("Save")
        self.save_button.setFixedHeight(34)
        self.save_button.clicked.connect(self.save_log)
        layout.addWidget(self.save_button)
        return panel

    def save_log(self):
        """Save a snapshot of the entire log without changing the session."""
        try:
            filename = self.engine.save_log()
        except OSError as error:
            QMessageBox.warning(self, "Save failed", str(error))
            return
        self.save_button.setToolTip(f"Last saved: {Path(filename).resolve()}")

    def roll_dice(self):
        # Preserve the backend's expected order: d4, d6, d8, d10, d12, d20.
        counts = [self.inputs[sides].value() for sides in self.engine.dice]
        if not any(counts):
            return

        # Dice.roll() already calls save_roll(), so do not call it again.
        timestamp, results = self.engine.roll(counts)

        self.display_roll(results)
        self.history.setPlainText(self.engine.log)
        scrollbar = self.history.verticalScrollBar()
        scrollbar.setValue(scrollbar.maximum())


    def display_roll(self, results):
        """Show all results in shuffled, centered rows with vertical scrolling."""
        # Copy the values out of the backend arrays. Do not alter self.engine.n
        # or the ordered log when shuffling the graphical arrangement.
        dice = [(sides, int(value))
                for sides, values in zip(self.engine.dice, results)
                for value in values]
        self.display_rng.shuffle(dice)

        # maximumViewportSize() gives the available area without scrollbars.
        viewport = self.roll_area.maximumViewportSize()
        scrollbar_width = self.roll_area.verticalScrollBar().sizeHint().width()
        columns, size, rows = grid_geometry(
            len(dice), viewport.width(), viewport.height(), scrollbar_width
        )

        content = QWidget()
        content.setStyleSheet("background-color: white;")
        grid = QVBoxLayout(content)
        grid.setContentsMargins(*(GRID_MARGIN,) * 4)
        grid.setSpacing(GRID_SPACING)
        # Center the block vertically if it fits; for overflow the content
        # grows to its minimum height and the scroll area handles scrolling.
        grid.addStretch(1)

        for row_index in range(rows):
            row = QHBoxLayout()
            row.setContentsMargins(0, 0, 0, 0)
            row.setSpacing(GRID_SPACING)
            row.addStretch(1)
            first = row_index * columns
            for sides, value in dice[first:first + columns]:
                row.addWidget(DieIcon(sides, value=value, size=size))
            row.addStretch(1)
            grid.addLayout(row)

        grid.addStretch(1)

        if rows:
            content.setMinimumHeight(
                2 * GRID_MARGIN + rows * size + (rows - 1) * GRID_SPACING
            )

        # QScrollArea takes ownership and deletes the previous content widget.
        self.roll_content = content
        self.roll_area.setWidget(content)
        self.roll_area.verticalScrollBar().setValue(0)


def main():
    app = QApplication(sys.argv)
    window = DiceWindow()
    window.show()
    return app.exec()


if __name__ == "__main__":
    sys.exit(main())
