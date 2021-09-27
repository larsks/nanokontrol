import logging
import mido
import time

from nanokontrol import datatypes
from nanokontrol import exc
from nanokontrol import sysex

LOG = logging.getLogger(__name__)


class Nanokontrol(object):
    def __init__(self, name=None, midi_in_cb=None):
        if name is None:
            name = self.discover()

        if name is None:
            raise exc.NoDeviceError()

        self._port = mido.open_ioport(name)

        if midi_in_cb:
            self._in.callback = midi_in_cb

    def discover(self):
        for name in mido.get_ioport_names():
            if name.startswith('nanoKONTROL2'):
                LOG.info('found port %s', name)
                return name

    def send(self, msg, **kwargs):
        return self._port.send(msg, **kwargs)

    def receive(self, **kwargs):
        return self._port.receive(**kwargs)

    def __iter__(self):
        return iter(self._port)

    def get_current_config(self):
        for retries in range(5):
            LOG.info('sending current scene dump request')
            self.send(sysex.CurrentSceneRequest())

            for i in range(2000):
                msg = self.receive(block=False)
                if msg is None:
                    time.sleep(0.001)
                    continue

                LOG.debug('message %s', msg)

                try:
                    res = datatypes.KorgMessage.parse(bytes(msg.data))
                    dump_response = datatypes.DataDumpResponse.parse(res.data)
                    dump_params = datatypes.DataDumpParams.parse(dump_response.data)
                    return dump_params
                except exc.InvalidSysexMessage:
                    LOG.info('received unknown sysex message: %s', msg)
                    continue

        raise exc.NoDeviceError()

    def build_control_map(self, scene):
        LOG.info('building control map')
        controls = {}
        messages = {}

        group_params = scene.group_parameters
        for groupnum, group in enumerate(group_params):
            channel = (
                scene.common_parameters.global_midi_channel
                if group.midi_channel == 0x10
                else group.midi_channel
            )

            for control, params in group.controls.items():
                if control.startswith('_'):
                    continue

                k = '{}:{}'.format(channel, params.control_number)
                name = '{}-group-{}'.format(control, groupnum)

                spec = {
                    'name': name,
                    'channel': channel,
                    'control': params.control_number,
                    'type': params.type,
                    'led': params.type == 'button'
                }

                messages[k] = spec
                controls[name] = spec

        transport_params = scene.transport_parameters
        channel = (
            scene.common_parameters.global_midi_channel
            if transport_params.midi_channel == 0x10
            else transport_params.midi_channel
        )
        for control, params in transport_params.controls.items():
            if control.startswith('_'):
                continue

            k = '{}:{}'.format(channel, params.control_number)
            name = 'transport-{}'.format(control)

            spec = {
                'name': name,
                'channel': channel,
                'control': params.control_number,
                'type': 'button',
                'led': False,
            }

            messages[k] = spec
            controls[name] = spec

        return {
            'controls': controls,
            'messages': messages,
        }
