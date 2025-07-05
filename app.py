#______________________________________________________________________________
from uuid import uuid4
from flask import Flask, request, jsonify, Response
from flask_cors import CORS
from bs_classes import Current_Board, Piece, Square
from typing import List, Tuple
import copy
import os


app = Flask(__name__)
CORS(app, origins=["http://localhost:5173"])

games = {}
GRID_SIZE = 10

def square_to_dict(sq: Square) -> dict:
	return {
		"coords": sq.coords,
		"shot": sq.shot,
		"hit": sq.hit,
		"sunk": sq.sunk
	}

@app.route("/new_game", methods=["POST"])
def new_game() -> Response:
	game_id = str(uuid4())
	pieces = [Piece(5, 1), Piece(4, 1), Piece(3, 2), Piece(2, 1)]
	squares = [
		[Square((r, c), shot=False) for c in range(GRID_SIZE)]
		for r in range(GRID_SIZE)
	]
	board = Current_Board(pieces, squares, GRID_SIZE)
	games[game_id] = {"history": [], "current": board}
	return jsonify({"game_id": game_id})

@app.route("/board", methods=["GET"])
def get_board() -> Response:
	game_id = request.args.get("game_id")
	if not game_id or game_id not in games:
		return jsonify({"error": "Invalid or missing game_id"}), 400
	board = games[game_id]["current"]
	grid = [
		[square_to_dict(sq) for sq in row]
		for row in board.squares
	]
	scores = [
		[
			board.get_total_score((r, c)) 
			if not board.squares[r][c].shot else None
			for c in range(GRID_SIZE)
		]
		for r in range(GRID_SIZE)
	]
	return jsonify({"grid": grid, "scores": scores})

@app.route("/shoot", methods=["POST"])
def shoot() -> Response:
	data = request.get_json(force=True)
	game_id = data.get("game_id")
	if not game_id or game_id not in games:
		return jsonify({"error": "Invalid or missing game_id"}), 400
	board = games[game_id]["current"]
	games[game_id]["history"].append(copy.deepcopy(board))
	row, col = tuple(data["coords"])
	if board.squares[row][col].shot:
		return jsonify({"error": "Selected square already shot"}), 400
	hit = data["hit"]
	sunk = data.get("sunk")
	board.squares[row][col].shoot(hit, sunk=sunk)
	sunk_coords = data.get("sunk_coords", [])
	if sunk and sunk_coords:
		for r, c in sunk_coords:
			if not board.squares[r][c].hit:
				return jsonify(
					{"error": "All sunk squares must already be hits"}
				), 400
		rows = [r for r, _ in sunk_coords]
		cols = [c for _, c in sunk_coords]
		if not (
			all(r == rows[0] for r in rows) or all(c == cols[0] for c in cols)
		):
			return jsonify(
				{"error": "Sunk squares must be in a straight line"}
			), 400
		if all(r == rows[0] for r in rows):
			col_range = sorted(cols)
			if col_range != list(range(min(cols), max(cols)+1)):
				return jsonify({"error": "Sunk squares must be adjacent"}), 400
		else:
			row_range = sorted(rows)
			if row_range != list(range(min(rows), max(rows)+1)):
				return jsonify({"error": "Sunk squares must be adjacent"}), 400
		sunk_size = len(sunk_coords)
		for piece in board.pieces:
			if piece.size == sunk_size and piece.qty > 0:
				piece.qty -= 1
				break
		else:
			return jsonify(
				{"error": f"No remaining pieces of size {sunk_size}"}
			), 400
		for r, c in sunk_coords:
			board.squares[r][c].sunk = True
	return jsonify({"message": "Shot recorded successfully."})

@app.route("/undo", methods=["POST"])
def undo() -> Response:
	data = request.get_json(force=True)
	game_id = data.get("game_id")
	if not game_id or game_id not in games:
		return jsonify({"error": "Invalid or missing game_id"}), 400
	game = games[game_id]
	if not game["history"]:
		return jsonify({"error": "Nothing to undo"}), 400
	game["current"] = game["history"].pop()
	return jsonify({"message": "Undo successful"})

if __name__ == "__main__":
	port = int(os.environ.get("PORT", 10000))
	app.run(host="0.0.0.0", port=port)