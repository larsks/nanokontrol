#!/usr/bin/python

import json
import logging
import mido
import pulsectl
import queue
import time

from nanokontrol import device
from nanokontrol import datatypes
from nanokontrol import exc
from nanokontrol import sysex

LOG = logging.getLogger(__name__)

logging.basicConfig(level='DEBUG')

transport_control_names = [
    'prev_track',
    'next_track',
    'cycle',
    'market_set',
    'prev_marker',
    'next_marker',
    'rew',
    'ff',
    'stop',
    'play',
    'rec',
]


class ControlEvent(object):
    def __init__(self, name, value):
        self.name = name
        self.value = value
    
    def __str__(self):
        return '<Event {0.name}:{0.value}>'.format(self)


class Controller(object):
    def __init__(self):
        self.q = queue.Queue()
        self.nk = device.Nanokontrol(
            midi_in_cb=self.midi_in_cb
        )

        self.pulse = pulsectl.Pulse('nanokontroller')
        self.pulse.event_callback_set(self.pulse_ev_cb)
        self.pulse.event_mask_set(
            pulsectl.PulseEventMaskEnum.sink,
            pulsectl.PulseEventMaskEnum.source,
        )

        self._discovery_complete = False

    def discover(self):
        LOG.debug('sending current scene dump request')
        self.nk.send(sysex.CurrentSceneRequest())

        while True:
            LOG.debug('waiting for current scene dump')
            evt_type, evt = self.q.get()
            if evt_type == 'midi' and evt.type == 'sysex':
                try:
                    msg = datatypes.KorgMessage.parse(bytes(evt.data))
                    dump_response = datatypes.DataDumpResponse.parse(msg.data)
                    dump_params = datatypes.DataDumpParams.parse(dump_response.data)
                except exc.InvalidMessage:
                    LOG.info('received unknown sysex message: %s', evt)
                    continue

                self.build_control_map(dump_params)
                break

    def build_control_map(self, params):
        LOG.info('building control map')
        controls = {}
        messages = {}

        for group in range(8):
            p = params['group_parameters'][group]

            channel = (
                params.common_parameters.global_midi_channel
                if p.group_midi_channel == 0x10
                else p.group_midi_channel
            )

            for control in ['slider', 'knob', 'solo', 'mute', 'rec']:
                if control in ['solo', 'mute', 'rec']:
                    control_type = 'button'
                    led = True
                else:
                    control_type = 'variable'
                    led = False

                k = (channel, p['{}_control_number'.format(control)])
                name = '{}-group-{}'.format(control, group)

                spec = {
                    'name': name,
                    'channel': k[0],
                    'control': k[1],
                    'type': control_type,
                    'led': led,
                }

                messages[k] = spec
                controls[name] = spec

            transport_params = params.transport_parameters
            channel = (
                params.common_parameters.global_midi_channel
                if transport_params.transport_midi_channel == 0x10
                else transport_params.transport_midi_channel
            )
            for control in transport_control_names:
                info = transport_params['{}_params'.format(control)]
                k = (channel, info.control_number)
                name = 'transport-{}'.format(control)

                spec = {
                    'name': name,
                    'channel': k[0],
                    'control': k[1],
                    'type': 'button',
                    'led': False,
                }

                messages[k] = spec
                controls[name] = spec

        self.controls = controls
        self.messages = messages

    def set_led(self, name, value):
        LOG.debug('set led %s value %s', name, value)
        control = self.controls[name]
        msg = mido.Message('control_change',
                           channel=control['channel'],
                           control=control['control'],
                           value=127 if value else 0)
        LOG.debug('sending %s', msg)
        self.nk.send(msg)

    def led_test(self):
        for name, control in self.controls.items():
            if control['led']:
                self.set_led(name, 1)
            time.sleep(0.01)
        for name, control in self.controls.items():
            if control['led']:
                self.set_led(name, 0)
            time.sleep(0.01)

    def start(self):
        self.discover()
        self.led_test()

        while True:
            LOG.debug('waiting for events')
            self.pulse.event_listen()
            self.process_q()

    def process_q(self):
        while True:
            try:
                evt_type, evt = self.q.get_nowait()
                LOG.debug('found %s event %s', evt_type, evt)
                if evt_type == 'midi':
                    self.handle_midi_event(evt)
                elif evt_type == 'pulse':
                    ...
                elif evt_type == 'control':
                    ...
            except queue.Empty:
                break

    def handle_midi_event(self, evt):
        if evt.type == 'control_change':
            key = (evt.channel, evt.control)
            if key in self.messages:
                event_name = self.messages[key]
                LOG.debug('channel %d control %d maps to %s',
                          evt.channel, evt.control, event_name)
                self.q.put(('control', ControlEvent(event_name, evt.value)))

    def pulse_ev_cb(self, event=None):
        '''Place a pulse event onto the queue and stop the
        pulsectl event loop.
        '''
        self.q.put(('pulse', event))
        raise pulsectl.PulseLoopStop()

    def midi_in_cb(self, msg):
        '''Place a midi event onto the queue and stop the
        pulsectl event loop.
        '''
        self.q.put(('midi', msg))
        self.pulse.event_listen_stop()

    def handle_pulse_event(self, event):
        sink = self.pulse.get_sink_by_name('@DEFAULT_SINK@')
        source = self.pulse.get_source_by_name('@DEFAULT_SOURCE@')

        if event.index == sink.index:
            print('change on default sink')
            value = 127 if sink.mute else 0
            msg = mido.Message('control_change', control=48, value=value)
            print('sending', msg)
            self.nk.send(msg)
        elif event.index == source.index:
            print('change on default source')
            value = 127 if source.mute else 0
            msg = mido.Message('control_change', control=49, value=value)
            print('sending', msg)
            self.nk.send(msg)

if __name__ == '__main__':
    c = Controller()
    c.start()
