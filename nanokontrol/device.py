import logging
import mido

LOG = logging.getLogger(__name__)


class NoDeviceError(Exception):
    pass


class Nanokontrol(object):
    def __init__(self, name=None, midi_in_cb=None):
        if name is None:
            name = self.discover()

        if name is None:
            raise NoDeviceError()

        self._in = mido.open_input(name)
        self._out = mido.open_output(name)

        if midi_in_cb:
            self._in.callback = midi_in_cb

    def discover(self):
        for name in mido.get_input_names():
            if name.startswith('nanoKONTROL2'):
                LOG.info('found device %s', name)
                return name

    def send(self, msg):
        return self._out.send(msg)

    def receive(self):
        return self._in.receive()

    def __iter__(self):
        return iter(self._in)
