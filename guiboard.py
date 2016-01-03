from kivy.app import App
from kivy.vector import Vector
from kivy.event import EventDispatcher
from kivy.animation import Animation

from kivy.uix.widget import Widget
from kivy.uix.anchorlayout import AnchorLayout
from kivy.uix.image import Image
from kivy.uix.boxlayout import BoxLayout
from kivy.uix.modalview import ModalView
from kivy.uix.floatlayout import FloatLayout
from kivy.uix.label import Label

from kivy.uix.behaviors import ButtonBehavior

from kivy.properties import (NumericProperty, ListProperty,
                             ReferenceListProperty, StringProperty,
                             BooleanProperty, ObjectProperty,
                             DictProperty, OptionProperty)
from kivy.clock import Clock

from abstractboard import AbstractBoard

import random
from os.path import exists

def sign(n):
    return 1 if n >= 0 else -1

def coords_in_grid(coords, shape):
    x, y = coords
    if (x < 0 or y < 0 or x >= (shape[0]-1) or y >= (shape[1]-1)):
        return False
    return True

class SingularPopup(ModalView):
    def __init__(self, **kwargs):
        popup = App.get_running_app().popup
        if popup is not None:
            popup.dismiss()
        super(SingularPopup, self).__init__(**kwargs)
        App.get_running_app().popup = self

class NextTutorialPopup(SingularPopup):
    number = StringProperty('')
    next_file = StringProperty('')
    next_mode = StringProperty('')
    winner_text = StringProperty('')
    tutorial_text = StringProperty('')
    next_text = StringProperty('Next tutorial')


class FinishedTutorialsPopup(SingularPopup):
    number = StringProperty('')


class PlayAgainPopup(SingularPopup):
    ai = BooleanProperty(False)
    winner_text = StringProperty('')
    next_mode = StringProperty('normal')


class Message(Label):
    board = ObjectProperty()
    board_width = NumericProperty(100.)
    board_message = StringProperty('')


class ActiveButton(ButtonBehavior, BoxLayout):
    '''Widget accepting button input that also has an active property and
    an animation progress property to/from that state.'''
    text = StringProperty('')
    anim_progress = NumericProperty(0)
    active = BooleanProperty(True)
    anim_to_active = ObjectProperty(Animation(anim_progress=1, duration=0.1))
    anim_to_inactive = ObjectProperty(Animation(anim_progress=0, duration=0.1))

    def on_active(self, *args):
        Animation.cancel_all(self)
        if self.active:
            self.anim_to_active.start(self)
        else:
            self.anim_to_inactive.start(self)

class ColourChangeButton(ActiveButton):
    '''Active button that changes between two colours.'''
    colour_before = ListProperty([0.3, 0.3, 0.3, 1])
    colour_after = ListProperty([0.7, 0.7, 0.7, 1])
    colour_diff = ListProperty([0, 0, 0, 0])

class ConfirmButton(ColourChangeButton):
    pass


class MoveButton(ColourChangeButton):
    pass


class PlayManButton(ColourChangeButton):
    pass

class ToggleModeButton(ColourChangeButton):
    pass


class InterfaceButtons(BoxLayout):
    board = ObjectProperty()
    mode = StringProperty('play_man')
    touch_mode = StringProperty('')
    can_confirm = BooleanProperty(False)


class MoveMakingMarker(Widget):
    '''Marker showing the position of the current touch (where a move will
    be made).
    '''
    coords = ListProperty([0, 0])
    anim_progress = NumericProperty(0.0)
    board = ObjectProperty()
    animation_in = ObjectProperty(Animation(anim_progress=1,
                                            t='out_quint',
                                            duration=0.3))
    animation_out = ObjectProperty(Animation(anim_progress=0,
                                             t='out_quint',
                                             duration=0.3))
    mode = OptionProperty('play_man', options=['play_man',
                                               'move_ball'])
    colour = ListProperty([0.2, 0.2, 0.8])
    def on_mode(self, *args):
        mode = self.mode
        if mode == 'play_man':
            self.colour = [0.2, 0.2, 0.8]
        else:
            self.colour = [0.2, 0.8, 0.2]
    def on_coords(self, *args):
        coords = self.coords
        pos = self.board.coords_to_pos(coords)
        self.pos = pos
    def anim_in(self, *args):
        Animation.cancel_all(self)
        self.animation_in.start(self)
    def anim_out(self, *args):
        Animation.cancel_all(self)
        self.animation_out.start(self)
        

class VictoryPopup(ModalView):
    winner = StringProperty('')


class ConflictingSegmentMarker(Widget):
    '''Marker that draws a red line between two coordinates, with an
    animation making the line fade to nothing and be removed.'''
    points = ListProperty([])


class SpeculativeSegmentMarker(Widget):
    '''Marker that draws a line denoting a speculative movement.'''
    start_coords = ListProperty([0, 0])
    end_coords = ListProperty([0, 0])
    start_pos = ListProperty([0, 0])
    end_pos = ListProperty([0, 0])

    y_shifts = ListProperty([])
    points = ListProperty([])
    points_per_step = NumericProperty(5)


class Ball(Image):
    '''Widget representing the 'ball' piece.'''
    coords = ListProperty([0, 0])


class Man(Image):
    '''Widget representing the 'man' pieces.'''
    coords = ListProperty([0, 0])


class LegalMoveMarker(Widget):
    '''Widget representing a possible legal move.'''
    coords = ListProperty([0, 0])


class BoardInterface(BoxLayout):
    '''The widget for a whole board interface, intended to take up the
    whole screen.'''


class BoardContainer(FloatLayout):
    board = ObjectProperty()
    use_ai = BooleanProperty(False)


class Board(Widget):
    grid_x = NumericProperty(15)
    grid_y = NumericProperty(19)
    grid = ReferenceListProperty(grid_x, grid_y)

    shape_x = NumericProperty(15)
    shape_y = NumericProperty(19)
    shape = ReferenceListProperty(shape_x, shape_y)

    padding_x = NumericProperty(0)
    padding_y = NumericProperty(0)
    padding = ReferenceListProperty(padding_x, padding_y)

    cell_size_x = NumericProperty()
    cell_size_y = NumericProperty()
    cell_size = ReferenceListProperty(cell_size_x, cell_size_y)

    portrait = BooleanProperty()  # True if shape_x < shape_y
    aspect_ratio = NumericProperty()

    player = OptionProperty('bottom', options=['top', 'bottom'])

    board_image = StringProperty('boards/edphoto_section_light.png')

    grid_points = ListProperty([])
    goal_rectangle_size = ListProperty([0, 0])
    top_rectangle_pos = ListProperty([0, 0])
    bottom_rectangle_pos = ListProperty([0, 0])

    ball = ObjectProperty(None, allownone=True)
    men = DictProperty({})
    legal_move_markers = DictProperty({})
    speculative_segment_markers = DictProperty({})

    abstractboard = ObjectProperty()
    use_ai = BooleanProperty(False)
    move_marker = ObjectProperty()
    touch = ObjectProperty(None, allownone=True)

    message = StringProperty('')

    current_player = OptionProperty('top', options=['top',
                                                    'bottom'])
    touch_mode = StringProperty('play_man', options=['play_man',
                                                     'move_ball',
                                                     'toggle_man',
                                                     'dormant'])
    can_confirm = BooleanProperty(False)
    touch_offset = NumericProperty(0)

    game_mode = StringProperty('normal')
    '''Property used to know what to do at the end of the game, e.g.
    return to menu, offer a new game, or more forward in the tutorials
    or puzzles.'''

    show_legal_moves = BooleanProperty(True)

    def __init__(self, *args, **kwargs):
        self.register_event_type('on_win')
        if 'use_ai' in kwargs:
            use_ai = kwargs.pop('use_ai')
        else:
            use_ai = False
        super(Board, self).__init__(*args, **kwargs)
        self.abstractboard = AbstractBoard(shape=self.grid)
        self.abstractboard.reset()
        self.use_ai = use_ai
#        Clock.schedule_once(self.initialise_ball, 0)
        #self.initialise_ball()

    def on_win(self, winner):
        # import ipdb
        # ipdb.set_trace()
        mode = self.game_mode
        print('mode is', mode)
        if mode[:8] == 'tutorial':
            number = int(mode[8:]) + 1
            if winner == 'bottom':
                number -= 1
            next_file = 'puzzles/dir01_tutorials/tutorial{}.phut'.format(number)
            next_mode = 'tutorial{}'.format(number)
            print('next file is', next_file, exists(next_file))
            if exists(next_file):
                if winner == 'bottom':
                    winner_text = 'You lose'
                    tutorial_text = 'Do you want to try again?'
                    next_text = 'Try again'
                else:
                    winner_text = '[color=#dbebc3]You win![/color]'
                    tutorial_text = 'Tutorial {} complete'.format(number-1)
                    next_text = 'Next tutorial'
                NextTutorialPopup(number=str(number-1),
                                  next_file=next_file,
                                  next_mode=next_mode,
                                  winner_text=winner_text,
                                  tutorial_text=tutorial_text,
                                  next_text=next_text).open()
            else:
                FinishedTutorialsPopup(number=str(number)).open()
        elif mode == 'ainormal':
            winner_text = {
                'top': '[color=#dbebc3]You win![/color]',
                'bottom': '[color=#ffcab2]You lose[/color]'}[winner]
            PlayAgainPopup(ai=True, winner_text=winner_text,
                           next_mode='ainormal').open()
        else:
            winner_text = '[color=#ffffff]{} player wins[/color]'.format(
                winner)
            PlayAgainPopup(ai=False, winner_text=winner_text,
                           next_mode='normal').open()

    def on_touch_mode(self, *args):
        mode = self.touch_mode
        if mode == 'play_man':
            self.abstractboard.reset_speculation()
            self.clear_transient_ui_elements()
            self.display_legal_moves()
            self.move_marker.mode = 'play_man'
        else:
            self.move_marker.mode = 'move_ball'

    def advance_player(self):
        if self.player == 'bottom':
            self.player = 'top'
        else:
            self.player = 'bottom'

    def check_for_win(self):
        '''Checks if either player has won, i.e. that the ball is in one of
        the goals.'''
        winner = self.abstractboard.check_for_win()
        if winner == 'top':
            self.dispatch('on_win', 'top')
        elif winner == 'bottom':
            self.dispatch('on_win', 'bottom')

    def follow_instructions(self, instructions):
        '''Takes instructions from an AbstractBoard and uses them to update
        the gui.'''

        if instructions is None:
            return  # Nothing changes

        if 'add' in instructions:
            add_coords = instructions['add']
            for coords in add_coords:
                self.add_man(coords)
        if 'remove' in instructions:
            remove_coords = instructions['remove']
            for coords in remove_coords:
                self.remove_man(coords)
        if 'speculative_marker' in instructions:
            speculative_markers = instructions['speculative_marker']
            self.sync_speculative_segment_markers(speculative_markers)
        if 'conflicting_paths' in instructions:
            conflicting_markers = instructions['conflicting_paths']
            self.draw_conflicting_markers(conflicting_markers)
        if 'clear_transient' in instructions:
            self.clear_transient_ui_elements()
            self.display_legal_moves()
        if 'move_ball_to' in instructions:
            ball_coords = instructions['move_ball_to']
            ball = self.ball
            ball.coords = ball_coords
            ball.pos = self.coords_to_pos(ball_coords)

    def draw_conflicting_markers(self, components):
        end_coords, paths = components
        end_pos = (Vector(self.coords_to_pos(end_coords)) +
                   Vector(self.cell_size)/2.)
        lines = []
        for path in paths:
            path = [Vector(self.coords_to_pos(coords)) +
                    Vector(self.cell_size)/2.
                    for coords in path]
            points = []
            for entry in path:
                points.append(entry[0])
                points.append(entry[1])
            points.append(end_pos[0])
            points.append(end_pos[1])
            lines.append(points)

        anim = Animation(opacity=0, duration=0.75, t='out_quad')
        for line in lines:
            marker = ConflictingSegmentMarker(points=line)
            self.add_widget(marker)
            anim.start(marker)
            anim.bind(on_complete=self.remove_widget_from_anim)

    def remove_widget_from_anim(self, animation, widget):
        self.remove_widget(widget)

    def sync_speculative_segment_markers(self, new_markers):
        existing_markers = self.speculative_segment_markers
        for identifier in new_markers:
            if identifier not in existing_markers:
                self.add_speculative_segment_marker(identifier)
        for identifier in list(existing_markers.keys()):
            if identifier not in new_markers:
                self.remove_speculative_segment_marker(identifier)

    def add_speculative_segment_marker(self, identifier):
        if identifier in self.speculative_segment_markers:
            return
        start_coords = tuple(identifier[:2])
        end_coords = tuple(identifier[2:])
        start_pos = (Vector(self.coords_to_pos(start_coords)) +
                     Vector(self.cell_size)/2.)
        end_pos = (Vector(self.coords_to_pos(end_coords)) +
                   Vector(self.cell_size)/2.)
        marker = SpeculativeSegmentMarker(start_coords=start_coords,
                                          end_coords=end_coords,
                                          start_pos=start_pos,
                                          end_pos=end_pos)
        self.add_widget(marker)
        self.speculative_segment_markers[identifier] = marker

    def remove_speculative_segment_marker(self, identifier):
        if identifier not in self.speculative_segment_markers:
            return
        marker = self.speculative_segment_markers.pop(identifier)
        self.remove_widget(marker)

    def clear_speculative_segment_markers(self):
        for identifier in list(self.speculative_segment_markers.keys()):
            self.remove_speculative_segment_marker(identifier)

    def add_man(self, coords):
        '''Adds a man (a black piece) at the given coordinates.'''
        coords = tuple(coords)
        if coords in self.men or (coords[0] == self.ball.coords[0] and
                                  coords[1] == self.ball.coords[1]):
            return
        man = Man(coords=coords)
        self.men[coords] = man
        man.pos = self.coords_to_pos(coords)
        man.size = self.cell_size
        self.add_widget(man)

    def remove_man(self, coords):
        '''Removes the man at the given coords, if one exists.'''
        coords = tuple(coords)
        if coords not in self.men:
            return
        man = self.men.pop(coords)
        self.remove_widget(man)

    def clear_men(self):
        '''Removes all men from the gui board.'''
        for coords in list(self.men.keys()):
            self.remove_man(coords)

    def toggle_man(self, coords):
        '''Toggles a man at the given coords.'''
        coords = tuple(coords)
        if coords == self.abstractboard.ball_coords:
            return
        if coords in self.men:
            self.remove_man(coords)
        else:
            self.add_man(coords)

    def add_legal_move_marker(self, coords):
        '''Toggles a LegalMoveMarker at the given coords.'''
        coords = tuple(coords)
        if coords in self.legal_move_markers:
            return
        marker = LegalMoveMarker(pos=self.coords_to_pos(coords),
                                 size=self.cell_size,
                                 coords=coords)
        self.legal_move_markers[coords] = marker
        self.add_widget(marker)

    def remove_legal_move_marker(self, coords):
        '''Removes any LegalMoveMarker at the given coords.'''
        coords = tuple(coords)
        if coords not in self.legal_move_markers:
            return
        marker = self.legal_move_markers.pop(coords)
        self.remove_widget(marker)

    def clear_legal_move_markers(self):
        for marker_coords in list(self.legal_move_markers.keys()):
            marker = self.legal_move_markers.pop(marker_coords)
            self.remove_widget(marker)

    def clear_transient_ui_elements(self, *args):
        '''Removes any transient ui elements, e.g. LegalMoveMarkers.'''
        self.clear_legal_move_markers()
        self.clear_speculative_segment_markers()

    def reposition_ui_elements(self, *args):
        '''Checks the coords of any ui elements (stones , rectangles etc.),
        and repositions them appropriately with respect to the
        board. Called on resize/position.

        '''
        if self.ball is not None:
            self.ball.pos = self.coords_to_pos(self.abstractboard.ball_coords)
            self.ball.size = self.cell_size
        for man_coords, man in self.men.items():
            man.pos = self.coords_to_pos(man.coords)
            man.size = self.cell_size
        for marker_coords, marker in self.legal_move_markers.items():
            marker.pos = self.coords_to_pos(marker.coords)
            marker.size = self.cell_size
        self.goal_rectangle_size = (Vector([self.grid[0], 2]) *
                                    Vector(self.cell_size))
        self.top_rectangle_pos = self.coords_to_pos((0, self.grid[1]-2))
        self.bottom_rectangle_pos = self.coords_to_pos((0, 0))

        cell_size = self.cell_size
        for marker_coords, marker in self.speculative_segment_markers.items():
            start_coords = marker.start_coords
            end_coords = marker.end_coords
            start_pos = (Vector(self.coords_to_pos(start_coords)) +
                         Vector(self.cell_size)/2.)
            end_pos = (Vector(self.coords_to_pos(end_coords)) +
                       Vector(self.cell_size)/2.)
            marker.start_pos = start_pos
            marker_end_pos = end_pos

        self.move_marker.size = cell_size
        self.move_marker.on_coords()

    def on_cell_size(self, *args):
        cell_size = self.cell_size
        if self.ball:
            self.ball.size = self.cell_size
        for man_coords in self.men:
            man = self.men[man_coords]
            man.size = self.cell_size
        for marker_coords, marker in self.legal_move_markers.items():
            marker.size = self.cell_size
        for marker_coords, marker in self.speculative_segment_markers.items():
            start_coords = marker.start_coords
            end_coords = marker.end_coords
            start_pos = (Vector(self.coords_to_pos(start_coords)) +
                         Vector(self.cell_size)/2.)
            end_pos = (Vector(self.coords_to_pos(end_coords)) +
                       Vector(self.cell_size)/2.)
            marker.start_pos = start_pos
            marker_end_pos = end_pos

    def initialise_ball(self, *args):
        if self.ball is None:
            self.ball = Ball()
            self.ball.size = self.cell_size
            self.add_widget(self.ball)

        centre_coords = list(map(int, Vector(self.grid)/2.0))
        self.ball.pos = self.coords_to_pos(centre_coords)
        self.ball.coords = centre_coords

        self.abstractboard.ball_coords = centre_coords
        self.abstractboard.speculative_ball_coords = centre_coords

    def on_touch_down(self, touch):
        if self.collide_point(*touch.pos):
            self.touch = touch
            touch.grab(self)
            self.move_marker.anim_in()
            self.on_touch_move(touch)
        
    def on_touch_move(self, touch):
        if touch is not self.touch:
            return
        coords = self.pos_to_coords(touch.pos)
        coords = (coords[0], coords[1] + self.touch_offset)
        self.move_marker.coords = coords

    def on_touch_up(self, touch):
        if touch is not self.touch:
            return
        touch.ungrab(self)
        coords = self.pos_to_coords(touch.pos)
        self.do_move_at(coords)
        self.move_marker.anim_out()

    def do_move_at(self, coords):
        coords = tuple(coords)
        mode = self.touch_mode

        # Check if move is valid
        if coords in self.men:
            return
        if coords == tuple(self.ball.coords):
            return
        
        if mode == 'dormant':
            return
        elif mode == 'toggle_man':
            self.follow_instructions(self.abstractboard.toggle_man(coords))
        elif mode == 'play_man':
            instructions = self.abstractboard.play_man_at(coords)
            self.follow_instructions(instructions)
            if instructions is not None:
                self.advance_player()
            self.clear_speculative_segment_markers()
            self.switch_current_player()
        elif mode == 'move_ball':
            instructions = self.abstractboard.speculative_move_ball_to(coords)
            self.follow_instructions(instructions)

        self.clear_legal_move_markers()
        self.display_legal_moves()

    def on_current_player(self, *args):
        self.abstractboard.current_player = self.current_player

    def switch_current_player(self):
        self.current_player = {'top': 'bottom',
                               'bottom': 'top'}[self.current_player]
        if self.use_ai and self.current_player == 'bottom':
            self.do_ai_move()

    def do_ai_move(self, *args):
        self.abstractboard.do_ai_move()
        self.confirm_speculation()

    def confirm_speculation(self):
        instructions = self.abstractboard.confirm_speculation()
        if instructions is None:
            return
        self.follow_instructions(instructions)
        self.check_for_win()
        self.switch_current_player()
        self.touch_mode = 'play_man'

    def display_legal_moves(self, force=False):
        if self.show_legal_moves or force:
            legal_moves = self.abstractboard.speculative_legal_moves
            for coords in legal_moves:
                self.add_legal_move_marker(coords)

    def pos_to_coords(self, pos):
        '''Takes a pos in screen coordinates, and converts to a grid
        position.'''

        pos = Vector(pos)
        cell_size = Vector(self.cell_size)
        self_pos = Vector(self.pos) + Vector(cell_size) / 2.0
        padding = Vector(self.padding)
        diff = pos - (self_pos + padding * cell_size)
        number_of_steps = diff / cell_size

        return tuple(map(int, map(round, number_of_steps)))

    def coords_to_pos(self, coords):
        '''Takes coords on the board grid, and converts to a screen
        position.'''
        cell_size = Vector(self.cell_size)
        self_pos = Vector(self.pos)
        padding = Vector(self.padding)
        return self_pos + (padding + Vector(coords)) * cell_size

    def calculate_lines(self, *args):
        '''Calculates the points that should make up the board lines, and sets
        self.grid_points appropriately.'''

        pos = Vector(self.pos)
        padding = Vector(self.padding)
        shape = Vector(self.shape)
        grid = Vector(self.grid)
        cell_size = Vector(self.cell_size)

        # Initial offset
        init_offset = cell_size / 2.

        # grid corners
        bl = pos + init_offset + padding*cell_size
        br = bl + Vector((grid[0]-1) * cell_size[0], 0)
        tr = bl + (grid-Vector(1, 1)) * cell_size
        tl = bl + Vector(0, (grid[1]-1) * cell_size[1])

        points = [bl[0], bl[1], br[0], br[1],
                  tr[0], tr[1], tl[0], tl[1],
                  bl[0], bl[1]]

        cur_pos = bl
        dir = 1
        for x in range(grid[0]-1):
            cur_pos[0] += cell_size[0]
            points.append(cur_pos[0])
            points.append(cur_pos[1])
            cur_pos[1] += (grid[1]-1) * cell_size[1] * dir
            points.append(cur_pos[0])
            points.append(cur_pos[1])
            dir *= -1

        ydir = -1
        for y in range(grid[1]-1):
            cur_pos[1] += cell_size[1] * dir
            points.append(cur_pos[0])
            points.append(cur_pos[1])
            cur_pos[0] += (grid[0]-1) * cell_size[0] * ydir
            points.append(cur_pos[0])
            points.append(cur_pos[1])
            ydir *= -1

        self.grid_points = points

    def save_position(self, filen):
        '''Asks the AbstractBoard to save in the given filename.'''
        self.abstractboard.save_state(filen)

    def load_position(self, filen):
        '''Tries to load position from the given filename.'''
        self.abstractboard.load_file(filen)
        self.resync_with_abstractboard()
        

    def clear_all_transient_widgets(self):
        '''Clears all transient stones, markers etc.'''
        self.clear_transient_ui_elements()
        self.clear_men()
        self.clear_legal_move_markers()

    def resync_with_abstractboard(self):
        ab = self.abstractboard
        self.clear_all_transient_widgets()
        self.shape = ab.shape
        for coords in ab.man_coords:
            self.add_man(coords)
        self.display_legal_moves()
        Clock.schedule_once(self.sync_ball, 0)
        print('ab ball_coords are', ab.ball_coords)
        self.message = ab.message

    def sync_ball(self, *args):
        print('syncing ab ball_coords are', self.abstractboard.ball_coords)
        self.ball.pos = self.coords_to_pos(self.abstractboard.ball_coords)

    def reset(self, *args, **kwargs):
        self.abstractboard.reset()
        self.clear_all_transient_widgets()
        #self.clear_legal_move_markers()
        self.resync_with_abstractboard()
        self.initialise_ball()
        self.message = ''
        self.touch_mode = (kwargs['touch_mode'] if 'touch_mode' in kwargs
                           else 'play_man')
        self.game_mode = (kwargs['game_mode'] if 'game_mode' in kwargs
                          else 'normal')
