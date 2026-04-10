# TORCS Reinforcement Learning Driver

Train / evaluate an RL agent on TORCS with Stable-Baselines3.

## Layout

```
ml_driver/
├── config.yaml       ← Various settings
├── wrappers.py       ← Gymnasium wrapper
├── utils.py          ← factories + helpers
├── train.py          ← RL agent training
├── evaluate.py       ← eval + demo (--episodes 1)
├── requirements.txt
└── README.md
```

## Setup

```bash
pip install -r requirements.txt
```

## Train

```bash
python train.py
python train.py --timesteps 50000 --algorithm SAC
```

Training settings can be changed in `config.yaml`
Logs → `logs/` (TensorBoard), checkpoints → `checkpoints/`.

## Evaluate

```bash
python evaluate.py                          # 10 episodes → results.json
python evaluate.py --episodes 1             # quick demo
python evaluate.py --model checkpoints/torcs_rl_50000_steps.zip --episodes 20
```

## Potential Issues
- All development was done on Python 3.10, other versions may not work
- Make sure TORCS is in focus while launching because we simulate keyboard inputs to start the race
- If TORCS is closing before the race starts you might need to increase the wait time in `gym_torcs/autostart.py`