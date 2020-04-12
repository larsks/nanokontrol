#!/usr/bin/python

import click
import dbus
import logging
import mido
import pulsectl

import scaler

import evdev
from evdev import ecodes

LOG = logging.getLogger(__name__)

KEY_MAPPING = {
    42: 'KEY_STOP',
    41: 'KEY_PLAY',
    58: 'KEY_PREVIOUSSONG',
    59: 'KEY_NEXTSONG',
    60: ('KEY_LEFTMETA', 'KEY_HOME'),
    61: ('KEY_LEFTMETA', 'KEY_PAGEUP'),
    62: ('KEY_LEFTMETA', 'KEY_PAGEDOWN'),
}


class Controller(object):
    def __init__(self):
        self.pulse = pulsectl.Pulse('nanokontrol')
        self.input = evdev.UInput()

        self.session_bus = dbus.SessionBus()
        self.gsproxy = self.session_bus.get_object(
            'org.gnome.Shell', '/org/gnome/Shell')
        self.gsinterface = dbus.Interface(self.gsproxy, 'org.gnome.Shell')

    @property
    def sink(self):
        return self.pulse.get_sink_by_name('@DEFAULT_SINK@')

    @property
    def source(self):
        return self.pulse.get_source_by_name('@DEFAULT_SOURCE@')

    def toggle_input_mute(self):
        source = self.source
        if source.mute:
            self.pulse.mute(source, False)
            self.gsinterface.ShowOSD({
                "icon": "microphone-sensitivity-medium",
            })
        else:
            self.pulse.mute(source, True)
            self.gsinterface.ShowOSD({
                "icon": "microphone-sensitivity-muted",
            })

    def toggle_output_mute(self):
        sink = self.sink
        if sink.mute:
            self.pulse.mute(sink, False)
            self.gsinterface.ShowOSD({
                "icon": "audio-volume-medium",
            })
        else:
            self.pulse.mute(sink, True)
            self.gsinterface.ShowOSD({
                "icon": "audio-volume-muted",
            })

    def set_input_volume(self, val):
        source = self.source
        self.pulse.volume_set_all_chans(source, val)
        self.gsinterface.ShowOSD({
            "icon": "microphone-sensitivity-medium",
            "level": val,
        })

    def set_output_volume(self, val):
        sink = self.sink
        self.pulse.volume_set_all_chans(sink, val)
        self.gsinterface.ShowOSD({
            "icon": "audio-volume-medium",
            "level": val,
        })

    def key(self, keys, keystate):
        if not isinstance(keys, tuple):
            keys = (keys,)

        for key in keys:
            keyval = getattr(ecodes, key)
            self.input.write(ecodes.EV_KEY, keyval, keystate)

        self.input.syn()


@click.command()
@click.option('-v', '--verbose', count=True)
@click.option('-c', '--channel', default=0, type=int)
@click.option('-i', '--midi-in', 'midi_in_name')
@click.option('-l', '--list-inputs', is_flag=True)
def main(verbose, channel, midi_in_name, list_inputs):
    try:
        loglevel = [logging.WARNING, logging.INFO, logging.DEBUG][verbose]
    except IndexError:
        loglevel = logging.DEBUG

    logging.basicConfig(
        level=loglevel
    )

    if list_inputs:
        input_names = mido.get_input_names()
        print('\n'.join(input_names))
        return

    midi_in = mido.open_input()
    controller = Controller()
    m2p = scaler.Scaler(0, 127, 0, 1)

    for msg in midi_in:
        if msg.channel != channel:
            LOG.debug('ignoring message on channel %d: %s',
                      msg.channel, msg)
            continue

        LOG.debug('message: %s', msg)

        if msg.control == 48 and msg.value == 0:
            LOG.info('toggle output mute')
            controller.toggle_output_mute()
        elif msg.control == 49 and msg.value == 0:
            LOG.info('toggle input mute')
            controller.toggle_input_mute()
        elif msg.control == 0:
            scaled = m2p.scale(msg.value)
            LOG.info('set output volume %d %f', msg.value, scaled)
            controller.set_output_volume(scaled)
        elif msg.control == 1:
            scaled = m2p.scale(msg.value)
            LOG.info('set input volume %d %f', msg.value, scaled)
            controller.set_input_volume(scaled)
        elif msg.control in KEY_MAPPING:
            keys = KEY_MAPPING[msg.control]
            LOG.info('key %s', keys)
            controller.key(keys, msg.value == 127)


if __name__ == '__main__':
    main()
