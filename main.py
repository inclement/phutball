from guiboard import BoardInterface
from interface import PhutballManager

from kivy.app import App


class PhutballApp(App):
    def build(self):
        return PhutballManager()


if __name__ == "__main__":
    PhutballApp().run()
