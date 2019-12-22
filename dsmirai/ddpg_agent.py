import torch
import torch.optim as optim
import torch.nn.functional as F

from dsmirai.models import Critic, Actor
from dsmirai.utils_ddpg import ReplayMemory


class DDPGAgent:

    def __init__(self, obs_dim, action_dim, gamma, tau, buffer_maxlen, critic_learning_rate, actor_learning_rate, chkpt_dir):
        self.device = torch.device("cuda" if torch.cuda.is_available() else "cpu")

        self.obs_dim = obs_dim
        self.action_dim = action_dim

        # hyperparameters
        self.gamma = gamma
        self.tau = tau

        # initialize actor and critic networks
        self.critic = Critic(self.obs_dim, self.action_dim, name='critic', chkpt_dir=chkpt_dir).to(self.device)
        self.critic_target = Critic(self.obs_dim, self.action_dim, name='critic_target', chkpt_dir=chkpt_dir).to(self.device)

        self.actor = Actor(self.obs_dim, self.action_dim, name='actor', chkpt_dir=chkpt_dir).to(self.device)
        self.actor_target = Actor(self.obs_dim, self.action_dim, name='actor_target', chkpt_dir=chkpt_dir).to(self.device)

        # Copy critic target parameters
        for target_param, param in zip(self.critic_target.parameters(), self.critic.parameters()):
            target_param.data.copy_(param.data)
        for target_param, param in zip(self.actor_target.parameters(), self.actor.parameters()):
            target_param.data.copy_(param.data)
        # optimizers
        self.critic_optimizer = optim.Adam(self.critic.parameters(), lr=critic_learning_rate)
        self.actor_optimizer = optim.Adam(self.actor.parameters(), lr=actor_learning_rate)

        self.replay_buffer = ReplayMemory(buffer_maxlen)

    def get_action(self, obs):
        """
        Used to select actions
        :param state:
        :param epsilon:
        :return: action
        """
        self.actor.eval()
        state = torch.FloatTensor(obs).unsqueeze(0).to(self.device)
        action = self.actor.forward(state)
        # TODO: added [0].item() to return a python native variable
        action = action.squeeze(0).cpu().detach().numpy()
        self.actor.train()
        return action

    def update(self, batch_size):
        """
        Used for learning useful policy
        :return:
        """
        states, actions, rewards, next_states, _ = self.replay_buffer.sample(batch_size)
        state_batch = torch.FloatTensor(states).to(self.device)
        action_batch = torch.FloatTensor(actions).to(self.device)
        reward_batch = torch.FloatTensor(rewards).to(self.device)
        next_state_batch = torch.FloatTensor(next_states).to(self.device)

        self.actor_target.eval()
        self.critic_target.eval()
        self.critic.eval()

        target_actions = self.actor_target.forward(next_state_batch)
        critic_value_ = self.critic_target.forward(next_state_batch, target_actions.detach())
        critic_value = self.critic.forward(state_batch, action_batch)
        target_q = reward_batch + self.gamma * critic_value_

        # update critic
        self.critic.train()
        self.critic.optimizer.zero_grad()
        q_loss = F.mse_loss(critic_value, target_q.detach())

        q_loss.backward()
        self.critic.optimizer.step()

        # update actor
        self.critic.eval()
        self.actor.optimizer.zero_grad()

        mu = self.actor.forward(state_batch)
        self.actor.train()
        actor_loss = -self.critic.forward(state_batch, mu)
        actor_loss = torch.mean(actor_loss)
        actor_loss.backward()
        self.actor.optimizer.step()

        self.update_network_parameters()

    def update_network_parameters(self, tau=None):
        """
        Used to update target networks
        :return:
        """
        if tau is None:
            tau = self.tau

        actor_params = self.actor.named_parameters()
        critic_params = self.critic.named_parameters()
        target_actor_params = self.actor_target.named_parameters()
        target_critic_params = self.critic_target.named_parameters()

        critic_state_dict = dict(critic_params)
        actor_state_dict = dict(actor_params)
        target_critic_dict = dict(target_critic_params)
        target_actor_dict = dict(target_actor_params)

        for name in critic_state_dict:
            critic_state_dict[name] = tau*critic_state_dict[name].clone() + \
                                      (1-tau)*target_critic_dict[name].clone()

        self.critic_target.load_state_dict(critic_state_dict)

        for name in actor_state_dict:
            actor_state_dict[name] = tau*actor_state_dict[name].clone() + \
                                     (1-tau)*target_actor_dict[name].clone()
        self.actor_target.load_state_dict(actor_state_dict)

    def save_models(self):
        """
        Used to save models
        :return:
        """
        self.actor.save_checkpoint()
        self.actor_target.save_checkpoint()
        self.critic.save_checkpoint()
        self.critic_target.save_checkpoint()

    def load_models(self):
        """
        Used to load models
        :return:
        """
        self.actor.load_checkpoint()
        self.actor_target.load_checkpoint()
        self.critic.load_checkpoint()
        self.critic_target.load_checkpoint()
