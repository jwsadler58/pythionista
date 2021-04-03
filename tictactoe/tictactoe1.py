from scene import *
import random
import sound
import ui
from menu import MenuScene

A = Action

# TicTacToe basics
# The board is numbered
#		1 2 3
#		4 5 6
#		7 8 9
# and represented as a list of length 10, where the zeroth entry is unused to simplify notation
# where 0 is an empty square, 1 is a computer-held square, and -1 is a player-held square
# using this convention you can add up the values of the squares in a row, col, of diag to determine 
# whether there is a win (+3), a loss (-3), or a threat (2 of 3 occupied)

class TTT:
	# Tuple of all winning tictactoes, ordered so as to favor stronger moves
	# by the heuristic in my_moves
	wins = ((5,1,9), (5,3,7), (5,2,8), (5,4,6), (1,3,2), (7,9,8), (1,7,4), (3,9,6))
	
	def __init__(self):
		self.board = [0 for i in range(10)]		# board[0] is ignored to match human and computer notation
		self.turn = random.choice([self.my_move, self.your_move])
		self.n_moves = 0
		self.status = ''
		self.check_board()		# create self.threats 
		
	def check_board(self):
		''' Check board for wins, return True if game is still on, False if it’s over.
		'''
		r = []
		for line in self.wins:
			t = self.board[line[0]] + self.board[line[1]] + self.board[line[2]]
			r.append(t)
		
		self.threats = r
	
		if 3 in r:		# Program wins
			self.game_over('win')
			return False
		elif -3 in r:	# player wins
			self.game_over('lose')
			return False
		elif self.n_moves > 8:
			self.game_over('draw')
			return False
		else:
			return True
		
	def game_over(self, outcome):
		if outcome == 'win':
			self.status = 'I crush you!'
		elif outcome == 'lose':
			self.status = 'You win'
		else:
			self.status = 'Tie Game'
			
	def my_move(self):
		''' Choose move heuristically and return it.
		
		First move: pick corner or center at random. 
		Subsequent moves:
		(Strategy denotes order of lines to target from threat vector)
		> First try to win (2)
		> Then try to block a loss (-2)
		> Then try to threaten a win (1)
		> Then try to block player’s threat
		> If all else fails choose an open tile at random
		'''
		assert self.status == ''
		# set a sentinel value so we can tell whether a move has been selected
		m = -1
		# first move is a random choice among the "good" tiles
		if self.n_moves == 0:
			m = random.choice((1, 3, 5, 7, 9, 5))
		else:
			strategy = (2, -2, 1, -1)
			for tol in strategy:
				if tol in self.threats:  # Get all threat lines that match the criterion
					lines = []
					for i in range(len(self.threats)):
						if self.threats[i] == tol:
							lines.append(i)
					if len(lines) == 0:
						continue
					i = random.choice(lines)
					line = self.wins[i]
					moves = []
					for j in line:				# choose an empty tile
						if self.board[j] == 0:
							moves.append(j)
					if len(moves) > 0:
						m = random.choice(moves)
						break
		# if we still don’t have a selection, choose among the open tiles
		# in this order: center, corners, then edges
		if m == -1:
			opens = [i for i in range(1, 10) if self.board[i] == 0]
			for tm in (5, 1, 3, 9, 7, 2, 4, 6, 8):
				if tm in opens:
					m = tm
					break
		
		# We must have chosen a move by now - otherwise the game was already over
		assert m != -1
		self.board[m] = 1
		self.n_moves += 1
		self.turn = self.your_move
		return m
	
	def your_move(self, m):
		opens = [i for i in range(1, 10) if self.board[i] == 0]
		if m not in opens:
			return False

		self.board[m] = -1 # grab the selected tile for the player
		self.n_moves += 1
		self.turn = self.my_move
		return True

#
# This is the graphical part of the game
#
class MyScene (Scene):
	def setup(self):
		self.background_color = '#9e9e9e'
		board_color =	'#4f372e'
		# Size the board to fit the tiles with a gap on all sides
		# use the centerpoint of the display as the origin for placing the tiles
		# Node origins seem to default to their centerpoints, so this simplifies the math
		l_tile = self.l_tile = 128
		gap = self.gap = 16
		l_board = (3 * l_tile) + (4 * gap)

		board_shape = ui.Path.rounded_rect(0, 0, l_board, l_board, l_tile/6)
		self.board = ShapeNode(path=board_shape, parent=self)
		self.board.fill_color = board_color
		self.board.size = (l_board, l_board)
		self.board.position = self.size/2
		
		self.run_action(A.sequence(A.wait(0.5), A.call(self.show_start_menu)))
	
	def new_game(self):
		self.ttt = TTT()
		tile_color =	'#b3baff'
		l_tile = self.l_tile
		gap = self.gap
		# insert tiles onto board in order from top left to bottom right, row major order
		# so that the order they appear in <tiles> matches the convention in the TicTacToe class
		self.tiles = []
		index = 1
		for row in range(1, -2, -1):
			for col in range(-1, 2):
				tile_shape = ui.Path.rounded_rect(0, 0, l_tile, l_tile, l_tile/8)
				tile = ShapeNode(path=tile_shape, parent=self.board)
				tile.size = (l_tile, l_tile)
				tile.position = (col * (l_tile + gap), row * (l_tile + gap))
				tile.fill_color = tile_color
				tile.index = index
				label = LabelNode(' ', font=('Marker Felt', l_tile/2), parent=tile)
				label.color = '#1e1e1e'
				self.tiles.append(tile)
				index += 1

		sound.play_effect('digital:ZapThreeToneUp')
				
		if self.ttt.turn == self.ttt.my_move:
			move = self.ttt.my_move()
			self.tiles[move-1].children[0].text = 'O'
			self.ttt.check_board()		
	
	def did_change_size(self):
		self.board.position = self.size/2
	
	def update(self):
		pass
	
	def touch_began(self, touch):
		touch_loc = self.board.point_from_scene(touch.location)
		for tile in self.tiles:
			if touch_loc in tile.frame:
				if self.ttt.your_move(tile.index):
					tile.children[0].text = 'X'
					tile.children[0].alpha = 0.1
					sound.play_effect('game:Woosh_1')
					tile.children[0].run_action(A.fade_to(1.0, 0.3))
				else:
					sound.play_effect('game:Error')
					tile.children[0].run_action(A.sequence(A.move_by(8,0,0.03), A.move_by(-16,0,0.06), A.move_by(16,0,0.06), A.move_by(-8,0,0.03)))
		
	def touch_moved(self, touch):
		pass
	
	def touch_ended(self, touch):
		# check for a human win before making a move
		if not self.ttt.check_board():
			if -3 in self.ttt.threats:
				# highlight the winning squares
				i = self.ttt.threats.index(-3)
				line = self.ttt.wins[i]
				for t in line:
					self.tiles[t-1].fill_color = '#49f825'
			self.run_action(A.sequence(A.wait(1), A.call(self.show_end_menu)))
		elif (self.ttt.turn == self.ttt.my_move):
			move = self.ttt.my_move()
			textnode = self.tiles[move-1].children[0]
			textnode.text = 'O'
			textnode.alpha = 0.1
			sound.play_effect('drums:Drums_12')
			textnode.run_action(A.fade_to(1.0, 0.3))
			if not self.ttt.check_board():
				if 3 in self.ttt.threats:
					# highlight the winning squares
					i = self.ttt.threats.index(3)
					line = self.ttt.wins[i]
					for t in line:
						self.tiles[t-1].fill_color = '#f86088'
				self.run_action(A.sequence(A.wait(1), A.call(self.show_end_menu)))
					
	def menu_button_selected(self, title):
		if title == 'New Game':
			self.dismiss_modal_scene()
			self.menu = None
			self.paused = False
			self.new_game()
	
	def show_start_menu(self):
		self.paused = True
		self.menu = MenuScene('TicTacToe', '', ['New Game'])
		self.present_modal_scene(self.menu)
	
	def show_end_menu(self):
		sound.play_effect('arcade:Laser_4')
		self.paused = True
		self.menu = MenuScene('Game Over', self.ttt.status, ['New Game'])
		self.present_modal_scene(self.menu)
	
if __name__ == '__main__':
	run(MyScene(), show_fps=False)
