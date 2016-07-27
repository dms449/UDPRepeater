from kivy.config import Config
Config.set('graphics', 'width', '500')
Config.set('graphics', 'height', '200')

from kivy.uix.actionbar import ActionItem
from kivy.app import App
import os.path
import sys
import pandas as pd
from kivy.core.window import Window
from kivy.uix.textinput import TextInput
from kivy.uix.switch import Switch
from kivy.uix.treeview import TreeViewLabel,TreeView, TreeViewNode
from kivy.uix.boxlayout import BoxLayout
from kivy.uix.floatlayout import FloatLayout
from kivy.uix.bubble import Bubble,BubbleContent,BubbleButton
from kivy.properties import StringProperty
from kivy.properties import ObjectProperty
from kivy.properties import NumericProperty
from kivy.uix.popup import Popup
from kivy.uix.behaviors.focus import FocusBehavior

from twisted.internet.protocol import DatagramProtocol
from twisted.internet import reactor
from twisted.internet.error import CannotListenError

from threading import Thread


class MyBubble(Bubble):
    pass


class NewTreeViewLabel(TreeViewLabel):
    def __init__(self,**kwargs):
        super(NewTreeViewLabel, self).__init__(**kwargs)
        # self.doubletap = doubletap_func

    def on_touch_down(self, touch):
        if touch.is_double_tap:
            self.add_widget(MyBubble())
        super(NewTreeViewLabel, self).on_touch_down(touch)


class ActionSwitch(ActionItem,Switch):
    def __init__(self, **kwargs):
       super(ActionSwitch, self).__init__()


class SaveDialog(FloatLayout):
    save = ObjectProperty(None)
    dont_save = ObjectProperty(None)
    text_input = ObjectProperty(None)
    cancel = ObjectProperty(None)
    path = StringProperty(None)


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
        self.running = False
        self.recording = False
        self.reactor = reactor
        self.inputs = {}
        self.nodes = {}
        self.ports = {}
        self.selected = False
        self.flag = True

        # initialize the keyboard
        self._keyboard = Window.request_keyboard(self._keyboard_closed, self)
        self._keyboard.bind(on_key_down=self._on_keyboard_down)

        self.ids['On_Off'].bind(active=self.toggle_on_off)
        self.ids['record'].bind(active=self.toggle_recording)

    def _keyboard_closed(self):
        print('My keyboard has been closed!')
        self._keyboard.unbind(on_key_down=self._on_keyboard_down)
        self._keyboard = None

    def _on_keyboard_down(self, keyboard, keycode, text, modifiers):
        if keycode[1] == 'w':
            self.player1.center_y += 10
        elif keycode[1] == 's':
            self.player1.center_y -= 10
        elif keycode[1] == 'up':
            self.player2.center_y += 10
        elif keycode[1] == 'down':
            self.player2.center_y -= 10
        return True

    def validate_input(self, instance=False, value=False):
        """ Determine if the information provided is valid. If it is, add the connection.
        Otherwise, alert the user of the error.

        :param instance:
        :param value:
        :return:
        """
        ADDSOCKET = False
        name = self.ids['name'].text
        ip = self.ids['ip'].text
        port = self.ids['port'].text
        # try:
        address = (ip,int(port))
        # except ValueError:
        #     self.show_error("invalid port number. Must be an integer.")

        if name == '' or ip == '' or port == '':
            self.show_error('There is an empty field.')
        elif name in self.inputs.keys():
            self.show_error("Error! A connection by this name already exists!")
        else:
            if self.inputs:
                for input in self.inputs.values():
                    if address == (input.ip,input.port):
                        self.show_error(str(sys.exc_info()[0]))
                        break
                    # elif address in input.output.values():
                    #     self.show_error("A socket is already using this ip and port.\nPlease try another one.")
                    else:
                        ADDSOCKET = True
            else:
                ADDSOCKET = True

        if ADDSOCKET:
            self.add_connection()



    def select(self, instance, value=False):
        if value:
            self.selected = instance
        else:
            self.selected = False


    def add_connection(self):
        name = self.ids['name'].text
        ip = self.ids['ip'].text
        port = int(self.ids['port'].text)
        if not self.selected:
            self.inputs[name] = Connection(name,ip,port)
            try:
                node = NewTreeViewLabel(text=name, on_touch_down=self.select)
                port = reactor.listenUDP(port, self.inputs[name], interface=ip)
                self.ids['Input_Output'].add_node(node)
                self.nodes[name] = node
                self.ports[name] = port
            except CannotListenError:
                self.show_error('Could not listen on port')

        elif self.selected.parent_node.text == 'Root':
            try:
                self.inputs[self.selected.text].add_output(name,(ip,port))
                node = NewTreeViewLabel(text=name, on_touch_down=self.select)
                self.ids['Input_Output'].add_node(node, self.selected)
                self.nodes[name] = node
            except:
                self.show_error('invalid socket:\n'+str(sys.exc_info()[0]))

        else:
            self.show_error('Cannot add a connection to an output')

    def delete_connection(self):
        """ This method handles the deletion of either an input or output node. """
        if not self.recording and not self.running:

            # Delete an input node
            if self.selected.parent_node.text == 'Root':
                name = self.selected.text
                self.inputs.pop(name)
                self.ports.pop(name)

                # Remove the node from the TreeView
                node = self.nodes.pop(name)
                self.ids['Input_Output'].remove_node(node)

            # Delete and output node
            elif self.selected.parent_node.parent_node.text == 'Root':
                name = self.selected.text
                self.inputs[self.selected.parent_node.text].remove_output(name)

                # Remove the node from the TreeView
                node = self.nodes.pop(name)
                self.ids['Input_Output'].remove_node(node)
        else:
            self.show_error('You must stop running and recording in order to add/remove connections.')

    def start_recording(self):
        pass

    def stop_recording(self):
        pass

    # ----------------------- Toggles the repeater on and off -----------------------
    # ------------------------- (Does not include recording) ----------------------
    def toggle_on_off(self, instance, value):
        """ This method toggles whether or not the program is reading the input ports. This
        includes what is done with the inputs and also affects the recording.

        :param instance: The object calling this method
        :param value: A value for it
        :return:
        """
        if self.flag:
            Thread(target=reactor.run).start()
            self.ids['record'].disabled = False
            self.flag = False
            self.running = True
        else:
            if self.running:
                # If the program is recording, warn the user and do not allow it to stop reading
                #  the ports until the recording has been shut off
                if self.recording:
                    self.show_error('Please stop recording first')

                # If the program is not recording, tell each input port to stop reading and set
                #   the record button so that it cannot but used.
                else:
                    for port in self.ports.values():
                        port.stopReading()
                    self.ids['record'].disabled = True
                    self.running = False
            else:
                # If the program is not running, tell each input port to start reading and enable the
                # record switch
                for port in self.ports.values():
                    port.startReading()
                self.ids['record'].disabled = False
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
