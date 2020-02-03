import sqlalchemy as sa
import sqlalchemy_jsonfield
import json


class Challenge(Base):
    __tablename__ = "challenge"
    id = sa.Column(primary_key=True)
    title = sa.Column(sa.String)
    doc = sa.Column(sa.String)
    specs = sa.Column(sqlalchemy_jsonfield.JSONField(
        json=json), nullable=False)
