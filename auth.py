from functools import wraps
from datetime import datetime, timedelta, timezone

import jwt
from flask import Blueprint, request, jsonify, current_app

from extensions import db
from models import User

auth_bp = Blueprint("auth", __name__, url_prefix="/api/auth")


def generate_token(user):
    payload = {
        "user_id": user.id,
        "exp": datetime.now(timezone.utc)
        + timedelta(hours=current_app.config["JWT_EXP_HOURS"]),
    }
    return jwt.encode(payload, current_app.config["SECRET_KEY"], algorithm="HS256")


def token_required(view_func):
    """Protects a route: requires a valid 'Authorization: Bearer <token>' header.

    On success, the logged-in User is passed as the first argument to the
    wrapped view (so routes look like `def list_tasks(current_user): ...`).
    """

    @wraps(view_func)
    def wrapper(*args, **kwargs):
        auth_header = request.headers.get("Authorization", "")

        if not auth_header.startswith("Bearer "):
            return jsonify({"error": "Missing or malformed authorization header"}), 401

        token = auth_header.split(" ", 1)[1]

        try:
            payload = jwt.decode(
                token, current_app.config["SECRET_KEY"], algorithms=["HS256"]
            )
        except jwt.ExpiredSignatureError:
            return jsonify({"error": "Token has expired, please log in again"}), 401
        except jwt.InvalidTokenError:
            return jsonify({"error": "Invalid token"}), 401

        current_user = User.query.get(payload["user_id"])
        if current_user is None:
            return jsonify({"error": "User no longer exists"}), 401

        return view_func(current_user, *args, **kwargs)

    return wrapper


@auth_bp.route("/register", methods=["POST"])
def register():
    data = request.get_json(silent=True) or {}
    username = (data.get("username") or "").strip()
    email = (data.get("email") or "").strip().lower()
    password = data.get("password") or ""

    if not username or not email or not password:
        return jsonify({"error": "Username, email and password are all required"}), 400

    if len(password) < 6:
        return jsonify({"error": "Password must be at least 6 characters long"}), 400

    if User.query.filter_by(username=username).first():
        return jsonify({"error": "That username is already taken"}), 409

    if User.query.filter_by(email=email).first():
        return jsonify({"error": "That email is already registered"}), 409

    user = User(username=username, email=email)
    user.set_password(password)
    db.session.add(user)
    db.session.commit()

    token = generate_token(user)
    return jsonify({"token": token, "user": user.to_dict()}), 201


@auth_bp.route("/login", methods=["POST"])
def login():
    data = request.get_json(silent=True) or {}
    identifier = (data.get("username") or data.get("email") or "").strip()
    password = data.get("password") or ""

    if not identifier or not password:
        return jsonify({"error": "Username/email and password are required"}), 400

    user = User.query.filter(
        (User.username == identifier) | (User.email == identifier.lower())
    ).first()

    if user is None or not user.check_password(password):
        return jsonify({"error": "Invalid credentials"}), 401

    token = generate_token(user)
    return jsonify({"token": token, "user": user.to_dict()}), 200


@auth_bp.route("/logout", methods=["POST"])
@token_required
def logout(current_user):
    # The API is stateless (JWT), so there is no server-side session to end.
    # The real logout step is the frontend deleting its stored token; this
    # endpoint exists so the frontend has a clear, symmetrical call to make.
    return jsonify({"message": "Logged out successfully"}), 200


@auth_bp.route("/me", methods=["GET"])
@token_required
def me(current_user):
    return jsonify({"user": current_user.to_dict()}), 200
