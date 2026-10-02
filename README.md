# GDEH042Z96 MicroPython driver

`epaper4in2.py` contains the `EPD_4in2_B` driver for a 400×300 display.
Construction immediately initializes the device and clears both planes.
The refactor shares the 50-byte row reversal used by `test_blk` and `test_red`;
it preserves byte/bytearray return types, partial rows and empty-buffer behavior.
SPI command bytes, per-byte DC/CS transitions, default pins, baud rate,
framebuffer dimensions, startup clearing and delays are unchanged.

## Known existing import problem

The file ends with an active example that references undefined `w`, `h` and
`newframebuf`. A normal import raises `NameError` for `w` after defining the
class. This pre-existing defect is intentionally not fixed by the pure
refactor. Moving/removing the demo is a separate behavior change.

## Host characterization tests

```sh
python3 -B -m unittest discover -s tests -v
```

The tests explicitly assert the import failure and exercise the definitions
already executed before it, using fake Pin/SPI/framebuffer/clock objects.
They check the constructor's entire command/data stream (including the clear),
per-byte pin transitions, and row reversal. They do not claim that ordinary
import succeeds or validate real MicroPython framebuffers, BUSY timing,
display orientation, refresh quality or electrical operation.
