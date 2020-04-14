import faust
import datetime
from faust.models import FieldDescriptor
from faust.exceptions import ValidationError
from typing import List, Any, Iterable, Mapping, Optional
from uuid import UUID
from tzlocal import get_localzone
from dateutil.parser import parse as parse_date


def tz_parser(*args, default_tzinfo=get_localzone(), **kwargs):
    dt = parse_date(*args, **kwargs)
    return dt.replace(tzinfo=dt.tzinfo or default_tzinfo)


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
    window_start: datetime.datetime
    window_end: datetime.datetime
    symbol: str
    tick_count: int
    execute_px: float
    median: float
    std: float
    avg_spread: float
    method: ChoiceField(["MEAN"])


class CandleStick(faust.Record):
    px_last: float
    px_open: float
    px_high: float
    px_low: float


class Tick(faust.Record):
    timestamp: datetime.datetime
    symbol: str
    ask: float
    bid: float


class Order(faust.Record, coerce=True):

    SIDE_SELL = 'LONG'
    SIDE_BUY = 'SHORT'

    id: UUID
    model_id: str
    side: ChoiceField([SIDE_SELL, SIDE_BUY])
    agent_type:  ChoiceField(["MEAN"], default="MEAN")
    symbol: str
    amount: float

    # Default Value
    exec_price: ExecutedPrice = None
    timestmap: datetime.datetime = datetime.datetime.now()
    status: ChoiceField(["SUCCESS", "FAILED"]) = None
    msg: Mapping[str, str] = None
    # paper orders are not executed.
    paper_trade: bool = False
    testing: bool = False
