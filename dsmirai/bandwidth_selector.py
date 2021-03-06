from dsmirai.global_dqn_agent import GlobalDQNAgent as dqn
from dsmirai.ddpg_agent import DDPGAgent as ddpg
from dsmirai.utils_ddpg import OUNoise
import numpy as np
from mirai_project import settings


def get_smart_bw_value(state, rl_type='dqn'):
    """
    Used to get bandwidth actions values
    :param state:
    :param rl_type:
    :return: Selected action
    """
    action_size = 10
    epsilon = 0.0001
    state_size = 2
    print('State_size: {}'.format(state_size))
    print('Action_size: {}'.format(action_size))
    print('The received state is: {}'.format(state))
    if rl_type == 'dqn':
        agent = dqn(state_size, action_size, epsilon=epsilon)
        # Loading the Model's weights generated by the selected model
        agent.load(settings.LINK_MODEL, rl_type)
        state = np.reshape(state, [1, state_size])
        action = agent.get_action(state)
        action = action * 100
    else:
        gamma = 0.99
        tau = 1e-2
        buffer_maxlen = 100000
        critic_lr = 1e-3
        actor_lr = 1e-3
        action_space = 1
        agent = ddpg(state_size, action_space, gamma, tau, buffer_maxlen, critic_lr, actor_lr, settings.LINK_MODEL)
        # Used to generate size
        noise = OUNoise(action_space)
        # Loading the Model's weights generated by the selected model
        agent.load_models()
        state = np.reshape(state, [1, state_size])
        action = agent.get_action(state)
        action = noise.get_action(action, 1000)
    return action
