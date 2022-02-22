"""Scrub configured PHI"""
import jmespath
import json
import re

# birth year pattern - may include "eq" before YYYY-MM-DD
birth_year_pattern = re.compile(r"(eq)?(\d{4})-\d{2}-\d{2}")


def scrub_patient_object(data, scrub_map):
    """Return PHI scrubbed version of a patient object
    Example input:
      "patient": {
        "subject.id": "211",
        "subject:Patient.birthdate": "eq1975-06-17",
        "subject:Patient.name.given": "marcus",
        "subject:Patient.name.family": "aurelius"}
    """
    keys = (
        "subject:Patient.birthdate",
        "subject:Patient.name.given",
        "subject:Patient.name.family",
    )
    patient = data.copy()
    for key in keys:
        if key in patient:
            patient[key] = scrub_map.clean(patient[key])
    return patient


def scrub_patients(data, scrub_map):
    patients = jmespath.search("*.patient", data)
    if not patients:
        return data

    s_r = []
    for p_phi in patients:
        if not isinstance(p_phi, str):
            assert len(patients) == 1
            data["event"]["patient"] = scrub_patient_object(p_phi, scrub_map)
            break

        p_clean = scrub_map.clean(p_phi)
        s_r.append((p_phi, p_clean))

    transformed = json.dumps(data)
    for s, r in s_r:
        # Avoid replacing substrings that happen to match PHI - strictly match
        # the JSON output with strings wrapped in double quotes
        transformed = transformed.replace(f'"{s}"', f'"{r}"')
    return json.loads(transformed)


def scrub_input(data):
    """Scrub input data as configured

    :param data: incoming data with PHI, in JSON format
    :returns: clean_data, scrub_map tuple.  Clean data is the scrubbed version of input;
        Scrub map reports all scrubbed strings for debugging or reverse lookup - NOT PHI safe!
    """
    scrub_map = ScrubMap()
    results = []
    for item in data:
        results.append(scrub_patients(item, scrub_map))

    return results, scrub_map.map


class ScrubMap(object):
    """Maintains map of all scrubbed data

    Scrubbed data needs to follow a few rules, for example:
    - dates of YYYY-MM-DD format need to preserve the YYYY only
    - names separated by spaces should map consistently when tokenized,
      i.e. "first last" produces same as "first" + " " + "last"

    """

    def __init__(self):
        self.map = dict()

    def hash_string(self, value):
        """generates a human friendly (i.e. short) hash for a string"""
        # taking least sig digits isn't guaranteed unique - use more as needed
        digits = 2
        full_hash = str(hash(value))

        def first_letter(letter):
            if letter == " ":
                return "_"
            return letter

        while True:
            # maintain first letter and append needed len of hash to keep unique
            first = first_letter(value[0])
            hashed = first + full_hash[-digits:]
            if hashed not in self.map.values():
                return hashed
            digits += 1

    def clean(self, value):
        """generates a "clean" version of value, returning previously used if found"""
        if not value:
            return value

        # lowercase to generate same value for "Name" and "name"
        value = value.lower()
        dob_match = re.match(birth_year_pattern, value)
        if dob_match:
            # remove preceding 'eq' if present so YYYY-MM-DD generates same w/ and w/o
            if dob_match.groups()[0]:
                value = value[2:]

        if value not in self.map:
            if dob_match:
                self.map[value] = dob_match.groups()[1]
            elif " " in value:
                # split on whitespace, so patterns like "first_name last_name" will
                # consistently use same string for a given first_name
                tokens = value.split(" ")
                hashed_tokens = []
                for token in tokens:
                    # empty strings in tokens imply extra or embedded white space
                    # retain to map uniquely as needed
                    if token == "":
                        token = " "
                    if token not in self.map:
                        self.map[token] = self.hash_string(token)
                    hashed_tokens.append(self.map[token])

                self.map[value] = " ".join(hashed_tokens)
            else:
                self.map[value] = self.hash_string(value)

        return self.map[value]
