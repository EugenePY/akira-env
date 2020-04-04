import faust
import datetime
from faust.models import FieldDescriptor
from faust.exceptions import ValidationError
from typing import List, Any, Iterable
from uuid import UUID


class ChoiceField(FieldDescriptor[str]):

    def __init__(self, choices: List[str], **kwargs: Any) -> None:
        self.choices = choices
        # Must pass any custom args to init,
        # so we pass the choices keyword argument also here.
        super().__init__(choices=choices, **kwargs)

    def validate(self, value: str) -> Iterable[ValidationError]:
        if value not in self.choices:
            choices = ', '.join(self.choices)
            yield self.validation_error(
                f'{self.field} must be one of {choices}')


class ExecutedPrice(faust.Record):
    timestamp: datetime.datetime
    symbol: str
    tick_count: int
    execute_px: float
    time_zone: ChoiceField(["ASIA", "LONDON", "NEW_YORK"])
    method: ChoiceField(["MEAN"])


class Tick(faust.Record):
    timestamp: datetime.datetime
    symbol: str
    ask: float
    bid: float


class Order(faust.Record):

    SIDE_SELL = 'LONG'
    SIDE_BUY = 'SHORT'

    id: UUID 
    model_id: str
    side: ChoiceField([SIDE_SELL, SIDE_BUY])
    order_type:  ChoiceField(["MEAN"])
    symbol: str
    side: str
    amount: float
    price: ExecutedPrice = None

    # paper orders are not executed.
    paper_trade: bool = False

    testing: bool = False
