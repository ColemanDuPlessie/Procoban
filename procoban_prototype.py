import random
from tkinter import Tk, Canvas
from time import sleep

canvas_padding = 10

tile_size = 50
box_tile_padding = 3
player_size = 40
target_size = 30
target_thickness = 5

floor_color = "#e0c890"
wall_color = "#206000"
box_color = "#603030"
target_color = "#404090"
player_color = "#a04040"

DIRECTIONS = ((0, 1), (1, 0), (0, -1), (-1, 0))

class Board:
    
    has_won = False
    
    def __init__(self, width, height):
        self.width = width
        self.height = height
        
        self.raw_tiles = [[0 for i in range(width)] for j in range(height)] # 0 = empty, 1 = wall, 2 = target
        self.player_coords = (0, 0) # coords are x, y, meaning that we need to go tiles[coords[1]][coords[0]] to access the right tile
        self.boxes_coords = set()
    
    def set_board(self, board):
        assert len(board) == self.height
        assert len(board[0]) == self.width
        self.raw_tiles = board
        
    def set_boxes(self, boxes_list):
        self.boxes_coords = set(boxes_list)
    
    def set_boxes_solved(self):
        self.boxes_coords = set()
        for i, row in enumerate(self.raw_tiles):
            for j, entry in enumerate(row):
                if entry == 2:
                    self.boxes_coords.add((j, i))
        
    def set_player(self, coords):
        self.player_coords = coords
        
    def get_tile(self, coords):
        return self.raw_tiles[coords[1]][coords[0]]
    
    def check_win(self):
        for i, row in enumerate(self.raw_tiles):
            for j, entry in enumerate(row):
                if entry == 2 and (j, i) not in self.boxes_coords:
                    return False
        self.has_won = True
        return True
    
    def check_tile_legality(self, target_coords):
        if target_coords[0] < 0 or target_coords[1] < 0 or target_coords[0] >= self.width or target_coords[1] >= self.height:
            return False
        if self.get_tile(target_coords) == 1:
            return False
        return True

    def attempt_move(self, target_coords, push_coords):
        if not self.check_tile_legality(target_coords):
            return False
        if target_coords in self.boxes_coords and (not self.check_tile_legality(push_coords) or push_coords in self.boxes_coords):
            return False
        self.player_coords = target_coords
        if target_coords in self.boxes_coords:
            self.boxes_coords.remove(target_coords)
            self.boxes_coords.add(push_coords)
        return True
        
    def move_player_up(self):
        target_coords = (self.player_coords[0], self.player_coords[1]-1)
        push_coords = (self.player_coords[0], self.player_coords[1]-2)
        return self.attempt_move(target_coords, push_coords)

    def move_player_right(self):
        target_coords = (self.player_coords[0]+1, self.player_coords[1])
        push_coords = (self.player_coords[0]+2, self.player_coords[1])
        return self.attempt_move(target_coords, push_coords)

    def move_player_down(self):
        target_coords = (self.player_coords[0], self.player_coords[1]+1)
        push_coords = (self.player_coords[0], self.player_coords[1]+2)
        return self.attempt_move(target_coords, push_coords)

    def move_player_left(self):
        target_coords = (self.player_coords[0]-1, self.player_coords[1])
        push_coords = (self.player_coords[0]-2, self.player_coords[1])
        return self.attempt_move(target_coords, push_coords)
    
    def draw(self, canvas):
        for i, row in enumerate(self.raw_tiles):
            for j, entry in enumerate(row):
                if entry == 1:
                    canvas.create_rectangle(canvas_padding+j*tile_size, canvas_padding+i*tile_size, canvas_padding+(j+1)*tile_size, canvas_padding+(i+1)*tile_size, fill=wall_color, outline="")
        for coords in self.boxes_coords:
            canvas.create_rectangle(canvas_padding+box_tile_padding+coords[0]*tile_size, canvas_padding+box_tile_padding+coords[1]*tile_size, canvas_padding-box_tile_padding+(coords[0]+1)*tile_size, canvas_padding-box_tile_padding+(coords[1]+1)*tile_size, fill=box_color, outline="")
        canvas.create_oval(canvas_padding+(self.player_coords[0]+0.5)*tile_size-player_size/2, canvas_padding+(self.player_coords[1]+0.5)*tile_size-player_size/2, canvas_padding+(self.player_coords[0]+0.5)*tile_size+player_size/2, canvas_padding+(self.player_coords[1]+0.5)*tile_size+player_size/2, fill=player_color, outline="")
        for i, row in enumerate(self.raw_tiles):
            for j, entry in enumerate(row):
                if entry == 2:
                    canvas.create_line(canvas_padding+(j+0.5)*tile_size-target_size/2, canvas_padding+(i+0.5)*tile_size-target_size/2, canvas_padding+(j+0.5)*tile_size+target_size/2, canvas_padding+(i+0.5)*tile_size+target_size/2, width=target_thickness, fill=target_color)
                    canvas.create_line(canvas_padding+(j+0.5)*tile_size+target_size/2, canvas_padding+(i+0.5)*tile_size-target_size/2, canvas_padding+(j+0.5)*tile_size-target_size/2, canvas_padding+(i+0.5)*tile_size+target_size/2, width=target_thickness, fill=target_color)

def random_gen_board_badly(board, num_goals, wall_probability = 0.2):
    goals = set(random.sample([(i, j) for i in range(board.width) for j in range(board.height)], num_goals))
    raw_tiles = [[2 if (i, j) in goals else 1 if random.random() < wall_probability else 0 for i in range(board.width)] for j in range(board.height)]
    board.set_board(raw_tiles)

def pushless_flood_fill(board, coords):
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
            elif searching_tile in board.boxes_coords:
                continue
            else:
                tiles_occupied.add(searching_tile)
                untested_tiles_occupied.append(searching_tile)
    return tiles_occupied

def get_legal_reverse_pushes(board):
    viable_spaces = pushless_flood_fill(board, board.player_coords)
    viable_pushes = set() # A push is a 2-tuple of 2-tuples. The first 2-tuple is the box start coords. The second 2-tuple is the box end coords.
    for box in board.boxes_coords:
        for delta in DIRECTIONS:
            if (box[0]+delta[0], box[1]+delta[1]) in viable_spaces and board.check_tile_legality((box[0]+2*delta[0], box[1]+2*delta[1])) and (box[0]+2*delta[0], box[1]+2*delta[1]) not in board.boxes_coords:
                viable_pushes.add((box, (box[0]+delta[0], box[1]+delta[1])))
    return viable_pushes

def get_legal_reverse_push_lines(board):
    viable_spaces = pushless_flood_fill(board, board.player_coords)
    viable_pushes = set() # A push is a 2-tuple of 2-tuples. The first 2-tuple is the box start coords. The second 2-tuple is the box end coords.
    for box in board.boxes_coords:
        for delta in DIRECTIONS:
            steps = 1
            while (box[0]+steps*delta[0], box[1]+steps*delta[1]) in viable_spaces and board.check_tile_legality((box[0]+(steps+1)*delta[0], box[1]+(steps+1)*delta[1])) and (box[0]+(steps+1)*delta[0], box[1]+(steps+1)*delta[1]) not in board.boxes_coords:
                viable_pushes.add((box, (box[0]+steps*delta[0], box[1]+steps*delta[1])))
                steps += 1
    return viable_pushes

def repeated_random_reverse_push(board, n_times, lines=True):
    get_options = get_legal_reverse_push_lines if lines else get_legal_reverse_pushes
    past_pushes = [] # These pushes are actually reversed
    failed_pushes = []
    n_successful_pushes = 0
    while n_successful_pushes < n_times:
        options = get_options(board)-set(past_pushes+failed_pushes)
        if len(options) == 0:
            print(f"flag {len(failed_pushes)}, only {n_successful_pushes} succeeded")
            board.player_coords = past_pushes[-1][0]
            board.boxes_coords.remove(past_pushes[-1][0])
            board.boxes_coords.add(past_pushes[-1][1])
            failed_pushes.append(past_pushes.pop())
            n_successful_pushes -= 1
            continue
        choice = random.choice(tuple(options)) # TODO BFS/DFS?
        board.player_coords = (min(1, max(-1, choice[1][0]-choice[0][0]))+choice[1][0], min(1, max(-1, choice[1][1]-choice[0][1]))+choice[1][1])
        board.boxes_coords.remove(choice[0])
        board.boxes_coords.add(choice[1])
        past_pushes.append((choice[1], choice[0]))
        n_successful_pushes += 1
    board.player_coords = random.choice(tuple(pushless_flood_fill(board, board.player_coords)))
    return past_pushes

if __name__ == "__main__":
    
    from tile_based_boardgen import gen_puzzle # These have to be here to avoid a circular import
    from principled_tree_search_setup import gen_puzzle_optimal
    
    grid_W = 11
    grid_H = 8
    num_boxes = 4
    num_push_lines = 6
    gen_structured = True
    optimal_structure = True
    openness_bias = lambda x: 0
    
    tk = Tk()
    tk.title("Procoban Prototype")
    canvas = Canvas(tk, width=canvas_padding*2+grid_W*tile_size, height=canvas_padding*2+grid_H*tile_size, bg=floor_color)
    canvas.pack()
    
    game = Board(grid_W, grid_H)
    
    if gen_structured:
        if optimal_structure:
            gen_puzzle_optimal(game, num_boxes, openness_bias)
        else:
            gen_puzzle(game, num_boxes, num_push_lines, openness_bias)
    else:
        random_gen_board_badly(game, num_boxes)
        
        game.set_boxes_solved()
        game.set_player((1, 1))
        repeated_random_reverse_push(game, num_push_lines)
    
    print(get_legal_reverse_pushes(game))
    
    def onKeyPress(event):
        if event.char == 'w':
            game.move_player_up()
        elif event.char == 'a':
            game.move_player_left()
        elif event.char == 's':
            game.move_player_down()
        elif event.char == 'd':
            game.move_player_right()
        game.check_win()
    
    tk.bind('<KeyPress>', onKeyPress)
    while not game.has_won:
        sleep(0.01)
        tk.update_idletasks()
        tk.update()
        canvas.delete("all")
        game.draw(canvas)
    tk.update_idletasks()
    tk.update()
    sleep(2)
    tk.destroy()