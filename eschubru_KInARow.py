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

import time # You'll probably need this to avoid losing a game due to exceeding a time limit.

# Create your own type of agent by subclassing KAgent:

class OurAgent(KAgent):  # Keep the class name "OurAgent" so a game master knows how to instantiate your agent class.

    def __init__(self, twin=False):
        self.twin=twin
        self.nickname = 'ALI G'
        if twin: self.nickname += '2'
        self.long_name = 'Alistair Leslie Graham'
        if twin: self.long_name += ' II'
        self.persona = 'bland'
        self.voice_info = {'Chrome': 10, 'Firefox': 2, 'other': 0}
        self.playing = "don't know yet" # e.g., "X" or "O".
        self.alpha_beta_cutoffs_this_turn = -1
        self.num_static_evals_this_turn = -1
        self.zobrist_table_num_entries_this_turn = -1
        self.zobrist_table_num_hits_this_turn = -1
        self.current_game_type = None
        self.playing_mode = KAgent.DEMO

    def introduce(self):
        intro = '\nAyy yo wagwan it be ALI-G here.\n'+\
            '"A little birdy told me that we be playing tic tac toes for a giggle\n'
        if self.twin: intro += "By the way, I'm the TWIN.\n"
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
       
        def __init__(self):

            self.current_game_type = game_type # the game type is a class that has intial state which has a board representation
            self.who_i_play = what_side_to_play
            self.opponent_nickname = opponent_nickname


            ## need to still add intialisation of utterance 

            return "Ok"
   
    # The core of your agent's ability should be implemented here:             
    def make_move(self, current_state, current_remark, time_limit=1000,
                  use_alpha_beta=True,
                  use_zobrist_hashing=False, max_ply=3,
                  special_static_eval_fn=None):

        
        # --- HOW TO IMPLEMENT make_move ---


        # 1. Generate candidate moves: iterate over rows and columns of
        #    current_state.board; any square equal to ' ' is a legal move.

        ## moves are denoted as a state coordinate and the only valid state to move to are those with state ''

        best = None # (move, state, utterance)

        # 2. For each candidate position (i, j), build a successor state:
        #      new_s = State(old=current_state)       # deep copy
        #      new_s.board[i][j] = current_state.whose_move
        #      new_s.change_turn()                    # switch X <-> O

        for i in range(len(current_state.board)):
            for j in range(len(current_state.board[i])):
                if current_state.board[i][j] != ' ':
                    continue

                new_s = State(old=current_state)
                new_s.board[i][j] = current_state.whose_move
                new_s.change_turn()


                # 3. Count blank squares before searching to detect a full board (draw)
                #    and to limit recursion depth appropriately.
        
                blank_square_count = sum(row.count(' ') for row in new_s.board)

                if blank_square_count == 0:
                    return [None, 'Dammit, it appears 2 be a draw'] ## if no free squares then game is finished 

                # 4. Call self.minimax(...) on the current state to get the best move.

                elif blank_square_count > 0:
                    score = self.minimax(state=new_s, depth_remaining= max_ply - 1, pruning=use_alpha_beta)[0] ## have already checked first depth

                    mover = current_state.whose_move
                    if (best is None or (mover == 'X' and score > best[0]) or (mover == 'O' and score < best[0])):
                        best = (score, (i, j), new_s)
                    
        # 5. Compose an utterance string appropriate to your agent's persona.


        # 6. Return format:
        #      DEMO / COMPETITION: [[move, new_state], utterance]
        #      AUTOGRADER:         [[move, new_state, stats], utterance]
        #    where stats is a dict with keys defined in agent_base.py, e.g.:
        #      stats['alpha_beta_cutoffs_this_turn']        = self.alpha_beta_cutoffs_this_turn
        #      stats['num_static_evals_this_turn']          = self.num_static_evals_this_turn
        #      stats['zobrist_table_num_entries_this_turn'] = self.zobrist_table_num_entries_this_turn
        #      stats['zobrist_table_num_hits_this_turn']    = self.zobrist_table_num_hits_this_turn
        
        if self.playing_mode == 0 or self.playing_mode ==1: # is in demo mode
            return [[best[0], best[1]], best[2]]
            
        elif self.playing_mode == 2: # is autograder mode

            ## add stats calculation in here

            return [[best[0], best[1], None], best[2]]
    

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

        # only set the window on the root call; children receive the parent's window
        if alpha is None:
            alpha = float('-inf')
        if beta is None:
            beta = float('inf')

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
            return [self.static_eval(state), None, None]

        is_max = (state.whose_move == 'X')
        best_val = float('-inf') if is_max else float('inf')
        best_move = None
        best_state = None

        for move, child in children:
            score = self.minimax(child, depth_remaining - 1, pruning, alpha, beta)[0]

            if (is_max and score > best_val) or (not is_max and score < best_val):
                best_val, best_move, best_state = score, move, child

            if pruning:
                if is_max:
                    alpha = max(alpha, best_val)
                else:
                    beta = min(beta, best_val)
                if alpha >= beta:
                    break  # remaining siblings cannot change the result

        return [best_val, best_move, best_state]
 
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


        DIRECTIONS = {
            'horizontal': (0, 1),
            'vertical':   (1, 0),
            'diag_down':  (1, 1),    # top-left to bottom-right
            'diag_up':    (1, -1),   # top-right to bottom-left
            }

        
        board = state.board
        rows, cols = len(board), len(board[0])
        data = {}
        for r in range(rows): # iterate down rows
            for c in range(cols):  # iterate across columns

                for name, (dr, dc) in DIRECTIONS.items():

                    end_r, end_c = r + dr * (k - 1), c + dc * (k - 1) # get the end index of k in a row for each direction 

                    if not (0 <= end_r < rows and 0 <= end_c < cols):
                        continue     # skip if k in a row does not fit on the board in that direction

                    x = o = 0 # set the streak of x and o to 0 for this k window

                    dead = False

                    for i in range(k): # complete the steps along the k squares in the search window

                        cell = board[r + dr * i][c + dc * i] # calculate the cell

                        if cell == '-':
                            dead = True # stop the streak
                            break # do we need to keep going if the k in a row is already blocked 

                        elif cell == 'X':
                            x += 1 # increase the x streak
                        
                        elif cell == 'O':
                            o += 1 # increase the o streak
                    
                    if dead or (x and o):  # blocked, so no one can win here 
                        continue 

                    data.setdefault((r, c), {})[name] = (x, o)

        # calculate the static evaluation score

        score = 0 # instatiate the score with a zero value

        for directions in data.values():
            for entry in directions.values():
                score += entry[0] / k # add the x entry percentage of a k in row
                score -= entry[1] / k # add the O entry percentage of a k in row
                # note that only one of entry[0] and entry[1] will be no zero

        return score


    




            




            
        
 
# OPTIONAL THINGS TO KEEP TRACK OF:

#  WHO_MY_OPPONENT_PLAYS = other(WHO_I_PLAY)
#  MY_PAST_UTTERANCES = []
#  OPPONENT_PAST_UTTERANCES = []
#  UTTERANCE_COUNT = 0
#  REPEAT_COUNT = 0 or a table of these if you are reusing different utterances

