"""
Based on the work in Taylor and Parberry, 2011 (https://ianparberry.com/techreports/LARC-2011-01.pdf)
"""
import random
from copy import deepcopy
from procoban_prototype import repeated_random_reverse_push, pushless_flood_fill, DIRECTIONS

RECURSE_IF_DEAD_END = False
TEMPLATES_IS_SET = False

TEMPLATES = [ # This set is hardcoded and taken from Taylor and Parberry
    ((-1, -1, -1, -1, -1),
     (-1,  0,  0,  0, -1),
     (-1,  0,  0,  0, -1),
     (-1,  0,  0,  0, -1),
     (-1, -1, -1, -1, -1)),
    
    ((-1, -1, -1, -1, -1),
     (-1,  1,  0,  0, -1),
     (-1,  0,  0,  0, -1),
     (-1,  0,  0,  0, -1),
     (-1, -1, -1, -1, -1)),
    
    ((-1, -1, -1,  0,  0),
     (-1,  1,  1,  0,  0),
     (-1,  0,  0,  0, -1),
     (-1,  0,  0,  0, -1),
     (-1, -1, -1, -1, -1)),
    
    ((-1, -1, -1, -1, -1),
     (-1,  1,  1,  1, -1),
     (-1,  0,  0,  0, -1),
     (-1,  0,  0,  0, -1),
     (-1, -1, -1, -1, -1)),
    
    ((-1, -1, -1, -1, -1),
     (-1,  1,  1,  1, -1),
     (-1,  1,  0,  0, -1),
     (-1,  1,  0,  0, -1),
     (-1, -1, -1, -1, -1)),
    
    ((-1, -1,  0, -1, -1),
     (-1,  1,  0,  0, -1),
     ( 0,  0,  0,  0, -1),
     (-1,  0,  0,  1, -1),
     (-1, -1, -1, -1, -1)),
    
    ((-1, -1, -1, -1, -1),
     (-1,  1,  0,  0, -1),
     ( 0,  0,  0,  0, -1),
     (-1,  1,  0,  0, -1),
     (-1, -1, -1, -1, -1)),
    
    ((-1, -1,  0, -1, -1),
     (-1,  1,  0,  0, -1),
     ( 0,  0,  0,  0, -1),
     (-1,  1,  0,  1, -1),
     (-1, -1,  0, -1, -1)),
    
    ((-1, -1,  0, -1, -1),
     (-1,  1,  0,  1, -1),
     ( 0,  0,  0,  0,  0),
     (-1,  1,  0,  1, -1),
     (-1, -1,  0, -1, -1)),
    
    ((-1, -1,  0, -1, -1),
     (-1,  1,  0,  1, -1),
     (-1,  1,  0,  0,  0), # TODO make center equal False. This tile is treated as a wall for connectivity tests but is a floor tile
     (-1,  1,  1,  1, -1),
     (-1, -1, -1, -1, -1)),
    
    ((-1, -1, -1, -1, -1),
     (-1,  1,  1,  1, -1),
     (-1,  0,  0,  0, -1),
     (-1,  1,  1,  1, -1),
     (-1, -1, -1, -1, -1)),
    
    ((-1, -1, -1, -1, -1),
     (-1,  0,  0,  0,  0),
     (-1,  0,  1,  0,  0),
     (-1,  0,  0,  0, -1),
     (-1, -1, -1, -1, -1)),
    
     #((-1, -1, -1, -1, -1),
     # (-1,  1,  1,  1, -1),
     # (-1,  1,  1,  1, -1),
     # (-1,  1,  1,  1, -1),
     # (-1, -1, -1, -1, -1)),
    
    ((-1, -1, -1, -1, -1),
     (-1,  1,  1,  1, -1),
     (-1,  1,  0,  0, -1),
     ( 0,  0,  0,  0, -1),
     ( 0,  0, -1, -1, -1)),
    
    ((-1,  0, -1,  0, -1),
     (-1,  0,  0,  0, -1),
     (-1,  1,  0,  1, -1),
     (-1,  0,  0,  0, -1),
     (-1,  0, -1,  0, -1)),
    
    ((-1, -1, -1, -1, -1),
     (-1,  1,  1,  1, -1),
     (-1,  1,  1,  1, -1),
     (-1,  0,  0,  0, -1),
     (-1,  0,  0,  0, -1)),
    
    ((-1, -1, -1, -1, -1),
     (-1,  1,  1,  1, -1),
     ( 0,  0,  1,  0,  0),
     (-1,  0,  0,  0, -1),
     (-1,  0,  0, -1, -1))]

flips = [tuple(reversed(t)) for t in TEMPLATES] # we only need to do vertical flips because we rotate next, so vertical and horizontal flips are equivalent
TEMPLATES.extend(flips)

def rotate_clockwise(matrix):
   return tuple(tuple(element) for element in zip(*reversed(matrix)))

def rotate_anticlockwise(matrix):
   return tuple(tuple(element) for element in reversed(tuple(zip(*(matrix)))))

rotations = []
for t in TEMPLATES:
    rotations.append(rotate_clockwise(t))
    rotations.append(rotate_anticlockwise(t))
    rotations.append(rotate_clockwise(rotate_clockwise(t)))
TEMPLATES.extend(rotations)

if TEMPLATES_IS_SET: TEMPLATES = set(TEMPLATES)

TEMPLATES_TUPLE = tuple(TEMPLATES)

def check_adjacencies_raw(raw_board, coords):
    ans = []
    height = len(raw_board)
    width = len(raw_board[0])
    for d in DIRECTIONS:
        if coords[0]+d[0] < 0 or coords[0]+d[0] >= width or coords[1]+d[1] < 0 or coords[1]+d[1] >= height:
            ans.append(1)
        else:
            ans.append(min(1, max(0, raw_board[coords[1]+d[1]][coords[0]+d[0]])))
    return ans

def check_adjacencies(board, coords):
    """
    Returns an iterable of coordinates, each corresponding to one direction
    """
    return check_adjacencies_raw(board.raw_tiles, coords)

def random_gen_without_goals(board_object): # TODO check continuity
    assert board_object.width % 3 == 2
    assert board_object.height % 3 == 2
    tile_width = board_object.width // 3
    tile_height = board_object.height // 3
    board = [[-1 for i in range(board_object.width)] for j in range(board_object.height)]
    
    for row in range(tile_height):
        for col in range(tile_width):
            template_options = list(TEMPLATES_TUPLE)
            while len(template_options) != 0: # this mess of for-else stuff is not elegant
                template = template_options.pop(random.choice(range(len(template_options))))
                # print(f"Attempting to fill template in row {row}, column {col}")
                tentative_board = deepcopy(board)
                for row_offset in range(5):
                    for col_offset in range(5):
                        board_value = board[row*3+row_offset][col*3+col_offset]
                        template_value = template[row_offset][col_offset]
                        if board_value != -1 and template_value != -1 and board_value != template_value:
                            # print(f"Tile {col*3+col_offset}, {row*3+row_offset} failed!")
                            # print(f"Expected value: {template_value}, Actual value: {board_value}")
                            break # This breaks both loops because of the else-continue-break clause
                        else:
                            tentative_board[row*3+row_offset][col*3+col_offset] = template_value
                    else:
                        continue
                    break
                else:
                    board = tentative_board
                    break
            else:
                raise Exception("Failed, shoud recurse")
    
    board = [[1 if i == -1 else i for i in row] for row in board]
    board_object.set_board(board)
    
    board_perfect = False
    available_spaces = None
    while not board_perfect:
        board_perfect = True
        for row_idx, row in enumerate(board_object.raw_tiles):
            for col_idx, space in enumerate(row):
                if space != 1:
                    if available_spaces == None:
                        available_spaces = pushless_flood_fill(board_object, (col_idx, row_idx))
                    if (col_idx, row_idx) not in available_spaces: # Board not continuous
                        print(f"Failed to connect to tile ({col_idx}, {row_idx}). Retrying...")
                        return random_gen_without_goals(board_object) # TODO this is not the right way to recurse
                    if sum(check_adjacencies(board_object, (col_idx, row_idx))) >= 3: # Dead-end tile
                        if RECURSE_IF_DEAD_END:
                            print(f"Tile ({col_idx}, {row_idx}) is a dead end, and apparently that's boring. Retrying...")
                            return random_gen_without_goals(board_object) # TODO this is not the right way to recurse
                        else:
                            print(f"Tile ({col_idx}, {row_idx}) is a dead end. Fixing...")
                            board_perfect = False
                            board_object.raw_tiles[row_idx][col_idx] = 1

def randomly_place_goals_and_player(board_object, num_goals):
    options = []
    for row in range(board_object.height):
        for col in range(board_object.width):
            if board_object.get_tile((col, row)) == 0:
                options.append((col, row))
    goals_plus_player = random.sample(options, num_goals+1)
    for goal in goals_plus_player[:-1]:
        board_object.raw_tiles[goal[1]][goal[0]] = 2
    board_object.set_player(goals_plus_player[-1])

def gen_puzzle(board, n_boxes, n_pushes):
    random_gen_without_goals(board)
    randomly_place_goals_and_player(board, n_boxes)
    board.set_boxes_solved()
    repeated_random_reverse_push(board, n_pushes)