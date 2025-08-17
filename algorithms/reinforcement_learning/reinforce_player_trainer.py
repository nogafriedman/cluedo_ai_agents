import numpy as np
import torch
import torch.nn as nn
import torch.optim as optim
from game_elements.action import Action

GAMMA = 0.99

# NN definitions 
class PolicyNetwork(nn.Module):
    def __init__(self, input_size, output_size):
        super(PolicyNetwork, self).__init__()
        self.fc1 = nn.Linear(input_size, 128)
        self.fc2 = nn.Linear(128, 64)
        self.fc3 = nn.Linear(64, output_size)

    def forward(self, x):
        x = torch.relu(self.fc1(x))
        x = torch.relu(self.fc2(x))
        return torch.softmax(self.fc3(x), dim=-1)

class ReinforcePlayerTrainer:
    def __init__(self, input_size, output_size, lr=1e-3):
        self.policy_network = PolicyNetwork(input_size, output_size)
        self.optimizer = optim.Adam(self.policy_network.parameters(), lr=lr)
        self.trajectory = []
        self.episode_rewards = []
        self.episode_log_probs = []
        self.gamma = GAMMA

    def select_action(self, state):
        state_tensor = torch.FloatTensor(state)
        probs = self.policy_network(state_tensor)

        # Get actions and their probabilities
        sorted_probs, sorted_actions = torch.sort(probs, descending=True)

        return sorted_actions, sorted_probs
    
    def store_trajectory(self, rewards, log_probs):
        self.episode_rewards.extend(rewards)
        self.episode_log_probs.extend(log_probs)

    def update_policy(self):
        returns = []
        G = 0
        for reward, log_prob in zip(reversed(self.episode_rewards), reversed(self.episode_log_probs)):
            G = reward + self.gamma * G
            returns.insert(0, G)
        
        returns = torch.tensor(returns)
        returns = (returns - returns.mean()) / (returns.std() + 1e-9)
        
        policy_loss = []
        for G, log_prob in zip(returns, self.episode_log_probs):
            policy_loss.append(-log_prob * G)
        
        policy_loss = torch.stack(policy_loss).sum()
        
        self.optimizer.zero_grad()
        policy_loss.backward()
        self.optimizer.step()
        
        self.episode_rewards = []
        self.episode_log_probs = []