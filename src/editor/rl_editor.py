"""
🤖 Reinforcement Learning Parameter Editor — Adaptive Cas-AI System

Advanced reinforcement learning-based parameter editing inspired by
adaptive CRISPR systems. Like evolution learning the best editing
strategies, these RL agents learn optimal parameter modifications.

From random mutations to intelligent design. From trial-and-error to mastery.
"""

import numpy as np
import torch
import torch.nn as nn
import torch.nn.functional as F
import torch.optim as optim
from torch.distributions import Normal
from typing import Dict, List, Optional, Tuple, Any
from datetime import datetime
import logging
from dataclasses import dataclass, field
import random
from collections import namedtuple
import warnings

from ..core.base_layers import BaseEditor, EditResult, TargetSite
from ..core.genome import FinancialGenome

# Suppress warnings for cleaner output
warnings.filterwarnings('ignore')
logger = logging.getLogger(__name__)

# Experience replay buffer components
Experience = namedtuple('Experience', ['state', 'action', 'reward', 'next_state', 'done'])


@dataclass
class RLConfig:
    """
    🎯 Reinforcement Learning Configuration
    
    Advanced configuration for RL-based parameter editing with
    multiple algorithms and adaptive strategies.
    """
    # Algorithm selection
    algorithm: str = "PPO"  # "DQN", "A2C", "PPO", "SAC"

    # Network architecture
    hidden_sizes: List[int] = field(default_factory=lambda: [256, 256, 128])
    activation: str = "relu"  # "relu", "tanh", "gelu"
    dropout_rate: float = 0.1

    # Training parameters
    learning_rate: float = 3e-4
    batch_size: int = 64
    buffer_size: int = 100000
    gamma: float = 0.99  # Discount factor
    tau: float = 0.005  # Soft update rate

    # PPO specific
    ppo_epochs: int = 10
    ppo_clip_ratio: float = 0.2
    value_loss_coef: float = 0.5
    entropy_coef: float = 0.01

    # DQN specific
    epsilon_start: float = 1.0
    epsilon_end: float = 0.01
    epsilon_decay: float = 0.995
    target_update_freq: int = 1000
    double_dqn: bool = True

    # Environment settings
    max_edit_magnitude: float = 0.5  # Maximum parameter change
    reward_scaling: float = 1.0
    punishment_factor: float = -2.0
    stability_weight: float = 0.3
    performance_weight: float = 0.7

    # Training control
    train_frequency: int = 4
    gradient_steps: int = 1
    max_grad_norm: float = 0.5


class ParameterEditEnvironment:
    """
    🌍 Parameter Editing Environment
    
    RL environment for learning optimal parameter editing strategies.
    Like a laboratory where AI learns the best genetic modifications.
    """

    def __init__(self,
                 genome: FinancialGenome,
                 target_sites: List[TargetSite],
                 config: RLConfig):
        self.genome = genome
        self.target_sites = target_sites
        self.config = config

        # Environment state
        self.current_parameters = self._get_parameter_values()
        self.initial_parameters = self.current_parameters.copy()
        self.edit_history = []
        self.step_count = 0
        self.max_steps = len(target_sites) * 3  # Allow multiple edits per parameter

        # Performance tracking
        self.initial_fitness = self._calculate_fitness()
        self.best_fitness = self.initial_fitness
        self.stability_score = 1.0

    def _get_parameter_values(self) -> np.ndarray:
        """Get current parameter values as numpy array."""
        values = []
        for site in self.target_sites:
            param_path = site.parameter_path
            gene = self.genome.get_gene(param_path)

            if isinstance(gene.value, (int, float)):
                values.append(float(gene.value))
            elif isinstance(gene.value, np.ndarray):
                values.extend(gene.value.flatten().tolist())
            else:
                values.append(0.0)  # Fallback

        return np.array(values, dtype=np.float32)

    def _set_parameter_values(self, values: np.ndarray):
        """Set parameter values from numpy array."""
        value_idx = 0

        for site in self.target_sites:
            param_path = site.parameter_path
            gene = self.genome.get_gene(param_path)

            if isinstance(gene.value, (int, float)):
                new_value = float(values[value_idx])
                self.genome.set_parameter(param_path, new_value, "rl_edit")
                value_idx += 1
            elif isinstance(gene.value, np.ndarray):
                shape = gene.value.shape
                size = gene.value.size
                new_value = values[value_idx:value_idx + size].reshape(shape)
                self.genome.set_parameter(param_path, new_value, "rl_edit")
                value_idx += size

    def _calculate_fitness(self) -> float:
        """Calculate fitness score for current parameters."""
        # Simplified fitness calculation
        # In practice, this would involve backtesting or forward simulation

        # Portfolio-based fitness (example)
        param_values = self._get_parameter_values()

        # Reward moderate parameter values, penalize extremes
        fitness = 1.0

        for i, (value, site) in enumerate(zip(param_values, self.target_sites)):
            gene = self.genome.get_gene(site.parameter_path)

            # Check constraint violations
            if gene.constraints:
                if 'min' in gene.constraints and value < gene.constraints['min']:
                    fitness -= 0.5
                if 'max' in gene.constraints and value > gene.constraints['max']:
                    fitness -= 0.5

            # Reward values near optimal ranges (example heuristic)
            if 'momentum' in site.parameter_path.lower():
                # Momentum parameters: prefer moderate values
                optimal_range = (10, 50)
                if optimal_range[0] <= value <= optimal_range[1]:
                    fitness += 0.1
                else:
                    fitness -= 0.05

            elif 'volatility' in site.parameter_path.lower():
                # Volatility parameters: prefer lower values
                if 0.05 <= value <= 0.25:
                    fitness += 0.1
                else:
                    fitness -= 0.05

        # Add some randomness to simulate market uncertainty
        noise = np.random.normal(0, 0.02)
        fitness += noise

        return max(0.0, fitness)

    def _calculate_stability(self) -> float:
        """Calculate stability score based on parameter changes."""
        if len(self.edit_history) == 0:
            return 1.0

        # Penalize large changes
        total_change = sum(abs(edit['magnitude']) for edit in self.edit_history)
        stability = max(0.0, 1.0 - total_change / len(self.target_sites))

        return stability

    def get_state(self) -> np.ndarray:
        """Get current environment state."""
        # State includes:
        # - Current parameter values (normalized)
        # - Parameter bounds and constraints
        # - Edit history features
        # - Performance metrics

        state_components = []

        # Current parameter values (normalized to [-1, 1])
        param_values = self._get_parameter_values()

        # Normalize based on constraints
        normalized_params = []
        for i, site in enumerate(self.target_sites):
            value = param_values[i] if i < len(param_values) else 0.0
            gene = self.genome.get_gene(site.parameter_path)

            if gene.constraints and 'min' in gene.constraints and 'max' in gene.constraints:
                min_val, max_val = gene.constraints['min'], gene.constraints['max']
                normalized = 2 * (value - min_val) / (max_val - min_val) - 1
            else:
                normalized = np.tanh(value / 10.0)  # Fallback normalization

            normalized_params.append(normalized)

        state_components.extend(normalized_params)

        # Performance metrics
        current_fitness = self._calculate_fitness()
        fitness_change = (current_fitness - self.initial_fitness) / (self.initial_fitness + 1e-8)
        stability = self._calculate_stability()

        state_components.extend([
            fitness_change,
            stability,
            self.step_count / self.max_steps,  # Progress
            len(self.edit_history) / self.max_steps  # Edit density
        ])

        # Recent edit history (last 3 edits)
        recent_edits = self.edit_history[-3:] if len(self.edit_history) >= 3 else self.edit_history
        edit_features = []

        for i in range(3):
            if i < len(recent_edits):
                edit = recent_edits[i]
                edit_features.extend([
                    edit['parameter_idx'] / len(self.target_sites),
                    edit['magnitude'],
                    edit['reward']
                ])
            else:
                edit_features.extend([0.0, 0.0, 0.0])

        state_components.extend(edit_features)

        return np.array(state_components, dtype=np.float32)

    def step(self, action: np.ndarray) -> Tuple[np.ndarray, float, bool, Dict]:
        """Execute action and return new state, reward, done, info."""
        self.step_count += 1

        # Decode action
        parameter_idx = int(action[0] * len(self.target_sites))
        parameter_idx = np.clip(parameter_idx, 0, len(self.target_sites) - 1)

        edit_magnitude = action[1] * self.config.max_edit_magnitude

        # Apply parameter edit
        old_params = self._get_parameter_values().copy()
        new_params = old_params.copy()

        if parameter_idx < len(new_params):
            # Get parameter constraints
            site = self.target_sites[parameter_idx]
            gene = self.genome.get_gene(site.parameter_path)

            old_value = new_params[parameter_idx]
            new_value = old_value + edit_magnitude

            # Apply constraints
            if gene.constraints:
                if 'min' in gene.constraints:
                    new_value = max(new_value, gene.constraints['min'])
                if 'max' in gene.constraints:
                    new_value = min(new_value, gene.constraints['max'])

            new_params[parameter_idx] = new_value

            # Update genome
            self._set_parameter_values(new_params)

            # Record edit
            edit_record = {
                'parameter_idx': parameter_idx,
                'parameter_path': site.parameter_path,
                'old_value': old_value,
                'new_value': new_value,
                'magnitude': abs(new_value - old_value),
                'step': self.step_count
            }

        # Calculate reward
        new_fitness = self._calculate_fitness()
        new_stability = self._calculate_stability()

        # Reward components
        performance_reward = (new_fitness - self.initial_fitness) * self.config.performance_weight
        stability_reward = new_stability * self.config.stability_weight

        # Penalty for constraint violations
        constraint_penalty = 0.0
        for site in self.target_sites:
            gene = self.genome.get_gene(site.parameter_path)
            if not self.genome._check_constraints(gene):
                constraint_penalty += self.config.punishment_factor

        reward = (performance_reward + stability_reward + constraint_penalty) * self.config.reward_scaling

        # Update tracking
        if parameter_idx < len(new_params):
            edit_record['reward'] = reward
            self.edit_history.append(edit_record)

        if new_fitness > self.best_fitness:
            self.best_fitness = new_fitness

        self.stability_score = new_stability

        # Check if episode is done
        done = (self.step_count >= self.max_steps or
                new_stability < 0.1 or  # Too unstable
                len(self.edit_history) >= len(self.target_sites) * 2)  # Enough edits

        # Get new state
        new_state = self.get_state()

        # Info dictionary
        info = {
            'fitness': new_fitness,
            'stability': new_stability,
            'best_fitness': self.best_fitness,
            'edits_made': len(self.edit_history),
            'constraint_violations': constraint_penalty != 0.0
        }

        return new_state, reward, done, info

    def reset(self) -> np.ndarray:
        """Reset environment to initial state."""
        self._set_parameter_values(self.initial_parameters)
        self.edit_history = []
        self.step_count = 0
        self.stability_score = 1.0

        return self.get_state()


class ActorCriticNetwork(nn.Module):
    """
    🎭 Actor-Critic Network for PPO
    
    Neural network that learns both policy (actor) and value function (critic)
    for intelligent parameter editing decisions.
    """

    def __init__(self, state_dim: int, action_dim: int, config: RLConfig):
        super(ActorCriticNetwork, self).__init__()

        self.config = config

        # Shared layers
        layers = []
        prev_size = state_dim

        for hidden_size in config.hidden_sizes:
            layers.extend([
                nn.Linear(prev_size, hidden_size),
                self._get_activation(),
                nn.Dropout(config.dropout_rate)
            ])
            prev_size = hidden_size

        self.shared_layers = nn.Sequential(*layers)

        # Actor head (policy)
        self.actor_mean = nn.Linear(prev_size, action_dim)
        self.actor_log_std = nn.Parameter(torch.zeros(action_dim))

        # Critic head (value function)
        self.critic = nn.Linear(prev_size, 1)

        # Initialize weights
        self.apply(self._init_weights)

    def _get_activation(self):
        """Get activation function based on config."""
        if self.config.activation == "relu":
            return nn.ReLU()
        if self.config.activation == "tanh":
            return nn.Tanh()
        if self.config.activation == "gelu":
            return nn.GELU()
        return nn.ReLU()

    def _init_weights(self, module):
        """Initialize network weights."""
        if isinstance(module, nn.Linear):
            torch.nn.init.orthogonal_(module.weight, gain=np.sqrt(2))
            torch.nn.init.constant_(module.bias, 0.0)

    def forward(self, state):
        shared = self.shared_layers(state)

        # Actor
        action_mean = self.actor_mean(shared)
        action_log_std = self.actor_log_std.expand_as(action_mean)
        action_std = torch.exp(action_log_std)

        # Critic
        value = self.critic(shared)

        return action_mean, action_std, value

    def get_action_and_value(self, state, action=None):
        action_mean, action_std, value = self.forward(state)

        # Create distribution
        dist = Normal(action_mean, action_std)

        if action is None:
            action = dist.sample()

        action_logprob = dist.log_prob(action).sum(axis=-1)
        dist_entropy = dist.entropy().sum(axis=-1)

        return action, action_logprob, dist_entropy, value


class DQNNetwork(nn.Module):
    """
    🎯 Deep Q-Network for discrete parameter editing
    
    Q-learning network that learns optimal action values
    for parameter modification decisions.
    """

    def __init__(self, state_dim: int, action_dim: int, config: RLConfig):
        super(DQNNetwork, self).__init__()

        layers = []
        prev_size = state_dim

        for hidden_size in config.hidden_sizes:
            layers.extend([
                nn.Linear(prev_size, hidden_size),
                nn.ReLU(),
                nn.Dropout(config.dropout_rate)
            ])
            prev_size = hidden_size

        layers.append(nn.Linear(prev_size, action_dim))

        self.network = nn.Sequential(*layers)

        # Initialize weights
        self.apply(self._init_weights)

    def _init_weights(self, module):
        if isinstance(module, nn.Linear):
            torch.nn.init.xavier_uniform_(module.weight)
            torch.nn.init.constant_(module.bias, 0.0)

    def forward(self, state):
        return self.network(state)


class PPOAgent:
    """
    🏆 Proximal Policy Optimization Agent
    
    Advanced RL agent using PPO algorithm for stable and efficient
    parameter editing strategy learning.
    """

    def __init__(self, state_dim: int, action_dim: int, config: RLConfig):
        self.config = config
        self.device = torch.device("cuda" if torch.cuda.is_available() else "cpu")

        # Network
        self.network = ActorCriticNetwork(state_dim, action_dim, config).to(self.device)
        self.optimizer = optim.Adam(self.network.parameters(), lr=config.learning_rate)

        # Training data storage
        self.states = []
        self.actions = []
        self.logprobs = []
        self.rewards = []
        self.values = []
        self.dones = []

    def get_action(self, state: np.ndarray, training: bool = True):
        """Get action from current policy."""
        state_tensor = torch.FloatTensor(state).unsqueeze(0).to(self.device)

        with torch.no_grad():
            action, logprob, entropy, value = self.network.get_action_and_value(state_tensor)

        if training:
            self.states.append(state)
            self.actions.append(action.cpu().numpy()[0])
            self.logprobs.append(logprob.cpu().numpy()[0])
            self.values.append(value.cpu().numpy()[0])

        # Clip actions to valid range
        action_np = action.cpu().numpy()[0]
        action_np = np.clip(action_np, -1.0, 1.0)

        return action_np

    def store_experience(self, reward: float, done: bool):
        """Store experience for training."""
        self.rewards.append(reward)
        self.dones.append(done)

    def update(self):
        """Update policy using PPO algorithm."""
        if len(self.states) == 0:
            return {}

        # Convert to tensors
        states = torch.FloatTensor(np.array(self.states)).to(self.device)
        actions = torch.FloatTensor(np.array(self.actions)).to(self.device)
        old_logprobs = torch.FloatTensor(np.array(self.logprobs)).to(self.device)
        rewards = torch.FloatTensor(np.array(self.rewards)).to(self.device)
        values = torch.FloatTensor(np.array(self.values)).to(self.device)
        dones = torch.BoolTensor(np.array(self.dones)).to(self.device)

        # Calculate advantages and returns
        advantages, returns = self._calculate_advantages(rewards, values, dones)

        # Normalize advantages
        advantages = (advantages - advantages.mean()) / (advantages.std() + 1e-8)

        # PPO updates
        total_policy_loss = 0
        total_value_loss = 0
        total_entropy_loss = 0

        for _ in range(self.config.ppo_epochs):
            # Get current policy outputs
            _, new_logprobs, entropy, new_values = self.network.get_action_and_value(states, actions)

            # Policy loss
            ratio = torch.exp(new_logprobs - old_logprobs)
            surr1 = ratio * advantages
            surr2 = torch.clamp(ratio, 1 - self.config.ppo_clip_ratio, 1 + self.config.ppo_clip_ratio) * advantages
            policy_loss = -torch.min(surr1, surr2).mean()

            # Value loss
            value_loss = F.mse_loss(new_values.squeeze(), returns)

            # Entropy loss
            entropy_loss = -entropy.mean()

            # Total loss
            loss = (policy_loss +
                   self.config.value_loss_coef * value_loss +
                   self.config.entropy_coef * entropy_loss)

            # Update
            self.optimizer.zero_grad()
            loss.backward()
            torch.nn.utils.clip_grad_norm_(self.network.parameters(), self.config.max_grad_norm)
            self.optimizer.step()

            total_policy_loss += policy_loss.item()
            total_value_loss += value_loss.item()
            total_entropy_loss += entropy_loss.item()

        # Clear buffers
        self.states = []
        self.actions = []
        self.logprobs = []
        self.rewards = []
        self.values = []
        self.dones = []

        return {
            'policy_loss': total_policy_loss / self.config.ppo_epochs,
            'value_loss': total_value_loss / self.config.ppo_epochs,
            'entropy_loss': total_entropy_loss / self.config.ppo_epochs
        }

    def _calculate_advantages(self, rewards, values, dones):
        """Calculate GAE advantages and returns."""
        advantages = []
        returns = []

        gae = 0
        next_value = 0

        for step in reversed(range(len(rewards))):
            if step == len(rewards) - 1:
                next_non_terminal = 1.0 - dones[step].float()
                next_value = 0
            else:
                next_non_terminal = 1.0 - dones[step].float()
                next_value = values[step + 1]

            delta = rewards[step] + self.config.gamma * next_value * next_non_terminal - values[step]
            gae = delta + self.config.gamma * 0.95 * next_non_terminal * gae  # GAE lambda = 0.95

            advantages.insert(0, gae)
            returns.insert(0, gae + values[step])

        advantages = torch.stack(advantages)
        returns = torch.stack(returns)

        return advantages, returns


class ReinforcementLearningEditor(BaseEditor):
    """
    🤖 Reinforcement Learning Parameter Editor
    
    Advanced RL-based parameter editing system that learns optimal
    modification strategies through interaction with financial environments.
    
    Biological Analogy:
    - RL Agent → Adaptive Cas Protein
    - Environment → Cellular Context
    - Reward → Evolutionary Fitness
    - Policy → Learned Editing Strategy
    """

    def __init__(self,
                 name: str = "RLEditor",
                 config: Optional[RLConfig] = None):
        """
        Initialize reinforcement learning editor.
        
        Args:
            name: Editor identifier
            config: RL configuration
        """
        super().__init__(name)

        self.config = config or RLConfig()

        # RL components
        self.agent: Optional[PPOAgent] = None
        self.is_trained = False

        # Training tracking
        self.training_episodes = 0
        self.training_rewards = []
        self.training_losses = []

        logger.info(f"Initialized {self.name} with {self.config.algorithm} algorithm")

    def _initialize_agent(self, state_dim: int):
        """Initialize RL agent with proper dimensions."""
        action_dim = 2  # [parameter_index, edit_magnitude]

        if self.config.algorithm == "PPO":
            self.agent = PPOAgent(state_dim, action_dim, self.config)
        else:
            raise NotImplementedError(f"Algorithm {self.config.algorithm} not implemented")

    def train(self,
             training_genomes: List[FinancialGenome],
             training_targets: List[List[TargetSite]],
             num_episodes: int = 1000) -> Dict[str, Any]:
        """
        🎓 Train RL agent on parameter editing tasks
        
        Args:
            training_genomes: List of genomes for training
            training_targets: Corresponding target sites for each genome
            num_episodes: Number of training episodes
            
        Returns:
            Training results and metrics
        """
        logger.info(f"Training RL editor for {num_episodes} episodes")

        if len(training_genomes) != len(training_targets):
            raise ValueError("Number of genomes and targets must match")

        try:
            episode_rewards = []
            episode_lengths = []

            for episode in range(num_episodes):
                # Select random genome and targets
                genome_idx = random.randint(0, len(training_genomes) - 1)
                genome = training_genomes[genome_idx]
                targets = training_targets[genome_idx]

                # Create environment
                env = ParameterEditEnvironment(genome, targets, self.config)

                # Initialize agent if needed
                if self.agent is None:
                    state_dim = len(env.get_state())
                    self._initialize_agent(state_dim)

                # Run episode
                state = env.reset()
                episode_reward = 0
                episode_length = 0

                while True:
                    # Get action
                    action = self.agent.get_action(state, training=True)

                    # Execute action
                    next_state, reward, done, info = env.step(action)

                    # Store experience
                    self.agent.store_experience(reward, done)

                    episode_reward += reward
                    episode_length += 1
                    state = next_state

                    if done:
                        break

                episode_rewards.append(episode_reward)
                episode_lengths.append(episode_length)

                # Update agent
                if episode % self.config.train_frequency == 0:
                    losses = self.agent.update()
                    if losses:
                        self.training_losses.append(losses)

                # Logging
                if episode % 100 == 0:
                    avg_reward = np.mean(episode_rewards[-100:])
                    avg_length = np.mean(episode_lengths[-100:])
                    logger.info(f"Episode {episode}: Avg Reward={avg_reward:.3f}, Avg Length={avg_length:.1f}")

            self.training_episodes = num_episodes
            self.training_rewards = episode_rewards
            self.is_trained = True

            training_results = {
                'training_completed': True,
                'episodes_trained': num_episodes,
                'final_avg_reward': np.mean(episode_rewards[-100:]),
                'final_avg_length': np.mean(episode_lengths[-100:]),
                'best_episode_reward': max(episode_rewards),
                'algorithm_used': self.config.algorithm,
                'total_parameter_edits': sum(episode_lengths)
            }

            logger.info(f"Training completed: {training_results}")

            return training_results

        except Exception as e:
            logger.error(f"Training failed: {str(e)}")
            raise

    def edit_parameters(self,
                       model_genome: FinancialGenome,
                       target_sites: List[TargetSite]) -> EditResult:
        """
        🎯 Edit parameters using trained RL agent
        
        Args:
            model_genome: Genome to edit
            target_sites: Target sites for editing
            
        Returns:
            Edit results with RL-optimized modifications
        """
        if not self.is_trained:
            raise ValueError("Agent must be trained before editing")

        logger.debug(f"RL editing {len(target_sites)} target sites")

        try:
            # Create environment for editing
            env = ParameterEditEnvironment(model_genome, target_sites, self.config)

            # Execute editing episode
            state = env.reset()
            edits_made = []
            total_reward = 0

            while True:
                # Get action from trained agent
                action = self.agent.get_action(state, training=False)

                # Execute action
                next_state, reward, done, info = env.step(action)

                total_reward += reward
                state = next_state

                if done:
                    break

            # Analyze results
            parameter_changes = {}
            successful_edits = []

            for edit in env.edit_history:
                param_path = edit['parameter_path']
                parameter_changes[param_path] = {
                    'old_value': edit['old_value'],
                    'new_value': edit['new_value'],
                    'change_magnitude': edit['magnitude'],
                    'reward_received': edit['reward']
                }
                successful_edits.append(param_path)

            # Calculate performance improvement
            fitness_improvement = info['best_fitness'] - env.initial_fitness

            edit_result = EditResult(
                success=len(successful_edits) > 0,
                target_parameters=successful_edits,
                edit_strategy="reinforcement_learning",
                parameter_changes=parameter_changes,
                fitness_improvement=fitness_improvement,
                performance_delta=fitness_improvement * 100,  # Convert to percentage
                timestamp=datetime.now(),
                metadata={
                    'algorithm': self.config.algorithm,
                    'total_reward': total_reward,
                    'edits_attempted': len(env.edit_history),
                    'final_stability': info['stability'],
                    'constraint_violations': info['constraint_violations'],
                    'episode_length': env.step_count
                }
            )

            logger.debug(f"RL editing complete: {len(successful_edits)} successful edits, "
                        f"fitness improvement: {fitness_improvement:.3f}")

            return edit_result

        except Exception as e:
            logger.error(f"RL parameter editing failed: {str(e)}")

            # Return failure result
            return EditResult(
                success=False,
                target_parameters=[],
                edit_strategy="reinforcement_learning",
                parameter_changes={},
                fitness_improvement=0.0,
                performance_delta=0.0,
                timestamp=datetime.now(),
                error_message=str(e)
            )

    def save_agent(self, filepath: str):
        """💾 Save trained RL agent"""
        if not self.is_trained:
            raise ValueError("No trained agent to save")

        save_dict = {
            'agent_state_dict': self.agent.network.state_dict(),
            'config': self.config.__dict__,
            'training_episodes': self.training_episodes,
            'training_rewards': self.training_rewards,
            'training_losses': self.training_losses
        }

        torch.save(save_dict, filepath)
        logger.info(f"RL agent saved to {filepath}")

    def load_agent(self, filepath: str):
        """📂 Load trained RL agent"""
        save_dict = torch.load(filepath, map_location='cpu')

        # Recreate config
        config_dict = save_dict['config']
        self.config = RLConfig(**config_dict)

        # Load training data
        self.training_episodes = save_dict['training_episodes']
        self.training_rewards = save_dict['training_rewards']
        self.training_losses = save_dict.get('training_losses', [])

        # Note: Agent will be recreated when first used
        self.is_trained = True

        logger.info(f"RL agent loaded from {filepath}")

    def get_training_statistics(self) -> Dict[str, Any]:
        """📊 Get training performance statistics"""
        if not self.training_rewards:
            return {'status': 'No training data available'}

        return {
            'total_episodes': len(self.training_rewards),
            'average_reward': np.mean(self.training_rewards),
            'best_reward': max(self.training_rewards),
            'worst_reward': min(self.training_rewards),
            'reward_std': np.std(self.training_rewards),
            'final_100_avg': np.mean(self.training_rewards[-100:]) if len(self.training_rewards) >= 100 else np.mean(self.training_rewards),
            'learning_curve_trend': np.polyfit(range(len(self.training_rewards)), self.training_rewards, 1)[0] if len(self.training_rewards) > 1 else 0,
            'algorithm_used': self.config.algorithm
        }
