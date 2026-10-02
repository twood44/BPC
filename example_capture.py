from picosdk.ps4000a import ps4000a as ps
from picoscope4424a import PicoScope4424A
from datetime import datetime
import matplotlib.pyplot as plt
import struct
from matplotlib import ticker as tick
import os



DATA_LOCATION="/home/pstester/bpc_Test/output/"
timestamp=datetime.now().strftime("%Y%m%d_%H%M%S")
CSV_FILE = f"{DATA_LOCATION}{timestamp}_pscope.csv"
PNG_FILE=  f"{DATA_LOCATION}picoscope_4424A_capture.png"
PNG2_FILE = f"{DATA_LOCATION}{timestamp}_pscope.png"
 
def plot(t,mv,chan,rms):
      # ========================================================
    # PLOT
    # ========================================================

        plt.figure()
#    plt.plot(time_s, voltage_a_v-.3,label="Ch A")
        plt.plot(t, mv,label="Ch_B")
 #   plt.plot(time_s, voltage_c_v,label="Ch_C")
 #   plt.plot(time_s, voltage_d_v,label="Ch_D")
        plt.xlabel("Time (s)")
        plt.ylabel("Voltage (mV)")
        plt.title(f"{PNG2_FILE}")
        plt.legend()
        plt.grid(True)
        plt.text(
                 .02,.95,
                 f"Noise 1 Test Ch {chan}: RMS {rms * 1000:.1f} mV",
                 transform=plt.gca().transAxes,
                 fontsize=12,
                 verticalalignment="top" 
                )
        plt.tight_layout()
        plt.savefig(PNG_FILE,dpi=300,bbox_inches="tight")
        os.system(f"cp {PNG_FILE} {PNG2_FILE}")
        plt.show()


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
            voltage_range=10 #ps.PS4000A_RANGE["PS4000A_100MV"],
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
            #"pico4424a_capture.csv",
            CSV_FILE,
            t,
            data,
        )

        plot(t,1000*volts_b,1,1000*rms)






if __name__ == "__main__":
    main()
