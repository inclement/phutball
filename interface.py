'''Widgets for the full app interface.'''

from kivy.uix.boxlayout import BoxLayout
from kivy.uix.actionbar import ActionBar
from kivy.uix.gridlayout import GridLayout
from kivy.uix.label import Label
from kivy.uix.button import Button
from kivy.uix.screenmanager import ScreenManager, Screen, SlideTransition
from kivy.properties import ListProperty, ObjectProperty

from os.path import exists
from glob import glob
import random

class NavBar(ActionBar):
    pass

class PhutballInterface(BoxLayout):
    manager = ObjectProperty()
    actionbar = ObjectProperty()

class PhutballManager(ScreenManager):
    def new_board(self, ai=True, from_file=None, ):
        '''Creates and moves to a new board screen.'''
        if not self.has_screen('board'):
            new_screen = GameScreen(name='board')
            self.add_widget(new_screen)
        board = self.get_screen('board').children[0].board
        board.use_ai = ai
        self.current = 'board'

    def on_current(self, *args):
        super(PhutballManager, self).on_current(*args)

    def go_back(self, *args):
        if self.transition.is_active:
            return
        self.transition = SlideTransition(direction='right')
        if self.current == 'board':
            self.current = 'home'
        self.transition = SlideTransition(direction='left')

    def try_save(self):
        '''Tries to save the current board in a new filename, automatically generated.

        This method is not intended for general use, only for
        development.

        '''
        filen = 'board'
        i = 0
        while exists(filen + '{}.phut'.format(i)):
            i += 1
        filen = filen + '{}.phut'.format(i)
        if self.has_screen('board'):
            screen = self.get_screen('board')
            board = screen.children[0].board
            board.save_position(filen)

    def try_load(self):
        '''Tries to load a random game.'''
        filens = glob('board*.phut')
        if not filens:
            return
        filen = random.choice(filens)
        self.new_board()
        screen = self.get_screen('board')
        board = screen.children[0].board
        board.load_position(filen)
        

            
        

class GameScreen(Screen):
    '''Screen containing a BoardInterface'''
    

class HomeScreen(Screen):
    pass


class ProblemChooserScreen(Screen):
    pass


class ProblemRow(GridLayout):
    pass

class ProblemButton(Button):
    pass

class ProblemLabel(Label):
    pass

class ProblemChooser(GridLayout):
    pass
