import copy
from random import randrange
from time import perf_counter

from Bots.bot_ai import BotAI
from Bots.data import PlayState

class StayinAlignAI(BotAI):
    def __init__(self):
        self.name = "StayinAlign"

    def play(self, state: PlayState):
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
        good_moves = self.find_good_moves(state.board, state.coin_id, sensible_moves, 3, state.bombs, state.round)
        if good_moves:
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

    def simulate_bomb(self, board, bombs):
        if not bombs:
            return board

        exploded = copy.deepcopy(board)
        for bomb in bombs:
            row = bomb.get("row")
            col = bomb.get("col")
            if row is None or col is None:
                continue
            for dRow, dCol in ((0, 0), (1, 0), (-1, 0), (0, 1), (0, -1)):
                r = row + dRow
                c = col + dCol
                if 0 <= r < 6 and 0 <= c < 7:
                    exploded[r][c] = 0

        # apply gravity
        for c in range(7):
            stack = [exploded[r][c] for r in range(6) if exploded[r][c] != 0]
            for r in range(6):
                exploded[r][c] = 0
            for idx, val in enumerate(stack):
                exploded[idx][c] = val

        return exploded

    def find_good_moves(self, board, coin_id, possible_moves, depth, bombs, current_round):
        # find all moves that are good, plan number of depth moves ahead
        # plan our and opponent moves and find the best move
        if depth <= 0 or not possible_moves:
            return [xCol for xCol, _ in possible_moves]

        opponent_id = 2 if coin_id == 1 else 1

        def is_win(current_board, player, xCol, yRow):
            return (
                self.count_horizontal(current_board, xCol, yRow, player) >= 4
                or self.count_vertical(current_board, xCol, yRow, player) >= 4
                or self.count_diagonal(current_board, xCol, yRow, player) >= 4
            )

        def heuristic(current_board, current_round):
            # quick, cheap evaluation: immediate wins and double threats
            moves = self.find_possible_moves(current_board)
            my_wins = len(self.find_winning_moves(current_board, coin_id, moves))
            opponent_wins = len(self.find_winning_moves(current_board, opponent_id, moves))
            my_double_threats = len(self.find_double_threat_moves(current_board, coin_id, moves))
            bomb_score = 0
            if bombs:
                soonest = min(b.get("explode_in_round", 1000) - current_round for b in bombs)
                # only project the explosion if it will happen within the search horizon
                if soonest <= depth:
                    post_board = self.simulate_bomb(current_board, bombs)
                    post_moves = self.find_possible_moves(post_board)
                    post_my_wins = len(self.find_winning_moves(post_board, coin_id, post_moves))
                    post_opponent_wins = len(self.find_winning_moves(post_board, opponent_id, post_moves))
                    bomb_score += (post_my_wins - post_opponent_wins) * 20
            return my_wins * 50 + my_double_threats * 10 - opponent_wins * 50 + bomb_score

        def score(current_board, current_player, current_depth, alpha, beta, current_round):
            moves = self.find_possible_moves(current_board)
            if current_depth == 0 or not moves:
                return heuristic(current_board, current_round)

            maximizing = current_player == coin_id
            best_val = -10_000 if maximizing else 10_000

            for xMove, yMove in moves:
                current_board[yMove][xMove] = current_player
                try:
                    if is_win(current_board, current_player, xMove, yMove):
                        value = 500 if maximizing else -500
                    else:
                        next_player = opponent_id if maximizing else coin_id
                        value = score(current_board, next_player, current_depth - 1, alpha, beta, current_round + 1)
                finally:
                    current_board[yMove][xMove] = 0

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
                    move_score = score(board, opponent_id, depth - 1, -10_000, 10_000, current_round + 1)
            finally:
                board[yRow][xCol] = 0

            if move_score > best_score:
                best_score = move_score
                best_moves = [xCol]
            elif move_score == best_score:
                best_moves.append(xCol)

        if len(best_moves) > 1:
            priority = {col: idx for idx, col in enumerate((3, 2, 4, 1, 5, 0, 6))}
            best_moves.sort(key=lambda col: priority.get(col, len(priority)))
        return best_moves
