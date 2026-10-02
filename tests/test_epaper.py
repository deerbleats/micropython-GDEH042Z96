"""Host characterization of the class, including its constructor side effects.

The existing trailing demo raises NameError during normal import. Class tests
use the definitions executed before that error; they do not claim import works.
"""
import contextlib
import importlib.util
import io
from pathlib import Path
import sys
import types
import unittest
from unittest.mock import patch


class EpaperTests(unittest.TestCase):
    def setUp(self):
        self.events = []
        owner = self

        class Pin:
            OUT, IN, PULL_UP = 1, 0, 2
            def __init__(self, number, *args):
                self.number = number
                owner.events.append(('pin_init', number, args))
            def value(self, *args):
                owner.events.append(('pin', self.number, args))
                return 0  # BUSY is released; no physical timing is simulated.

        class SPI:
            def __init__(self, number): owner.events.append(('spi_init', number))
            def init(self, **kwargs): owner.events.append(('spi_config', kwargs))
            def write(self, data): owner.events.append(('spi_write', bytes(data)))

        def framebuffer(buffer, width, height, layout):
            self.events.append(('framebuffer', len(buffer), width, height, layout))
            return object()

        spec = importlib.util.spec_from_file_location(
            'epaper_under_test', Path(__file__).resolve().parents[1] / 'epaper4in2.py')
        self.module = importlib.util.module_from_spec(spec)
        fakes = {'machine': types.SimpleNamespace(Pin=Pin, SPI=SPI),
                 'framebuf': types.SimpleNamespace(FrameBuffer=framebuffer, MONO_HLSB=3),
                 'utime': types.SimpleNamespace(sleep=lambda n: self.events.append(('sleep', n)),
                                               sleep_ms=lambda n: self.events.append(('sleep_ms', n)))}
        with patch.dict(sys.modules, fakes):
            with self.assertRaisesRegex(NameError, "name 'w' is not defined"):
                spec.loader.exec_module(self.module)

    def test_constructor_initializes_and_clears_both_planes(self):
        with contextlib.redirect_stdout(io.StringIO()):
            epd = self.module.EPD_4in2_B()
        self.assertEqual((epd.width, epd.height), (400, 300))
        self.assertEqual((len(epd.buffer_black), len(epd.buffer_red)), (15000, 15000))
        self.assertIn(('spi_config', {'baudrate': 1000000}), self.events)
        writes = [e[1][0] for e in self.events if e[0] == 'spi_write']
        # Complete original command/data byte stream, including constructor Clear.
        init = [0x12, 0x74, 0x54, 0x7E, 0x3B, 0x2B, 0x04, 0x63,
                0x0C, 0x8B, 0x9C, 0x96, 0x0F, 0x01, 0x2B, 0x01, 0,
                0x11, 1, 0x44, 0, 0x31, 0x45, 0x2B, 1, 0, 0,
                0x3C, 1, 0x18, 0x80, 0x22, 0xB1, 0x20, 0x4E, 0, 0x4F, 0x2B, 1]
        self.assertEqual(writes, init + [0x24] + [255] * 15000 + [0x26] + [0] * 15000
                         + [0x22, 0xC7, 0x20])
        self.assertEqual([e for e in self.events if e[0].startswith('sleep')],
                         [('sleep', 0.01), ('sleep', 0.01), ('sleep_ms', 10)])

    def test_command_and_data_keep_per_byte_pin_order(self):
        epd = self.module.EPD_4in2_B.__new__(self.module.EPD_4in2_B)
        epd.dc_pin = self.module.Pin(2)
        epd.cs_pin = self.module.Pin(14)
        epd.spi = self.module.SPI(2)
        self.events.clear()
        epd.send_command(0x24)
        epd.send_data(0xFF)
        self.assertEqual(self.events, [('pin', 2, (0,)), ('pin', 14, (0,)),
                                     ('spi_write', b'\x24'), ('pin', 14, (1,)),
                                     ('pin', 2, (1,)), ('pin', 14, (0,)),
                                     ('spi_write', b'\xff'), ('pin', 14, (1,))])

    def test_reverse_rows_preserves_partial_rows_types_and_input(self):
        epd = self.module.EPD_4in2_B.__new__(self.module.EPD_4in2_B)
        for length in (0, 1, 49, 50, 51, 100, 101, 15000):
            for kind in (bytes, bytearray):
                data = kind(i % 256 for i in range(length))
                expected = b''.join(data[i:i + 50] for i in reversed(range(0, length, 50)))
                epd.buffer_black = data
                epd.buffer_red = data
                for method in (epd.test_blk, epd.test_red):
                    result = method()
                    self.assertEqual(result, expected)
                    self.assertIs(type(result), kind if length else bytes)
                    self.assertEqual(data, kind(i % 256 for i in range(length)))


if __name__ == '__main__':
    unittest.main()
