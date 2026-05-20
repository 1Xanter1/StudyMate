from flask import Flask, render_template, request, jsonify
from logic import TaskService, SessionService, FlashcardService, ProgressService
import database as db

app = Flask(__name__)
db.init_db()


@app.route("/")
def index():
    return render_template("index.html")


@app.route("/api/tasks", methods=["GET"])
def get_tasks():
    return jsonify(TaskService.get_all(request.args.get("sort", "deadline")))


@app.route("/api/tasks", methods=["POST"])
def create_task():
    return jsonify(TaskService.create(request.get_json())), 201


@app.route("/api/tasks/<int:task_id>", methods=["PUT"])
def update_task(task_id):
    result = TaskService.update(task_id, request.get_json())
    if not result:
        return jsonify({"error": "Not found"}), 404
    return jsonify(result)


@app.route("/api/tasks/<int:task_id>", methods=["DELETE"])
def delete_task(task_id):
    TaskService.delete(task_id)
    return jsonify({"ok": True})


@app.route("/api/tasks/<int:task_id>/toggle", methods=["POST"])
def toggle_task(task_id):
    result = TaskService.toggle(task_id)
    if not result:
        return jsonify({"error": "Not found"}), 404
    return jsonify(result)


@app.route("/api/sessions", methods=["GET"])
def get_sessions():
    return jsonify(SessionService.get_recent(request.args.get("limit", 20, type=int)))


@app.route("/api/sessions", methods=["POST"])
def create_session():
    return jsonify(SessionService.create(request.get_json())), 201


@app.route("/api/flashcards", methods=["GET"])
def get_flashcards():
    return jsonify(FlashcardService.get_all())


@app.route("/api/flashcards/review", methods=["GET"])
def get_review_cards():
    return jsonify(FlashcardService.get_due())


@app.route("/api/flashcards", methods=["POST"])
def create_flashcard():
    return jsonify(FlashcardService.create(request.get_json())), 201


@app.route("/api/flashcards/<int:card_id>", methods=["PUT"])
def update_flashcard(card_id):
    result = FlashcardService.update(card_id, request.get_json())
    if not result:
        return jsonify({"error": "Not found"}), 404
    return jsonify(result)


@app.route("/api/flashcards/<int:card_id>", methods=["DELETE"])
def delete_flashcard(card_id):
    FlashcardService.delete(card_id)
    return jsonify({"ok": True})


@app.route("/api/flashcards/<int:card_id>/review", methods=["POST"])
def review_flashcard(card_id):
    result = FlashcardService.review(card_id, request.get_json().get("correct", False))
    if not result:
        return jsonify({"error": "Not found"}), 404
    return jsonify(result)


@app.route("/api/progress", methods=["GET"])
def get_progress():
    return jsonify(ProgressService.get_stats())


if __name__ == "__main__":
    app.run(debug=True, port=5000)
