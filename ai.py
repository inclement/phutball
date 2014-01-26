'''Module for a simple phutball playing ai.'''

from abstractboard import AbstractBoard

def max_height_in_coords(coords):
    max_height = 0
    for coord in coords:
        if coord[1] > max_height:
            max_height = coord
    return max_height

def min_height_in_coords(coords):
    min_height = 0
    for coord in coords:
        if coord[1] < min_height:
            min_height = coord
    return min_height

class AI(object):

    def __init__(self, abstractboard=None):
        if abstractboard is not None:
            self.abstractboard = abstractboard
        else:
            self.abstractboard = AbstractBoard()
    
    def get_move(self):
        legal_moves = self.abstractboard.legal_moves
        current = self.abstractboard.ball_coords
        shape = self.abstractboard.shape

        # Check max/min possible moves
        y_max = 0
        max_move = (0, 0)
        y_min = shape[1]
        min_move = (100, 100)
        for move in legal_moves:
            if move[1] > y_max:
                y_max = move[1]
                max_move = move
            if move[1] < y_min:
                y_min = move[1]
                min_move = move

        # If can win, win
        if min_index <= 1:
            print 'AI: Win by playing at {}'.format(min_index)
            return ('move', min_move)

        # If opponent can move 6 spaces and end up closer than that to the bottom
        jump = y_max - current[1]
        if jump >= 6:
            if shape[1]-2 - y_max < jump:
                print ('AI: Opponent can jump too far to {}, '
                       'trying to prevent.').format(max_move)

                # If can jump more than one move and end up closer to bottom
                down_jump = current[1] - y_min
                if down_jump >= 6:
                    if 2 + y_max < jump:
                        print 'AI: Performing counter-jump to {}'.format(min_move)
                        return ('move', min_move)
                        
                # If can flip parity usefully, do so
                best_change = max_move
                best_play = (0, 0)
                for coords in legal_moves[max_move]:
                    self.abstractboard.speculatively_play_man_at(coords)
                    new_legal_moves = self.abstractboard.speculative_legal_moves
                    new_max_coord = max_height_in_coords(new_legal_moves.keys())
                    if new_max_coord[1] < best_change[1]:
                        best_change = new_max_coord
                        best_play = coords
                    self.abstractboard.reset_speculation()
                if best_change[0] != max_move[0] and best_change[1] != max_move[1]:
                    print 'AI: Flipping parity, playing at {}'.format(best_change)
                    return ('move', best_change)

        # If opponent can win, at least try to jump away.
        # TODO

        # Else, make a move to get higher
        print 'AI: Nothing else useful to do, trying to jump further.'
        return ('play', (max_move[0], max_move[1]+1))
