import time
import pynvml

pynvml.nvmlInit()

handle = pynvml.nvmlDeviceGetHandleByIndex(0)

for _ in range(50):

    util = pynvml.nvmlDeviceGetUtilizationRates(handle)
    mem = pynvml.nvmlDeviceGetMemoryInfo(handle)

    print(f"GPU Utilization: {util.gpu}%")
    print(f"Memory Used: {mem.used/1024**2:.2f} MB")

    time.sleep(1)