from picosdk.ps4000a import ps4000a as ps

from picoscope4424a import PicoScope4424A


def main():
    with PicoScope4424A() as scope:
        # Disable unused channels
        scope.configure_channel("A", enabled=False)
        scope.configure_channel("C", enabled=False)
        scope.configure_channel("D", enabled=False)

        # Channel B: AC coupled, +/-100 mV range
        scope.configure_channel(
            "B",
            enabled=True,
            coupling="AC",
            voltage_range=ps.PS4000A_RANGE["PS4000A_100MV"],
        )

        # Trigger on Channel B at 0 ADC counts, rising edge
        scope.configure_trigger(
            channel="B",
            threshold_adc=0,
            direction="RISING",
            auto_trigger_ms=500,
        )

        # Capture 100,000 samples
        t, data = scope.capture(
            pre_trigger=10_000,
            post_trigger=90_000,
            starting_timebase=799,
        )

        volts_b = data["B"]
        rms = scope.calculate_rms(volts_b)

        print(f"Channel B RMS: {rms:.9g} V")
        print(f"Channel B RMS: {rms * 1000:.6g} mV")

        scope.save_csv(
            "pico4424a_capture.csv",
            t,
            data,
        )


if __name__ == "__main__":
    main()
