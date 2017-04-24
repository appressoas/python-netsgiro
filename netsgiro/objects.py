import collections
from decimal import Decimal
from typing import List

import attr

import netsgiro
from netsgiro.records import Record


__all__ = [
    'Transmission',
    'Assignment',
    'Transaction',
    'parse',
]


class Serializable:
    def to_dict(self):
        return attr.asdict(self)


@attr.s
class Transmission(Serializable):
    number = attr.ib()
    data_transmitter = attr.ib()
    data_recipient = attr.ib()

    # TODO For AvtaleGiro payment request, this should be the earliest due date
    nets_date = attr.ib(default=None)

    assignments = attr.ib(default=attr.Factory(list))

    @classmethod
    def from_records(cls, records: List[Record]) -> 'Transmission':
        if len(records) < 2:
            raise ValueError(
                'At least 2 records required, got {}'.format(len(records)))

        start, body, end = records[0], records[1:-1], records[-1]

        assert isinstance(start, netsgiro.TransmissionStart)
        assert isinstance(end, netsgiro.TransmissionEnd)

        return cls(
            number=start.transmission_number,
            data_transmitter=start.data_transmitter,
            data_recipient=start.data_recipient,
            nets_date=end.nets_date,
            assignments=get_assignments(body),
        )

    def add_assignment(
            self, *,
            service_code, assignment_type, agreement_id=None, number, account,
            nets_date=None
            ) -> 'Assignment':

        assignment = Assignment(
            service_code=service_code,
            type=assignment_type,
            agreement_id=agreement_id,
            number=number,
            account=account,
            nets_date=nets_date,
        )
        self.assignments.append(assignment)
        return assignment


@attr.s
class Assignment(Serializable):
    service_code = attr.ib(convert=netsgiro.ServiceCode)
    type = attr.ib(convert=netsgiro.AssignmentType)
    agreement_id = attr.ib()
    number = attr.ib()
    account = attr.ib()

    nets_date = attr.ib(default=None)

    transactions = attr.ib(default=attr.Factory(list))

    _next_transaction_number = 1

    @classmethod
    def from_records(cls, records: List[Record]) -> 'Assignment':
        if len(records) < 2:
            raise ValueError(
                'At least 2 records required, got {}'.format(len(records)))

        start, body, end = records[0], records[1:-1], records[-1]

        assert isinstance(start, netsgiro.AssignmentStart)
        assert isinstance(end, netsgiro.AssignmentEnd)

        return cls(
            service_code=start.service_code,
            type=start.assignment_type,
            agreement_id=start.agreement_id,
            number=start.assignment_number,
            account=start.assignment_account,
            nets_date=end.nets_date,
            transactions=get_transactions(body)
        )

    def add_payment_request(
            self, *,
            kid, due_date, amount,
            reference=None, payer_name=None, bank_notification=None
            ) -> 'Transaction':

        assert self.service_code == netsgiro.ServiceCode.AVTALEGIRO, (
            'Can only add payment requests to AvtaleGiro assignments')
        assert self.type == netsgiro.AssignmentType.TRANSACTIONS, (
            'Can only add payment requests to transaction assignments')

        if bank_notification:
            transaction_type = (
                netsgiro.TransactionType.AVTALEGIRO_WITH_BANK_NOTIFICATION)
        else:
            transaction_type = (
                netsgiro.TransactionType.AVTALEGIRO_WITH_PAYEE_NOTIFICATION)

        if isinstance(bank_notification, str):
            text = bank_notification
        else:
            text = ''

        number = self._next_transaction_number
        self._next_transaction_number += 1

        transaction = Transaction(
            service_code=self.service_code,
            type=transaction_type,
            number=number,
            nets_date=due_date,
            amount=amount,
            kid=kid,
            reference=reference,
            text=text,

            centre_id=None,
            day_code=None,
            partial_settlement_number=None,
            partial_settlement_serial_number=None,
            sign=None,
            form_number=None,
            bank_date=None,
            debit_account=None,
            filler=None,

            payer_name=payer_name,
        )
        self.transactions.append(transaction)
        return transaction


def get_assignments(records: List[Record]) -> List[Assignment]:
    assignments = collections.OrderedDict()

    current_assignment_number = None
    for record in records:
        if isinstance(record, netsgiro.AssignmentStart):
            current_assignment_number = record.assignment_number
            assignments[current_assignment_number] = []
        if current_assignment_number is None:
            raise ValueError(
                'Expected AssignmentStart record, got {!r}'.format(record))
        assignments[current_assignment_number].append(record)
        if isinstance(record, netsgiro.AssignmentEnd):
            current_assignment_number = None

    return [Assignment.from_records(rs) for rs in assignments.values()]


@attr.s
class Transaction(Serializable):
    service_code = attr.ib(convert=netsgiro.ServiceCode)
    type = attr.ib(convert=netsgiro.TransactionType)
    number = attr.ib()
    nets_date = attr.ib()
    amount = attr.ib(convert=Decimal)
    kid = attr.ib()
    reference = attr.ib()
    text = attr.ib()

    # Specific to OCR Giro
    centre_id = attr.ib()
    day_code = attr.ib()
    partial_settlement_number = attr.ib()
    partial_settlement_serial_number = attr.ib()
    sign = attr.ib()
    form_number = attr.ib()
    bank_date = attr.ib()
    debit_account = attr.ib()
    _filler = attr.ib()

    # Specific to AvtaleGiro
    payer_name = attr.ib()

    @property
    def amount_in_cents(self):
        return int(self.amount * 100)

    @classmethod
    def from_records(cls, records: List[Record]) -> 'Transaction':
        amount_item_1 = records.pop(0)
        assert isinstance(amount_item_1, netsgiro.TransactionAmountItem1)
        amount_item_2 = records.pop(0)
        assert isinstance(amount_item_2, netsgiro.TransactionAmountItem2)

        if amount_item_1.service_code == netsgiro.ServiceCode.OCR_GIRO:
            text = get_ocr_giro_text(records)
        elif amount_item_1.service_code == netsgiro.ServiceCode.AVTALEGIRO:
            text = netsgiro.TransactionSpecification.to_text(records)
        else:
            text = None

        return cls(
            service_code=amount_item_1.service_code,
            type=amount_item_1.transaction_type,
            number=amount_item_1.transaction_number,
            nets_date=amount_item_1.nets_date,
            amount=Decimal(amount_item_1.amount) / 100,
            kid=amount_item_1.kid,
            reference=amount_item_2.reference,
            text=text,

            # Specific to OCR Giro
            centre_id=amount_item_1.centre_id,
            day_code=amount_item_1.day_code,
            partial_settlement_number=amount_item_1.partial_settlement_number,
            partial_settlement_serial_number=(
                amount_item_1.partial_settlement_serial_number),
            sign=amount_item_1.sign,
            form_number=amount_item_2.form_number,
            bank_date=amount_item_2.bank_date,
            debit_account=amount_item_2.debit_account,
            filler=amount_item_2._filler,

            # Specific to AvtaleGiro
            payer_name=amount_item_2.payer_name,
        )


def get_transactions(records: List[Record]) -> List[Transaction]:
    transactions = collections.OrderedDict()

    for record in records:
        if record.transaction_number not in transactions:
            transactions[record.transaction_number] = []
        transactions[record.transaction_number].append(record)

    return [Transaction.from_records(rs) for rs in transactions.values()]


def get_ocr_giro_text(records: List[Record]) -> str:
    if (
            len(records) == 1 and
            isinstance(records[0], netsgiro.TransactionAmountItem3)):
        return records[0].text


def parse(data: str) -> Transmission:
    records = netsgiro.get_records(data)
    return Transmission.from_records(records)
