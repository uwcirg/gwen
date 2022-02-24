import requests
from flask import Blueprint, abort, current_app, jsonify, request
from flask.json import JSONEncoder
from gwen.models.scrub import scrub_input

base_blueprint = Blueprint("base", __name__, cli_group=None)


@base_blueprint.route("/")
def root():
    return {"message": "ok"}


@base_blueprint.route("/settings", defaults={"config_key": None})
@base_blueprint.route("/settings/<string:config_key>")
def config_settings(config_key):
    """Non-secret application settings"""

    # workaround no JSON representation for datetime.timedelta
    class CustomJSONEncoder(JSONEncoder):
        def default(self, obj):
            return str(obj)

    current_app.json_encoder = CustomJSONEncoder

    # return selective keys - not all can be be viewed by users, e.g.secret key
    blacklist = ("SECRET", "KEY")

    if config_key:
        key = config_key.upper()
        for pattern in blacklist:
            if pattern in key:
                abort(status_code=400, messag=f"Configuration key {key} not available")
        return jsonify({key: current_app.config.get(key)})

    settings = {}
    for key in current_app.config:
        matches = any(pattern for pattern in blacklist if pattern in key)
        if matches:
            continue
        settings[key] = current_app.config.get(key)

    return jsonify(settings)


@base_blueprint.route("/events")
def scrub_events():
    """request events and scrub before returning"""
    response = requests.get(current_app.config["LOGSERVER_URL"] + "/events")
    response.raise_for_status()

    clean_data, scrub_map = scrub_input(response.json())

    # Hide the scrub_map unless specifically requested
    if "map" not in request.args:
        return jsonify(clean_data)

    return jsonify(clean_data=clean_data, scrub_map=scrub_map)
