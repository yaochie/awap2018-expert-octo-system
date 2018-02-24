from base_player import BasePlayer
import networkx as nx
import operator
import random
import copy
import inspect

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
        self.long_term_attack_targets = set() 
        self.long_term_protect_targets = set()
        self.long_term_unit_counts = dict() #Contains (prev_enemy_count, curr_enemy_count)
        self.long_term_movements = dict() # Contains list of nodes to move to

        return

    """
    Called at the start of every placement phase and movement phase.
    """
    def init_turn(self, board, nodes, max_units):
        super().init_turn(board, nodes, max_units)       #Initializes turn-level state variables
        self.list_graph = sorted(list(self.board.nodes(data=True)))
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
        ids = set()
        frontier = []
        for node in self.nodes:
            for neighbor in self.board[node]:
                neighbor_id = self.board.nodes[neighbor]['owner']
                if neighbor_id != self.player_num and neighbor_id not in ids:
                    ids.add(neighbor_id)
                    frontier.append(neighbor)
        return frontier

    """
    Determine number of enemy units connected to this node
    min_val == True: Return minimum number of units needed to take over an adjacent node
    min_val == False: Return sum of all enemies adject to this node
    """
    def get_enemy_units(self, node, min_val=False):
        neighbors = self.board.neighbors(node)
        curr_enemy_count = 0
        min_count = 9999999
        for n in neighbors:
            n_node = self.board.nodes[n]
            if (n_node['owner'] != self.player_num):
                min_count = min(min_count, n_node['old_units'])
                curr_enemy_count += n_node['old_units']
        if (min_val):
            if (min_count == 9999999):
                return 0
            return min_count
        return curr_enemy_count



    """
    Called during the placement phase to request player moves
    """
    def player_place_units(self):
        """
        Insert player logic here to determine where to place your units
        """

        for target in self.long_term_unit_counts:
            curr_enemy_count = self.get_enemy_units(target)
            prev_enemy_count = self.long_term_unit_counts[target][0]
            self.long_term_unit_counts[target] = (prev_enemy_count, curr_enemy_count)

        for target in copy.copy(self.long_term_protect_targets):
            if (self.board.nodes[target]['owner'] != self.player_num):
                continue # Oh no, someone took the node before we could protect it 

            if (target in self.long_term_unit_counts):
                count = self.long_term_unit_counts[target]
                self.verify_and_place_unit(target, count[1] - count[0])
                self.long_term_unit_counts[target] = (self.long_term_unit_counts[target][1], self.get_enemy_units(target))
            else:
                self.long_term_unit_counts[target] = (0, self.get_enemy_units(target))
            if (self.long_term_unit_counts[target][1] == 0):
                self.long_term_unit_counts.pop(target, None)
                self.long_term_protect_targets.remove(target)

        for target in copy.copy(self.long_term_attack_targets):
            if (self.board.nodes[target]['owner'] != self.player_num):
                continue # Oh no, someone took the node before we could attack from it

            if (target in self.long_term_unit_counts):
                self.long_term_unit_counts[target] = (self.long_term_unit_counts[target][1], self.get_enemy_units(target, True))
            else:
                self.long_term_unit_counts[target] = (0, self.get_enemy_units(target, True))

            count = self.long_term_unit_counts[target]
            new_units = min(count[1] - self.list_graph[target][1]['old_units'] + 2, self.max_units)
            self.verify_and_place_unit(target, new_units)
            if (self.long_term_unit_counts[target][1] == 0):
                self.long_term_unit_counts.pop(target, None)
                self.long_term_attack_targets.remove(target)

        for i in range(self.max_units, 0, -1):
            node = random.choice(list(self.nodes))
            self.verify_and_place_unit(node, 1)


        return self.dict_moves #Returns moves built up over the phase. Do not modify!

    

    def execute_single_turn_actions(self):
        for nodes in self.nodes:
            neighbors = self.board.neighbors(nodes)
            for n in neighbors:
                self_units =self.board.nodes[nodes]['old_units']
                n_node = self.board.nodes[n]
                n_units = n_node['old_units']
                n_owner = n_node['owner']

                if (n_owner != self.player_num):
                    # For now, prioritize attacking
                    if ((n_units + 1) < self_units):
                        self.verify_and_move_unit(nodes, n, n_units + 1)
                    else:
                        self.long_term_attack_targets.add(nodes)    #Maybe I'll get around to it

                    # Protect nodes at risk                
                    if ((n_owner != None) and (n_owner != self.player_num)):                    
                        if (n_units > self_units/2):
                            self.long_term_protect_targets.add(nodes)
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
