setup:
	bash scripts/setup.sh

build:
	bash scripts/build.sh

run:
	bash scripts/run_pipeline.sh

sim:
	bash scripts/run_sim.sh

benchmark:
	bash scripts/benchmark.sh

profile:
	bash scripts/gpu_profile.sh

tensorrt:
	bash scripts/export_tensorrt.sh

demo:
	bash scripts/record_demo.sh

train-rl:
	bash scripts/train_rl.sh

eval-rl:
	bash scripts/evaluate_rl.sh