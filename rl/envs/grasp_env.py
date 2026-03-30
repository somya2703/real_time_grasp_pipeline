import gymnasium as gym
from gymnasium import spaces
import numpy as np


class GraspEnv(gym.Env):
    """
    Simple tabletop grasp environment.

    Observation: 6-dim vector [object_x, object_y, object_z,
                                gripper_x, gripper_y, gripper_z]
    Action:      Discrete(3) — top grasp, side grasp, angled grasp
    Reward:      +1 on success, -1 on failure
    """

    metadata = {"render_modes": []}

    def __init__(self):
        super().__init__()

        self.action_space = spaces.Discrete(3)

        self.observation_space = spaces.Box(
            low=-10.0,
            high=10.0,
            shape=(6,),
            dtype=np.float32
        )

        # Success probabilities per action
        self.success_prob = [0.6, 0.5, 0.4]

        self.object_position = np.zeros(3, dtype=np.float32)

    def reset(self, seed=None, options=None):
        super().reset(seed=seed)

        self.object_position = self.np_random.uniform(
            low=-0.2, high=0.2, size=(3,)
        ).astype(np.float32)

        gripper_position = self.np_random.random(3).astype(np.float32)

        obs = np.concatenate([self.object_position, gripper_position])

        info = {}
        return obs, info

    def step(self, action):
        success = self.np_random.random() < self.success_prob[action]

        reward = 1.0 if success else -1.0

        # Each episode is a single grasp attempt
        terminated = True
        truncated = False

        obs = self.np_random.random(6).astype(np.float32)

        info = {"success": success, "action": int(action)}

        return obs, reward, terminated, truncated, info

    def render(self):
        pass

    def close(self):
        pass