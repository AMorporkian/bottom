""" asyncio-based rfc2812-compliant IRC Client """
import asyncio
from . import connection
from . import event
from . import pack
from . import unpack
__all__ = ["Client"]
__version__ = "1.0.0"


class Client(event.EventsMixin):
    __conn_cls = connection.Connection

    def __init__(self, host, port, *, encoding='UTF-8', ssl=True, loop=None):
        if loop is None:
            loop = asyncio.get_event_loop()
        super().__init__(unpack.parameters, loop=loop)
        self.connection = self.__conn_cls(host, port, self, ssl=ssl,
                                          encoding=encoding, loop=loop)

    def send(self, command, **kwargs):
        '''
        Send a message to the server.

        Examples
        --------
        client.send('nick', nick='weatherbot')
        client.send('privmsg', target='#python', message="Hello, World!")

        '''
        packed_command = pack.pack_command(command, **kwargs)
        self.connection.send(packed_command)

    async def connect(self):
        await self.connection.connect()

    async def disconnect(self):
        await self.connection.disconnect()

    @property
    def connected(self):
        return self.connection.connected

    async def run(self):
        ''' Run the client until it disconnects (without reconnecting) '''
        await self.connection.run()

    def on(self, command):
        '''
        Decorate a function to be invoked when a :param:`command` occurs.
        '''
        return super().on(command.upper())
