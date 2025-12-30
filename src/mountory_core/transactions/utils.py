from collections.abc import Collection

from mountory_core.transactions.models import Transaction
from mountory_core.users.types import UserId


def calc_transactions_total(
    transactions: Collection[Transaction],
    user_ids: Collection[UserId] | None = None,
) -> int:
    if not user_ids:
        _transactions = transactions
    else:
        _transactions = [t for t in transactions if t.user_id in user_ids]

    return sum(t.amount or 0 for t in _transactions)
