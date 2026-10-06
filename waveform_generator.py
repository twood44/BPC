from abc import ABC, abstractmethod
import pyvisa
import time

class WaveformGenerator(ABC):
    """Generic interface for a waveform generator."""

    @abstractmethod
    def connect(self):
        pass

    @abstractmethod
    def set_ramp(self, frequency, amplitude, offset=0, symmetry=50, channel=1):
        pass

    @abstractmethod
    def set_square(self, frequency, amplitude, offset=0, channel=1):
        pass

    @abstractmethod
    def set_dc(self, voltage, channel=1):
        pass

    @abstractmethod
    def output_on(self, channel=1):
        pass

    @abstractmethod
    def output_off(self, channel=1):
        pass

    @abstractmethod
    def close(self):
        pass


class Agilent33220A(WaveformGenerator):
    """LAN/PyVISA implementation."""

    def __init__(self, ip, timeout_ms=5000, max_retries=10, retry_delay=0.1):
        self.ip = ip
        self.timeout_ms = timeout_ms
        self.max_retries=max_retries
        self.retry_delay=retry_delay

        self.rm = None
        self.inst = None

    def connect(self):
        if self.rm is None:
         self.rm = pyvisa.ResourceManager()

        resource=f"TCPIP0::{self.ip}::inst0::INSTR"
        for attempt in range (1,self.max_retries+1):
            try:
                self.inst = self.rm.open_resource(resource)
                self.inst.timeout = self.timeout_ms
                print(f"Connected on attempt {attempt}:")
                print(self.identify)

                return
            except Exception as err:
                print(
                        f"Connection attempt "
                        f"{attempt}/{self.max_retries} failed:"
                )
                print(err) 

                if self.inst is not None:
                    try:
                        self.inst.close()
                    except Exception:
                        pass
                    self.inst=None
                
                if attempt< self.max_retries:
                    time.sleep(self.retry_delay)


        raise ConnectionError(
            f"Could not connect to waveform generator at "
            f"{self.ip} after {self.max_retries} attempts"
        )     
        
#        print("Connected to:")
 #       print(self.identify())

    def _check_connection(self):
        if self.inst is None:
            raise RuntimeError("Call connect() before using the generator.")

    def _source(self, channel):
        if channel not in (1, 2):
            raise ValueError("channel must be 1 or 2")
        return f"SOUR{channel}"

    def set_ramp(self, frequency, amplitude, offset=0, symmetry=50, channel=1):
        self._check_connection()
        src = self._source(channel)
        self.inst.write(f"{src}:FUNC RAMP")
        self.inst.write(f"{src}:FUNC:RAMP:SYMM {symmetry}")
        self.inst.write(f"{src}:VOLT:UNIT VPP")
        self.inst.write(f"{src}:VOLT {amplitude}")
        self.inst.write(f"{src}:VOLT:OFFS {offset}")
        self.inst.write(f"{src}:FREQ {frequency}")

    def set_square(self, frequency, amplitude, offset=0, channel=1):
        self._check_connection()
        src = self._source(channel)
        self.inst.write(f"{src}:FUNC SQUARE")
        self.inst.write(f"{src}:VOLT:UNIT VPP")
        self.inst.write(f"{src}:VOLT {amplitude}")
        self.inst.write(f"{src}:VOLT:OFFS {offset}")
        self.inst.write(f"{src}:FREQ {frequency}")

    def set_dc(self, voltage, channel=1):
        self._check_connection()
        src = self._source(channel)
        self.inst.write(f"{src}:FUNC DC")
        self.inst.write(f"{src}:VOLT:OFFS {voltage}")

    def output_on(self, channel=1):
        self._check_connection()
        self.inst.write(f"OUTP{channel}:LOAD INF")
        self.inst.write(f"OUTP{channel} ON")

    def output_off(self, channel=1):
        self._check_connection()
        self.inst.write(f"OUTP{channel} OFF")

    def identify(self):
        self._check_connection()
        return self.inst.query("*IDN?").strip()

    def close(self):
        if self.inst is not None:
            self.inst.close()
            self.inst = None
        if self.rm is not None:
            self.rm.close()
            self.rm = None



class Keysight33500B(WaveformGenerator):
    """LAN/PyVISA implementation."""

    def __init__(self, ip, timeout_ms=5000, max_retries=10, retry_delay=0.1):
        self.ip = ip
        self.timeout_ms = timeout_ms
        self.max_retries=max_retries
        self.retry_delay=retry_delay

        self.rm = None
        self.inst = None

    def connect(self):
        if self.rm is None:
         self.rm = pyvisa.ResourceManager()

        resource=f"TCPIP0::{self.ip}::inst0::INSTR"
        for attempt in range (1,self.max_retries+1):
            try:
                self.inst = self.rm.open_resource(resource)
                self.inst.timeout = self.timeout_ms
                print(f"Connected on attempt {attempt}:")
                print(self.identify)

                return
            except Exception as err:
                print(
                        f"Connection attempt "
                        f"{attempt}/{self.max_retries} failed:"
                )
                print(err) 

                if self.inst is not None:
                    try:
                        self.inst.close()
                    except Exception:
                        pass
                    self.inst=None
                
                if attempt< self.max_retries:
                    time.sleep(self.retry_delay)


        raise ConnectionError(
            f"Could not connect to waveform generator at "
            f"{self.ip} after {self.max_retries} attempts"
        )     
        
#        print("Connected to:")
 #       print(self.identify())

    def _check_connection(self):
        if self.inst is None:
            raise RuntimeError("Call connect() before using the generator.")

    def _source(self, channel):
        if channel not in (1, 2):
            raise ValueError("channel must be 1 or 2")
        return f"SOUR{channel}"

    def set_ramp(self, frequency, amplitude, offset=0, symmetry=50, channel=1):
        self._check_connection()
        src = self._source(channel)
        self.inst.write(f"{src}:FUNC RAMP")
        self.inst.write(f"{src}:FUNC:RAMP:SYMM {symmetry}")
        self.inst.write(f"{src}:VOLT:UNIT VPP")
        self.inst.write(f"{src}:VOLT {amplitude}")
        self.inst.write(f"{src}:VOLT:OFFS {offset}")
        self.inst.write(f"{src}:FREQ {frequency}")

    def set_square(self, frequency, amplitude, offset=0, channel=1):
        self._check_connection()
        src = self._source(channel)
        self.inst.write(f"{src}:FUNC SQUARE")
        self.inst.write(f"{src}:VOLT:UNIT VPP")
        self.inst.write(f"{src}:VOLT {amplitude}")
        self.inst.write(f"{src}:VOLT:OFFS {offset}")
        self.inst.write(f"{src}:FREQ {frequency}")

    def set_dc(self, voltage, channel=1):
        self._check_connection()
        src = self._source(channel)
        self.inst.write(f"{src}:FUNC DC")
        self.inst.write(f"{src}:VOLT:OFFS {voltage}")

    def output_on(self, channel=1):
        self._check_connection()
        self.inst.write(f"OUTP{channel}:LOAD INF")
        self.inst.write(f"OUTP{channel} ON")

    def output_off(self, channel=1):
        self._check_connection()
        self.inst.write(f"OUTP{channel} OFF")

    def identify(self):
        self._check_connection()
        return self.inst.query("*IDN?").strip()

    def close(self):
        if self.inst is not None:
            self.inst.close()
            self.inst = None
        if self.rm is not None:
            self.rm.close()
            self.rm = None
