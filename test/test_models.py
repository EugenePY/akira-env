import pytest

import sqlalchemy as sa
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy.orm import scoped_session, sessionmaker, relationship, backref
from akira_test.models.env import Experiment, ExperimentSchema, BaseEnv
from akira_test.models.base import Base

engine = sa.create_engine("sqlite:///:memory:")
session = scoped_session(sessionmaker(bind=engine))
Base.metadata.create_all(engine)

@pytest.fixture
def exp_data():
    exp_data = {"env": "basket",
                "owner": "eugenepy",
                "model": "bmk"}
    return exp_data


def test_experment_load_dump(exp_data):
    schema = ExperimentSchema()
    instance = schema.load(exp_data, session=session)
    assert issubclass(instance.env, BaseEnv)
    assert schema.dump(instance)["env"] == exp_data["env"]
    print(dir(instance))
    session.add(instance)
    session.commit()