'''Module for a simple phutball playing ai.'''

from abstractboard import AbstractBoard

def max_height_in_coords(coords):
    max_height = 0
    for coord in coords:
        if coord[1] > max_height:
            max_height = coord
    return max_height

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
            return ('move', min_move)

        # If opponent can move 6 spaces and end up closer than that to the bottom
        jump = y_max - current[1]
        if jump >= 6:
            if shape[1]-2 - y_max < jump:

                # If can jump more than one move and end up closer to bottom
                down_jump = current[1] - y_min
                if down_jump >= 6:
                    if 2 + y_max < jump:
                        return ('move', min_move)
                        
                # If can flip parity usefully, do so
                # TODO


        # Else, make a move to get higher
        return ('play', (max_move[0], max_move[1]+1))
