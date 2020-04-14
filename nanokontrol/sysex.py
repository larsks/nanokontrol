import mido

__all__ = [
    'SysexMessage',
    'CurrentSceneRequest',
]


class SysexMessage(mido.Message):
    def __init__(self, data=None):
        if data is None:
            data = []

        super().__init__('sysex', data=data)


class CurrentSceneRequest(SysexMessage):
    def __init__(self, channel=0):
        super().__init__(data=[
            0x42, 0x40 | channel, 0x00, 0x01, 0x13, 0x00,
            0x1f, 0x10, 0x00
        ])
