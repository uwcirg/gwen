from flask import Flask
from werkzeug.middleware.proxy_fix import ProxyFix

from gwen.views import base_blueprint


def create_app(testing=False, cli=False):
    """Application factory, used to create application"""
    app = Flask("gwen")
    app.config.from_object("gwen.config")
    app.config["TESTING"] = testing

    register_blueprints(app)
    configure_proxy(app)

    return app


def register_blueprints(app):
    """register all blueprints for application"""
    app.register_blueprint(base_blueprint)


def configure_proxy(app):
    """Add werkzeug fixer to detect headers applied by upstream reverse proxy"""
    if app.config.get("PREFERRED_URL_SCHEME", "").lower() == "https":
        app.wsgi_app = ProxyFix(
            app=app.wsgi_app,
            # trust X-Forwarded-Host
            x_host=1,
            # trust X-Forwarded-Port
            x_port=1,
        )
