import os
import socket
import subprocess
from time import sleep

from .Client import Client
from .Server import Server
from .Flags import Flags


class Peer:
    """
    Connect the server and client together to create the application's peer
    """

    def __init__(self, name: str, port: int):
        self.flags = Flags(b"HEADER_START", b"HEADER_END", b"DATA_END", b"HEARTBEAT", b"FIN")
        self.server_address = '0.0.0.0'
        self.listen_port = port
        self.name = name
        self.retries = 3
        self.timeout = 2
        self.server: Server
        self.client = Client(self.flags, self.name)

    def listen(self, progress_handler, gui_init):
        """
        Create a server object and start the listening thread

        Very simple function which only passes some arguments to the server
        object constructor and starts the listening thread from the outside.

        :param function progress_handler: handle the information about file sending progress
        :param function gui_init: initialize GUI when message header is received
        """
        self.server = Server(self.listen_port, self.server_address, self.flags, self.name, progress_handler, gui_init)
        self.server.start()

    def send_file(self, hostname, port, file_path, gui_update):
        """
        Connect to the specified socket and send a file contents + header

        Decide if the file should be sent now or in a background process depending
        on the status of the other peer.

        :param str hostname: IP address of the target
        :param int port: port of the target
        :param str file_path: path to the to-be-sent file
        :param function gui_update: Refresh the GUI to update some elements
        """
        if not self.is_alive(hostname, port):
            self.client.available_func(False)
            run = [os.path.abspath("app.py"), '-bg', hostname, str(port), file_path, self.name]
            print("Creating a subprocess for sending a file")
            subprocess.Popen(" ".join(run), shell=True)
            return
        else:
            self.client.available_func(True)
        gui_update()
        self.client.connect(hostname, port)
        file_name = file_path.split("/")[-1]
        file = open(file_path, 'rb')
        self.client.send_file(file.read(), file_name)

    def is_alive(self, hostname, port):
        """
        Try to send a heartbeat message a specified amount of times

        :param str hostname: IP address of the target
        :param int port: port of the target
        :return: Is the other peer available
        :rtype: bool
        """
        for i in range(self.retries):
            if self.client.send_heartbeat(hostname, port, self.timeout):
                return True
            else:
                print(f"Peer not accessible trying again ({i + 1}/{self.retries})")
                continue
        print("Peer not accessible")
        return False

    def background_send(self, hostname, port, file_path, loop_interval):
        """
        Try to send a file every `loop_interval` amount of seconds

        :param str hostname: IP address of the target
        :param int port: port of the target
        :param str file_path: File path of the sending file
        :param int loop_interval: Amount of seconds to wait before checking again
        """
        file_name = file_path.split("/")[-1]
        file = open(file_path, 'rb')
        file_data = file.read()
        file.close()
        while not self.client.send_heartbeat(hostname, port, self.timeout):
            sleep(loop_interval)
        self.client.confirm_func = print
        self.client.connect(hostname, port)
        self.client.send_file(file_data, file_name)
        exit(0)
