#!/usr/bin/env python3
"""Standalone DMM/GPIB connectivity check — run before calibration to verify
the HP 3458A is reachable over the NI GPIB-USB-HS adapter (linux-gpib),
without touching EPICS or the ATE.

Usage:
  python3 check_dmm.py
"""
import os
import sys
from time import sleep
#from common import ate_udp, preflight,ate_epics, psc_epics, site_config  # noqa: E402
#from epics import caget, caput
#from common.initialize_dut import DUT 
#from common.psc_models import PSCModel  
import socket
#from Gpib import Gpib
import inspect
#import gpib


_REPO_ROOT = os.path.dirname(os.path.abspath(__file__))
if _REPO_ROOT not in sys.path:
    sys.path.insert(0, _REPO_ROOT)




'''
dmm=Gpib(name=0,pad=10,timeout=30,eos_mode=0x040A)

print("Opened")
print(dmm.__dict__)
print(inspect.getsource(Gpib))
#print(dir(Gpib))
print(dir(gpib))


print("EOS char :",dmm.ask(gpib.IbaEOSchar))
print("EOS read :",dmm.ask(gpib.IbaEOSrd))
print("EOS write :",dmm.ask(gpib.IbaEOSwrt))
print("EOS vmp :",dmm.ask(gpib.IbaEOScmp))
print("EOS cmp :",dmm.ask(gpib.IbaEOScmp))
#print("EOS 7-bit EOS :",dmm.ask(gpib.Iba7BitEOS))


#dmm.write("ID?")
#print("ID sent")

#dmm.write("TARM HOLD")
dmm.write("NRDGS 1")
dmm.write("AZERO ON")
dmm.write("NPLC 30")


for i in range(5):
    #dmm.write("NRDGS 1")
    dmm.write("TRIG SGL")
    sleep(1)
    print("dmm write TARM SGL, ... waiting ...")
    result=dmm.read(100)
    print("Result: ",repr(result))

exit()


'''





#from common import preflight, site_config  # noqa: E402

LiveFault = "Lab:PSC-U29:Chan1:FaultsLive-I"

sock = None
addr = None

'''
//DI Fault Bits
if( !strncmp(packetBuffer, "DI1", 3) ){
fault_byte = (uint8_t)atoi(packetBuffer+3);
if (fault_byte == 1) digitalWrite(pin_on_sts_CH1, HIGH);     0X100
if (fault_byte == 11) digitalWrite(pin_flt1_sts_CH1, HIGH);  0X80
if (fault_byte == 21) digitalWrite(pin_flt2_sts_CH1, HIGH);   0X100
if (fault_byte == 31) digitalWrite(pin_spare_sts_CH1, HIGH);  0X100
if (fault_byte == 0) digitalWrite(pin_on_sts_CH1, LOW);
if (fault_byte == 10) digitalWrite(pin_flt1_sts_CH1, LOW);
if (fault_byte == 20) digitalWrite(pin_flt2_sts_CH1, LOW);
if (fault_byte == 30) digitalWrite(pin_spare_sts_CH1, LOW);
Serial.println("CH1 fault = ");
Serial.println(ovc_CH1);
//Serial.println(mps_CH1);
}
'''

REMOTE_IP="192.168.0.46"
REMOTE_PORT=5000
#message=b"DI111\n"  # 0x80 - works


#message=b"DI121\n"  # gives 0x100


#message=b"DI11\n"  # 0x100

#message=b"DI130\n"  # 0x100

#message=b"DI101\n"  # 


#message=b"D0\n"


# Heartbeat is D13 J58-7
message=b"DI401\n"   #Gives 3 S pulse on D11, J58-5  pin_on_sts_CH1
#message=b"DI411\n"   #Gives 3 S pulse on D12, J58-6  pin_flt1_sts_CH1
#message=b"DI421\n"   # D13 J58-7 high 5 s, otherwise follows heartbeat pin_flt2_sts_CH1
#message=b"DI430\n"   # D14 J58-8 high/low pin_spare_sts_CH1

#message=b"D4\n"
#message=b"D0\n"


message=b"CALDAC-.05033\n" 
message=b"22222222Loop"
#message=b"SDrd"
#sudo tcpdump -i any -nn -X 'udp and dst host 192.168.1.60 and dst port 5000' 


def displayValue(id: str):
    print(f"{id}: \t{caget(id):.6f}")

def main():

    with socket.socket(socket.AF_INET, socket.SOCK_DGRAM) as sock:
        sock.sendto(message,(REMOTE_IP,REMOTE_PORT))

        data, addr = sock.recvfrom(2048)
        print(data)
        print(len(data))
        header=data[:8]
        payload=data[8:]
        
	
    exit()

    for i in range(3):
        displayValue("Lab:PSC-U29:Chan4:FaultsLive-I")
        displayValue("Lab:PSC-U29:Chan4:FaultsLat-I")
        sleep(.25)


#    print(f"Checking HP 3458A on GPIB board {site_config.DMM_GPIB_BOARD} "
#         f"addr {site_config.DMM_GPIB_ADDR}...")
#    ate_epics.initialize()
#    sock, addr = ate_udp.connect()
#    a=psc_epics.chan_pv("Lab:PSC-U29:NumChannels-Mode")
 #   print(a)

#    print("-->")
 #   displayValue("Lab:PSC-U21:Chan1:DigIn-I.B0")


#    caput("Lab:PSC-U21:Chan2:DigOut_ON1-SP",1)
#    caput("Lab:PSC-U21:Chan2:DigOut_ON2-SP",1)
#    caput("Lab:PSC-U21:Chan2:DigOut_Park-SP",1)

#    displayValue("Lab:PSC-U21:Chan2:DigOut_ON1-SP")
#    displayValue("Lab:PSC-U21:Chan2:DigOut_ON1-SP")
#    displayValue("Lab:PSC-U21:Chan2:DigOut_Park-SP")

#    caput("Lab:PSC-U21:Chan2:DigOut_Park-SP",0,wait=True)
#    displayValue("Lab:PSC-U21:Chan2:DigOut_Park-SP")
#    displayValue("Lab:PSC-U21:Chan2:PSOnOff-SP")
#    caput("Lab:PSC-U21:Chan2:PSOnOff-SP",1)

    """
    print(f"Lab:PSC-U29:Chan2:DAC-Gain-I: {caget("Lab:PSC-U29:Chan2:DAC-Gain-I"):.6f}")
    print(f"{caget("Lab:PSC-U29:Chan2:DAC-Offset-I"):.6f}")   
    print(f"{caget("Lab:PSC-U29:Chan2:DCCT1-Gain-I"):.6f}")
    print(f"{caget("Lab:PSC-U29:Chan2:DCCT1-Offset-I"):.6f}")
    print(f"{caget("Lab:PSC-U29:Chan2:DCCT2-Gain-I"):.6f}")
    print(f"{caget("Lab:PSC-U29:Chan2:DCCT2-Offset-I"):.6f}")    
    print(f"{caget("Lab:PSC-U29:Chan2:Error-Gain-I"):.6f}")
    print(f"{caget("Lab:PSC-U29:Chan2:Error-Offset-I"):.6f}")
    print(f"{caget("Lab:PSC-U29:Chan2:Reg-Gain-I"):.6f}")
    print(f"{caget("Lab:PSC-U29:Chan2:Reg-Offset-I"):.6f}")    
    print(f"{caget("Lab:PSC-U29:Chan2:Volt-Gain-I"):.6f}")
    print(f"{caget("Lab:PSC-U29:Chan2:Volt-Offset-I"):.6f}")
    print(f"{caget("Lab:PSC-U29:Chan2:Gnd-Gain-I"):.6f}")
    print(f"{caget("Lab:PSC-U29:Chan2:Gnd-Offset-I"):.6f}")   
    """
    print("---->")
""""
    displayValue("Lab:PSC-U29:Chan2:DAC-Gain-I")
    displayValue("Lab:PSC-U29:Chan2:DAC-Offset-I")
    displayValue("Lab:PSC-U29:Chan2:DCCT1-Gain-I")
    displayValue("Lab:PSC-U29:Chan2:DCCT1-Offset-I")
    displayValue("Lab:PSC-U29:Chan2:DCCT2-Gain-I")
    displayValue("Lab:PSC-U29:Chan2:DCCT2-Offset-I")
    displayValue("Lab:PSC-U29:Chan2:Error-Gain-I")
    displayValue("Lab:PSC-U29:Chan2:Error-Offset-I")
    displayValue("Lab:PSC-U29:Chan2:Reg-Gain-I")
    displayValue("Lab:PSC-U29:Chan2:Reg-Offset-I")
    displayValue("Lab:PSC-U29:Chan2:Volt-Gain-I")
    displayValue("Lab:PSC-U29:Chan2:Gnd-Offset-I")

    print("<----")


    print("---->")

    displayValue("Lab:PSC-U29:Chan3:DAC-Gain-I")
    displayValue("Lab:PSC-U29:Chan3:DAC-Offset-I")
    displayValue("Lab:PSC-U29:Chan3:DCCT1-Gain-I")
    displayValue("Lab:PSC-U29:Chan3:DCCT1-Offset-I")
    displayValue("Lab:PSC-U29:Chan3:DCCT2-Gain-I")
    displayValue("Lab:PSC-U29:Chan3:DCCT2-Offset-I")
    displayValue("Lab:PSC-U29:Chan3:Error-Gain-I")
    displayValue("Lab:PSC-U29:Chan3:Error-Offset-I")
    displayValue("Lab:PSC-U29:Chan3:Reg-Gain-I")
    displayValue("Lab:PSC-U29:Chan3:Reg-Offset-I")
    displayValue("Lab:PSC-U29:Chan3:Volt-Gain-I")
    displayValue("Lab:PSC-U29:Chan3:Gnd-Offset-I")

    print("<----")


    print("---->")

    displayValue("Lab:PSC-U25:Chan3:DAC-Gain-I")
    displayValue("Lab:PSC-U25:Chan3:DAC-Offset-I")
    displayValue("Lab:PSC-U25:Chan3:DCCT1-Gain-I")
    displayValue("Lab:PSC-U25:Chan3:DCCT1-Offset-I")
    displayValue("Lab:PSC-U25:Chan3:DCCT2-Gain-I")
    displayValue("Lab:PSC-U25:Chan3:DCCT2-Offset-I")
    displayValue("Lab:PSC-U25:Chan3:Error-Gain-I")
    displayValue("Lab:PSC-U25:Chan3:Error-Offset-I")
    displayValue("Lab:PSC-U25:Chan3:Reg-Gain-I")
    displayValue("Lab:PSC-U25:Chan3:Reg-Offset-I")
    displayValue("Lab:PSC-U25:Chan3:Volt-Gain-I")
    displayValue("Lab:PSC-U25:Chan3:Gnd-Offset-I")

    print("<----")
    """
""" 
    print(f"{caget("Lab:PSC-U25:Chan3:DCCT2-Offset-I"):.6f}")    


    print(f"{caget("Lab:PSC-U29:Chan2:DACSetPt-Gain-I"):.6f}")
    print(f"{caget("Lab:PSC-U29:Chan2:DACSetPt-Offset-I"):.6f}")
    print("----")



    print(f"{caget("Lab:PSC-U29:Chan2:DACSetPt-Gain-I"):.6f}")
    print(f"{caget("Lab:PSC-U29:Chan2:DACSetPt-Offset-I"):.6f}")   

    
    print(caget("Lab:PSC-U29:Chan2:DAC_OpMode-SP"))
    print(caget("Lab:PSC-U29:Chan2:DCCT1-I"))
    print(caget("Lab:PSC-U29:Chan2:DCCT2-I"))

    #print(caget("Lab:PSC-U25:Chan1:DCCT2-I"))
    #print(caget("Lab:PSC-U25:Chan1:DAC_OpMode-SP"))
    print(caget("Lab:PSC-U29:Chan2:DCCT2-I"))
    print(caget("Lab:PSC-U29:Chan2:DAC_OpMode-SP"))
    print(caget("Lab:PSC-U25:Chan3:DCCT2-I"))
    print(caget("Lab:PSC-U25:Chan3:DAC_OpMode-SP"))
    print(caget("Lab:PSC-U25:Chan4:DCCT2-I"))
    print(caget("Lab:PSC-U25:Chan4:DAC_OpMode-SP"))
    """
    #dut = DUT()
    #dut.prompt_inputs(require_model=True)
    #preflight.check_ioc(dut.PVprefix)
    #print(caget("Lab:PSC-U29:Chan2:DCCT1-Gain-SP"))
    #print(caget("Lab:PSC-U29:Chan2:DAC_OpMode-SP"))
    #print(caget("Lab:PSC-U29:NumChannels-Mode"))
    #psc_epics.set_power_off("Lab:PSC-U29:", 2)
    #dut.query_psc_config()
    #print(caget(a))

if __name__ == "__main__":
    main()
