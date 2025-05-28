# bot/state_machine.py
# определены состояния загрузки файла с использованием Enum,
# что позволяет удобно управлять этапами генерации отчета:
from enum import Enum, auto

class ReportState(Enum):
    AWAITING_WORD = auto()
    AWAITING_PDF = auto()
    AWAITING_EXCEL = auto()
    COMPLETE = auto()
