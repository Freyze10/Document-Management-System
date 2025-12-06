from PyQt6.QtCore import QEvent, QObject


class DateWheelEventFilter(QObject):
    def eventFilter(self, obj, event):
        if event.type() == QEvent.Type.Wheel:
            return True  # Indicate that the event has been handled and should not propagate
        return super().eventFilter(obj, event)