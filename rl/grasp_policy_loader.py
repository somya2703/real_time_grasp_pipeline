from stable_baselines3 import PPO
import numpy as np


class RLGraspPolicy:

    def __init__(self):

        #self.model = PPO.load("models/grasp_policy")
        self.model = PPO.load("/workspace/models/grasp_policy")

    def select_grasp(self, state):

        state = np.array(state)

        action, _ = self.model.predict(state)

        return action