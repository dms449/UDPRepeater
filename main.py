from kivy.config import Config
Config.set('graphics', 'width', '500')
Config.set('graphics', 'height', '300')
from kivy.uix.actionbar import ActionItem
from kivy.app import App
import os.path
import sys
import pandas as pd
from kivy.core.window import Window
from kivy.uix.label import Label
from kivy.uix.switch import Switch
from kivy.uix.checkbox import CheckBox
from kivy.uix.treeview import TreeViewLabel,TreeView, TreeViewNode
from kivy.uix.boxlayout import BoxLayout
from kivy.uix.floatlayout import FloatLayout
from kivy.uix.bubble import Bubble,BubbleContent,BubbleButton
from kivy.properties import StringProperty, BooleanProperty, ObjectProperty, NumericProperty
from kivy.uix.popup import Popup
from kivy.uix.button import Button
from twisted.internet.protocol import DatagramProtocol
from twisted.internet import reactor
from twisted.internet.error import CannotListenError
from threading import Thread


class ActionSwitch(ActionItem,Switch):
    def __init__(self, **kwargs):
        super(ActionSwitch, self).__init__()


class SaveDialog(FloatLayout):
    save = ObjectProperty(None)
    dont_save = ObjectProperty(None)
    text_input = ObjectProperty(None)
    cancel = ObjectProperty(None)
    path = StringProperty(None)


class OutputConnection(BoxLayout, TreeViewLabel):
    def __init__(self, name, ip, port):
        super(OutputConnection, self).__init__()
        self.orientation = 'horizontal'
        self.size = (200, 30)
        self.add_widget(Label(text=name))
        self.add_widget(Label(text=ip))
        self.add_widget(Label(text=str(port)))
        self.add_widget(CheckBox(opacity = 0, disabled = True))
        self.name = name
        self.ip = ip
        self.port = port

    def show_error(self, text):
        """ Handles the creation ofself.root,  an Error pop-up window.

        :param text: (string) The text to be displayed on the popup.
        :return: None
        """
        content = ErrorDialog(error=text,cancel=self.dismiss_error)
        self._error = Popup(title="An error occured", content=content,size_hint=(None,None),size=(400,200))
        self._error.open()

    def dismiss_error(self):
        """ A handle to this function is passed to ErrorDialog during creation in order to close the window."""
        self._error.dismiss()


class InputConnection(DatagramProtocol, OutputConnection):
    """ This class reads data from a UDP port and then passes it on to each address in 'self.output'. """

    def __init__(self, name, ip, port, write_to_file):
        DatagramProtocol.__init__(self)
        OutputConnection.__init__(self, name, ip, port)

        # If the instantiation is meant to be an input, show recording box
        self.checkbox = self.children[0]
        self.checkbox.disabled = False
        self.checkbox.opacity = 1.0
        self.output = {}
        self.write = write_to_file

    def add_output(self, name, object):
        """ This method provides an interface for adding an output port to the dictionary self.output.

        :param name: (string) The name of the output port. This must be unique for this Input Connection instance.
        :param address: (tuple) = (ip, port) The address of the output connection
        :return:
        """
        if name in self.output.values():
            self.show_error('An output by this name already exists on this input.')
        else:
            self.output[name] = object

    def remove_output(self, name):
        """ Remove the output from the dictionary self.output

        :param name: (string) The name of an output
        :return:
        """
        try:
            return self.output.pop(name)
        except ValueError:
            error_msg = "The output '{}' was not listed under this input.".format(name)
            self.show_error(error_msg)

    def datagramReceived(self, data, address):
        """ Pass 'data' on to every connection in the dictionary 'output'.

        NOTE: Although this class is used to create both inputs and outputs,
        because, 'reactor' is never told to listen on this port when this
        class is being instantiated as an output, this method will never be
        called when used as an output.

        :param data: The byte data received on the port
        :param address: The address from whence the data came
        :return: None
        """
        if self.checkbox.active:
            self.write(self.name, data)
        for connection in self.output.values():
            self.transport.write(data, (connection.ip, connection.port))


class ErrorDialog(BoxLayout):
    error = StringProperty(None)
    cancel = ObjectProperty(None)


class RootWidget(BoxLayout):
    """
    Root Widget for the App
    """

    def __init__(self, **kwargs):
        super(RootWidget, self).__init__(**kwargs)
        self.running = False
        self.reactor = reactor
        self.inputs = {}
        self.ports = {}
        self.flag = True
        self.root = self.ids['Input_Output'].get_root()
        self.root.text = "Inputs"
        self.file = None
        self._last_path = os.getcwd()

        # initialize the keyboard
        self._keyboard = Window.request_keyboard(self._keyboard_closed, self)
        self._keyboard.bind(on_key_down=self._on_keyboard_down)

        self.ids['On_Off'].bind(active=self.toggle_on_off)

    #TODO: Reopen keyboard when a text input is not selected
    def _keyboard_closed(self):
        print('My keyboard has been closed!')
        self._keyboard.unbind(on_key_down=self._on_keyboard_down)
        self._keyboard = None

    #TODO: Allow the 'delete' key to be used to remove node
    def _on_keyboard_down(self, keyboard, keycode, text, modifiers):
        """ Define actions to take on keypresses from the keyboard.

        :param keyboard:
        :param keycode:
        :param text:
        :param modifiers:
        :return:
        """
        if keycode[1] == 'w':
            self.player1.center_y += 10
        elif keycode[1] == 's':
            self.player1.center_y -= 10
        elif keycode[1] == 'up':
            self.player2.center_y += 10
        elif keycode[1] == 'down':
            self.player2.center_y -= 10
        return True

    #TODO: consider if necessary and think of more potential problems
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

        if name == '' or ip == '' or port == '':
            self.show_error('There is an empty field.')
        elif name in self.inputs.keys():
            self.show_error("Error! A connection by this name already exists!")
        else:
            try:
                address = (ip, int(port))
                if self.inputs:
                    for input in self.inputs.values():
                        if address == (input.ip,input.port):
                            self.show_error(str(sys.exc_info()[0]))
                            break
                        else:
                            ADDSOCKET = True
                else:
                    ADDSOCKET = True

            except ValueError:
                self.show_error("invalid port number. Must be an integer.")

        if ADDSOCKET:
            self.add_connection()

    def add_connection(self):
        name = self.ids['name'].text
        ip = self.ids['ip'].text
        port = int(self.ids['port'].text)

        current_node = self.ids['Input_Output'].get_selected_node()

        # If no node is selected assume that they are adding an input
        if current_node is None:
            current_node = self.root

        # If the selected node is the root node, we are adding an input
        if current_node is self.root:
            node = InputConnection(name, ip, port, self.write_data)
            self.inputs[name] = node
            try:
                port = reactor.listenUDP(port, self.inputs[name], interface=ip)
                self.ids['Input_Output'].add_node(node)
                self.ports[name] = port
            except CannotListenError:
                self.show_error('Could not listen on port')

        # If the selected nodes parent is the root node, we are adding an output
        elif current_node.parent_node is self.root:
            try:
                if name in self.inputs[current_node.name].output.keys():
                    self.show_error('Cannot add the same output twice to the same input.')
                else:
                    node = OutputConnection(name, ip, port)
                    self.inputs[current_node.name].add_output(name, node)
                    self.ids['Input_Output'].add_node(node, current_node)
            except:
                self.show_error('invalid socket:\n'+str(sys.exc_info()[0]))
        else:
            self.show_error('Cannot add a connection to an output')

    def delete_connection(self):
        """ This method handles the deletion of either an input or output node. """
        # Get the current selected node.
        current_node = self.ids['Input_Output'].get_selected_node()

        # If no node is selected or if it is the root node show an error
        if current_node is None or current_node is self.root:
            self.show_error('Must select a valid node.')

        else:
            if current_node.parent_node is self.root:
                removable_outputs = list(current_node.output.values())

                for output in removable_outputs:
                    current_node.remove_output(output.name)
                    self.ids['Input_Output'].remove_node(output)
                self.ports.pop(current_node.name)
                self.ids['Input_Output'].remove_node(current_node)
                self.inputs.pop(current_node.name)

            elif current_node.parent_node.parent_node is self.root:
                self.inputs[current_node.parent_node.name].remove_output(current_node.name)
                self.ids['Input_Output'].remove_node(current_node)

            else:
                self.show_error('If this error is appearing something is very wrong.')

    def write_data(self, name, data):
        self.file.loc[len(self.file)] = [name, data]


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

    def show_save(self):
        self.get_parent_window().on_resize(800,500)
        content = SaveDialog(save=self.save_as, dont_save=self.dont_save,
                             cancel=self.dismiss_popup, path=self._last_path)
        self._popup = Popup(title="Save file", content=content)
        self._popup.open()

    def save_as(self, path, filename):
        if filename == '':
            self.show_error('Please enter a valid name')
        else:
            path_name = os.path.join(path, filename+'.csv')
            if os.path.isfile(path_name):
                self.show_error('a file by this name already exists.')
            else:
                self.file.to_csv(path_name)
                self.file = pd.DataFrame(columns = ['input', 'bytes'])
                self.dismiss_popup()
            self._last_path = path

    def dont_save(self):
        self.file = pd.DataFrame(columns = ['input', 'bytes'])
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
        return RootWidget(width=500,height=300)

if __name__ == "__main__":
    UDPApp().run()
