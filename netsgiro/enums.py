from enum import IntEnum


__all__ = [
    'ServiceCode',
    'RecordType',
    'AvtaleGiroAssignmentType',
    'TransactionType',
    'AvtaleGiroRegistrationType',
]


class ServiceCode(IntEnum):
    NONE = 0
    OCR_GIRO = 9
    AVTALEGIRO = 21


class RecordType(IntEnum):
    TRANSMISSION_START = 10
    ASSIGNMENT_START = 20
    TRANSACTION_AMOUNT_1 = 30
    TRANSACTION_AMOUNT_2 = 31
    TRANSACTION_AMOUNT_3 = 32  # Only for TransactionType 20 and 21
    TRANSACTION_SPECIFICATION = 49
    TRANSACTION_AGREEMENTS = 70  # TODO Better name?
    ASSIGNMENT_END = 88
    TRANSMISSION_END = 89


class TransactionType(IntEnum):
    FROM_GIRO_DEBITED_ACCOUNT = 10
    FROM_STANDING_ORDERS = 11
    FROM_DIRECT_REMITTANCE = 12
    FROM_BUSINESS_TERMINAL_GIRO = 13
    FROM_COUNTER_GIRO = 14
    FROM_AVTALEGIRO = 15
    FROM_TELEGIRO = 16
    FROM_CASH_GIRO = 17

    REVERSING_WITH_KID = 18
    PURCHASE_WITH_KID = 19
    REVERSING_WITH_TEXT = 20
    PURCHASE_WITH_TEXT = 21

    AVTALEGIRO_NO_NOTIFICATION_FROM_BANK = 2   # TODO Better name?
    AVTALEGIRO_NOTIFICATION_FROM_BANK = 21     # TODO Better name?
    AVTALEGIRO_CANCELATION = 93                # TODO Better name?
    AVTALEGIRO_AGREEMENTS = 94                 # TODO Better name?


class AvtaleGiroAssignmentType(IntEnum):
    PAYMENT_REQUESTS = 0    # TODO Better name?
    AGREEMENTS = 24         # TODO Better name?
    CANCELATIONS = 36       # TODO Better name?


class AvtaleGiroRegistrationType(IntEnum):
    ALL_AGREEMENTS = 0
    NEW_OR_UPDATED_AGREEMENTS = 1
    DELETED_AGREEMENTS = 2
