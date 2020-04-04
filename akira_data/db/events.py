from marshmallow_mongoengine import ModelSchema
import mongoengine as me
from marshmallow import fields
from .db_model import Model
from .fields import EnumType
from .currency import SymbolEnum
from enum import Enum
from .fields import ParseEnum

COUNTRY_ID = {
    'AU': 25,
    'CA': 6,
    'CN': 37,
    'DE': 17,
    'FR': 22,
    'IT': 10,
    'JP': 35,
    'SE': 9,
    'NZ': 43,
    'GB': 4,
    'US': 5,
    'EZ': 72,
    'EU': 72,
    'KR': 11,
    'TW': 46,
    'TH': 41,
    'Argentina': 29,
    'Australia': 25,
    'Austria': 54,
    'Bahrain': 145,
    'Bangladesh': 47,
    'Belgium': 34,
    'Bosnia-Herzegovina': 174,
    'Botswana': 163,
    'Brazil': 32,
    'Bulgaria': 70,
    'Canada': 6,
    'Chile': 27,
    'China': 37,
    'Colombia': 122,
    'Costa Rica': 15,
    "Cote D'Ivoire": 78,
    'Croatia': 113,
    'Cyprus': 107,
    'Czech Republic': 55,
    'Denmark': 24,
    'Ecuador': 121,
    'Egypt': 59,
    'Estonia': 89,
    'Euro Zone': 72,
    "EU": 72,
    'Europe': 72,
    'Finland': 71,
    'France': 22,
    'Germany': 17,
    'Greece': 51,
    'Hong Kong': 39,
    'Hungary': 93,
    'Iceland': 106,
    'India': 14,
    'Indonesia': 48,
    'Iraq': 66,
    'Ireland': 33,
    'Israel': 23,
    'Italy': 10,
    'Jamaica': 119,
    'Japan': 35,
    'Jordan': 92,
    'Kazakhstan': 102,
    'Kenya': 57,
    'Kuwait': 94,
    'Latvia': 97,
    'Lebanon': 68,
    'Lithuania': 96,
    'Luxembourg': 103,
    'Malawi': 111,
    'Malaysia': 42,
    'Malta': 109,
    'Mauritius': 188,
    'Mexico': 7,
    'Mongolia': 139,
    'Montenegro': 247,
    'Morocco': 105,
    'Namibia': 172,
    'Netherlands': 21,
    'New Zealand': 43,
    'Nigeria': 20,
    'Norway': 60,
    'Oman': 87,
    'Pakistan': 44,
    'Palestinian Territory': 193,
    'Peru': 125,
    'Philippines': 45,
    'Poland': 53,
    'Portugal': 38,
    'Qatar': 170,
    'Romania': 100,
    'Russia': 56,
    'Rwanda': 80,
    'Saudi Arabia': 52,
    'Serbia': 238,
    'Singapore': 36,
    'Slovakia': 90,
    'Slovenia': 112,
    'South Africa': 110,
    'South Korea': 11,
    'Spain': 26,
    'Sri Lanka': 162,
    'Sweden': 9,
    'Switzerland': 12,
    'Taiwan': 46,
    'Tanzania': 85,
    'Thailand': 41,
    'Tunisia': 202,
    'Turkey': 63,
    'Uganda': 123,
    'Ukraine': 61,
    'United Arab Emirates': 143,
    'United Kingdom': 4,
    'United States': 5,
    'Venezuela': 138,
    'Vietnam': 178,
    'Zambia': 84,
    'Zimbabwe': 75}


CountryCode = ParseEnum("CountryCode", COUNTRY_ID, module=__name__)

# County and Symbol mapping

COUNTRY2SYMBOL = {CountryCode.AU: SymbolEnum.AUD,
                  CountryCode.CA: SymbolEnum.CAD,
                  CountryCode.EZ: SymbolEnum.EUR,
                  CountryCode.DE: SymbolEnum.EUR,
                  CountryCode.IT: SymbolEnum.EUR,
                  CountryCode.JP: SymbolEnum.JPY,
                  CountryCode.FR: SymbolEnum.EUR,
                  CountryCode.GB: SymbolEnum.EUR,
                  CountryCode.US: SymbolEnum.USD,
                  CountryCode.CN: SymbolEnum.CNH,
                  CountryCode.NZ: SymbolEnum.NZD,
                  CountryCode.SE: SymbolEnum.CHF,
                  CountryCode.TW: SymbolEnum.TWD,
                  CountryCode.Thailand: SymbolEnum.THB,
                  CountryCode.KR: SymbolEnum.KRW}


class EcoEvent(me.Document):
    event_id = me.IntField()
    index = me.DateTimeField()
    name = me.StringField()
    row_id = me.IntField()
    country = me.StringField()
    vol = me.StringField()
    release = me.StringField()
    forecast = me.StringField(null=True)
    previous = me.StringField(null=True)
    revised = me.StringField(null=True)

    def __repr__(self):
        return '< EcoEvent(id={self.id!r}, event_id={self.event_id!r},'\
            ' name={self.name!r}, country={self.country!r}) >'.format(self=self)


class EcoEventSchema(ModelSchema):
    class Meta:
        model = EcoEvent

    country = EnumType(CountryCode)
    index = fields.DateTime(format="%Y/%m/%d %H:%M:%S")

    def from_investing_data(self, event):
        out = {}
        out["event_id"] = event["event_attr_id"]
        out["row_id"] = event["id"].replace("eventRowId_", "")
        out["name"] = " ".join(list(event.find_all('td')[3])[0].text.split())
        out["index"] = event["data-event-datetime"]
        out["country"] = list(event.find_all('td')[1])[0]["title"]
        out["vol"] = event.find_all('td')[2]["title"]
        out["release"] = "".join(event.find_all('td')[4].text.split())
        forecast = "".join(event.find_all('td')[5].text.split())

        if len(forecast) > 0:
            out["forecast"] = forecast
        else:
            out["forecast"] = None

        out["previous"] = "".join(
            list(event.find_all('td')[6])[0].text.split())
        if len(list(event.find_all('td')[6])[0]["title"]) > 0:
            out["revised"] = list(event.find_all('td')[6]
                                  )[0]["title"].replace("Revised From ", "")
        else:
            out["revised"] = None
        return self.load(out)
