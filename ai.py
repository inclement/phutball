'''Module for a simple phutball playing ai.'''

def max_height_in_coords(coords):
    max_height = (0, 0)
    for coord in coords:
        if coord[1] > max_height[1]:
            max_height = coord
    return max_height

def min_height_in_coords(coords):
    min_height = 0
    for coord in coords:
        if coord[1] < min_height:
            min_height = coord
    return min_height

class AI(object):

    def __init__(self, abstractboard):
        self.abstractboard = abstractboard
    
    def get_move(self):
        legal_moves = self.abstractboard.legal_moves
        current_pos = self.abstractboard.ball_coords
        current = self.abstractboard.ball_coords
        shape = self.abstractboard.shape

        if len(legal_moves) == 0:
            return ('play', (current_pos[0], current_pos[1]-1))

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
        if min_move[1] <= 1:
            print( 'AI: Win by playing at {}'.format(min_move))
            return ('move', min_move)

        # If opponent can move 6 spaces and end up closer than that to the bottom
        jump = y_max - current[1]
        if jump >= 6:
            if shape[1]-2 - y_max < jump:
                print('AI: Opponent can jump too far to {}, '
                      'trying to prevent.'.format(max_move))

                # If can jump more than one move and end up closer to bottom
                down_jump = current[1] - y_min
                if down_jump >= 6:
                    if 2 + y_max < jump:
                        print( 'AI: Performing counter-jump to {}'.format(min_move))
                        return ('move', min_move)
                        
                # If can flip parity usefully, do so
                best_change = max_move
                best_play = (0, 0)
                for coords in legal_moves[max_move][0][1:]:
                    coords = tuple(coords)
                    self.abstractboard.speculative_play_man_at(coords)
                    new_legal_moves = self.abstractboard.speculative_legal_moves
                    new_max_coord = max_height_in_coords(new_legal_moves.keys())
                    if new_max_coord[1] < best_change[1]:
                        best_change = new_max_coord
                        best_play = coords
                    self.abstractboard.reset_speculation()
                if best_change[0] != max_move[0] and best_change[1] != max_move[1]:
                    print('AI: Flipping parity, playing at {}'.format(best_change))
                    return ('play', best_play)

        # If opponent can win, at least try to jump away.
        # TODO

        # Else, make a move to get higher
        print('AI: Nothing else useful to do, trying to jump further.')
        if current_pos[1] < min_move[1]:
            new_move = (current_pos[0], current_pos[1]-1)
        else:
            new_move = (min_move[0], min_move[1]-1)
        return ('play', new_move)
