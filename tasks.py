from datetime import datetime

from flask import Blueprint, request, jsonify

from extensions import db
from models import Task, TASK_STATUSES, TASK_PRIORITIES
from auth import token_required

tasks_bp = Blueprint("tasks", __name__, url_prefix="/api/tasks")


def parse_due_date(value):
    """Returns a date object from an 'YYYY-MM-DD' string, or None."""
    if not value:
        return None
    try:
        return datetime.strptime(value, "%Y-%m-%d").date()
    except ValueError:
        return "INVALID"


def validate_task_fields(data, partial=False):
    """Checks title/status/priority/due_date. Returns an error string, or None if valid."""
    if not partial or "title" in data:
        if not (data.get("title") or "").strip():
            return "Task title cannot be empty"

    if not partial or "status" in data:
        if data.get("status", TASK_STATUSES[0]) not in TASK_STATUSES:
            return f"Status must be one of: {', '.join(TASK_STATUSES)}"

    if not partial or "priority" in data:
        if data.get("priority", TASK_PRIORITIES[1]) not in TASK_PRIORITIES:
            return f"Priority must be one of: {', '.join(TASK_PRIORITIES)}"

    if data.get("due_date") and parse_due_date(data["due_date"]) == "INVALID":
        return "due_date must be in YYYY-MM-DD format"

    return None


@tasks_bp.route("", methods=["GET"])
@token_required
def list_tasks(current_user):
    query = Task.query.filter_by(owner_id=current_user.id)

    status = request.args.get("status")
    if status:
        if status not in TASK_STATUSES:
            return jsonify({"error": f"Status must be one of: {', '.join(TASK_STATUSES)}"}), 400
        query = query.filter_by(status=status)

    priority = request.args.get("priority")
    if priority:
        if priority not in TASK_PRIORITIES:
            return jsonify({"error": f"Priority must be one of: {', '.join(TASK_PRIORITIES)}"}), 400
        query = query.filter_by(priority=priority)

    search = request.args.get("search")
    if search:
        query = query.filter(Task.title.ilike(f"%{search}%"))

    tasks = query.order_by(Task.created_at.desc()).all()
    return jsonify({"tasks": [t.to_dict() for t in tasks]}), 200


@tasks_bp.route("/stats", methods=["GET"])
@token_required
def task_stats(current_user):
    tasks = Task.query.filter_by(owner_id=current_user.id).all()
    stats = {"total": len(tasks), "Pending": 0, "In Progress": 0, "Completed": 0}
    for t in tasks:
        stats[t.status] = stats.get(t.status, 0) + 1
    return jsonify({"stats": stats}), 200


@tasks_bp.route("", methods=["POST"])
@token_required
def create_task(current_user):
    data = request.get_json(silent=True) or {}

    error = validate_task_fields(data)
    if error:
        return jsonify({"error": error}), 400

    task = Task(
        title=data["title"].strip(),
        description=(data.get("description") or "").strip(),
        status=data.get("status", TASK_STATUSES[0]),
        priority=data.get("priority", TASK_PRIORITIES[1]),
        due_date=parse_due_date(data.get("due_date")),
        owner_id=current_user.id,
    )
    db.session.add(task)
    db.session.commit()
    return jsonify({"task": task.to_dict()}), 201


def get_owned_task_or_error(task_id, current_user):
    """Returns (task, None) on success, or (None, (json_response, status)) on failure."""
    task = Task.query.get(task_id)
    if task is None:
        return None, (jsonify({"error": "Task not found"}), 404)
    if task.owner_id != current_user.id:
        return None, (jsonify({"error": "You do not have access to this task"}), 403)
    return task, None


@tasks_bp.route("/<int:task_id>", methods=["GET"])
@token_required
def get_task(current_user, task_id):
    task, error = get_owned_task_or_error(task_id, current_user)
    if error:
        return error
    return jsonify({"task": task.to_dict()}), 200


@tasks_bp.route("/<int:task_id>", methods=["PUT", "PATCH"])
@token_required
def update_task(current_user, task_id):
    task, error = get_owned_task_or_error(task_id, current_user)
    if error:
        return error

    data = request.get_json(silent=True) or {}
    validation_error = validate_task_fields(data, partial=True)
    if validation_error:
        return jsonify({"error": validation_error}), 400

    if "title" in data:
        task.title = data["title"].strip()
    if "description" in data:
        task.description = (data["description"] or "").strip()
    if "status" in data:
        task.status = data["status"]
    if "priority" in data:
        task.priority = data["priority"]
    if "due_date" in data:
        task.due_date = parse_due_date(data["due_date"])

    db.session.commit()
    return jsonify({"task": task.to_dict()}), 200


@tasks_bp.route("/<int:task_id>", methods=["DELETE"])
@token_required
def delete_task(current_user, task_id):
    task, error = get_owned_task_or_error(task_id, current_user)
    if error:
        return error

    db.session.delete(task)
    db.session.commit()
    return jsonify({"message": "Task deleted"}), 200
