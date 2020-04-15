import construct


class InvalidSysexMessage(construct.core.ConstError):
    pass

class NoDeviceError(Exception):
    pass
