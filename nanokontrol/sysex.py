import mido


class Sysex(object):
    @property
    def message(self):
        return mido.Message('sysex', data=self.bytes)


class CurrentSceneRequest(Sysex):
    def __init__(self, channel=0):
        self.channel = 0

    @property
    def bytes(self):
        return [
            0x42, 0x40 | self.channel, 0x00, 0x01, 0x13, 0x00,
            0x1f, 0x10, 0x00
        ]
