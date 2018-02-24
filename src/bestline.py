from base_player import BasePlayer
import networkx as nx
import operator
import random
import copy
import inspect
from enum import Enum
from math import ceil

class PlacementPolicies(Enum):
    SINGLE = 1          # place only on a single node
    EVEN = 2            # place evenly across all minimum nodes

class MovementPolicies(Enum):
    AGGRESSIVE = 1      # attack all that can be won

class Player(BasePlayer):

    """
    You will implement this class for the competition.
    You can add any additional variables / methods in this file. 
    Do not modify the class name or the base class and do not modify the lines marked below.
    """

    def __init__(self, p_id):
        super().__init__(p_id)  #Initializes the super class. Do not modify!

        """
        Insert player-specific initialization code here
        """

        self.place_policy = PlacementPolicies.SINGLE
        self.move_policy = MovementPolicies.AGGRESSIVE

        return

    """
    Called at the start of every placement phase and movement phase.
    """
    def init_turn(self, board, nodes, max_units):
        super().init_turn(board, nodes, max_units)       #Initializes turn-level state variables
        self.list_graph = sorted(list(self.board.nodes(data=True)))

        self.frontier = self.get_frontier()
        self.owned_frontier = self.get_outer()
        self.dist_from_frontier = self.distance_from_frontier()
        """
        Insert any player-specific turn initialization code here
        """
        return

    
    """
    Looks at the call stack to see who the caller is - can be useful debugging error messages
    """
    def find_caller(self):
        frame,filename,line_number,function_name,lines,index = inspect.stack()[2]
        # (filename, line_number, function_name, lines, index) = inspect.getframeinfo(previous_frame)
        print(function_name, ':', line_number)
        return

    """
    Run some basic checks and then call the parent function to add the move
    """
    def verify_and_place_unit(self, node, amount):
        if (self.list_graph[node] is None):
            raise Exception("Error: Node does not exist in list_graph")
            return

        if (self.list_graph[node][1]['owner'] != self.player_num):
            raise Exception("Error: You do not own this node you are placing into")
            self.find_caller()
            return

        if (amount <= 0):
            raise Exception("you are not placing any nodes...")
            return

        if (amount > self.max_units):
            raise Exception("Error: You are trying to place too many units")
            return

        super().place_unit(node, amount)
        return

    """
    Run some basic checks and then call the parent function to add the move
    """
    def verify_and_move_unit(self, start, end, amount):
        if (amount <= 0):
            raise Exception("you are not placing any nodes...")
            return

        start_node = self.list_graph[start]
        end_node = self.list_graph[end]

        if ((start is None) or (end is None)):
            raise Exception("Error: Node does not exist in list_graph")
            return

        if (start_node[1]['owner'] != self.player_num):
            raise Exception("Error: You do not own this node you are starting from")
            return

        if (start == end):
            raise Exception("start == end")
            return

        if (start_node[1]['old_units'] <= amount):
            raise Exception("You are requesting", amount, "units, but you only have ", start_node[1]['old_units'], 'units')
            self.find_caller()
            return

        super().move_unit(start, end, amount)
        return

    def get_frontier(self):
        frontier = []
        for node in self.nodes:
            for neighbor in self.board[node]:
                neighbor_id = self.board.nodes[neighbor]['owner']
                if neighbor_id != self.player_num and neighbor not in frontier:
                    frontier.append(neighbor)
        return frontier

    def get_outer(self):
        outer = []
        for node in self.nodes:
            for neighbor in self.board[node]:
                if self.board.nodes[neighbor]['owner'] != self.player_num:
                    outer.append(node)
                    break
        return outer

    """
    Called during the placement phase to request player moves
    """
    def player_place_units(self):
        """
        Insert player logic here to determine where to place your units
        """

        """
        Given nodes in the frontier, allocate to node with the fewest adjacent nodes
        that belong to others
        (most defensible)
        """

        frontier_with_units = [(n, self.board.nodes[n]['old_units']) for n in self.frontier]
        frontier_with_units = sorted(frontier_with_units, key=lambda node: node[1])

        #print('front', frontier_with_units)

        assignments = []
        for node, units in frontier_with_units:
            for neighbor in self.board.neighbors(node):
                n = self.board.nodes[neighbor]
                if n['owner'] == self.player_num:
                    assignments.append([neighbor, node, units + 1])

        remaining_units = {k: self.board.nodes[k]['old_units'] for k in self.nodes}

        #print('assn', assignments)
        
        units_to_place = self.max_units
        units_to_be_placed = {}
        self.jobs = []
        while len(assignments) > 0:
            assignments = sorted(
                    assignments,
                    key=lambda x: remaining_units[x[0]] - x[2]
            )

            remaining_units[assignments[0][0]] -= (assignments[0][2] + 1)
            if remaining_units[assignments[0][0]] < 1:
                if units_to_place < 1 - remaining_units[assignments[0][0]]:
                        break
                units_to_place -= (1 - remaining_units[assignments[0][0]])
                if assignments[0][0] not in units_to_be_placed:
                    units_to_be_placed[assignments[0][0]] = 0
                units_to_be_placed[assignments[0][0]] += (1 - remaining_units[assignments[0][0]])
                remaining_units[assignments[0][0]] = 1

            self.jobs.append(assignments[0])
            assignments.pop(0)

        print('jobs', self.jobs)
            
        if units_to_place > 0:
            if len(self.jobs) > 0:
                self.jobs[0][2] += units_to_place
                if self.jobs[0][0] not in units_to_be_placed:
                    units_to_be_placed[self.jobs[0][0]] = 0
                units_to_be_placed[self.jobs[0][0]] += units_to_place
            else:
                if assignments[0][0] not in units_to_be_placed:
                    units_to_be_placed[assignments[0][0]] = 0
                units_to_be_placed[assignments[0][0]] += units_to_place
                
        for node in units_to_be_placed:
            self.verify_and_place_unit(node, units_to_be_placed[node])

        return self.dict_moves #Returns moves built up over the phase. Do not modify!

    def distance_from_frontier(self):
        frontier = self.get_frontier()
        distances = {}
        all_nodes = [n for n in self.nodes] + frontier
        for node in all_nodes:
            queue = []
            queue.append((node, 0))
            visited = set()
            while len(queue) > 0:
                cur, dist = queue[0]
                queue = queue[1:]
                if cur in visited:
                    continue
                visited.add(cur)
                if cur in frontier:
                    distances[node] = dist
                    break
                for nxt in self.board[cur]:
                    queue.append((nxt, dist + 1))
        return distances
    
    def execute_single_turn_actions(self):
        
        #move to frontier
        for nodes in self.nodes:
            if nodes in self.owned_frontier:
                continue #already is on outer..

            self_units = self.board.nodes[nodes]['old_units']            
            if self_units <= 1:
                continue #no point in moving
            
            neighbors = self.board.neighbors(nodes)
            neighbors = filter(lambda x: self.board.nodes[x]['owner'] == self.player_num, neighbors)

            best_neighbor = min(neighbors, key = lambda x: self.dist_from_frontier[x])

            self.verify_and_move_unit(nodes, best_neighbor, self_units-1)

        #attacking
        for node, neighbor, units in self.jobs:
            self.verify_and_move_unit(node, neighbor, units)
        # for nodes in self.nodes:
        #     self_units = self.board.nodes[nodes]['old_units']
        #
        #     if self_units <= 1:
        #         continue
        #
        #     can_attack = []
        #     
        #     neighbors = self.board.neighbors(nodes)
        #     for n in neighbors:
        #         
        #         n_node = self.board.nodes[n]
        #         n_units = n_node['old_units']
        #         n_owner = n_node['owner']
        #
        #         if (n_owner != self.player_num) and (self_units > n_units + 1):
        #             can_attack.append((n, n_units +1))
        #
        #     #do_attack = {}
        #     remaining_units = self_units
        #     can_attack = sorted(can_attack, key = lambda x: x[1])
        #     for i, (n, units) in enumerate(can_attack):
        #         if remaining_units - units < 1:
        #             break
        #
        #         used_units = units
        #         if i == len(can_attack) - 1 or \
        #                 can_attack[i][1] + can_attack[i + 1][1] >= remaining_units:
        #             used_units = remaining_units - 1
        #         self.verify_and_move_unit(nodes, n, used_units)
        #         remaining_units -= used_units
        return
    
    """
    Called during the move phase to request player moves
    """
    def player_move_units(self):
        """
        Insert player logic here to determine where to move your units
        """

        self.execute_single_turn_actions()
        return self.dict_moves
