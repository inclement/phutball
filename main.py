
from kivy.core.window import Window
Window.clearcolor = (1, 1, 1, 1)

from guiboard import BoardInterface, Message
from interface import PhutballManager, PhutballInterface

from kivy.app import App
from kivy.properties import ObjectProperty
from kivy.core.window import Window
from kivy.utils import platform


class PhutballApp(App):
    manager = ObjectProperty()
    popup = ObjectProperty(None, allownone=True)
    def build(self):
        self.bind(on_start=self.post_build_init)
        interface = PhutballInterface()
        manager = interface.manager
        self.manager = manager
        return interface

    def post_build_init(self,ev):
        if platform() == 'android':
            import android
            android.map_key(android.KEYCODE_BACK, 1001)

        win = Window
        win.bind(on_keyboard=self.key_handler)

    def key_handler(self, window, keycode1, keycode2, text, modifiers):
        if keycode1 == 27 or keycode1 == 1001:
            self.manager.go_back()
            return True
        return False

    def on_pause(self):
        return True


if __name__ == "__main__":
    PhutballApp().run()
