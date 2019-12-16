from jass.base.const import *
from jass.base.player_round import PlayerRound
from jass.base.round_factory import get_round_from_player_round
from jass.player.fabian_mcts.sampler import Sampler
from jass.player.fabian_mcts.node import Node
from jass.player.fabian_mcts.UCB import UCB
from jass.player.random_player_schieber import RandomPlayerSchieber
import time


class MCTS:
    @staticmethod
    def monte_carlo_tree_search(rnd: PlayerRound, run_time_seconds=1000) -> (Node, int):
        end_time = time.time() + run_time_seconds

        sampled_round = Sampler.sample(rnd)
        root_node = Node()
        root_node.player_nr = rnd.player
        root_node.round = sampled_round

        simulated_rounds = 0
        while time.time() < end_time:
            promising_node = MCTS._select_promising_node(root_node)

            if len(promising_node.childs) == 0:
                MCTS._expand_node(promising_node, sampled_round)

            if len(promising_node.childs) > 0:
                node_to_explore = promising_node.get_random_child()
            else:
                node_to_explore = promising_node

            win = MCTS._simulate_round(node_to_explore)
            MCTS._back_propagation(node_to_explore, sampled_round.player, win)
            simulated_rounds += 1
        #winner = root_node.get_child_with_max_visit_count()
        #print(f"{simulated_rounds} rounds simulated in {run_time_seconds} seconds")
        #print(f"winner: {winner.card} with visit count {winner.visit_count} ({round(winner.visit_count/simulated_rounds, 3)}), valid cards: {np.flatnonzero(sampled_round.get_valid_cards())}")
        return root_node

    @staticmethod
    def _select_promising_node(root_node: Node) -> Node:
        node = root_node
        while len(node.childs) != 0:
            ucb = UCB()
            node = ucb.find_best_node_ucb(node)
        return node

    @staticmethod
    def _expand_node(node: Node, round: PlayerRound):
        valid_cards = np.flatnonzero(round.get_valid_cards())
        for card in valid_cards:
            new_node = Node()
            new_node.parent = node
            new_node.round = round
            new_node.player_nr = node.player_nr
            new_node.card = card
            node.add_child(new_node)

    @staticmethod
    def _simulate_round(node: Node) -> bool:
        rnd = get_round_from_player_round(node.round, node.round.hands)
        player = rnd.player
        rnd.action_play_card(node.card)
        cards = rnd.nr_played_cards
        random_player = RandomPlayerSchieber()
        while cards < 36:
            player_rnd = PlayerRound()
            player_rnd.set_from_round(rnd)
            card_action = random_player.play_card(player_rnd)
            rnd.action_play_card(card_action)
            cards += 1

        max_points = rnd.points_team_0 + rnd.points_team_1
        my_points = rnd.get_points_for_player(player)
        enemy_points = max_points - my_points

        return my_points > enemy_points

    @staticmethod
    def _back_propagation(node: Node, player_nr: int, win: bool):
        temp_node = node
        while temp_node:
            temp_node.increment_visit()
            if temp_node.player_nr == player_nr:
                if win:
                    temp_node.win_count += 1
                else:
                    temp_node.lose_count += 1
            temp_node = temp_node.parent
