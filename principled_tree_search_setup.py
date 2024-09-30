import random
from copy import deepcopy
from procoban_prototype import DIRECTIONS
from tile_based_boardgen import randomly_place_goals_and_player, random_gen_without_goals

def pushless_flood_fill_separate_boxes(board, coords, boxes):
    tiles_occupied = set([coords])
    failed_tiles = set()
    untested_tiles_occupied = [coords]
    while len(untested_tiles_occupied) != 0:
        testing_tile = untested_tiles_occupied.pop(0)
        for delta in DIRECTIONS:
            searching_tile = (testing_tile[0]+delta[0], testing_tile[1]+delta[1])
            if searching_tile in failed_tiles or searching_tile in tiles_occupied:
                continue
            elif not board.check_tile_legality(searching_tile):
                continue
            elif searching_tile in boxes:
                continue
            else:
                tiles_occupied.add(searching_tile)
                untested_tiles_occupied.append(searching_tile)
    return tiles_occupied

def get_legal_reverse_push_lines_separate_boxes(board, coords, boxes):
    viable_spaces = pushless_flood_fill_separate_boxes(board, coords, boxes)
    viable_pushes = set() # A push is a 2-tuple of 2-tuples. The first 2-tuple is the box start coords. The second 2-tuple is the box end coords.
    for box in boxes:
        for delta in DIRECTIONS:
            steps = 1
            while (box[0]+steps*delta[0], box[1]+steps*delta[1]) in viable_spaces and board.check_tile_legality((box[0]+(steps+1)*delta[0], box[1]+(steps+1)*delta[1])) and (box[0]+(steps+1)*delta[0], box[1]+(steps+1)*delta[1]) not in boxes:
                viable_pushes.add((box, (box[0]+steps*delta[0], box[1]+steps*delta[1])))
                steps += 1
    return viable_pushes

class SetupBoardState:
    
    all_states = {}
    
    def get_all_states(self):
        return SetupBoardState.all_states[self.board]
    
    def __init__(self, board, box_coords=None, player_coords=None, distance=0, parent=None):
        self.board = board # A board object. Note that we ONLY use the map, not the box or player coords
        self.distance = distance # The number of reverse push lines necessary to get to this state
        if self.board not in SetupBoardState.all_states.keys():
            SetupBoardState.all_states[self.board] = {}
        if box_coords == None:
            self.box_coords = frozenset(board.boxes_coords)
        else:
            self.box_coords = frozenset(box_coords) # A set of 2-tuples
        if player_coords == None:
            self.player_coords = frozenset(pushless_flood_fill_separate_boxes(board, board.player_coords, self.box_coords))
        elif isinstance(player_coords, frozenset):
            self.player_coords = player_coords
        else:
            self.player_coords = frozenset(pushless_flood_fill_separate_boxes(board, player_coords, self.box_coords))
        self.get_all_states()[(self.box_coords, self.player_coords)] = self
        self.child_states = set()
        self.parent_states = set()
        if parent != None: self.parent_states.add(parent)
    
    def parent_found(self, parent, new_dist):
        self.parent_states.add(parent)
        if new_dist < self.distance: self.distance = new_dist
    
    def __hash__(self):
        return hash((self.box_coords, self.player_coords))
    
    def __eq__(self, other):
        if not isinstance(other, self.__class__):
            return False
        return self.board == other.board and self.box_coords == other.box_coords and self.player_coords == other.player_coords
    
    def __ne__(self, other): return not self.__eq__(other)
    
    def get_child_states(self):
        """
        Returns a 2-tuple whose first element is all child states and whose
        second element is all child states not seen before
        """
        push_options = get_legal_reverse_push_lines_separate_boxes(self.board, next(iter(self.player_coords)), self.box_coords)
        new_states = set()
        for choice in push_options:
            box_coords = set(self.box_coords)
            box_coords.remove(choice[0])
            box_coords.add(choice[1])
            box_coords = frozenset(box_coords)
            player_coords = (min(1, max(-1, choice[1][0]-choice[0][0]))+choice[1][0], min(1, max(-1, choice[1][1]-choice[0][1]))+choice[1][1])
            player_coords = frozenset(pushless_flood_fill_separate_boxes(self.board, player_coords, box_coords))
            if (box_coords, player_coords) in self.get_all_states():
                found_state = self.get_all_states()[(box_coords, player_coords)]
                found_state.parent_found(self, self.distance+1)
                self.child_states.add(found_state)
            else:
                discovered_state = SetupBoardState(self.board, box_coords, player_coords, self.distance+1, parent=self)
                self.child_states.add(discovered_state)
                new_states.add(discovered_state)
        return (set(self.child_states), new_states)
    
    def get_farthest_known_state(self):
        assert self.distance == 0 # TODO generalize this
        return max(self.get_all_states().values(), key=lambda x: x.distance)

def find_farthest_state(board):
    initial_state = SetupBoardState(board)
    states_to_check = [initial_state]
    states_checked = 0
    print("Generating...")
    while len(states_to_check) != 0:
        # print(f"Now checking state {states_checked}")
        current_state = states_to_check.pop(0)
        states_to_check.extend(current_state.get_child_states()[1])
        states_checked += 1
    best_state = initial_state.get_farthest_known_state()
    print(f"This puzzle takes {best_state.distance} moves to solve (a move consists of pushing one box any number of tiles in a straight line). Good luck!")
    return (best_state.box_coords, best_state.player_coords)

def gen_puzzle_optimal(board, n_boxes, openness_bias=lambda x: 0.0):
    random_gen_without_goals(board, openness_bias)
    randomly_place_goals_and_player(board, n_boxes)
    board.set_boxes_solved()
    start_state = find_farthest_state(board)
    board.set_boxes(start_state[0])
    board.set_player(random.choice(tuple(start_state[1])))