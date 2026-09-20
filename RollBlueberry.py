from PyQt6.QtCore import (
    QEasingCurve,
    QObject,
    QParallelAnimationGroup,
    QPointF,
    QVariantAnimation,
)
from PyQt6.QtGui import QPixmap
from PyQt6.QtWidgets import QGraphicsPixmapItem
from PyQt6.QtCore import Qt


class RollingBlueberry(QObject):

    def __init__(
        self,
        image_path: str,
        target_height: int = 120,
        parent: QObject = None,
    ):
        super().__init__(parent)

        # 1. Create the underlying QGraphicsPixmapItem
        pixmap = QPixmap(image_path).scaledToHeight(
            target_height, Qt.TransformationMode.SmoothTransformation
        )
        self.item = QGraphicsPixmapItem(pixmap)

        # Set origin point to center for smooth rotation
        bounds = self.item.boundingRect()
        self.item.setTransformOriginPoint(
            bounds.width() / 2, bounds.height() / 2
        )
        self.item.setZValue(2)

        # 2. Position Animation
        self.pos_anim = QVariantAnimation(self)
        self.pos_anim.setEasingCurve(QEasingCurve.Type.OutCubic)
        self.pos_anim.valueChanged.connect(self.item.setPos)

        # 3. Rotation Animation
        self.rot_anim = QVariantAnimation(self)
        self.rot_anim.setEasingCurve(QEasingCurve.Type.OutCubic)
        self.rot_anim.valueChanged.connect(self.item.setRotation)

        # 4. Group Animations
        self.anim_group = QParallelAnimationGroup(self)
        self.anim_group.addAnimation(self.pos_anim)
        self.anim_group.addAnimation(self.rot_anim)

    def roll_to(
        self,
        start_pos: QPointF,
        end_pos: QPointF,
        rotations: float = 2.0,
        duration_ms: int = 1800,
    ):
        """Configures and plays the rolling animation."""
        self.pos_anim.setDuration(duration_ms)
        self.pos_anim.setStartValue(start_pos)
        self.pos_anim.setEndValue(end_pos)

        self.rot_anim.setDuration(duration_ms)
        self.rot_anim.setStartValue(0.0)
        self.rot_anim.setEndValue(360.0 * rotations)

        self.anim_group.start()