#Step reponse
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
from waveform_generator import Keysight33500B
from picosdk.ps4000a import ps4000a as ps
from picosdk.functions import adc2mV, assert_pico_ok
import ctypes
import csv
from datetime import datetime
from bpc import  BPC
from picoscope4424a import PicoScope4424A



def sds_send(sock, scpi_cmd):
	sock.sendall(scpi_cmd)
	print(scpi_cmd)
	time.sleep(0.4)

#oscope = "Tek"
oscope = "Sig"

F=14
model = sys.argv[1]
serial = sys.argv[2]
chan = sys.argv[3]

td=0.3
td1=0.1

modelname = "%s_%s" % (model,serial)
filename = "%s_%s_CH%s_step_resp.png" %(model, serial, chan)
#filepath = './2ch/' + modelname + '/'
filepath = "./_temp/"


#rm = pyvisa.ResourceManager()
#print(rm.list_resources() )
#inst = rm.open_resource('USB0::1689::851::2347672::0::INSTR')
#inst = rm.open_resource('USB0::1689::851::2347693::0::INSTR')
#print(inst.query("*IDN?"))

remote_ip = "192.168.0.100"
if oscope == "Tek":
	port = 4000 # the port number of the instrument service
if oscope == "Sig": #Siglent
	port = 5025 # the port number of the instrument service

"""	
try:
	#create an AF_INET, STREAM socket (TCP)
	s = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
	s.settimeout(1)
except socket.error:
	print ("Failed to create socket.")
	sys.exit();
try:
	#Connect to remote server
	s.connect((remote_ip , port))
except socket.error:
	print ("failed to connect to ip " + remote_ip)

"""

def pico_setup_o(pico):
	# Capture settings
    PRE_TRIGGER = 2500
    POST_TRIGGER = 7500          # 10,000 samples total
    STARTING_TIMEBASE = 799

# Channel settings
    A_RANGE_V = 5.0
    D_RANGE_V = 2.0

# Trigger: Tek CH4, rising edge, +1 V
    TRIGGER_VOLTAGE = 1.0

    try:
        # Open PicoScope
        pico.open()

         #with PicoScope4424A() as pico:
        # Tek CH1 -> Pico Channel A
        pico.configure_channel(
            "A",
            enabled=True,
            coupling="DC",
            voltage_range=A_RANGE_V,
            offset=0.0,
        )

        # Tek CH2/CH3 -> disabled
        pico.configure_channel("B", enabled=False)
        pico.configure_channel("C", enabled=False)

        # Tek CH4 -> Pico Channel D
        pico.configure_channel(
            "D",
            enabled=True,
            coupling="DC",
            voltage_range=D_RANGE_V,
            offset=0.0,
        )

        # Convert +1 V trigger threshold to ADC counts.
        max_adc = pico._get_max_adc()
        threshold_adc = int(
            (TRIGGER_VOLTAGE / D_RANGE_V) * max_adc
        )

        pico.configure_trigger(
            channel="D",
            threshold_adc=threshold_adc,
            direction="RISING",
            delay=0,
            auto_trigger_ms=500,
            enabled=True,
        )

        print("Waiting for trigger / capturing waveform...")

        t, data = pico.capture(
            pre_trigger=PRE_TRIGGER,
            post_trigger=POST_TRIGGER,
            starting_timebase=STARTING_TIMEBASE,
        )

        volts_a = data["A"]
        volts_d = data["D"]

        print(f"Captured {len(t)} samples")
        print(f"Sample interval: {pico.time_interval_ns} ns")
        if len(t) > 1:
            print(f"Capture duration: {(t[-1] - t[0]) * 1e6:.3f} us")



    # ========================================================
    # PLOT
    # ========================================================
        DATA_LOCATION="/home/pstester/bpc_Test/output/"
        timestamp=datetime.now().strftime("%Y%m%d_%H%M%S")
        CSV_FILE = f"{DATA_LOCATION}{timestamp}_pscope.csv"
        PNG_FILE=  f"{DATA_LOCATION}picoscope_4424A_capture.png"
        PNG2_FILE = f"{DATA_LOCATION}{timestamp}_pscope.png"


        # Plot captured waveforms
        plt.figure()
        plt.plot(t * 1e6, volts_a, label="Channel A - Step response")
        plt.plot(t * 1e6, volts_d, label="Channel D - Trigger")
        plt.axvline(0, linestyle="--", label="Trigger")
        plt.xlabel("Time (us)")
        plt.ylabel("Voltage (V)")
        plt.title("PicoScope 4424A Step Response")
        plt.grid(True)
        plt.legend()
        plt.tight_layout()
        plt.show()
        plt.savefig(PNG_FILE,dpi=300,bbox_inches="tight")
        os.system(f"cp {PNG_FILE} {PNG2_FILE}")

    finally:
        # Ensure the scope is stopped/closed even if acquisition fails.
        pico.close()


def smooth_wfm(wfm):
	N=len(wfm)
	L=8
	w = np.zeros(N-L)
	for i in range(N-L):
		w[i] = np.mean(wfm[i:i+L])
	return w

def get_MSO4054_wfm(CH):
	ch_str = 'DATA:SOU ' + CH + '\n'
	#s.send(b'DATA:SOU CH2\n')
	s.send(ch_str.encode('UTF-8'))
	s.send(b'WFMOutpre:BYT_Nr 2\n')
	s.send(b'CURV?\n')
	time.sleep(0.3)
	data = s.recv(20100)
	#data = s.recv(200200)
	#print(len(data))
	#print(data[0:20])
	#print(len(data))
	wfm = np.asarray(struct.unpack('9900h', data[0+100:19800+100]))
	#wfm = np.asarray(struct.unpack('99000H', data[0+100:198000+100]))
	#print(len(wfm))
	s.send(b'WFMOutpre:YMU?\n')
	#time.sleep(td)
	rdg=bytearray()
	while len(rdg)<3:
		tmp = s.recv(100)
		rdg.extend(tmp)
	m = float(rdg.decode("UTF-8"))
	s.send(b'WFMOutpre:YOF?\n')
	#time.sleep(td)
	rdg=bytearray()
	while len(rdg)<3:
		tmp = s.recv(100)
		rdg.extend(tmp)
	b = float(rdg.decode("UTF-8"))
	#print(b)
	#print(m)
	wfm1 = (wfm-b)*m
	#wfm1 = wfm*1
	#print(wfm1[0:50])
	#fig = plt.figure(1, figsize=(14,9))
	#plt.plot(wfm1, 'k.', label = "") # dib
	#plt.show()
	return wfm1
	

def get_MSO4054_XINcr():
	s.send(b'WFMOutpre:XINcr?\n')
	rdg=bytearray()
	while len(rdg)<3:
		tmp = s.recv(4096)
		rdg.extend(tmp)
	Ts = rdg.decode("UTF-8")
	return float(Ts)


def get_SIGLENT_wfm(CH):
    #import struct
    #import numpy as np
    #import time

    sds_send(s, b'CHDR OFF\n') # suppress headers
    
    ch_str = f'C{CH}:WF? DAT2\n'  # Request waveform data from channel CH
    s.send(ch_str.encode('UTF-8'))

    # Receive header
    header1 = s.recv(5)
    header = s.recv(2)
    print("header = %s" % header)
    if header != b'#9':
    #if header != b'C2':
        raise Exception("Unexpected header format")

    # Receive length of waveform data
    len_str = s.recv(9)
    num_bytes = int(len_str.decode())
    print(num_bytes)

    # Receive waveform data
    z = bytearray()
    while len(z) < num_bytes:
        data = s.recv(1024)
        z.extend(data)

    # Convert binary data to numpy array
    wfm = np.frombuffer(z, dtype=np.int8)
    N=len(wfm)
    print(N)

    # Request vertical scale (e.g., V/div)
    s.send(f'C{CH}:VDIV?\n'.encode('UTF-8'))
    vdiv = float(s.recv(100).decode())
    print(vdiv)

    # Request horizontal scale (e.g., s/div)
    s.send(f'TDIV?\n'.encode('UTF-8'))
    tdiv = float(s.recv(100).decode())
    print(tdiv)
    Ts = tdiv*14/num_bytes
    print(Ts)

    # Request vertical offset
    s.send(f'C{CH}:OFST?\n'.encode('UTF-8'))
    ofst = float(s.recv(100).decode().strip())
    print(ofst)

    # Apply vertical scaling
    # Siglent sends data centered around 127 (i.e., 8-bit unsigned int)
    volt_per_bit = vdiv / 25  # 10 div screen, 250 levels
    print(volt_per_bit)
    wfm1 = wfm*volt_per_bit-ofst

    return wfm1[0:N-2], num_bytes, Ts
    

	

#AFG1022
#inst.write('SOUR1:FUNC:SHAP DC')
#inst.write('SOUR1:VOLT:LEV:IMM:OFFS 2.1')


#inst.write('SOUR1:FUNC:SHAP SQU')
#inst.write('SOUR1:VOLT:LEV:IMM:OFFS 0.5')
#inst.write('SOUR1:VOLT:LEV:IMM:AMPL 0.5')
#nst.write('SOUR1:FREQ:FIX 20')
#nst.write('OUTP1:STAT ON')

#print(inst.query('OUTP2:STAT?'))
#print(inst.query('SOUR2:FUNC:SHAP?'))

WAVE_IP = "192.168.0.210"

#wave = Agilent33220A(AGILENT_IP)
wave = Keysight33500B(WAVE_IP)
try:
        wave.connect()
		#        wave.set_dc(1.3, channel=1)
        wave.set_square( 20, .5, .5, channel=1)
        wave.output_on(1)
        print("Waveform output configured.")
finally:
        wave.close()

print ("XXXXXXXX")

pico = PicoScope4424A()
pico_setup_o(pico)




exit()


try:
	print("Measuring step response...")
	

	if oscope == 'Tek':
		s.send(b'SELECT:CH1 ON\n')
		s.send(b'SELECT:CH2 OFF\n')
		s.send(b'SELECT:CH3 OFF\n')
		s.send(b'SELECT:CH4 ON\n')
		#set Tek scope trigger
		s.send(b'TRIG:A:EDGE:SOUR CH4\n')
		s.send(b'TRIG:A:LEV 1\n')
		s.send(b'TRIG:A:EDGE:SLO RISE\n')
		#set Tek scope horizontal scale
		s.send(b'HOR:DEL:MOD ON\n')
		s.send(b'HOR:RECOrdlength 10000\n')
		if model == "6201" or model == "6101" or model=='6401':
			s.send(b'HOR:SCA 0.001\n')
			s.send(b'HOR:DEL:TIM 0.003\n')
		if model == "6202":
			s.send(b'HOR:SCA 40e-6\n')
			s.send(b'HOR:DEL:TIM 120e-6\n')
		#set Tek scope vertical scale
		s.send(b'CH1:SCALE 0.5\n')
		s.send(b'CH1:COUP DC\n')
		s.send(b'CH1:POS -4\n') #position is in divisions
		s.send(b'CH4:SCALE 0.2\n')
		s.send(b'CH4:COUP DC\n')
		s.send(b'CH4:POS -4\n')
		s.send(b'CH1:BANDWIDTH TWENTY\n')
		s.send(b'CH4:BANDWIDTH TWENTY\n')
		
		s.send(b'MEASU:MEAS1:TYPE RISE\n')
		s.send(b'MEASU:MEAS1:SOUR CH1\n')
		s.send(b'MEASU:MEAS1:STATE ON\n')
		
	if oscope == 'Sig':
		sds_send(s, b'*RST\n')
		rdg=0
		x=0
		while (rdg==0 and x<10):
			try:
				sds_send(s, b'*IDN?\n')
				rdg = s.recv(1000)
				print(rdg)
			except:
				x+=1
				#print(rdg)
		try:		
			rdg = s.recv(1000) # clear serial buffer
		except:
			pass
			
		print("Configuring instruments...")
		time.sleep(3) # wait after reset
		
		sds_send(s, b'C1:TRACE OFF\n') #Trace on/off
		sds_send(s, b'C2:TRACE OFF\n')
		sds_send(s, b'C3:TRACE OFF\n')
		sds_send(s, b'C4:TRACE OFF\n')
				
		sds_send(s, b'C1:ATTENUATION 10\r\n')
		sds_send(s, b'C1:COUPLING D1M\r\n')               
		sds_send(s, b'C1:VOLT_DIV 1\r\n')            
		sds_send(s, b'C1:OFFSET -0.5V\r\n')     
				
		sds_send(s, b'C4:ATTENUATION 1\r\n')
		sds_send(s, b'C4:COUPLING D1M\r\n')               
		sds_send(s, b'C4:VOLT_DIV 0.5\r\n')            
		sds_send(s, b'C4:OFFSET -1.5\r\n')  
		
		sds_send(s, b'BANDWIDTH_LIMIT C1,ON\n')  
				
		sds_send(s, b'TRIG_MODE NORM\n')            
		sds_send(s, b'C4:TRIG_LEVEL 1\n')
		sds_send(s, b'C4:TRIG_SLOPE POS\n')    
		
		
		if model == "6201" or model == "6101" or model=='6401' or model=="6203":
			sds_send(s, b'TIME_DIV 1MS\n') 
			sds_send(s, b'TRIG_DELAY -3MS\n')    
			                
		if model == "6202":
			sds_send(s, b'TIME_DIV 50US\n')
			sds_send(s, b'TRIG_DELAY -200US\n') 
			
		sds_send(s, b'MEMORY_SIZE 14K\n')      
	
				
		sds_send(s, b'PARAMETER_CUSTOM:RISE,C1\n')
	
	print("Acquiring data...")
	time.sleep(2)
	
	if oscope == 'Tek':
		Wfm1 = get_MSO4054_wfm('CH1')
		Wfm2 = get_MSO4054_wfm('CH4')
		#Wfm3 = get_MSO4054_wfm('CH3')
		Ts = get_MSO4054_XINcr()
	if oscope == 'Sig':
		[Wfm1, num_bytes, Ts] = get_SIGLENT_wfm('1')
		[Wfm2, num_bytes, Ts] = get_SIGLENT_wfm('4')

	N = len(Wfm1)
	t = np.arange(N)*Ts
	f0 = 1/(N*Ts)
	f = np.arange(N)*f0
	
	y1 = smooth_wfm(Wfm2)
	y2 = smooth_wfm(Wfm1)
	M=len(y1)
	
	if oscope == 'Tek':
		s.send(b'MEASU:MEAS1:VAL?\n')
		time.sleep(0.2)
		rdg = s.recv(4096).decode('UTF-8') #convert byte array to list of strings
		tr = np.array(rdg).astype(float) # make list into array then float
		print("Transition duration = %1.7f s" % tr)
	
	if oscope == 'Sig':
		s.sendall(b'C1:PAVA? RISE\n')       # Query RMS value
		rdg= s.recv(100).decode("UTF-8")
		print(rdg)
		tr = float(rdg.split(",")[1])
		print("Rise time: %f" % tr)
		
	
	#fp = open("test.txt", 'a')
	#fp.write("%f,%f,%f,%f,%f,%f\n" %(f, vtrim, itrim, vcoil, pha1, pha2))
	#fp.close()

#except socket.error:
except Exception as err:
	#print ("failed to send to ip " + remote_ip)
	print(err)
	
#s.close()

print("Making plot...")
fig1 = plt.figure(1, figsize=(11,8))
#fig1 = plt.figure(1)
ax1a = fig1.add_subplot(1,1,1)
#ax1b = fig1.add_subplot(2,1,2)
		
plt.figure(1)
plt.axes(ax1a)
plt.plot(t[0:M],y1, 'k', label = "Vin") # dib
plt.plot(t[0:M],y2, 'r', label = "Vout") # dib
ax1a.set_xlabel('Time (s)', fontsize=F)
ax1a.set_ylabel('Amplitude (V)', fontsize=F)
title_str = "Model %s S/N %s CH %s Small Signal Voltage Step Response" % (model, serial, chan)
plt.title(title_str, fontsize=F)
#ax1.ticklabel_format(useOffset=False, style='plain')
plt.xticks(fontsize=F, rotation=0)
plt.yticks(fontsize=F, rotation=0)
plt.ylim([0,4])
plt.grid('True')
#plt.text(0.0012,0.075,"Vout = 410 V", fontsize = 14)
plt.legend(loc="lower right", fontsize = 14)
#ax1a.yaxis.set_major_formatter(FormatStrFormatter('%1.5f'))
ax1a.yaxis.set_major_formatter(tick.FormatStrFormatter('%1.4f'))

if model == "6201" or model == "6101" or model=="6401" or model=="6203":
	plt.text(0.004, 0.2, "Rise time = %1.7f s" % tr, fontsize = 14)
if model == "6202":
	plt.text(0.0002, 0.2, "Rise time = %1.7f s" % tr, fontsize = 14)
if model == "6401" or model == "6101":
	plt.text(0.004, 0.2, "Rise time = %1.7f s" % tr, fontsize = 14)
	
try:
	os.mkdir(filepath)
except:
	pass
print("Writing to file %s" % (filepath+filename))
plt.savefig(filepath+filename)
plt.show()

s.close()
