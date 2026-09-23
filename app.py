import os

from flask import Flask, send_from_directory, jsonify
from flask_cors import CORS

from config import Config
from extensions import db
from auth import auth_bp
from tasks import tasks_bp

FRONTEND_DIR = os.path.join(os.path.dirname(__file__), "frontend")


def create_app():
    app = Flask(__name__, static_folder=FRONTEND_DIR, static_url_path="")
    app.config.from_object(Config)

    # Allows the frontend to call this API even if it's ever served from a
    # different origin/port (e.g. a separate dev server) instead of by Flask.
    CORS(app)

    db.init_app(app)

    app.register_blueprint(auth_bp)
    app.register_blueprint(tasks_bp)

    # --- Frontend pages (plain static files, no template engine needed) ---
    @app.route("/")
    def index():
        return send_from_directory(FRONTEND_DIR, "index.html")

    @app.route("/<page>.html")
    def page(page):
        return send_from_directory(FRONTEND_DIR, f"{page}.html")

    # --- API error handlers (so the frontend always gets JSON, not HTML) ---
    @app.errorhandler(404)
    def not_found(e):
        return jsonify({"error": "Not found"}), 404

    @app.errorhandler(500)
    def server_error(e):
        return jsonify({"error": "Internal server error"}), 500

    return app


app = create_app()

if __name__ == "__main__":
    app.run(debug=True, port=5000)
