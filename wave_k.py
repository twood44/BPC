import pyvisa
import argparse
import time


#python wave.py --mode=0  --freq=.5 --amp=10 --sym=33


# Agilent 33220A Function Generator - LAN ramp output

# Change this to the IP address shown on your 33220A
AGILENT_IP = "192.168.0.210"

rm = pyvisa.ResourceManager()
#print(rm)



parser=argparse.ArgumentParser(description="BPC Tester PICOSCOPE")
parser.add_argument(
	"--mode",
	type=int,
	nargs="?",
	default=0,
	help="0 is ramp, 1 is pulse"
)
parser.add_argument(
        "--freq",
        type=float,
        nargs="?",
        default=10,
        help="freq"
)

parser.add_argument(
        "--amp",
        type=float,
        nargs="?",
        default=5,
        help="amplitude"
)


parser.add_argument(
        "--offset",
        type=float,
        nargs="?",
        default=0,
        help="offset"
)

parser.add_argument(
        "--sym",
        type=float,
        nargs="?",
        default=50,
        help="ramp symmetry"
)


args=parser.parse_args()
mode=args.mode
freq=args.freq
amp=args.amp
offset=args.offset
sym=args.sym

print (f"Type {mode}")
print (f"Frequency {freq}")
print (f"Amplitude {amp}")
print (f"Offset : {offset}")
print (f"Ramp symetry {sym}")

done=0
while done==0:
 try:
    # Connect to the 33220A over LAN
    inst = rm.open_resource(f"TCPIP0::{AGILENT_IP}::inst0::INSTR")
    inst.timeout = 5000
    done=1
 except Exception as e:
    print("Error communicating with Agilent 33220A:")
    print(e)
    time.sleep(.1)



try:
    # Connect to the 33220A over LAN
#    inst = rm.open_resource(f"TCPIP0::{AGILENT_IP}::inst0::INSTR")
#    inst.timeout = 5000

    print(inst)

    # Verify connection
    print("Connected to:") 
    print(inst.query("*IDN?").strip())

    # Configure output for a high-impedance load
    inst.write("OUTP:LOAD INF")

    # Configure ramp: 0.125 Hz, 4 Vpp, 0 V offset

    if (mode==0):
     inst.write("FUNC RAMP")
     inst.write(f"FUNC:RAMP:SYMM {sym}")
     inst.write("VOLT:UNIT VPP")
     inst.write(f"VOLT {amp}")
     inst.write("VOLT:OFFS 0")
     inst.write(f"FREQ {freq}")
    elif (mode==1):
     inst.write("FUNC SQUARE")
     inst.write("VOLT:UNIT VPP")
     inst.write(f"VOLT {amp}")
     inst.write("VOLT:OFFS 0")
     inst.write(f"FREQ {freq}")
    elif (mode==2):
     inst.write("SOUR1:FUNC DC")
     inst.write(f"SOUR1:VOLT:OFFS {offset}")
     inst.write(f"SOUR1:VOLT {amp}")

     inst.write("OUTP1:LOAD INF")
     inst.write("OUTP1 ON")

     inst.write("SOUR2:FUNC DC")
     inst.write(f"SOUR2:VOLT:OFFS {offset}")
     inst.write("OUTP2:LOAD INF")
     inst.write("OUTP2 ON")
    elif (mode==3):
     inst.write("SOUR1:FUNC SQUARE")
     inst.write("SOUR1:VOLT:UNIT VPP")
     inst.write(f"SOUR1:FREQ {freq}")
     inst.write(f"SOUR1:VOLT {amp}")
     inst.write("SOUR1:VOLT:OFFS 0")
     inst.write("OUTP1:LOAD INF")
     inst.write("OUTP1 ON")

     inst.write("SOUR2:FUNC SQUARE")
     inst.write("SOUR2:VOLT:UNIT VPP")
     inst.write(f"SOUR2:FREQ {freq}")
     inst.write(f"SOUR2:VOLT {amp}")
     inst.write("SOUR2:VOLT:OFFS 0")
     inst.write("OUTP2:LOAD INF")
     inst.write("OUTP2 ON")

    elif (mode==4):
     inst.write("SOUR1:FUNC RAMP")
     inst.write(f"SOUR1:FUNC:RAMP:SYMM {sym}")
     inst.write("SOUR1:VOLT:UNIT VPP")
     inst.write(f"SOUR1:FREQ {freq}")
     inst.write(f"SOUR1:VOLT {amp}")
     inst.write("SOUR1:VOLT:OFFS 0")
     inst.write("OUTP1:LOAD INF")
     inst.write("OUTP1 ON")

     inst.write("SOUR2:FUNC RAMP")
     inst.write(f"SOUR2:FUNC:RAMP:SYMM {sym}")
     inst.write("SOUR2:VOLT:UNIT VPP")
     inst.write(f"SOUR2:FREQ {freq}")
     inst.write(f"SOUR2:VOLT {amp}")
     inst.write("SOUR2:VOLT:OFFS 0")
     inst.write("OUTP2:LOAD INF")
     inst.write("OUTP2 ON")



    #inst.write('FUNC  DC')
    #inst.write("FREQ 0.125")
    #inst.write('VOLT 4')
    #inst.write('VOLT:OFFS 0')
    #inst.write('OUTP1:STAT ON')
#print(inst.query('OUTP2:STAT?'))
#print(inst.query('SOUR2:FUNC:SHAP?'))



    # Turn output on
    inst.write("OUTP ON")

    print("Ramp output enabled:")
    print("  Frequency: 0.125 Hz")
    print("  Period:    8 s")
    print("  Amplitude: 4 Vpp")
    print("  Offset:    0 V")

    # Closing the VISA session does not intentionally turn the output off.
    inst.close()

except Exception as e:
    print("Error communicating with Agilent 33220A:")
    print(e)

finally:
    rm.close()
