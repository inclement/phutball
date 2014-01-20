from guiboard import BoardInterface

from kivy.app import App


class PhutballApp(App):
    def build(self):
        return BoardInterface()


if __name__ == "__main__":
    PhutballApp().run()
