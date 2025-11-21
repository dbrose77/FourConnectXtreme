import copy
from random import randrange
from time import perf_counter

from Bots.bot_ai import BotAI
from Bots.data import PlayState

# TODO:
# [x] project next move to not make a move that will give the opponent a winning move
# [x] tactical starting moves
# [x] try to use the middle column 
# [x] find double threat moves (simulate legal moves and find winning moves)
# [ ] find possible winning (and losing) moves with 2 coins in a row
# [ ] plan heuristic for future moves
# [ ] calculate bomb threats

class StayinAlignAI(BotAI):
    def __init__(self):
        self.name = "StayinAlign"

    def play(self, state: PlayState):
        start = perf_counter()
        # self._print_board(state.board)

        possible_moves = self.find_possible_moves(state.board)
        # if no possible moves, use a random column -> game is lost
        if not possible_moves:
            return randrange(0, 7)
        # print(possible_moves)
        
        if state.round == 1 or state.round == 2:
            return 3
        
        # find winning moves and use the first one
        winning_moves = self.find_winning_moves(state.board, state.coin_id, possible_moves)
        if winning_moves:
            return winning_moves[0]
        
        # find losing moves and use the first one
        losing_moves = self.find_losing_moves(state.board, state.coin_id, possible_moves)
        if losing_moves:
            return losing_moves[0]
        
        # find moves that will give the opponent a winning move
        sensible_moves = possible_moves
        losing_moves_plus1 = self.find_losing_moves_plus1(state.board, state.coin_id, possible_moves)
        if losing_moves_plus1:
            blocked_cols = set(losing_moves_plus1)
            sensible_moves = [move for move in possible_moves if move[0] not in blocked_cols]
            
        # find double threat moves
        double_threat_moves = self.find_double_threat_moves(state.board, state.coin_id, sensible_moves)
        if double_threat_moves:
            return double_threat_moves[0]
        
        # find good moves
        good_moves = self.find_good_moves(state.board, state.coin_id, sensible_moves, 3)
        if good_moves:
            elapsed_ms = (perf_counter() - start) * 1000
            print(f"StayinAlign play time: {elapsed_ms:.2f} ms")
            return good_moves[0]

        # fall back to a random move in legal columns
        sensible_cols = [xCol for xCol, _ in sensible_moves]
        # prefer the middle column
        if 3 in sensible_cols:
            return 3
        
        # if no more valid columns, use all possible columns -> probably a losing move
        if not sensible_cols:
            sensible_cols = [xCol for xCol, _ in possible_moves]
            
        col = randrange(0, 7)
        while col not in sensible_cols:
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

    def find_double_threat_moves(self, board, coin_id, possible_moves):
        # find all moves that will create a double threat
        double_threat_moves = []
        for move in possible_moves:
            xCol, yRow = move
            if self.find_double_threat_move(board, coin_id, xCol, yRow):
                double_threat_moves.append(xCol)
        return double_threat_moves
    
    def find_double_threat_move(self, board, coin_id, xCol, yRow):
        opponent_id = 2 if coin_id == 1 else 1
        projected_board = self.project_board(board, coin_id, xCol, yRow)
        opponent_moves = self.find_possible_moves(projected_board)
        double_threat_count = 0

        for opp_xCol, opp_yRow in opponent_moves:
            opp_projected = self.project_board(projected_board, opponent_id, opp_xCol, opp_yRow)
            my_moves = self.find_possible_moves(opp_projected)
            my_winning_moves = self.find_winning_moves(opp_projected, coin_id, my_moves)
            if len(my_winning_moves) >= 2:
                return True

        return False

    def find_good_moves(self, board, coin_id, possible_moves, depth):
        # find all moves that are good, plan number of depth moves ahead
        # plan our and opponent moves and find the best move
        if depth <= 0 or not possible_moves:
            return [xCol for xCol, _ in possible_moves]

        opponent_id = 2 if coin_id == 1 else 1

        def is_win(cur_board, player, xCol, yRow):
            return (
                self.count_horizontal(cur_board, xCol, yRow, player) >= 4
                or self.count_vertical(cur_board, xCol, yRow, player) >= 4
                or self.count_diagonal(cur_board, xCol, yRow, player) >= 4
            )

        def heuristic(cur_board):
            # quick, cheap evaluation: immediate wins and double threats
            moves = self.find_possible_moves(cur_board)
            my_wins = len(self.find_winning_moves(cur_board, coin_id, moves))
            opp_wins = len(self.find_winning_moves(cur_board, opponent_id, moves))
            my_double = len(self.find_double_threat_moves(cur_board, coin_id, moves))
            return my_wins * 50 + my_double * 10 - opp_wins * 50

        def score(cur_board, current_player, current_depth, alpha, beta):
            moves = self.find_possible_moves(cur_board)
            if current_depth == 0 or not moves:
                return heuristic(cur_board)

            maximizing = current_player == coin_id
            best_val = -10_000 if maximizing else 10_000

            for xMove, yMove in moves:
                cur_board[yMove][xMove] = current_player
                try:
                    if is_win(cur_board, current_player, xMove, yMove):
                        value = 500 if maximizing else -500
                    else:
                        next_player = opponent_id if maximizing else coin_id
                        value = score(cur_board, next_player, current_depth - 1, alpha, beta)
                finally:
                    cur_board[yMove][xMove] = 0

                if maximizing:
                    if value > best_val:
                        best_val = value
                    if best_val > alpha:
                        alpha = best_val
                else:
                    if value < best_val:
                        best_val = value
                    if best_val < beta:
                        beta = best_val

                if alpha >= beta:
                    break

            return best_val

        best_moves = []
        best_score = -10_000
        for xCol, yRow in possible_moves:
            board[yRow][xCol] = coin_id
            try:
                if is_win(board, coin_id, xCol, yRow):
                    move_score = 1_000
                else:
                    move_score = score(board, opponent_id, depth - 1, -10_000, 10_000)
            finally:
                board[yRow][xCol] = 0

            if move_score > best_score:
                best_score = move_score
                best_moves = [xCol]
            elif move_score == best_score:
                best_moves.append(xCol)

        return best_moves

    def is_good_move(self, board, coin_id, xCol, yRow):
        # check if playing at (xCol, yRow) is a good move
        # a good move is a move that will create a possible double threat
        # a good move is a move that will create three chips in a row (horizontal, vertical, diagonal) with the same coin_id with an open spot on the end
        if self.find_double_threat_move(board, coin_id, xCol, yRow):
            return True

        board[yRow][xCol] = coin_id
        try:
            for xStep, yStep in ((1, 0), (0, 1), (1, 1), (1, -1)):
                forward = self.count_direction(board, xCol, yRow, xStep, yStep, coin_id)
                backward = self.count_direction(board, xCol, yRow, -xStep, -yStep, coin_id)
                total = 1 + forward + backward
                if total < 3:
                    continue

                end1_x = xCol + (forward + 1) * xStep
                end1_y = yRow + (forward + 1) * yStep
                end2_x = xCol - (backward + 1) * xStep
                end2_y = yRow - (backward + 1) * yStep

                if (0 <= end1_x < 7 and 0 <= end1_y < 6 and board[end1_y][end1_x] == 0) or \
                   (0 <= end2_x < 7 and 0 <= end2_y < 6 and board[end2_y][end2_x] == 0):
                    return True
        finally:
            board[yRow][xCol] = 0

        return False
