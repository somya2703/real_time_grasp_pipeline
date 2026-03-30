import time
import csv

latencies = []

for i in range(50):

    start = time.time()

    # simulate step
    time.sleep(0.05)

    end = time.time()

    latency = (end-start)*1000
    latencies.append(latency)

with open("benchmark/latency_log.csv","w") as f:

    writer = csv.writer(f)
    writer.writerow(["frame","latency_ms"])

    for i,l in enumerate(latencies):
        writer.writerow([i,l])