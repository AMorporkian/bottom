import collections
import asyncio
from . import rfc


class Client(object):
    def __init__(self, host, port):
        self.handlers = Handlers()
        self.connection = Connection(host, port, self.handlers)

    def run(self):
        ''' Run the bot forever '''
        loop = asyncio.get_event_loop()
        loop.run_until_complete(self.connection.loop())

    def on(self, command):
        '''
        Decorate a function to be invoked on any :param:`command` message.

        Returns
        -------
        A function decorator that adds the decorated function to this
        :class:`~Client` handlers and returns the underlying function.

        Example
        -------

        bot = Client('localhost', 6697)

        @bot.on('connect')
        def autojoin(host, port):
            bot.send('USER', ['bottom.bot']*4)
            bot.send('NICK', 'bottom.bot')
            bot.send('JOIN', '#test')

        bot.run()
        '''
        def wrap(func):
            ''' Add the function to this client's handlers and return it '''
            self.handlers.add(command.upper(), func)
            return func
        return wrap


class Connection(object):
    def __init__(self, host, port, events):
        self.host, self.port = host, port
        self.reader, self.writer = None, None

        self.events = events
        self.encoding = 'UTF-8'
        self.ssl = True

    @asyncio.coroutine
    def connect(self):
        self.reader, self.writer = yield from asyncio.open_connection(
            self.host, self.port, ssl=self.ssl)
        yield from self.events('connect', self.host, self.port)

    @asyncio.coroutine
    def disconnect(self):
        if self.reader:
            self.reader.close()
            self.reader = None
        if self.writer:
            self.writer.close()
            self.writer = None
        yield from self.events('disconnect', self.host, self.port)

    @asyncio.coroutine
    def reconnect(self):
        yield from self.disconnect()
        yield from self.connect()

    @asyncio.coroutine
    def loop(self):
        self.connect()
        while True:
            msg = yield from self.read()
            if not msg:
                # Lost connection
                yield from self.reconnect()
                # Don't process the message
                continue
            yield from self.events(*rfc.parse(msg))

    def send(self, msg):
        self.writer.write((msg.strip() + '\n').encode(self.encoding))

    @asyncio.coroutine
    def read(self):
        try:
            msg = yield from self.read.readline()
            return msg.decode(self.encoding, 'ignore').strip()
        except EOFError:
            return ''


class Handlers(object):
    def __init__(self):
        self.handlers = collections.defaultdict(set)

    def add(self, event, handle):
        # Wrap the function in a coroutine so that we can
        # crete a task list and use asyncio.wait
        self.handlers[event].add(asyncio.coroutine(handle))

    @asyncio.coroutine
    def __call__(self, event, *args, **kwargs):
        tasks = [handle(*args, **kwargs) for handle in self.handlers[event]]
        asyncio.wait(tasks)
