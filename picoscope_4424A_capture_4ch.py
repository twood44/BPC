"""
PicoScope 4424A - Python block capture example

Captures Channel A and saves time/voltage data to CSV.

Requirements:
    1. Install PicoSDK from Pico Technology.
    2. Install Python packages:
           pip install picosdk numpy matplotlib
"""

import os
import ctypes
import time
import csv
import numpy as np
import argparse
import matplotlib.pyplot as plt
from datetime import datetime

from picosdk.ps4000a import ps4000a as ps
from picosdk.functions import adc2mV, assert_pico_ok

# ============================================================
# USER SETTINGS
# ============================================================




parser=argparse.ArgumentParser(description="BPC Tester PICOSCOPE")
parser.add_argument(
	"samples",
	type=int,
	help="# of seconds at 1 KHz"
)
args=parser.parse_args()
seconds=args.samples


print(seconds)




CHANNELA = ps.PS4000A_CHANNEL["PS4000A_CHANNEL_A"]
CHANNELB = ps.PS4000A_CHANNEL["PS4000A_CHANNEL_B"]
CHANNELC = ps.PS4000A_CHANNEL["PS4000A_CHANNEL_C"]
CHANNELD = ps.PS4000A_CHANNEL["PS4000A_CHANNEL_D"]



COUPLING = ps.PS4000A_COUPLING["PS4000A_AC"]

# +/- 5 V input range
VOLTAGE_RANGE =10 # ps.PS4000A_RANGE["PS4000A_5V"]

# Number of samples before/after trigger point.
# Trigger is disabled below, so these simply define capture length.
PRE_TRIGGER_SAMPLES = 0
POST_TRIGGER_SAMPLES = 1000*seconds*100  #20000
TOTAL_SAMPLES = PRE_TRIGGER_SAMPLES + POST_TRIGGER_SAMPLES

# PicoScope timebase.
# Adjust this to change sample interval/capture duration.
TIMEBASE = 799 #80002

DATA_LOCATION="/home/pstester/bpc_Test/output/"
timestamp=datetime.now().strftime("%Y%m%d_%H%M%S")
CSV_FILE = f"{DATA_LOCATION}{timestamp}_pscope.csv"
PNG_FILE=  f"{DATA_LOCATION}picoscope_4424A_capture.png"
PNG2_FILE = f"{DATA_LOCATION}{timestamp}_pscope.png"


print(CSV_FILE)
print(PNG_FILE)
print(PNG2_FILE)
# ============================================================
# OPEN PICOSCOPE
# ============================================================

status = {}
handle = ctypes.c_int16()

status["openunit"] = ps.ps4000aOpenUnit(
    ctypes.byref(handle),
    None
)
assert_pico_ok(status["openunit"])

print("PicoScope 4424A connected.")

try:
    # ========================================================
    # CONFIGURE CHANNEL A
    # ========================================================

    status["setChannelA"] = ps.ps4000aSetChannel(
        handle,
        CHANNELA,
        1,              # enabled
        COUPLING,
        VOLTAGE_RANGE,
        0.0             # analog offset
    )
    assert_pico_ok(status["setChannelA"])


    status["setChannelB"] = ps.ps4000aSetChannel(
        handle,
        CHANNELB,
        1,              # enabled
        COUPLING,
        VOLTAGE_RANGE,
        0.0             # analog offset
    )
    assert_pico_ok(status["setChannelB"])


    status["setChannelC"] = ps.ps4000aSetChannel(
        handle,
        CHANNELC,
        1,              # enabled
        COUPLING,
        VOLTAGE_RANGE,
        0.0             # analog offset
    )
    assert_pico_ok(status["setChannelC"])

    status["setChannelD"] = ps.ps4000aSetChannel(
        handle,
        CHANNELD,
        1,              # enabled
        COUPLING,
        VOLTAGE_RANGE,
        0.0             # analog offset
    )
    assert_pico_ok(status["setChannelD"])



    # Disable channels C-D
    for ch_name in [
#        "PS4000A_CHANNEL_B",
#        "PS4000A_CHANNEL_C",
#        "PS4000A_CHANNEL_D",
    ]:
        ch = ps.PS4000A_CHANNEL[ch_name]
        status[f"disable_{ch_name}"] = ps.ps4000aSetChannel(
            handle,
            ch,
            0,
            COUPLING,
            VOLTAGE_RANGE,
            0.0
        )
        assert_pico_ok(status[f"disable_{ch_name}"])

    # ========================================================
    # DISABLE TRIGGER
    # ========================================================

    status["trigger"] = ps.ps4000aSetSimpleTrigger(
        handle,
        0,      # trigger disabled
        CHANNELA,
        0,
        ps.PS4000A_THRESHOLD_DIRECTION["PS4000A_RISING"],
        0,
        0
    )
    assert_pico_ok(status["trigger"])

    # ========================================================
    # GET TIMEBASE INFORMATION
    # ========================================================

    time_interval_ns = ctypes.c_float()
    max_samples = ctypes.c_int32()

    status["getTimebase"] = ps.ps4000aGetTimebase2(
        handle,
        TIMEBASE,
        TOTAL_SAMPLES,
        ctypes.byref(time_interval_ns),
        ctypes.byref(max_samples),
        0
    )
    assert_pico_ok(status["getTimebase"])

    dt = time_interval_ns.value * 1e-9

    print(f"Sample interval: {dt:.9g} s")
    print(f"Sample rate: {1.0 / dt:.3f} samples/s")
    print(f"Capture duration: {TOTAL_SAMPLES * dt:.6f} s")

    # ========================================================
    # START BLOCK CAPTURE
    # ========================================================

    time_indisposed_ms = ctypes.c_int32()

    status["runBlock"] = ps.ps4000aRunBlock(
        handle,
        PRE_TRIGGER_SAMPLES,
        POST_TRIGGER_SAMPLES,
        TIMEBASE,
        ctypes.byref(time_indisposed_ms),
        0,
        None,
        None
    )
    assert_pico_ok(status["runBlock"])

    print("Capturing...")

    ready = ctypes.c_int16(0)

    while not ready.value:
        status["isReady"] = ps.ps4000aIsReady(
            handle,
            ctypes.byref(ready)
        )
        assert_pico_ok(status["isReady"])
        time.sleep(0.01)

    # ========================================================
    # CREATE DATA BUFFER
    # ========================================================

    buffer_a = (ctypes.c_int16 * TOTAL_SAMPLES)()
    buffer_b = (ctypes.c_int16 * TOTAL_SAMPLES)()
    buffer_c = (ctypes.c_int16 * TOTAL_SAMPLES)()
    buffer_d = (ctypes.c_int16 * TOTAL_SAMPLES)()


    status["setDataBufferA"] = ps.ps4000aSetDataBuffer(
        handle,
        CHANNELA,
        ctypes.byref(buffer_a),
        TOTAL_SAMPLES,
        0,
        ps.PS4000A_RATIO_MODE["PS4000A_RATIO_MODE_NONE"]
    )
    assert_pico_ok(status["setDataBufferA"])

    status["setDataBufferB"] = ps.ps4000aSetDataBuffer(
        handle,
        CHANNELB,
        ctypes.byref(buffer_b),
        TOTAL_SAMPLES,
        0,
        ps.PS4000A_RATIO_MODE["PS4000A_RATIO_MODE_NONE"]
    )
    assert_pico_ok(status["setDataBufferB"])

    status["setDataBufferC"] = ps.ps4000aSetDataBuffer(
        handle,
        CHANNELC,
        ctypes.byref(buffer_c),
        TOTAL_SAMPLES,
        0,
        ps.PS4000A_RATIO_MODE["PS4000A_RATIO_MODE_NONE"]
    )
    assert_pico_ok(status["setDataBufferA"])

    status["setDataBufferD"] = ps.ps4000aSetDataBuffer(
        handle,
        CHANNELD,
        ctypes.byref(buffer_d),
        TOTAL_SAMPLES,
        0,
        ps.PS4000A_RATIO_MODE["PS4000A_RATIO_MODE_NONE"]
    )
    assert_pico_ok(status["setDataBufferB"])



    # ========================================================
    # READ CAPTURED DATA
    # ========================================================

    sample_count = ctypes.c_int32(TOTAL_SAMPLES)
    overflow = ctypes.c_int16()

    status["getValues"] = ps.ps4000aGetValues(
        handle,
        0,
        ctypes.byref(sample_count),
        1,
        ps.PS4000A_RATIO_MODE["PS4000A_RATIO_MODE_NONE"],
        0,
        ctypes.byref(overflow)
    )
    assert_pico_ok(status["getValues"])

    n = sample_count.value

    # Get maximum ADC value for voltage conversion
    max_adc = ctypes.c_int16()

    status["maximumValue"] = ps.ps4000aMaximumValue(
        handle,
        ctypes.byref(max_adc)
    )
    assert_pico_ok(status["maximumValue"])

    voltage_a_mv = np.asarray(
        adc2mV(buffer_a[:n], VOLTAGE_RANGE, max_adc)
    )
    voltage_a_v = voltage_a_mv / 1000.0

    voltage_b_mv = np.asarray(
        adc2mV(buffer_b[:n], VOLTAGE_RANGE, max_adc)
    )
    voltage_b_v = voltage_b_mv / 1000.0


    voltage_c_mv = np.asarray(
        adc2mV(buffer_c[:n], VOLTAGE_RANGE, max_adc)
    )
    voltage_c_v = voltage_c_mv / 1000.0

    voltage_d_mv = np.asarray(
        adc2mV(buffer_d[:n], VOLTAGE_RANGE, max_adc)
    )
    voltage_d_v = voltage_d_mv / 1000.0


    time_s = np.arange(n) * dt

    # ========================================================
    # SAVE CSV
    # ========================================================

    with open(CSV_FILE, "w", newline="") as file:
        writer = csv.writer(file)
        writer.writerow(["Time_s", "Channel_A_V", "Channel_B_V", "Channel_C_V", "Channel_D_V"])

        for t, va,vb,vc,vd in zip(time_s, voltage_a_v,voltage_b_v,voltage_c_v,voltage_d_v):
            writer.writerow([t, va, vb, vc, vd])

    print(f"Saved {n} samples to {CSV_FILE}")

    # ========================================================
    # PLOT
    # ========================================================

    plt.figure()
#    plt.plot(time_s, voltage_a_mv,label="Ch A")
    plt.plot(time_s, voltage_b_mv,label="Ch_B")
 #   plt.plot(time_s, voltage_c_mv,label="Ch_C")
  #  plt.plot(time_s, voltage_d_mv,label="Ch_D")
    plt.xlabel("Time (s)")
    plt.ylabel("Voltage (mV)")
    plt.title(f"{PNG2_FILE}")
    plt.legend()
    plt.grid(True)
    plt.tight_layout()
    plt.savefig(PNG_FILE,dpi=300,bbox_inches="tight")	
    os.system(f"cp {PNG_FILE} {PNG2_FILE}")
    plt.show()
    

finally:
    # Stop acquisition and close the scope even if an error occurs.
    try:
        status["stop"] = ps.ps4000aStop(handle)
    except Exception:
        pass

    status["close"] = ps.ps4000aCloseUnit(handle)

    print("PicoScope closed.")
