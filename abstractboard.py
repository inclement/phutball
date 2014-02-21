from kivy.vector import Vector
from ai import AI


def get_speculative_move_identifiers(coords, steps):
    '''Returns a list of speculative move identifiers from end coords
    (coords) and a list of steps. Returns a list of 4-tuples containing
    the identifiers.
    '''
    identifiers = []
    for i in range(len(steps)-1):
        cur = steps[i]
        nex = steps[i+1]
        identifiers.append((cur[0], cur[1], nex[0], nex[1]))
    if len(steps) > 0:
        identifiers.append((steps[-1][0], steps[-1][1], coords[0], coords[1]))
    return identifiers


def coords_removed_on_step(start_coords, end_coords):
    '''Returns a list of coordinates on the straight line between
    start_coords and end_coords.'''
    start_coords = Vector(start_coords)
    end_coords = Vector(end_coords)
    number_of_steps = int(round(max(list(map(abs, end_coords - start_coords)))))
    direction = end_coords - start_coords
    jump = Vector(map(int, map(round, direction / number_of_steps)))

    removed_coords = []
    current_coords = start_coords
    for i in range(number_of_steps-1):
        current_coords += jump
        removed_coords.append(tuple(current_coords))
    return removed_coords


def removed_coords_from_steps(end_coord, steps):
    '''For each step, gets a list of removed coordinates. Returns all
    these lists.
    '''
    removed_coords = []
    for i in range(len(steps)-1):
        current_coords = steps[i]
        next_coords = steps[i+1]
        removed_coords.append(coords_removed_on_step(current_coords,
                                                     next_coords))
    removed_coords.append(coords_removed_on_step(steps[-1], end_coord))
    return removed_coords


def remove_coords_lists_from_set(coords_lists, coords_set):
    for coords_segment in coords_lists:
        for coords in coords_segment:
            coords = tuple(coords)
            if coords in coords_set:
                coords_set.remove(coords)


def add_coords_lists_to_set(coords_lists, coords_set):
    for coords_segment in coords_lists:
        for coords in coords_segment:
            coords = tuple(coords)
            if coords not in coords_set:
                coords_set.add(coords)


directions = list(map(Vector, [[1, 0], [1, 1], [0, 1], [-1, 1],
                               [-1, 0], [-1, -1], [0, -1], [1, -1]]))


def get_legal_moves(ball_coords, man_coords, shape=(15, 19),
                    previous_path=None, legal_moves=None,
                    depth=1, maxdepth=10):
    '''Returns a dictionary of legal move coordinates, along with the
    paths to reach them, by recursively making all possible moves.
    '''
    if depth > maxdepth:
        return
    if previous_path is None:
        previous_path = []
    if legal_moves is None:
        legal_moves = {}
    current_previous_path = previous_path[:]
    current_previous_path.append(ball_coords)

    ball_coords = Vector(ball_coords)
    for direction in directions:
        adj_coords = ball_coords + direction
        if tuple(adj_coords) in man_coords:
            path_man_coords = man_coords.copy()
            while tuple(adj_coords) in path_man_coords:
                path_man_coords.remove(tuple(adj_coords))
                adj_coords += direction
            new_legal_move = tuple(adj_coords)
            if new_legal_move not in legal_moves:
                legal_moves[tuple(adj_coords)] = [current_previous_path]
            else:
                legal_moves[tuple(adj_coords)].append(current_previous_path)
            get_legal_moves(new_legal_move, path_man_coords, shape,
                            current_previous_path, legal_moves,
                            depth=depth+1, maxdepth=maxdepth)
    return legal_moves


class AbstractBoard(object):
    '''A class that keeps track of the board logic; piece positions, legal
    moves etc.'''

    def __init__(self, shape=None):
        self.ai = None
        
        self.man_coords = set()
        self.ball_coords = (0, 0)
        self.shape = (15, 19)
        self.legal_moves = {}

        # Speculative attributes will hold data about the move the
        # player is currently making, without disrupting the full
        # logical state.
        self.speculative_ball_coords = (0, 0)
        self.speculative_man_coords = set()
        self.speculative_legal_moves = {}
        self.speculative_step_removals = []
        self.speculative_steps = []

        if 'shape' is not None:
            self.shape = shape

    def initialise_ai(self):
        if not self.ai:
            self.ai = AI(self)

    def check_for_win(self):
        '''Checks if either player has won.'''
        ball_coords = self.ball_coords
        if ball_coords[1] <= 1:
            return 'bottom'
        elif ball_coords[1] >= self.shape[1]-2:
            return 'top'
        else:
            return 'none'

    def speculative_move_ball_to(self, coords):
        '''Tries to move the ball to the given coordinates. Returns
        appropriate instructions for how the board should change in
        response.'''
        coords = tuple(coords)
        speculative_legal_moves = self.speculative_legal_moves

        if coords in self.speculative_legal_moves:
            possible_paths = self.speculative_legal_moves[coords]
            if len(possible_paths) > 1:
                short_paths = list(filter(lambda j: len(j) == 1, possible_paths))
                if not short_paths:
                    return {'conflicting_paths': (coords, possible_paths)}
                steps = short_paths[0]
            else:
                steps = possible_paths[0]

            self.speculative_ball_coords = coords
            newly_removed_coords = removed_coords_from_steps(coords, steps)
            remove_coords_lists_from_set(newly_removed_coords,
                                         self.speculative_man_coords)
            self.speculative_step_removals.extend(newly_removed_coords)
            self.speculative_legal_moves = get_legal_moves(
                self.speculative_ball_coords, self.speculative_man_coords,
                self.shape)
            self.speculative_steps.extend(list(map(tuple, steps)))
            return {'speculative_marker': get_speculative_move_identifiers(
                coords, self.speculative_steps)}

        if coords in self.speculative_steps:
            i = index = self.speculative_steps.index(coords)
            added_stones = self.speculative_step_removals[index:]
            self.speculative_ball_coords = coords
            self.speculative_steps = self.speculative_steps[:index]
            self.speculative_step_removals = self.speculative_step_removals[:i]
            add_coords_lists_to_set(added_stones, self.speculative_man_coords)
            self.speculative_legal_moves = get_legal_moves(
                self.speculative_ball_coords,
                self.speculative_man_coords,
                self.shape)
            return {'speculative_marker': get_speculative_move_identifiers(
                coords, self.speculative_steps)}

        return None

    def speculative_play_man_at(self, coords):
        '''Speculatively plays a man at the given coordinates.'''
        coords = tuple(coords)
        self.speculative_man_coords.add(coords)
        self.speculative_legal_moves = get_legal_moves(
            self.speculative_ball_coords,
            self.speculative_man_coords,
            self.shape)

    def confirm_speculation(self):
        '''Sets the current speculation state to the real board state. Returns
        a list of permanent instructions.'''
        if (not self.speculative_step_removals and 
            self.speculative_man_coords - self.man_coords == set()):
            return None
        new_men = self.speculative_man_coords - self.man_coords
        self.ball_coords = self.speculative_ball_coords
        self.man_coords = self.speculative_man_coords
        self.legal_moves = self.speculative_legal_moves
        if new_men:
            instructions = {'add': list(new_men)}
        else:
            removals = []
            for coords in self.speculative_step_removals:
                removals.extend(coords)
            instructions = {'move_ball_to': self.ball_coords,
                            'move_ball_via': get_speculative_move_identifiers(
                                tuple(self.ball_coords),
                                self.speculative_steps),
                            'remove': removals,
                            'clear_transient': None}
        self.reset_speculation()
        return instructions

    def reset_speculation(self):
        self.speculative_ball_coords = self.ball_coords
        self.speculative_man_coords = self.man_coords.copy()
        self.speculative_legal_moves = self.legal_moves
        self.speculative_step_removals = []
        self.speculative_steps = []

    def reset(self, *args):
        self.man_coords = set()
        self.ball_coords = (0, 0)
        self.reset_speculation()

    def add_man(self, coords):
        coords = tuple(coords)
        if coords in self.man_coords:
            return None
        self.man_coords.add(coords)
        return {'add': [coords]}

    def remove_man(self, coords):
        coords = tuple(coords)
        if coords not in self.man_coords:
            return None
        self.man_coords.remove(coords)
        return {'remove': [coords]}

    def toggle_man(self, coords):
        coords = tuple(coords)
        if coords in self.man_coords:
            instructions = self.remove_man(coords)
        else:
            instructions = self.add_man(coords)
        self.update_legal_moves()
        return instructions

    def play_man_at(self, coords):
        '''Method for attempting to play a man piece. Adds the man, and
        updates internal move state if necessary.
        '''
        instructions = self.add_man(coords)
        if instructions:
            self.update_legal_moves()
            self.reset_speculation()
        return instructions

    def do_ai_move(self):
        if not self.ai:
            self.initialise_ai()

        self.reset_speculation()

        move_type, coords = self.ai.get_move()
        print('ai wants to move at', coords, move_type)
        if move_type == 'move':
            self.speculative_move_ball_to(coords)
        elif move_type == 'play':
            self.speculative_play_man_at(coords)
#        legal_moves[current_pos] = 

    def update_legal_moves(self):
        moves = get_legal_moves(self.ball_coords, self.man_coords,
                                self.shape)
        self.legal_moves = moves
        return self.legal_moves

    def as_ascii(self, speculative=False, *args):
        '''Returns an ascii representation of the board.'''
        string_elements = []
        if not speculative:
            ball_coords = self.ball_coords
            man_coords = self.man_coords
            legal_moves = self.legal_moves
        else:
            ball_coords = self.speculative_ball_coords
            man_coords = self.speculative_man_coords
            legal_moves = self.speculative_legal_moves
        for y in range(self.shape[1])[::-1]:
            for x in range(self.shape[0]):
                coords = (x, y)
                if (coords[0] == ball_coords[0] and
                        coords[1] == ball_coords[1]):
                    string_elements.append('O')
                elif coords in man_coords:
                    string_elements.append('X')
                elif coords in legal_moves:
                    string_elements.append('@')
                elif coords[1] <= 1 or coords[1] >= self.shape[1]-2:
                    string_elements.append(',')
                else:
                    string_elements.append(',')
            string_elements.append('\n')
        return ''.join(string_elements)
