import ctypes
import time
import numpy as np

from picosdk.ps4000a import ps4000a as ps
from picosdk.functions import adc2mV, assert_pico_ok

from oscilloscope import Oscilloscope


class PicoScope4424A(Oscilloscope):
    """PicoScope 4424A implementation using PicoSDK ps4000a."""

    CHANNEL_MAP = {
        "A": ps.PS4000A_CHANNEL["PS4000A_CHANNEL_A"],
        "B": ps.PS4000A_CHANNEL["PS4000A_CHANNEL_B"],
        "C": ps.PS4000A_CHANNEL["PS4000A_CHANNEL_C"],
        "D": ps.PS4000A_CHANNEL["PS4000A_CHANNEL_D"],
    }

    COUPLING_MAP = {
        "AC": ps.PS4000A_COUPLING["PS4000A_AC"],
        "DC": ps.PS4000A_COUPLING["PS4000A_DC"],
    }

    DIRECTION_MAP = {
        "RISING": ps.PS4000A_THRESHOLD_DIRECTION["PS4000A_RISING"],
        "FALLING": ps.PS4000A_THRESHOLD_DIRECTION["PS4000A_FALLING"],
    }

    VOLTAGE_RANGE_MAP={
        0.01:   0,
        0.02:   1,
        0.05:   2,
        0.1:    3,
        0.2:    4,
        0.5:    5,
        1.0:    6,
        2.0:    7,
        5.0:    8,
        10.0:   9,
        20.0:   10,
        50.0:   11
    }

    def __init__(self):
        super().__init__()
        self.status = {}
        self.chandle = ctypes.c_int16()
        self.channel_settings = {}
        self.timebase = None
        self.time_interval_ns = None
        self.max_adc = None

    def open(self):
        if self.is_open:
            return

        self.status["openunit"] = ps.ps4000aOpenUnit(
            ctypes.byref(self.chandle),
            None,
        )
        assert_pico_ok(self.status["openunit"])

        self.is_open = True
        print("PicoScope 4424A opened.")

    def close(self):
        if not self.is_open:
            return

        self.status["stop"] = ps.ps4000aStop(self.chandle)
        assert_pico_ok(self.status["stop"])

        self.status["close"] = ps.ps4000aCloseUnit(self.chandle)
        assert_pico_ok(self.status["close"])

        self.is_open = False
        print("PicoScope closed.")

    def configure_channel(
        self,
        channel,
        enabled=True,
        coupling="AC",
        voltage_range=None,
        offset=0.0,
    ):
        if not self.is_open:
            raise RuntimeError("Open the PicoScope before configuring channels.")

        channel = channel.upper()
        coupling = coupling.upper()

        if channel not in self.CHANNEL_MAP:
            raise ValueError(f"Invalid channel: {channel}")

        if coupling not in self.COUPLING_MAP:
            raise ValueError("coupling must be 'AC' or 'DC'")

        if voltage_range is None:
            voltage_range =10 # ps.PS4000A_RANGE["PS4000A_100MV"]

        status_key = f"channel_{channel}"

        range_enum=self.VOLTAGE_RANGE_MAP[voltage_range]

        self.status[status_key] = ps.ps4000aSetChannel(
            self.chandle,
            self.CHANNEL_MAP[channel],
            int(enabled),
            self.COUPLING_MAP[coupling],
            range_enum,
            offset,
        )
        assert_pico_ok(self.status[status_key])

        self.channel_settings[channel] = {
            "enabled": bool(enabled),
            "coupling": coupling,
            "voltage_range": voltage_range,
            "offset": offset,
        }

    def configure_trigger(
        self,
        channel="B",
        threshold_adc=0,
        direction="RISING",
        delay=0,
        auto_trigger_ms=500,
        enabled=True,
    ):
        if not self.is_open:
            raise RuntimeError("Open the PicoScope before configuring the trigger.")

        channel = channel.upper()
        direction = direction.upper()

        if channel not in self.CHANNEL_MAP:
            raise ValueError(f"Invalid trigger channel: {channel}")

        if direction not in self.DIRECTION_MAP:
            raise ValueError("direction must be 'RISING' or 'FALLING'")

        self.status["trigger"] = ps.ps4000aSetSimpleTrigger(
            self.chandle,
            int(enabled),
            self.CHANNEL_MAP[channel],
            threshold_adc,
            self.DIRECTION_MAP[direction],
            delay,
            auto_trigger_ms,
        )
        assert_pico_ok(self.status["trigger"])

    def _find_timebase(
        self,
        total_samples,
        starting_timebase=799,
        max_timebase=10000,
    ):
        time_interval_ns = ctypes.c_float()
        returned_max_samples = ctypes.c_int32()
        timebase = starting_timebase

        while True:
            result = ps.ps4000aGetTimebase2(
                self.chandle,
                timebase,
                total_samples,
                ctypes.byref(time_interval_ns),
                ctypes.byref(returned_max_samples),
                0,
            )

            if result == 0:
                break

            timebase += 1

            if timebase > max_timebase:
                raise RuntimeError("Could not find a valid PicoScope timebase.")

        self.timebase = timebase
        self.time_interval_ns = time_interval_ns.value
        return timebase, time_interval_ns.value

    def _get_max_adc(self):
        if self.max_adc is None:
            max_adc = ctypes.c_int16()
            self.status["maximumValue"] = ps.ps4000aMaximumValue(
                self.chandle,
                ctypes.byref(max_adc),
            )
            assert_pico_ok(self.status["maximumValue"])
            self.max_adc = max_adc.value

        return self.max_adc

    def capture(
        self,
        pre_trigger=10_000,
        post_trigger=90_000,
        starting_timebase=799,
    ):
        if not self.is_open:
            raise RuntimeError("PicoScope must be opened before capture.")

        total_samples = pre_trigger + post_trigger

        enabled_channels = [
            name
            for name, settings in self.channel_settings.items()
            if settings["enabled"]
        ]

        if not enabled_channels:
            raise RuntimeError("No channels are enabled.")

        timebase, time_interval_ns = self._find_timebase(
            total_samples,
            starting_timebase,
        )

        dt = time_interval_ns * 1e-9

        print(f"Timebase: {timebase}")
        print(f"Sample interval: {time_interval_ns} ns")
        print(f"Samples: {total_samples}")
        print(f"Sample rate: {1.0 / dt:.3f} samples/s")
        print(f"Capture duration: {total_samples * dt:.6f} s")

        buffers = {}

        for channel_name in enabled_channels:
            buffer = (ctypes.c_int16 * total_samples)()

            self.status[f"buffer_{channel_name}"] = ps.ps4000aSetDataBuffer(
                self.chandle,
                self.CHANNEL_MAP[channel_name],
                buffer,
                total_samples,
                0,
                ps.PS4000A_RATIO_MODE["PS4000A_RATIO_MODE_NONE"],
            )
            assert_pico_ok(self.status[f"buffer_{channel_name}"])
            buffers[channel_name] = buffer

        time_indisposed_ms = ctypes.c_int32()

        self.status["runBlock"] = ps.ps4000aRunBlock(
            self.chandle,
            pre_trigger,
            post_trigger,
            timebase,
            ctypes.byref(time_indisposed_ms),
            0,
            None,
            None,
        )
        assert_pico_ok(self.status["runBlock"])

        print("Waiting for capture...")

        ready = ctypes.c_int16(0)
        while not ready.value:
            self.status["isReady"] = ps.ps4000aIsReady(
                self.chandle,
                ctypes.byref(ready),
            )
            assert_pico_ok(self.status["isReady"])
            time.sleep(0.01)

        n_samples = ctypes.c_uint32(total_samples)
        overflow = ctypes.c_int16()

        self.status["getValues"] = ps.ps4000aGetValues(
            self.chandle,
            0,
            ctypes.byref(n_samples),
            1,
            ps.PS4000A_RATIO_MODE["PS4000A_RATIO_MODE_NONE"],
            0,
            ctypes.byref(overflow),
        )
        assert_pico_ok(self.status["getValues"])

        count = n_samples.value
        max_adc = self._get_max_adc()
        data = {}

        for channel_name in enabled_channels:
            voltage_range = self.channel_settings[channel_name]["voltage_range"]
            adc_samples = np.asarray(
                buffers[channel_name][:count],
                dtype=np.int16,
            )

#            mv = np.asarray(
#                adc2mV(
#                   adc_samples,
#                   voltage_range,
#                    max_adc,
#                ),
#                dtype=float,
#           )

            mv = (
                adc_samples.astype(np.float64)
                * float(voltage_range)
                / float(max_adc)
            )



            data[channel_name] = mv #/ 1000.0

        t = np.arange(count, dtype=float) * dt

        if overflow.value:
            print("WARNING: input overflow detected. Increase the voltage range.")

        return t, data
