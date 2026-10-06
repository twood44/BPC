#Low frequency noise - band limit 10 kHz
import socket 
import sys
import time
import serial
import numpy as np
import matplotlib.pyplot as plt
import struct
from matplotlib import ticker as tick
import pyvisa
import os
from picosdk.ps4000a import ps4000a as ps
from picosdk.functions import adc2mV, assert_pico_ok
import ctypes
import csv
from datetime import datetime
from bpc import  BPC
#from waveform_generator import Agilent33220A
from waveform_generator import Keysight33500B
from picoscope4424a import PicoScope4424A

message = b"XXXXXXXXLoop"


def getUDPConnection():
 try:
     sock = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
     sock.settimeout(3)
     server_address = (IP, 5000)
     return sock,server_address
 except Exception as err:
     print("Socket error: %s" % err)
     return none,none


def poll_BPC():
		sock.sendto(message, server_address)
		data, addr = sock.recvfrom(2048)
#		print(data)
		header=data[:8]
#		payload=data[8:]
		return data[8:]

def getBPC_Parameter(payload,index):
  w = np.asarray(struct.unpack('>60f', payload)) 
  return w[index]

def pico_setup_o(pico):
    """
    Open and configure the PicoScope 4424A, capture Channel B,
    calculate RMS, and return the captured data.

    Returns
    -------
    time_s : numpy.ndarray
        Time axis in seconds.
    volts : numpy.ndarray
        Channel B samples in volts.
    rms : float
        RMS voltage of Channel B.
    """
#    pico = PicoScope4424A()

    try:
        # Open PicoScope
        pico.open()

        # Configure channels.
        # Channel B is enabled and AC coupled; all others are disabled.
        pico.configure_channel("A", enabled=False)

        pico.configure_channel(
            "B",
            enabled=True,
            coupling="AC",
            voltage_range=None,
            offset=0.0,
        )

        pico.configure_channel("C", enabled=False)
        pico.configure_channel("D", enabled=False)

        # Trigger on Channel B at 0 ADC counts, rising edge.
        pico.configure_trigger(
            channel="B",
            threshold_adc=0,
            direction="RISING",
            delay=0,
            auto_trigger_ms=500,
            enabled=True,
        )

        # Preserve the acquisition settings from the original pico_setup().
        time_s, data = pico.capture(
            pre_trigger=10_000,
            post_trigger=90_000,
            starting_timebase=799,
        )

        volts = data["B"]
        mv=1000*volts

        # calculate_rms() is inherited from the Oscilloscope base class.
        rms = pico.calculate_rms(volts)

        print(f"Channel B RMS: {rms:.9g} V")
        print(f"Channel B RMS: {rms * 1000:.6g} mV")

        #if overflow.value:
        #    print("WARNING: input overflow detected. Increase the voltage range.")

        # Save capture
        output = "pico4424a_capture.csv"
        with open(output, "w", newline="") as f:
            writer = csv.writer(f)
            writer.writerow(["time_s", "channel_B_V"])
            writer.writerows(zip(time_s, volts))

        print(f"Saved capture to {output}")




    # ========================================================
    # PLOT
    # ========================================================
        DATA_LOCATION="/home/pstester/bpc_Test/output/"
        timestamp=datetime.now().strftime("%Y%m%d_%H%M%S")
        CSV_FILE = f"{DATA_LOCATION}{timestamp}_pscope.csv"
        PNG_FILE=  f"{DATA_LOCATION}picoscope_4424A_capture.png"
        PNG2_FILE = f"{DATA_LOCATION}{timestamp}_pscope.png"

        plt.figure()
#    plt.plot(time_s, voltage_a_v-.3,label="Ch A")
        plt.plot(time_s, mv,label="Ch_Bx")
 #   plt.plot(time_s, voltage_c_v,label="Ch_C")
 #   plt.plot(time_s, voltage_d_v,label="Ch_D")
        plt.xlabel("Time (s)")
        plt.ylabel("Voltage (mV)")
        plt.title(f"{PNG2_FILE}")
        plt.legend()
        plt.grid(True)
        plt.text(
                 .02,.95,
                 f"Noise 1 Test Ch {chan}: RMS {rms * 1000:.6g} mV",
                 transform=plt.gca().transAxes,
                 fontsize=12,
                 verticalalignment="top" 
                )
        plt.tight_layout()
        plt.savefig(PNG_FILE,dpi=300,bbox_inches="tight")
        os.system(f"cp {PNG_FILE} {PNG2_FILE}")
        plt.show()


        #return time_s, volts, rms

    finally:
        # Ensure the scope is stopped/closed even if acquisition fails.
        pico.close()


def pico_setup():
    status = {}
    chandle = ctypes.c_int16()

    try:
        # Open PicoScope
        status["openunit"] = ps.ps4000aOpenUnit(
            ctypes.byref(chandle), None
        )
        assert_pico_ok(status["openunit"])
        print("PicoScope 4424A opened.")

        # Configure A, C, D disabled; B enabled and AC coupled.
        channels = [
            ("A", ps.PS4000A_CHANNEL["PS4000A_CHANNEL_A"], 0),
            ("B", ps.PS4000A_CHANNEL["PS4000A_CHANNEL_B"], 1),
            ("C", ps.PS4000A_CHANNEL["PS4000A_CHANNEL_C"], 0),
            ("D", ps.PS4000A_CHANNEL["PS4000A_CHANNEL_D"], 0),
        ]

        # Start with +/-10 mV range for low-level measurements.
        # Increase this if the signal clips/overranges.
       # voltage_range = ps.PS4000A_RANGE["PS4000A_10MV"]
        voltage_range =10 # ps.PICO_CONNECT_PROBE_RANGE["PICO_X1_PROBE_100MV"]


        for name, channel, enabled in channels:
            status[f"channel_{name}"] = ps.ps4000aSetChannel(
                chandle,
                channel,
                enabled,
                ps.PS4000A_COUPLING["PS4000A_AC"],
                voltage_range,
                0.0,
            )
            assert_pico_ok(status[f"channel_{name}"])

        # Trigger on Channel B.
        # Threshold = 0 ADC counts, rising edge.
        status["trigger"] = ps.ps4000aSetSimpleTrigger(
            chandle,
            1,
            ps.PS4000A_CHANNEL["PS4000A_CHANNEL_B"],
            0,
            ps.PS4000A_THRESHOLD_DIRECTION["PS4000A_RISING"],
            0,
            500,
        )
        assert_pico_ok(status["trigger"])

        # 100,000-point block capture
        pre_trigger = 10_000
        post_trigger = 90_000
        total_samples = pre_trigger + post_trigger

        # Find a valid timebase. Starting at 8 is conservative for this test.
        timebase = 799
        time_interval_ns = ctypes.c_float()
        returned_max_samples = ctypes.c_int32()

        while True:
            result = ps.ps4000aGetTimebase2(
                chandle,
                timebase,
                total_samples,
                ctypes.byref(time_interval_ns),
                ctypes.byref(returned_max_samples),
                0,
            )
            if result == 0:
                break
            timebase += 1
            if timebase > 10000:
                raise RuntimeError("Could not find a valid PicoScope timebase.")

        print(f"Timebase: {timebase}")
        print(f"Sample interval: {time_interval_ns.value} ns")
        print(f"Samples: {total_samples}")

        dt = time_interval_ns.value * 1e-9
        print(f"Sample interval: {dt:.9g} s")
        print(f"Sample rate: {1.0 / dt:.3f} samples/s")
        print(f"Capture duration: {total_samples * dt:.6f} s")


        # Allocate Channel B buffer
        buffer_b = (ctypes.c_int16 * total_samples)()

        status["setDataBufferB"] = ps.ps4000aSetDataBuffer(
            chandle,
            ps.PS4000A_CHANNEL["PS4000A_CHANNEL_B"],
            ctypes.byref(buffer_b), #buffer_b,
            total_samples,
            0,
            ps.PS4000A_RATIO_MODE["PS4000A_RATIO_MODE_NONE"],
        )
        assert_pico_ok(status["setDataBufferB"])

        # Start block acquisition
        time_indisposed_ms = ctypes.c_int32()

        status["runBlock"] = ps.ps4000aRunBlock(
            chandle,
            pre_trigger,
            post_trigger,
            timebase,
            ctypes.byref(time_indisposed_ms),
            0,
            None,
            None,
        )
        assert_pico_ok(status["runBlock"])

        print("Waiting for capture...")
        ready = ctypes.c_int16(0)

        while not ready.value:
            status["isReady"] = ps.ps4000aIsReady(
                chandle, ctypes.byref(ready)
            )
            assert_pico_ok(status["isReady"])
            time.sleep(0.01)

        # Retrieve samples
        n_samples = ctypes.c_uint32(total_samples)
        overflow = ctypes.c_int16()

        status["getValues"] = ps.ps4000aGetValues(
            chandle,
            0,
            ctypes.byref(n_samples),
            1,
            ps.PS4000A_RATIO_MODE["PS4000A_RATIO_MODE_NONE"],
            0,
            ctypes.byref(overflow),
        )
        assert_pico_ok(status["getValues"])

        count = n_samples.value

        # Get ADC maximum for conversion
        max_adc = ctypes.c_int16()
        status["maximumValue"] = ps.ps4000aMaximumValue(
            chandle, ctypes.byref(max_adc)
        )
        assert_pico_ok(status["maximumValue"])

        # Convert ADC samples to millivolts, then volts
        #adc_samples = np.array(buffer_b[:count], dtype=np.int16)
        #mv = np.array(
        #    adc2mV(adc_samples, voltage_range, max_adc),
        #    dtype=float,
        #)
        #volts = mv / 1000.0

        mv = np.asarray(
              adc2mV(buffer_b[:count], voltage_range, max_adc)
        )
        volts = mv / 1000.0



        # Time axis
        dt = time_interval_ns.value * 1e-9
        t = np.arange(count) * dt

        # AC RMS
        rms = float(np.sqrt(np.mean(volts ** 2)))

        print(f"Channel B RMS: {rms:.9g} V")
        print(f"Channel B RMS: {rms * 1000:.6g} mV")

        if overflow.value:
            print("WARNING: input overflow detected. Increase the voltage range.")

        # Save capture
        output = "pico4424a_capture.csv"
        with open(output, "w", newline="") as f:
            writer = csv.writer(f)
            writer.writerow(["time_s", "channel_B_V"])
            writer.writerows(zip(t, volts))

        print(f"Saved capture to {output}")




    # ========================================================
    # PLOT
    # ========================================================
        DATA_LOCATION="/home/pstester/bpc_Test/output/"
        timestamp=datetime.now().strftime("%Y%m%d_%H%M%S")
        CSV_FILE = f"{DATA_LOCATION}{timestamp}_pscope.csv"
        PNG_FILE=  f"{DATA_LOCATION}picoscope_4424A_capture.png"
        PNG2_FILE = f"{DATA_LOCATION}{timestamp}_pscope.png"

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






    finally:
        if chandle.value:
            try:
                ps.ps4000aStop(chandle)
            except Exception:
                pass
            try:
                ps.ps4000aCloseUnit(chandle)
                print("PicoScope closed.")
            except Exception:
                pass







def sds_send(sock, scpi_cmd):
	sock.sendall(scpi_cmd)
	print(scpi_cmd)
	time.sleep(0.15)
	    

#oscope = "Tek"
oscope = "Sig"

F=14
model = sys.argv[1]
serial = sys.argv[2]
chan = sys.argv[3]
IP = sys.argv[4]


modelname = "%s_%s" % (model,serial)
filename = "%s_%s_CH%s_dm_noise.png" %(model, serial, chan)
#filepath = './2ch/' + modelname + '/'
filepath = "./_temp/"

td=0.3
td1=0.1



#sock, server_address=getUDPConnection()
#for t in range(4):
#        payload=poll_BPC()
#        value=getBPC_Parameter(payload,54)
#        print(f"Val {value}")
#        time.sleep(1)

# IP = "192.168.1.100"

AGILENT_IP = "192.168.0.210"

#wave = Agilent33220A(AGILENT_IP)
wave = Keysight33500B(AGILENT_IP)
try:
        wave.connect()
        wave.set_dc(1.3, channel=1)
        wave.output_on(1)
        print("Waveform output configured.")
finally:
        wave.close()




bpc = BPC(IP)
#
try:
     #payload = bpc.poll_BPC()
     value = bpc.getBPC_Parameter( 45)
     print(value)
     print(bpc.getBPC_Parameter( 44))
     print(bpc.getBPC_Parameter( [44, 45, 46]))
     print(bpc.getBPC_Parameter( [1,2,3]))
finally:
     bpc.close()


#exit()
#/home/pstester/bpc_Test/python/bpc_Tester2
#os.system("python /home/pstester/bpc_Test/python/bpc_Tester2/wave_k.py --mode=2 --offset=.3")
pico = PicoScope4424A()
#pico_setup_o(pico)
pico_setup()


try:
        wave.connect()
        wave.set_dc(0, channel=1)
        wave.output_off(1)
        print("Waveform output off.")
finally:
        wave.close()


exit()


