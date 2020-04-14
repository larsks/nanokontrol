import more_itertools as mit

from construct import (
    Struct,
    Const,
    Byte,
    Array,
    GreedyBytes,
    Adapter,
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

DataDumpGroupParams = Struct(
    'group_midi_channel'    / Byte,
    'slider_assign_type'    / Byte,
    'reserved1'             / Byte,
    'slider_control_number' / Byte,
    'slider_min_value'      / Byte,
    'slider_max_value'      / Byte,
    'reserved2'             / Byte,
    'knob_assign_type'      / Byte,
    'reserved3'             / Byte,
    'knob_control_number'   / Byte,
    'knob_min_value'        / Byte,
    'knob_max_value'        / Byte,
    'reserved4'             / Byte,
    'solo_assign_type'      / Byte,
    'solo_behavior'         / Byte,
    'solo_control_number'   / Byte,
    'solo_off_value'        / Byte,
    'solo_on_value'         / Byte,
    'reserved5'             / Byte,
    'mute_assign_type'      / Byte,
    'mute_behavior'         / Byte,
    'mute_control_number'   / Byte,
    'mute_off_value'        / Byte,
    'mute_on_value'         / Byte,
    'reserved6'             / Byte,
    'rec_assign_type'       / Byte,
    'rec_behavior'          / Byte,
    'rec_control_number'    / Byte,
    'rec_off_value'         / Byte,
    'rec_on_value'          / Byte,
    'reserved7'             / Byte,
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

DataDumpTransportParams = Struct(
    'transport_midi_channel' / Byte,
    'prev_track_params'      / DataDumpTransportButtonParams,
    'next_track_params'      / DataDumpTransportButtonParams,
    'cycle_params'           / DataDumpTransportButtonParams,
    'market_set_params'      / DataDumpTransportButtonParams,
    'prev_marker_params'     / DataDumpTransportButtonParams,
    'next_marker_params'     / DataDumpTransportButtonParams,
    'rew_params'             / DataDumpTransportButtonParams,
    'ff_params'              / DataDumpTransportButtonParams,
    'stop_params'            / DataDumpTransportButtonParams,
    'play_params'            / DataDumpTransportButtonParams,
    'rec_params'             / DataDumpTransportButtonParams,
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
