# Copyright 2026 Taylor St Jean

from flask import Flask, render_template

from heimdall_neo import __version__
from heimdall_neo.mpc import NEOCPService


def create_app() -> Flask:
    app = Flask(__name__)
    service = NEOCPService()

    @app.get("/")
    def index():
        snapshot, diffs = service.get()
        return render_template("index.html", version=__version__, snapshot=snapshot, diffs=diffs)

    return app
