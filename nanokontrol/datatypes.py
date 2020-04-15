import more_itertools as mit

from construct import (
    Adapter,
    Array,
    Byte,
    Computed,
    Const,
    GreedyBytes,
    Struct,
    Terminated
)

__all__ = [
    'KorgMessage',
    'DataDumpGroupParams',
    'DataDumpCommonParams',
    'DataDumpTransportButtonParams',
    'DataDumpTransportParams',
    'DataDumpParams',
    'DataDumpResponse',
]


class EncodedBytesAdapter(Adapter):
    '''Decode 8-bit data from Nanokontrol.

    The Nanokontrol sends 7 8-bit bytes of data encoded
    as 8 7-bit bytes.

        Data (1set = 8bit x 7Byte)
        b7     ~      b0   b7     ~      b0   b7   ~~    b0   b7     ~      b0
        +-+-+-+-+-+-+-+-+  +-+-+-+-+-+-+-+-+  +-+-+-~~-+-+-+  +-+-+-+-+-+-+-+-+
        | | | | | | | | |  | | | | | | | | |  | | |    | | |  | | | | | | | | |
        +-+-+-+-+-+-+-+-+  +-+-+-+-+-+-+-+-+  +-+-+-~~-+-+-+  +-+-+-+-+-+-+-+-+
              7n+0               7n+1          7n+2 ~~ 7n+5         7n+6
     
         MIDI Data (1set = 7bit x 8Byte)
           b7b7b7b7b7b7b7     b6    ~     b0     b6 ~~    b0     b6    ~     b0
        +-+-+-+-+-+-+-+-+  +-+-+-+-+-+-+-+-+  +-+-+-~~-+-+-+  +-+-+-+-+-+-+-+-+
        |0| | | | | | | |  |0| | | | | | | |  |0| |    | | |  |0| | | | | | | |
        +-+-+-+-+-+-+-+-+  +-+-+-+-+-+-+-+-+  +-+-+-~~-+-+-+  +-+-+-+-+-+-+-+-+
        7n+6,5,4,3,2,1,0         7n+0          7n+1 ~~ 7n+5         7n+6
    '''

    def _decode(self, obj, ctx, path):
        chunker = mit.grouper(obj, 8)
        res = []
        for inset in chunker:
            outset = [0] * 7
            for i, bits in enumerate(inset[1:], start=1):
                if bits is None:
                    break

                outset[i - 1] = bits | (((inset[0] >> (i - 1)) & 1) << 7)

            res.extend(outset)

        return bytes(res)

    def _encode(self, obj, ctx, path):
        chunker = mit.grouper(obj, 7)
        res = []
        for inset in chunker:
            outset = [0] * 8
            for i, bits in enumerate(inset):
                if bits is None:
                    break

                outset[i + 1] = bits & 0x7f
                outset[0] = outset[0] | (((bits & 0x80) >> 7) << i)

            res.extend(outset)

        return bytes(res)


KorgMessage = Struct(
    'korg_exclusive'      / Const(b'\x42'),
    'global_midi_channel' / Byte,
    'software_project'    / Const(b'\x00\x01\x13\x00'),
    'format'              / Byte,
    'func_id_or_len'      / Byte,
    'data'                / GreedyBytes,
)

DataDumpGroupControlVariable = Struct(
    'type'           / Computed('variable'),
    'assign_type'    / Byte,
    'reserved1'      / Byte,
    'control_number' / Byte,
    'min_value'      / Byte,
    'max_value'      / Byte,
    'reserved2'      / Byte,
)

DataDumpGroupControlButton = Struct(
    'type'           / Computed('button'),
    'assign_type'    / Byte,
    'behavior'       / Byte,
    'control_number' / Byte,
    'off_value'      / Byte,
    'on_value'       / Byte,
    'reserved1'      / Byte,
)

DataDumpGroupControls = Struct(
    'slider' / DataDumpGroupControlVariable,
    'knob'   / DataDumpGroupControlVariable,
    'solo'   / DataDumpGroupControlButton,
    'mute'   / DataDumpGroupControlButton,
    'rec'    / DataDumpGroupControlButton,
)

DataDumpGroupParams = Struct(
    'midi_channel'    / Byte,
    'controls' / DataDumpGroupControls,
)

DataDumpCommonParams = Struct(
    'global_midi_channel' / Byte,
    'control_mode'        / Byte,
    'led_mode'            / Byte,
)

DataDumpTransportButtonParams = Struct(
    'button_assign_type' / Byte,
    'button_behavior'    / Byte,
    'control_number'     / Byte,
    'off_value'          / Byte,
    'on_value'           / Byte,
    'reserved1'          / Byte,
)

DataDumpTransportControlParams = Struct(
    'prev_track'      / DataDumpTransportButtonParams,
    'next_track'      / DataDumpTransportButtonParams,
    'cycle'           / DataDumpTransportButtonParams,
    'market_set'      / DataDumpTransportButtonParams,
    'prev_marker'     / DataDumpTransportButtonParams,
    'next_marker'     / DataDumpTransportButtonParams,
    'rew'             / DataDumpTransportButtonParams,
    'ff'              / DataDumpTransportButtonParams,
    'stop'            / DataDumpTransportButtonParams,
    'play'            / DataDumpTransportButtonParams,
    'rec'             / DataDumpTransportButtonParams,
)

DataDumpTransportParams = Struct(
    'midi_channel' / Byte,
    'controls'     / DataDumpTransportControlParams,
)

DataDumpParams = Struct(
    'common_parameters'    / DataDumpCommonParams,
    'group_parameters'     / Array(8, DataDumpGroupParams),
    'transport_parameters' / DataDumpTransportParams,
    'custom_daw_assign'    / Array(10, Byte),
    'reserved'             / Array(15, Byte),
    Terminated
)

DataDumpResponse = Struct(
    'structure'    / Byte,
    'num_data_msb' / Byte,
    'num_data_lsb' / Byte,
    'function_id'  / Byte,
    'data'         / EncodedBytesAdapter(Array(388, Byte)),
)
