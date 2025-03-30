import random
import time

class DummySerial:
    def __init__(self, baudrate=9600, timeout=1):
        self.baudrate = baudrate
        self.timeout = timeout
        self.in_waiting = True  # Simulate that data is always available

    def readline(self):
        # Simulate sensor values for 12 batteries (or channels)
        values = [str(random.randint(0, 1023)) for _ in range(12)]
        # Simulate a slight delay
        time.sleep(0.1)
        # Return a byte string as if read from an actual serial port
        return (",".join(values) + "\n").encode('utf-8')
