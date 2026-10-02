from abc import ABC, abstractmethod
import csv
import numpy as np


class Oscilloscope(ABC):
    """Abstract base class for oscilloscope implementations."""

    def __init__(self):
        self.is_open = False

    @abstractmethod
    def open(self):
        """Open/connect to the oscilloscope."""
        raise NotImplementedError

    @abstractmethod
    def close(self):
        """Close/disconnect from the oscilloscope."""
        raise NotImplementedError

    @abstractmethod
    def configure_channel(self, channel, enabled=True, **kwargs):
        """Configure one oscilloscope input channel."""
        raise NotImplementedError

    @abstractmethod
    def configure_trigger(self, channel, **kwargs):
        """Configure the oscilloscope trigger."""
        raise NotImplementedError

    @abstractmethod
    def capture(self, **kwargs):
        """
        Acquire a block of data.

        Returns
        -------
        time_s : np.ndarray
            Time axis in seconds.
        data : dict[str, np.ndarray]
            Channel name -> voltage samples in volts.
        """
        raise NotImplementedError

    @staticmethod
    def calculate_rms(signal):
        signal = np.asarray(signal, dtype=float)
        return float(np.sqrt(np.mean(signal ** 2)))

    @staticmethod
    def save_csv(filename, time_s, data):
        channel_names = list(data.keys())

        with open(filename, "w", newline="") as f:
            writer = csv.writer(f)
            writer.writerow(
                ["time_s"] + [f"channel_{name}_V" for name in channel_names]
            )

            for i in range(len(time_s)):
                writer.writerow(
                    [time_s[i]] + [data[name][i] for name in channel_names]
                )

        print(f"Saved capture to {filename}")

    def __enter__(self):
        self.open()
        return self

    def __exit__(self, exc_type, exc_value, traceback):
        self.close()
