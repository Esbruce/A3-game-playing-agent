'''
eschubru_KInARow.py
Authors: Schuster Bruce, Edward 

An agent for playing "K-in-a-Row with Forbidden Squares" and related games.

THIS IS A TEMPLATE WITH STUBS FOR THE REQUIRED FUNCTIONS.
YOU CAN ADD WHATEVER ADDITIONAL FUNCTIONS YOU NEED IN ORDER
TO PROVIDE A GOOD STRUCTURE FOR YOUR IMPLEMENTATION.

'''

from agent_base import KAgent
from game_types import State, Game_Type

AUTHORS = 'Edward Schuster Bruce' 
STUDENT_IDS = ['eschubru'] # The first ID here should match the one in the file name, 

TIME_MARGIN = 0.8  # fraction of time_limit the search may use, leaving room for overhead
DEMO_TIME_CAP = 2.5  # seconds; demo moves should take under 3 s whatever time_limit says
NODE_CHECK_INTERVAL = 256  # minimax checks the clock once per this many nodes

class OutOfTime(Exception):
    pass  # raised inside minimax when the deadline passes; make_move keeps the last finished depth

BASE = 10  # static_eval window weights: a window with n marks is worth BASE ** (n - 1)

def win_score_for(k):
    # Returned by static_eval when a completed k-in-a-row exists. The best window weight is
    # BASE ** (k - 2) and a board holds many such windows, so BASE ** (k + 1) keeps a real win
    # above any unfinished position whatever k is.
    return BASE ** (k + 1)

# Ali G's deterministic utterances. {} is filled with the chosen square. Each line is a
# fixed non-empty string, so every make_move return path has at least one word.

UTTERANCE_BANK = [
    "Wagwan! Me puttin it on {}, innit.",
    "Booyakasha, {} is where the action be at.",
    "Respect to you, but me takin {} anyway.",
    "Is it cos I is thinkin ahead? {} it is.",
    "Big up yourself, but {} be mine.",
    "Me no like to boast, but {} is well sick.",
    "Check it, {}. Dat is how we roll in da tic tac toe massive.",
]

BLOCKING_UTTERANCE = "Ayy well that wasn't very nice"
TWIN_HEADSTART_UTTERANCE = "Go on then, you take a headstart. I'm so much better than the original I'll still smash you."

WINNING_UTTERANCE = "Booyakasha! Me seen da win at {}. Respect da maths g, innit."
LOSING_UTTERANCE = "Aiii, dat {} look bad for me, but me still got da swagger."

import random # for the Zobrist keys
import time # You'll probably need this to avoid losing a game due to exceeding a time limit.

def blocks_k_in_a_row(board, move, mover, k):
    # True if the opponent playing on `move` (before the mover takes it) would have completed
    # k in a row, i.e. the mover's piece there stops an immediate opponent win.
    opponent = 'O' if mover == 'X' else 'X'
    row, col = move
    for dr, dc in ((0, 1), (1, 0), (1, 1), (1, -1)):
        run = 1  # the square itself
        for sign in (1, -1):
            r, c = row + sign * dr, col + sign * dc
            while 0 <= r < len(board) and 0 <= c < len(board[r]) and board[r][c] == opponent:
                run += 1
                r, c = r + sign * dr, c + sign * dc
        if run >= k:
            return True
    return False

def current_state_blank_count(state):
    return sum(row.count(' ') for row in state.board)

# Create your own type of agent by subclassing KAgent:

class OurAgent(KAgent):  # Keep the class name "OurAgent" so a game master knows how to instantiate your agent class.

    def __init__(self, twin=False):
        self.twin=twin
        self.nickname = 'ALI G'
        if twin: self.nickname += '2.0 (the self aclaimed better twin)'
        self.long_name = 'Alistair Leslie Graham'
        if twin: self.long_name += ' II'
        self.persona = 'bland'
        self.voice_info = {'Chrome': 10, 'Firefox': 2, 'other': 0}
        self.playing = "don't know yet" # e.g., "X" or "O".
        self.alpha_beta_cutoffs_this_turn = -1
        self.num_static_evals_this_turn = -1
        self.zobrist_table_num_entries_this_turn = -1
        self.zobrist_table_num_hits_this_turn = -1
        # Zobrist hashing state (all of this is unused while use_zobrist_hashing is False):
        self.zobrist_table_num_reads_this_turn = -1 # read attempts (hits are the successful ones)
        self.zobrist_num_useful_hits_for_minimax = -1 # hits deep enough to reuse a stored value
        self.zobrist_num_useful_hits_for_ordering = -1 # hits used to try the stored best move first
        self.utterance_count = 0 # utterances made so far this game, to rotate through UTTERANCE_BANK
        self.use_zobrist_hashing = False # copied from make_move's argument each turn
        self.zobrist_table = {} # the transposition table: position hash -> (depth searched, value, bound flag, best move)
        self.zobrist_keys = None # (row, col, piece) -> random 64-bit int; built in make_move once the board size is known
        self.zobrist_turn = 0 # random 64-bit int XORed in when it is O's move, so X-to-move and O-to-move hash differently
        self.zobrist_dims = None # (rows, cols) the keys were built for; rebuilt if the board size changes
        self.zobrist_root = None # the state make_move was called with; never answered from the table
        self.current_game_type = None
        self.playing_mode = KAgent.DEMO
        self.special_static_eval_fn = None
        self.expected_time_per_move = 0.1 # seconds, from prepare
        self.deadline = None # perf_counter() value after which minimax stops; None means no limit
        self.nodes_since_clock_check = 0
        self.win_score = win_score_for(3) # value of a completed line; reset from k in make_move
        self.depth_reached_this_turn = 0 # deepest fully completed iteration, for utterances

    def introduce(self):
        intro = '\nAyy yo wagwan it be ALI-G here.\n'+\
            '"A little birdy told me that we be playing tic tac toes for a giggle\n'
        if self.twin: intro += "By the way, I'm the the Upgrade.\n"
        return intro

    # Receive and acknowledge information about the game from
    # the game master:
    def prepare(
        self,
        game_type,
        what_side_to_play,
        opponent_nickname,
        expected_time_per_move = 0.1, # Time limits can be
                                      # changed mid-game by the game master.

        utterances_matter=True):      # If False, just return 'OK' for each utterance,
                                      # or something simple and quick to compute
                                      # and do not import any LLM or special APIs.
                                      # During the tournament, this will be False..
        if utterances_matter:
            pass ## leave for later once agent is working
            # Optionally, import your LLM API here.
            # Then you can use it to help create utterances.

        self.current_game_type = game_type # the game type is a class that has intial state which has a board representation
        self.who_i_play = what_side_to_play
        self.playing = what_side_to_play
        self.opponent_nickname = opponent_nickname
        self.expected_time_per_move = expected_time_per_move
        # a new game: stored results (and keys, which depend on board size) from the last one do not apply
        self.zobrist_table = {}
        self.zobrist_keys = None
        self.utterance_count = 0 # start the utterance rotation again for the new game

        return "OK"

    # The core of your agent's ability should be implemented here:             
    def make_move(self, current_state, current_remark, time_limit=1000,
                  use_alpha_beta=True,
                  use_zobrist_hashing=False, max_ply=3,
                  special_static_eval_fn=None):

        
        # --- HOW TO IMPLEMENT make_move ---

        # 1-2. Successor states (one per blank square) are generated inside minimax,
        #      so make_move makes a single root call and the alpha-beta window is
        #      shared across the root's children.

        # 3. Count blank squares before searching to detect a full board (game over).
        #    A full board has no legal move, so return a None move; the game master
        #    treats that as the end of the game.

        blank_square_count = sum(row.count(' ') for row in current_state.board)

        if blank_square_count == 0:
            return [None, 'Dammit, no free squares left, game over']

        # The arrogant twin throws away his first go to give his opponent a headstart: he
        # plays the first blank square without searching. (Not in the autograder, which
        # checks exact search statistics.)
        if self.twin and self.utterance_count == 0 and self.playing_mode != KAgent.AUTOGRADER:
            for i, row in enumerate(current_state.board):
                for j, square in enumerate(row):
                    if square == ' ':
                        new_s = State(old=current_state)
                        new_s.board[i][j] = current_state.whose_move
                        new_s.change_turn()
                        self.utterance_count += 1
                        return [[(i, j), new_s], TWIN_HEADSTART_UTTERANCE]

        if self.current_game_type is not None:
            self.win_score = win_score_for(self.current_game_type.k)

        # reset the per-turn statistics, and keep the autograder's evaluator (if any)
        # so that minimax uses it at every leaf
        self.alpha_beta_cutoffs_this_turn = 0
        self.num_static_evals_this_turn = 0
        self.zobrist_table_num_entries_this_turn = 0 # writes to the table
        self.zobrist_table_num_hits_this_turn = 0 # lookups that found an entry
        self.zobrist_table_num_reads_this_turn = 0 # lookups attempted
        self.zobrist_num_useful_hits_for_minimax = 0
        self.zobrist_num_useful_hits_for_ordering = 0

        # Stored values come from whichever evaluator was in use. If the evaluator has
        # changed (e.g. the autograder's special function), they are no longer comparable.

        if special_static_eval_fn is not self.special_static_eval_fn:
            self.zobrist_table = {}
        self.special_static_eval_fn = special_static_eval_fn

        # Zobrist hashing setup: one random 64-bit key per (square, piece), built once per
        # board size. A position's hash is the XOR of the keys of the pieces on it.
        self.use_zobrist_hashing = use_zobrist_hashing
        # The root must be searched, not answered from the table, because make_move needs
        # the move and state minimax returns for it (a table hit returns no state).
        self.zobrist_root = current_state
        if use_zobrist_hashing:
            dims = (len(current_state.board), len(current_state.board[0]))
            if self.zobrist_keys is None or self.zobrist_dims != dims: # first use, or a different board size
                rng = random.Random(415) # fixed seed, so runs are repeatable
                self.zobrist_keys = {(i, j, piece): rng.getrandbits(64)
                                     for i in range(dims[0]) for j in range(dims[1]) for piece in 'XO'}
                self.zobrist_turn = rng.getrandbits(64) # distinguishes X-to-move from O-to-move
                self.zobrist_dims = dims
                self.zobrist_table = {} # old hashes were made with different keys

        # 4. Call self.minimax(...) on the current state to get the best move.
        #    max_ply is passed through unchanged (at least 1, so a move always comes back).

        max_ply = max(max_ply, 1)
        if self.playing_mode == KAgent.AUTOGRADER:
            # the autograder checks exact leaf counts, so search exactly max_ply with no clock
            self.deadline = None
            result = self.minimax(current_state, max_ply, use_alpha_beta)
            self.depth_reached_this_turn = max_ply
        else:
            # Iterative deepening: search 1, 2, ... ply, keeping the last finished result, until
            # the deadline passes. Depth 1 always finishes so a move always comes back. In
            # COMPETITION mode max_ply is only a floor and the clock decides how deep to go;
            # in DEMO mode max_ply is also the ceiling.
            # the brief allows time_limit=None, meaning no limit set by the game master
            budget = float('inf') if time_limit is None else TIME_MARGIN * time_limit
            if self.playing_mode == KAgent.DEMO:
                budget = min(budget, DEMO_TIME_CAP)
            elif budget == float('inf'):
                budget = DEMO_TIME_CAP # competition with no stated limit: stay modest
            start = time.perf_counter()
            self.nodes_since_clock_check = 0
            result = None
            depth = 1
            while True:
                self.deadline = None if depth == 1 else start + budget
                try:
                    result = self.minimax(current_state, depth, use_alpha_beta)
                except OutOfTime:
                    break
                self.depth_reached_this_turn = depth
                if abs(result[0]) >= self.win_score: # forced result found, deeper search cannot change it
                    break
                if self.playing_mode == KAgent.DEMO and depth >= max_ply:
                    break
                if depth >= current_state_blank_count(current_state): # whole game tree searched
                    break
                depth += 1
                if time.perf_counter() - start >= budget:
                    break
            self.deadline = None
        move, new_s = result[1], result[2]

        # 5. Compose an utterance string appropriate to your agent's persona.

        # Deterministic, in character, and never empty: a forced win or loss found by the
        # search gets its own line, otherwise rotate through the bank. The score is from X's
        # point of view, so flip it to be from the mover's point of view.
        mover_score = result[0] if current_state.whose_move == 'X' else -result[0]
        if mover_score >= self.win_score:
            utterance = WINNING_UTTERANCE.format(move)
        elif (self.current_game_type is not None and move is not None and
              blocks_k_in_a_row(current_state.board, move, current_state.whose_move, self.current_game_type.k)):
            utterance = BLOCKING_UTTERANCE
        elif mover_score <= -self.win_score:
            utterance = LOSING_UTTERANCE.format(move)
        else:
            utterance = UTTERANCE_BANK[self.utterance_count % len(UTTERANCE_BANK)].format(move)
        self.utterance_count += 1

        # 6. Return format:
        #      DEMO / COMPETITION: [[move, new_state], utterance]
        #      AUTOGRADER:         [[move, new_state, stats], utterance]
        #    where stats is a dict with keys defined in agent_base.py.

        if self.playing_mode != KAgent.AUTOGRADER:
            return [[move, new_s], utterance]

        stats = {
            'alpha_beta_cutoffs_this_turn': self.alpha_beta_cutoffs_this_turn,
            'num_static_evals_this_turn': self.num_static_evals_this_turn,
            'zobrist_table_num_entries_this_turn': self.zobrist_table_num_entries_this_turn,
            'zobrist_table_num_hits_this_turn': self.zobrist_table_num_hits_this_turn,
            'zobrist_num_useful_hits_for_minimax': self.zobrist_num_useful_hits_for_minimax,
            'zobrist_num_useful_hits_for_ordering': self.zobrist_num_useful_hits_for_ordering
        }

        return [[move, new_s, stats], utterance]

    # The main adversarial search function:
    def minimax(self,
            state,
            depth_remaining,
            pruning=False,
            alpha=None,
            beta=None):
        
        # --- HOW TO IMPLEMENT minimax ---
        # Base cases — call static_eval and return its value:
        #   - depth_remaining == 0  (depth limit reached)
        #   - no blank squares remain on the board (draw)
        #   - terminal win/loss state (optional; static_eval can handle this)
        # Recursive case:
        #   is_max = (state.whose_move == 'X')   # X maximizes, O minimizes
        #   best_val = -inf if is_max else +inf
        #   For each successor state generated by your move generator:
        #     result = self.minimax(successor, depth_remaining - 1, pruning, alpha, beta)
        #     Update best_val and best_move.
        #     If pruning is True: check alpha/beta cutoff and break early.
        #     Update alpha (if is_max) or beta (if not is_max) after each child.
        # Return at minimum [score, best_move, best_state].
        # Additional values after index 0 can carry info back to make_move.

        # None means "do not use this feature": a None pruning is treated as False, and a
        # None alpha or beta becomes an unbounded window. When pruning is falsy, alpha and
        # beta are never read for a decision (no window update, no cutoff, no stored-bound
        # use), so whatever values are passed in are ignored.
        # only set the window on the root call; children receive the parent's window
        if alpha is None:
            alpha = float('-inf')  # initialise at inf
        if beta is None:
            beta = float('inf')

        # time management: look at the clock only every so often, since perf_counter is not free
        if self.deadline is not None:
            self.nodes_since_clock_check += 1
            if self.nodes_since_clock_check >= NODE_CHECK_INTERVAL: 
                self.nodes_since_clock_check = 0
                if time.perf_counter() > self.deadline:
                    raise OutOfTime()

        # terminal state: a completed k-in-a-row ends the game, so do not expand it;
        # it counts as a leaf. Closer wins score higher (and closer losses lower)
        # via depth_remaining. Skipped in AUTOGRADER mode, where the search must be
        # driven only by the special static evaluation function and max_ply.

        if self.special_static_eval_fn is None:
            terminal = self.static_eval(state)
            if terminal == self.win_score or terminal == -self.win_score: # check if the game is one
                self.num_static_evals_this_turn += 1
                return [float(terminal + (depth_remaining if terminal > 0 else -depth_remaining)), None, None] 
            

        # Zobrist hashing, part 1 (lookup): compute this position's hash, then look it up
        # and reuse a stored result if it was searched at least as deep.
        # A stored bound (from a pruned search) can still tighten the window or cause a cutoff.

        alpha_orig, beta_orig = alpha, beta # the window as passed in; needed later to classify the result as exact or a bound

        zhash = None # stays None when hashing is off, which also skips the store at the end
        stored = None

        ## generate zobrist key

        if self.use_zobrist_hashing and depth_remaining > 0: # leaves are cheap to evaluate, so only internal nodes use the table

            # the hash is the XOR of the keys of every X and O on the board
            zhash = 0
            for i in range(len(state.board)):
                for j in range(len(state.board[i])):
                    key = self.zobrist_keys.get((i, j, state.board[i][j])) # None for blank/forbidden squares
                    if key:
                        zhash ^= key
            if state.whose_move == 'O': # the same board with a different side to move is a different position
                zhash ^= self.zobrist_turn

        


            self.zobrist_table_num_reads_this_turn += 1
            stored = self.zobrist_table.get(zhash) # check the transposition table using the previously generated key ()

            if stored is not None: # if there is a stored evaluation use it

                self.zobrist_table_num_hits_this_turn += 1 # count the number of times the transposition has resulted in a match

                stored_depth, stored_val, stored_flag, stored_move = stored

                # only trust an entry searched at least as deep as we need now
                if stored_depth >= depth_remaining and state is not self.zobrist_root: 

                    if stored_flag == 'EXACT': # the true value: return it without searching 
                        self.zobrist_num_useful_hits_for_minimax += 1
                        return [stored_val, stored_move, None] # no state: only make_move's root call needs one 
                    
                    if pruning: # complete pruning

                        # a bound: LOWER means the true value is >= stored_val, UPPER means <=.
                        # Use it to narrow the window, and stop if the window closes.
                        if stored_flag == 'LOWER':
                            alpha = max(alpha, stored_val)
                        else:
                            beta = min(beta, stored_val)
                        if alpha >= beta:
                            self.zobrist_num_useful_hits_for_minimax += 1
                            return [stored_val, stored_move, None]

        # generate the successors once, so a single break can leave the search
        children = []
        for i in range(len(state.board)):
            for j in range(len(state.board[i])):
                if state.board[i][j] == ' ':
                    new_s = State(old=state)
                    new_s.board[i][j] = state.whose_move
                    new_s.change_turn()
                    children.append(((i, j), new_s))

        ## base cases: depth limit reached, or no blank squares left (draw)
        if depth_remaining == 0 or not children:
            self.num_static_evals_this_turn += 1
            if self.special_static_eval_fn is not None: # autograder supplies its own evaluator
                return [float(self.special_static_eval_fn(state)), None, None]
            return [float(self.static_eval(state)), None, None]

        # Zobrist hashing, part 2 (ordering): even when a stored entry could not be reused
        # directly, its best move is a good guess. Trying it first makes alpha-beta cut off
        # sooner. Not in AUTOGRADER mode, where moves must be considered in row-major order.
        if stored is not None and stored[3] is not None and pruning and self.special_static_eval_fn is None:
            for n in range(len(children)):
                if children[n][0] == stored[3]:
                    children.insert(0, children.pop(n))
                    self.zobrist_num_useful_hits_for_ordering += 1
                    break

        is_max = (state.whose_move == 'X')
        best_val = float('-inf') if is_max else float('inf')
        best_move = None
        best_state = None

        for move, child in children:
            score = self.minimax(child, depth_remaining - 1, pruning, alpha, beta)[0]

            # the first child is always taken, so a move is returned even if every score
            # equals the starting +-infinity (or is NaN); after that only a strictly better one replaces it
            if best_move is None or (is_max and score > best_val) or (not is_max and score < best_val):
                best_val, best_move, best_state = score, move, child

            if pruning: # prune
                if is_max:
                    alpha = max(alpha, best_val)
                else:
                    beta = min(beta, best_val)
                if alpha >= beta:
                    self.alpha_beta_cutoffs_this_turn += 1
                    break  # remaining siblings cannot change the result

        # Zobrist hashing, part 3 (store): record this position's result, flagged as exact
        # or as a bound if pruning cut the search short.

        if zhash is not None:
            if not pruning:
                flag = 'EXACT' # every child was searched fully
            elif best_val <= alpha_orig:
                flag = 'UPPER' # no move beat what was already available, so the true value is at most best_val
            elif best_val >= beta_orig:
                flag = 'LOWER' # a cutoff happened, so the true value is at least best_val
            else:
                flag = 'EXACT' # the value fell inside the window, so it is the true value
            # do not let a shallower search overwrite a deeper one
            if stored is None or depth_remaining >= stored[0]:
                self.zobrist_table[zhash] = (depth_remaining, best_val, flag, best_move)
                self.zobrist_table_num_entries_this_turn += 1

        # the score is always a float, as the brief requires, alongside the move (and state)
        return [float(best_val), best_move, best_state]


    def static_eval(self, state, game_type=None):
        # Return a numeric score: positive = good for X, negative = good for O.
        # Use game_type.k (the win length) to evaluate partial lines.
        # IMPORTANT: k is NOT stored in the state — you must get it from game_type.
        # In DEMO/COMPETITION mode game_type will be None; use self.current_game_type
        # (which you should have saved during prepare).
        if game_type is None:
            game_type = self.current_game_type

        # accesss the k value

        k = game_type.k


        DIRECTIONS = ((0, 1), (1, 0), (1, 1), (1, -1))  # horizontal, vertical, both diagonals

        board = state.board
        rows, cols = len(board), len(board[0])

        # Collection: tally live k-windows by how many marks the owner has in them.
        # x_windows[n] = number of windows containing exactly n X's and no O's or '-'.
        # Positions and directions are deliberately not stored; the scoring step below
        # only needs counts. If positional features are ever needed, append
        # (x, o, r, c, dr, dc) tuples to a flat list here instead.
        x_windows = [0] * (k + 1)
        o_windows = [0] * (k + 1)

        for r in range(rows):
            for c in range(cols):
                for dr, dc in DIRECTIONS:
                    end_r, end_c = r + dr * (k - 1), c + dc * (k - 1)  # last square of the k-window

                    if not (0 <= end_r < rows and 0 <= end_c < cols):
                        continue  # window does not fit on the board in this direction

                    x = o = 0
                    dead = False

                    for i in range(k):
                        cell = board[r + dr * i][c + dc * i]

                        if cell == '-':
                            dead = True  # blocked square: nobody can win through this window
                            break
                        elif cell == 'X':
                            x += 1
                        elif cell == 'O':
                            o += 1

                    if dead or (x and o):  # blocked or contested, so worth nothing
                        continue

                    # at most one of x, o is non-zero here
                    if x:
                        x_windows[x] += 1
                    elif o:
                        o_windows[o] += 1

        # A completed window is a win; no need to weigh anything else.
        if x_windows[k]:
            return win_score_for(k)
        if o_windows[k]:
            return -win_score_for(k)

        # Scoring: edit the weights (or this formula) freely; the scan above is unaffected.
        weights = [BASE ** (n - 1) if n else 0 for n in range(k + 1)]
        score = 0
        for n in range(1, k):
            score += weights[n] * (x_windows[n] - o_windows[n])

        return score


    




            




            
        
 
# OPTIONAL THINGS TO KEEP TRACK OF:

#  WHO_MY_OPPONENT_PLAYS = other(WHO_I_PLAY)
#  MY_PAST_UTTERANCES = []
#  OPPONENT_PAST_UTTERANCES = []
#  UTTERANCE_COUNT = 0
#  REPEAT_COUNT = 0 or a table of these if you are reusing different utterances

