import json
import os
from pytest import fixture
from gwen.models.scrub import ScrubMap, scrub_input


class MockResponse(object):
    """Wrap data in response like object"""

    def __init__(self, data, status_code=200):
        self.data = data
        self.status_code = status_code

    def json(self):
        return self.data

    def raise_for_status(self):
        if self.status_code == 200:
            return
        raise Exception("status code ain't 200")


def load_jsondata(datadir, filename):
    with open(os.path.join(datadir, filename), "r") as jsonfile:
        data = json.load(jsonfile)
    return data


@fixture
def events_w_patients_data(datadir):
    return load_jsondata(datadir, "events-containing-patients.json")


def test_dob_patterns():
    sm = ScrubMap()
    sm.clean("eq1999-10-12")
    assert "1999" in sm.map.values()
    sm.clean("1999-10-12")
    assert len(sm.map) == 1


def test_name_case():
    sm = ScrubMap()
    upper_hash = sm.clean("NaMe")
    lower_hash = sm.clean("name")
    assert upper_hash == lower_hash
    assert len(sm.map) == 1


def test_names_extra_whitespace():
    full_name = "first  last"
    sm = ScrubMap()
    full_hash = sm.clean(full_name)
    tokenized = []
    for i in ("first", " ", "last"):
        tokenized.append(sm.clean(i))

    assert full_hash == " ".join(tokenized)


def test_tokenized_name():
    full_name = "first last"
    sm = ScrubMap()
    full_hash = sm.clean(full_name)
    first = sm.clean("first")
    last = sm.clean("last")
    assert f"{first} {last}" == full_hash
    assert full_hash == sm.clean("FiRST LaSt")


def test_scrub(events_w_patients_data):
    clean_data, scrub_map = scrub_input(events_w_patients_data)
    assert "marcus" not in json.dumps(clean_data)
    assert "marcus aurelius" not in json.dumps(clean_data)
    assert "Marcus Aurelius" not in json.dumps(clean_data)
    assert "1975-06-17" not in json.dumps(clean_data)
    assert len(clean_data) == len(events_w_patients_data)
