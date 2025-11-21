import copy
from random import randrange
from time import perf_counter

from Bots.bot_ai import BotAI
from Bots.data import PlayState

# TODO:
# [ ] project next move to not make a move that will give the opponent a winning move
# [ ] find possible winning (and losing) moves with 2 coins in a row

class StayinAlignAI(BotAI):
    def __init__(self):
        self.name = "StayinAlign"

    def play(self, state: PlayState):
        start = perf_counter()
        self._print_board(state.board)

        possible_moves = self.find_possible_moves(state.board)
        print(possible_moves)
        
        # find winning moves and use the first one
        winning_moves = self.find_winning_moves(state.board, state.coin_id, possible_moves)
        if winning_moves:
            return winning_moves[0]
        
        # find losing moves and use the first one
        losing_moves = self.find_losing_moves(state.board, state.coin_id, possible_moves)
        if losing_moves:
            return losing_moves[0]
        
        # find moves that will give the opponent a winning move
        losing_moves_plus1 = self.find_losing_moves_plus1(state.board, state.coin_id, possible_moves)
        if losing_moves_plus1:
            blocked_cols = set(losing_moves_plus1)
            possible_moves = [move for move in possible_moves if move[0] not in blocked_cols]

        # fall back to a random move in legal columns
        valid_cols = [xCol for xCol, _ in possible_moves]
        col = randrange(0, 7)
        while col not in valid_cols:
            col = randrange(0, 7)

        elapsed_ms = (perf_counter() - start) * 1000
        print(f"StayinAlign play time: {elapsed_ms:.2f} ms")
        return col

    def _print_board(self, board):
        for row in board[::-1]:
            print(row)
        print("")

    def get_name(self):
        return self.name
    
    def find_possible_moves(self, board):
        # find all possible moves
        possible_moves = []
        for xCol in range(7):
            for yRow in range(6):
                if board[yRow][xCol] == 0:
                    possible_moves.append((xCol, yRow))
                    break
        return possible_moves
    
    def count_direction(self, board, xCol, yRow, xStep, yStep, coin_id):
        # count the number of coins in a row in the direction (xStep, yStep)
        count = 0
        xCol += xStep
        yRow += yStep
        while 0 <= xCol < 7 and 0 <= yRow < 6 and board[yRow][xCol] == coin_id:
            count += 1
            xCol += xStep
            yRow += yStep
        return count

    def count_horizontal(self, board, xCol, yRow, coin_id):
        # count the number of coins in a row horizontally
        count = 1
        count += self.count_direction(board, xCol, yRow, 1, 0, coin_id)
        count += self.count_direction(board, xCol, yRow, -1, 0, coin_id)
        return count
    
    def count_vertical(self, board, xCol, yRow, coin_id):
        # count the number of coins in a row vertically
        count = 1
        count += self.count_direction(board, xCol, yRow, 0, 1, coin_id)
        count += self.count_direction(board, xCol, yRow, 0, -1, coin_id)
        return count
    
    def count_diagonal(self, board, xCol, yRow, coin_id):
        # count the number of coins in a row diagonally
        diag_down = self.count_direction(board, xCol, yRow, 1, 1, coin_id) + self.count_direction(board, xCol, yRow, -1, -1, coin_id)
        diag_up = self.count_direction(board, xCol, yRow, 1, -1, coin_id) + self.count_direction(board, xCol, yRow, -1, 1, coin_id)
        return 1 + max(diag_down, diag_up)
    
    def find_winning_moves(self, board, coin_id, possible_moves):
        # find all moves that will win the game
        winning_moves = []
        for move in possible_moves:
            xCol, yRow = move
            horizontal = self.count_horizontal(board, xCol, yRow, coin_id)
            vertical = self.count_vertical(board, xCol, yRow, coin_id)
            diagonal = self.count_diagonal(board, xCol, yRow, coin_id)
            if horizontal >= 4 or vertical >= 4 or diagonal >= 4:
                winning_moves.append(xCol)
        return winning_moves
    
    def find_losing_moves(self, board, coin_id, possible_moves):
        # find all moves that will lose the game
        losing_moves = []
        opponent_id = 2 if coin_id == 1 else 1
        losing_moves = self.find_winning_moves(board, opponent_id, possible_moves)
        return losing_moves

    def project_board(self, board, coin_id, xCol, yRow):
        # create a board with the move at xCol, yRow played
        projected_board = copy.deepcopy(board)
        projected_board[yRow][xCol] = coin_id
        return projected_board
    
    def find_losing_move_plus1(self, board, coin_id, xCol, yRow):
        # check if playing at (xCol, yRow) gives opponent a winning move
        opponent_id = 2 if coin_id == 1 else 1
        projected_board = self.project_board(board, coin_id, xCol, yRow)
        opponent_moves = self.find_possible_moves(projected_board)
        opponent_wins = self.find_winning_moves(projected_board, opponent_id, opponent_moves)
        return len(opponent_wins) > 0
    
    def find_losing_moves_plus1(self, board, coin_id, possible_moves):
        # find all moves that will give the opponent a winning move
        losing_moves_plus1 = []
        for move in possible_moves:
            xCol, yRow = move
            if self.find_losing_move_plus1(board, coin_id, xCol, yRow):
                losing_moves_plus1.append(xCol)
        return losing_moves_plus1
