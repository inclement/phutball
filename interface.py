'''Widgets for the full app interface.'''

from kivy.uix.screenmanager import ScreenManager, Screen, SlideTransition
from kivy.properties import ListProperty

class PhutballManager(ScreenManager):
    previous = ListProperty([])
    def new_board(self, ai=True, from_file=None, ):
        '''Creates and moves to a new board screen.'''
        if not self.has_screen('board'):
            new_screen = GameScreen(name='board')
            self.add_widget(new_screen)
        self.current = 'board'

    def on_current(self, *args):
        super(PhutballManager, self).on_current(*args)
        current = self.current
        previous = self.previous
        if current in previous:
            print 'current in previous'
            self.previous = previous[:previous.index(current)]
        else:
            previous.append(current)

    def go_back(self, *args):
        if self.transition.is_active:
            return
        self.transition = SlideTransition(direction='right')
        if len(self.previous) < 2:
            self.previous = []
            self.current = 'home'
            return
        self.previous.pop()
        new = self.previous[-1]
        if new:
            self.current = new
        else:
            self.current = 'home'
        self.transition = SlideTransition(direction='left')
        

class GameScreen(Screen):
    '''Screen containing a BoardInterface'''
    

class HomeScreen(Screen):
    pass
