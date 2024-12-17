# Run `pip install -r requirements.txt` in your conda environment before running this code

import numpy as np
import gymnasium as gym
from frozen_lake_utils import plot_frozenlake_policy_iteration_results

class PolicyIteration:
    def __init__(self, render=False):
        self.env = gym.make('FrozenLake-v1', desc=None, map_name="4x4", is_slippery=True,
                            render_mode='human' if render else None).unwrapped
        self.num_actions = self.env.action_space.n
        self.num_states = self.env.observation_space.n

        # self.policy[s, a] = probability of taking action a in state s
        self.policy = np.ones((self.num_states, self.num_actions)) / self.num_actions  # uniform policy

        # Extract MDP dynamics from gym environment

        # self.P[s', s, a] = P(s' | s, a)
        self.P = np.zeros((self.num_states, self.num_states, self.num_actions))

        # self.r[s, a] = expected immediate reward in state s when taking action a
        self.r = np.zeros((self.num_states, self.num_actions))
        for state in range(self.num_states):
            for action in range(self.num_actions):
                for prob, next_state, reward, done in self.env.P[state][action]:
                    self.r[state, action] += prob * reward
                    self.P[next_state, state, action] += prob


    def policy_evaluation(self, gamma=1., epsilon=1e-8):
        """
        Run iterative policy evaluation for the current policy `self.policy`
        and return the corresponding state-value function `v`.
        :param gamma: discount factor
        :param epsilon: stop evaluation if delta < epsilon
        :return:
        """
        # TODO: Compute P_pi[s', s] = P(s' | s) when acting according to self.policy
        r_pi = np.einsum('sa,sa->s', self.r, self.policy)  
        P_pi = np.einsum('tsa,sa->ts', self.P, self.policy)

        v = np.zeros(self.num_states) 

        while True:
            delta = 0 
            v_old = v.copy() 

            v = r_pi + gamma * np.dot(P_pi.T, v_old)

            delta = np.max(np.abs(v - v_old))

            if delta < epsilon:
                break

        return v


    def compute_Q_from_v(self, v, gamma=1.):
        """
        Compute the Q values (i.e., a 2D-array) from
        the state-value function `v` and return Q.
        :param v: state-value function
        :param gamma: discount factor
        :return: Q values where Q[s, a] corresponds to the Q-value of taking action a in state s
        """

        # TODO: convert v function to Q function
        # Hint: You'll need the MDP dynamics stored in self.P and self.r
        Q = self.r + gamma * np.einsum('tsa,t->sa', self.P, v)
        assert Q.shape == (self.num_states, self.num_actions)
        return Q


    def policy_improvement(self, gamma=1.):
        """
        Iteratively evaluate a policy and improve it (by acting greedily w.r.t. q) until an optimal policy is found.
        We always start with a uniform policy.
        :param gamma: discount factor
        :return: optimal policy, optimal v values, optimal Q values
        """

        self.policy = np.ones((self.num_states, self.num_actions)) / self.num_actions  # uniform policy

        while True:
            policy_old = self.policy.copy()
            v = self.policy_evaluation(gamma)
            Q = self.compute_Q_from_v(v, gamma)

            # TODO: Improve policy (i.e., create a new one) by acting greedily w.r.t. Q
            self.policy = np.zeros_like(self.policy)
            self.policy[np.arange(self.num_states), np.argmax(Q, axis=1)] = 1.0

            if np.array_equal(policy_old, self.policy):
                break

        return self.policy, v, Q


    def run_episode(self, max_episode_length=1000):
        """
        Run an episode with the current policy `self.policy`
        and return the sum of rewards.
        We stop the episode if we reach a terminal state or
        if the episode length exceeds `max_episode_length`.
        :param max_episode_length: maximum episode length
        :return: sum of rewards of the episode
        """

        episode_reward = 0
        state, _ = self.env.reset()
        # sample action out of policy
        action = np.random.choice(self.num_actions, p=self.policy[state])

        for t in range(max_episode_length):
            next_state, reward, done, _, _ = self.env.step(action)
            episode_reward += reward
            next_action = np.random.choice(self.num_actions, p=self.policy[next_state])
            state, action = next_state, next_action
            if done:
                break

        return episode_reward


    def test_policy(self, num_episodes):
        """
        Run `num_episodes` episodes with the current policy `self.policy`.
        :param num_episodes: number of episodes to run
        :return: list of rewards of the episodes
        """

        rewards = []
        for _ in range(num_episodes):
            rewards.append(self.run_episode())

        return rewards


if __name__ == '__main__':
    # If you want to see the agent in action, set render=True
    policy_iteration = PolicyIteration(render=False)
    rewards = []
    episodes = [10, 100, 1000, 10000]
    for e in episodes:
        pi_star, v_star, q_star = policy_iteration.policy_improvement(gamma=1.0)
        test_rewards = policy_iteration.test_policy(num_episodes=e)
        rewards.append(test_rewards)
        plot_frozenlake_policy_iteration_results(policy_iteration, 1.0, test_rewards,
                                                 v_star, q_star, savefig=True)

    for e, r in zip(episodes, rewards):
        print(f'Num Episodes: {e}, Mean Reward: {np.mean(r)}')