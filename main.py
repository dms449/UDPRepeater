from kivy.config import Config
Config.set('graphics', 'width', '500')
Config.set('graphics', 'height', '200')

from kivy.uix.actionbar import ActionItem
from kivy.app import App
import os.path
import sys
import pandas as pd
from kivy.core.window import Window
from kivy.uix.switch import Switch
from kivy.uix.treeview import TreeViewLabel,TreeView, TreeViewNode
from kivy.uix.boxlayout import BoxLayout
from kivy.uix.floatlayout import FloatLayout
from kivy.properties import StringProperty
from kivy.properties import ObjectProperty
from kivy.properties import NumericProperty
from kivy.uix.popup import Popup

from twisted.internet.protocol import DatagramProtocol
from twisted.internet import reactor

from threading import Thread

class ActionSwitch(ActionItem,Switch):
    def __init__(self, **kwargs):
       super(ActionSwitch, self).__init__()

class TreeViewToggleButton(TreeViewNode):
    pass

class SaveDialog(FloatLayout):
    save = ObjectProperty(None)
    dont_save = ObjectProperty(None)
    text_input = ObjectProperty(None)
    cancel = ObjectProperty(None)
    path = StringProperty(None)

class InSocketVisual(BoxLayout):
    name = StringProperty(None)
    ip = StringProperty(None)
    port = StringProperty(None)
    remove = ObjectProperty(None)
    check = ObjectProperty(None)
    select = ObjectProperty(None)
    socket = ObjectProperty(None)

class OutSocketVisual(BoxLayout):
    name = StringProperty(None)
    ip = StringProperty(None)
    port = StringProperty(None)
    remove = ObjectProperty(None)
    select = ObjectProperty(None)


class Connection(DatagramProtocol):
    """ This class reads data from a UDP port and then passes it on to each address in 'self.output'. """

    def __init__(self, name, ip, port):
        self.output = {}
        self.name = name
        self.ip = ip
        self.port = port

    def show_error(self,text):
        """ Handles the creation of an Error pop-up window.

        :param text: (string) The text to be displayed on the popup.
        :return: None
        """
        content = ErrorDialog(error=text,cancel=self.dismiss_error)
        self._error = Popup(title="An error occured", content=content,size_hint=(None,None),size=(400,200))
        self._error.open()

    def dismiss_error(self):
        """ A handle to this function is passed to ErrorDialog during creation in order to close the window."""
        self._error.dismiss()

    def add_output(self, name, address):
        """ This method provides an interface for adding an output port to the dictionary self.output.

        :param name: (string) The name of the output port. This must be unique for this Input Connection instance.
        :param address: (tuple) = (ip, port) The address of the output connection
        :return:
        """
        if name in self.output.values():
            self.show_error('T')
        else:
            self.output[name] = address

    def remove_output(self, name):
        """ Remove the output from the dictionary self.output

        :param name: (string) The name of an output
        :return:
        """
        try:
            self.output.pop(name)
        except ValueError:
            error_msg = "The output '{}' was not listed under this input.".format(name)
            self.show_error(error_msg)

    def datagramReceived(self, data, address):
        """ Pass 'data' on to every address in self.output

        :param data: The byte data received on the port
        :param address: The address from whence the data came
        :return: None
        """
        for address in self.output.values():
            self.transport.write(data, address)


class ErrorDialog(BoxLayout):
    error = StringProperty(None)
    cancel = ObjectProperty(None)


class RootWidget(BoxLayout):
    """
    Root Widget for the App
    """
    in_sockets = ObjectProperty({})
    out_sockets = ObjectProperty({})
    relationships = ObjectProperty({})
    recording_sockets = ObjectProperty({})
    file_name = StringProperty(None)
    end = NumericProperty(0)
    in_select = ObjectProperty(None)
    out_select = ObjectProperty(None)

    def __init__(self,**kwargs):
        super(RootWidget,self).__init__(**kwargs)
        self._keyboard = Window.request_keyboard(self._keyboard_closed, self, 'text')
        self._keyboard.bind(on_key_down=self._on_keyboard_down)
        self.running = False
        self.recording = False
        self.reactor = reactor
        self.inputs = {}
        self.selected = False
        self.flag = True

        self.ids['On_Off'].bind(active=self.toggle_on_off)
        self.ids['record'].bind(active=self.toggle_recording)

    def _keyboard_closed(self):
        print('My keyboard has been closed!')
        self._keyboard.unbind(on_key_down=self._on_keyboard_down)
        self._keyboard = None

    def _on_keyboard_down(self, keyboard, keycode, text, modifiers):
        if keycode == 13: # enter
            self.add_port()
        return True

    def select(self, instance, value=False):
        if value:
            self.selected = instance
        else:
            self.selected = False

    def add_connection(self):
        try:
            name = self.ids['name'].text
            ip = self.ids['ip'].text
            port = int(self.ids['port'].text)
        except ValueError:
            self.show_error('Please provide a valid value.')
        if not self.selected:
            self.inputs[name] = Connection(name,ip,port)
            self.ids['Input_Output'].add_node(TreeViewLabel(text=name, on_touch_down=self.select))
        elif self.selected.parent_node.text == 'Root':
            try:
                self.inputs[self.selected.text].add_output(name,(ip,port))
                self.ids['Input_Output'].add_node(TreeViewLabel(text=name, on_touch_down=self.select), self.selected)
            except:
                self.show_error('invalid socket:\n'+str(sys.exc_info()[0]))

        else:
            self.show_error('Cannot add a connection to an output')

    def delete_connection(self):
        pass

    def start_recording(self):
        pass

    def stop_recording(self):
        pass

    # ----------------------- Toggles the repeater on and off -----------------------
    # ------------------------- (Does not include recording) ----------------------
    def toggle_on_off(self, instance, value):
        if self.flag:
            for input in self.inputs.values():
                reactor.listenUDP(input.port, input, interface=input.ip)
            self.flag = False

        if self.running:
            if self.recording:
                self.show_error('Please stop recording first')
            reactor.stopListening()
            self.running = False
        else:
            Thread(target=reactor.run).start()
            self.running = True


    def toggle_recording(self, instance, value):
        pass

    def show_save(self):
        content = SaveDialog(save=self.save_as, dont_save=self.dont_save,cancel=self.dismiss_popup,path=self._last_path)
        self._popup = Popup(title="Save file", content=content,
                            size_hint=(0.9, 0.9))
        self._popup.open()

    def save_as(self, path, filename):
        if filename == '':
            self.show_error('Please enter a valid name')
        else:
            path_name = os.path.join(path,filename+'.csv')
            if os.path.isfile(path_name):
                self.show_error('a file by this name already exists.')
            else:
                self.file.to_csv(path_name)
                self.file = pd.DataFrame(columns = ['input','bytes'])
                self.recording = False
                self._toggle_play_icon()
                self.dismiss_popup()
            self._last_path = path

    def dont_save(self):
        self.recording = False
        self._toggle_play_pause()
        self.file = pd.DataFrame(columns = ['input','bytes'])
        self._popup.dismiss()

    def dismiss_popup(self):
        self._popup.dismiss()

    def show_error(self,text):
        """ Handles the creation of an Error pop-up window.

        :param text: (string) The text to be displayed on the popup.
        :return: None
        """
        content = ErrorDialog(error=text,cancel=self.dismiss_error)
        self._error = Popup(title="An error occured", content=content,size_hint=(None,None),size=(400,200))
        self._error.open()

    def dismiss_error(self):
        """ A handle to this function is passed to ErrorDialog during creation in order to close the window."""
        self._error.dismiss()

# ===============================  The main App ==============================
class UDPApp(App):
    def build(self):
        return RootWidget()

if __name__ == "__main__":
    UDPApp().run()
