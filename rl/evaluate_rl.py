from stable_baselines3 import PPO
from rl.envs.grasp_env import GraspEnv


def evaluate():

    env = GraspEnv()

    model = PPO.load("models/grasp_policy")

    success = 0

    for _ in range(100):

        state = env.reset()

        action, _ = model.predict(state)

        _, reward, _, _ = env.step(action)

        if reward > 0:
            success += 1

    print("Success rate:", success / 100)


if __name__ == "__main__":
    evaluate()