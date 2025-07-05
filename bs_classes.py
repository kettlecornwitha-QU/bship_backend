#______________________________________________________________________________
from typing import Tuple, Optional, List


class Square:
	def __init__(
		self, 
		coords: Tuple[int, int], 
		shot: bool, 
		*, 
		hit: Optional[bool] = None, 
		sunk: Optional[bool] = None
	) -> None:
		self.coords = coords
		self.shot = shot
		self.hit = hit
		self.sunk = sunk

	def shoot(self, hit: bool, *, sunk: Optional[bool]) -> None:
		self.shot = True
		self.hit = hit
		self.sunk = sunk


class Piece:
	def __init__(self, size: int, qty: int) -> None:
		self.size = size
		self.qty = qty


class Current_Board:
	def __init__(
		self, pieces: List[Piece], squares: List[List[Square]], grid_size: int
	) -> None:
		self.pieces = pieces
		self.squares = squares
		self.grid_size = grid_size

	def in_bounds(self, row: int, col: int) -> bool:
		return 0 <= row < self.grid_size and 0 <= col < self.grid_size

	def get_clearance(self, coords: Tuple[int, int], direction: str) -> int:
		dir_map = {
			'L': (0, -1), 
			'R': (0, 1), 
			'U': (1, 0), 
			'D': (-1, 0)
		}
		row_dif, col_dif = dir_map[direction]
		row = coords[0] + row_dif
		col = coords[1] + col_dif
		clearance = 0
		if not self.in_bounds(row, col):
			return clearance
		while self.squares[row][col].shot == False:
			clearance += 1
			row += row_dif
			col += col_dif
			if not self.in_bounds(row, col):
				return clearance
		return clearance

	def get_spec_score(self, coords: Tuple[int, int], ship_size: int) -> int:
		directions = ('L', 'R', 'U', 'D')
		legs = {}
		for direction in directions:
			legs[direction] = self.get_clearance(coords, direction)
		score = 0
		if legs['L'] + legs['R'] + 1 >= ship_size:
			score += min(legs['L'], legs['R'], ship_size)
		if legs['U'] + legs['D'] + 1 >= ship_size:
			score += min(legs['U'], legs['D'], ship_size)
		return score

	def get_total_score(self, coords: Tuple[int, int]) -> int:
		current_sizes = [piece.size for piece in self.pieces if piece.qty > 0]
		return sum(self.get_spec_score(coords, size) for size in current_sizes)