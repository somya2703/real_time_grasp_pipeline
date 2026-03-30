import pandas as pd
import matplotlib.pyplot as plt

df = pd.read_csv("benchmark/latency_log.csv")

plt.hist(df["latency_ms"], bins=20)

plt.title("Pipeline Latency Distribution")
plt.xlabel("Latency (ms)")
plt.ylabel("Frames")

plt.savefig("benchmark/latency_distribution.png")
print("Saved to benchmark/latency_distribution.png")