# -*- coding: utf-8 -*-
"""
app.py
------
Flask application factory and main server entry point.
"""
from __future__ import annotations

import logging
import os
from pathlib import Path

from dotenv import load_dotenv
from flask import Flask, jsonify
from flask_cors import CORS



# Load environment configuration
load_dotenv()
from backend.routes.api import api_bp
logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s [%(levelname)s] %(name)s: %(message)s",
    datefmt="%H:%M:%S",
)
log = logging.getLogger("flood_backend")


def create_app() -> Flask:
    app = Flask(__name__)
    secret_key = os.getenv("SECRET_KEY")
    if not secret_key:
        raise RuntimeError("SECRET_KEY environment variable is required")
    app.config["SECRET_KEY"] = secret_key
    app.config["JSON_SORT_KEYS"] = False

    # Enable CORS for frontend origin
    frontend_origin = os.getenv("FRONTEND_ORIGIN", "http://localhost:5173")
    CORS(app, resources={r"/api/*": {"origins": [frontend_origin, "http://localhost:3000", "http://127.0.0.1:5173"]}})

    # Register blueprints
    app.register_blueprint(api_bp)

    @app.errorhandler(404)
    def not_found(e):
        return jsonify({"error": "Resource not found", "code": "NOT_FOUND"}), 404

    @app.errorhandler(500)
    def server_error(e):
        log.error("Internal server error: %s", e)
        return jsonify({"error": "Internal server error occurred", "code": "SERVER_ERROR"}), 500

    return app


if __name__ == "__main__":
    port = int(os.getenv("FLASK_PORT", 5000))
    app = create_app()
    log.info("Starting Flood Vulnerability API backend on port %d...", port)
    app.run(host="0.0.0.0", port=port, debug=False)
app = create_app()
