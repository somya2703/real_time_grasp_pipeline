import os
import sys

sys.path.insert(0, "/workspace")

from stable_baselines3 import PPO
from stable_baselines3.common.env_checker import check_env
from stable_baselines3.common.callbacks import (
    EvalCallback,
    CheckpointCallback,
    BaseCallback,
)
from stable_baselines3.common.monitor import Monitor
import numpy as np

from rl.envs.grasp_env import GraspEnv


LOG_DIR   = "/workspace/logs/ppo_grasp"
MODEL_DIR = "/workspace/models"
CKPT_DIR  = "/workspace/models/checkpoints"

os.makedirs(LOG_DIR,   exist_ok=True)
os.makedirs(CKPT_DIR,  exist_ok=True)


class TrainingProgressCallback(BaseCallback):
    """
    Logs additional metrics to TensorBoard at each rollout:
      - mean episode reward
      - mean episode length
      - success rate (reward > 0)
    """

    def __init__(self, verbose=0):
        super().__init__(verbose)
        self.episode_rewards = []
        self.episode_lengths = []

    def _on_step(self) -> bool:
        
        infos = self.locals.get("infos", [])
        for info in infos:
            if "episode" in info:
                self.episode_rewards.append(info["episode"]["r"])
                self.episode_lengths.append(info["episode"]["l"])

        return True

    def _on_rollout_end(self) -> None:
        if not self.episode_rewards:
            return

        mean_reward  = float(np.mean(self.episode_rewards))
        mean_length  = float(np.mean(self.episode_lengths))
        success_rate = float(np.mean([r > 0 for r in self.episode_rewards]))

        self.logger.record("grasp/mean_episode_reward",  mean_reward)
        self.logger.record("grasp/mean_episode_length",  mean_length)
        self.logger.record("grasp/success_rate",         success_rate)
        self.logger.record("grasp/episodes_collected",   len(self.episode_rewards))

        if self.verbose:
            print(
                f"  [rollout] reward={mean_reward:.3f}  "
                f"success={success_rate*100:.1f}%  "
                f"ep_len={mean_length:.1f}"
            )

        self.episode_rewards.clear()
        self.episode_lengths.clear()


def train():
    print("=" * 60)
    print("  Grasp Policy Training — PPO")
    print(f"  TensorBoard logs : {LOG_DIR}")
    print(f"  Checkpoints      : {CKPT_DIR}")
    print("=" * 60)
    print()
    print("  Launch TensorBoard in a separate terminal with:")
    print(f"    tensorboard --logdir {LOG_DIR} --host 0.0.0.0 --port 6006")
    print("  Then open http://localhost:6006 in your browser.")
    print()

    
    env      = Monitor(GraspEnv(), filename=os.path.join(LOG_DIR, "monitor"))
    eval_env = Monitor(GraspEnv())

    check_env(env, warn=True)

    model = PPO(
        "MlpPolicy",
        env,
        verbose=1,
        learning_rate=3e-4,
        n_steps=1024,
        batch_size=64,
        n_epochs=10,
        gamma=0.99,
        gae_lambda=0.95,
        clip_range=0.2,
        ent_coef=0.01,          # small entropy bonus for exploration
        device="cpu",           # MLP policy is faster on CPU
        tensorboard_log=LOG_DIR,
    )

    callbacks = [
        
        TrainingProgressCallback(verbose=1),

        
        EvalCallback(
            eval_env,
            best_model_save_path=MODEL_DIR,
            log_path=LOG_DIR,
            eval_freq=5000,
            n_eval_episodes=20,
            deterministic=True,
            verbose=1,
        ),

        #checkpoints every 25k steps
        CheckpointCallback(
            save_freq=25_000,
            save_path=CKPT_DIR,
            name_prefix="grasp_policy",
            verbose=1,
        ),
    ]

    model.learn(
        total_timesteps=200_000,
        callback=callbacks,
        tb_log_name="ppo_grasp",
        progress_bar=True,
    )

    
    final_path = os.path.join(MODEL_DIR, "grasp_policy")
    model.save(final_path)
    print(f"\nTraining complete. Final model saved to {final_path}.zip")

    env.close()
    eval_env.close()


if __name__ == "__main__":
    train()
