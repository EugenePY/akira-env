from enum import Enum
from .fields import EnumType, ParseEnum


class SymbolEnum(ParseEnum):
    EUR = "EUR"

    USD = "USD"
    DXY = USD

    GBP = "GBP"
    CHF = "CHF"
    NZD = "NZD"
    AUD = "AUD"
    CAD = "CAD"

    TWD = "TWD"
    NTN = "TWD"

    JPY = "JPY"
    IDR = "IDR"
    INR = "INR"
    CNH = "CNH"
    CNY = "CNY"
    SGD = "SGD"

    KRW = "KRW"
    KWN = KRW

    THB = "THB"

    MXN = "MXN"
    HUF = "HUF"
    SEK = "SEK"
    ZAR = "ZAR"
    ARS = "ARS"
    BRL = "BRL"
    PLN = "PLN"
    RUB = "RUB"
    MYR = "MYR"
    VND = "VND"
    PHP = "PHP"
    NOK = "NOK"