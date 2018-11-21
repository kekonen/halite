#!/usr/bin/env python3

# Import the Halite SDK, which will let you interact with the game.
import hlt
from hlt import constants, Direction, Position
from hlt.entity import Shipyard, Entity

import random
import logging
import numpy as np


# This game object contains the initial game state.
game = hlt.Game()
# Respond with your name.
game.ready("MyPythonBot")
ship_status = {}
ship_want_to_go = {}

gap = 3

def do(ship, what):
    if what == 0:
        return ship.move(Direction.North)
    elif what == 1:
        return ship.move(Direction.South)
    elif what == 2:
        return ship.move(Direction.East)
    elif what == 3:
        return ship.move(Direction.West)
    elif what == 4:
        return ship.stay_still()
    elif what == 5:
        return ship.make_dropoff()
#[Direction.North, Direction.South, Direction.East, Direction.West]

def vision(ship, game_map, me):
    retina = np.zeros((gap*2+1, gap*2+1, 5)) #(7, 7, 4)  0:halite [0;1], 1:occupied by friend [bool], 2:occupied by enemy [bool], 3:drop point [bool], 4:shipyard [bool]
    for x in range(-gap, gap+1):
        for y in range(-gap, gap+1):
#            logging.info(f'{x},{y}')
            check_position = ship.position + Position(x, y)
            retina[y+gap][x+gap][0] = game_map[check_position].halite_amount/1000
#            if retina[y+gap][x+gap][1] = game_map[check_position].is_occupied and not check_position == ship.position
            if game_map[check_position].is_occupied and not check_position == ship.position:
                if check_position not in [myship.position for myship in me.get_ships()]:
                    retina[y+gap][x+gap][2] = 1
                    logging.info(f'{ship.id}:enemy: {check_position}')
                else:
                    retina[y+gap][x+gap][1] = 1
                    logging.info(f'{ship.id}:friend: {check_position}')
            structure = game_map[check_position].structure_type
            if structure is Entity:
                retina[y+gap][x+gap][3] = 1
#                logging.info(f'p: {check_position} -> dropoff')
            if structure is Shipyard:
                retina[y+gap][x+gap][4] = 1
#                logging.info(f'p: {check_position} -> shipyard')
#            retina[y+gap][x+gap][2] = game_map[check_position].structure_type
#            logging.info(f'p: {check_position}, struct: {game_map[check_position].structure_type}')
            
#    logging.info(ship.position)
#    logging.info(retina)
#    logging.info(ship_position.x)
    return retina
    
def random_dest():
    return random.choice([Direction.North, Direction.South, Direction.East, Direction.West])

def is_safe_occupy(ship, direction, game_map):
    cell = game_map[ship.position.directional_offset(direction)]
    
    if cell.is_occupied or (cell.position in list(ship_want_to_go.values())):
        return False
    ship_want_to_go[ship.id] = cell.position
    return True

while True:
    # Get the latest game state.
    game.update_frame()
    # You extract player metadata and the updated map metadata here for convenience.
    me = game.me
    game_map = game.game_map

    # A command queue holds all the commands you will run this turn.
    command_queue = []
    
#    #
#    friend_ships = [ship for ship in me.get_ships()]
#    #
    for ship in me.get_ships():
        vision(ship, game_map, me)
        
    for ship in me.get_ships():

        command_queue.append(ship.move(game_map.naive_navigate(ship, Position(16,16))))
        continue
        # For each of your ships, move randomly if the ship is on a low halite location or the ship is full.
        #   Else, collect halite.
        if ship.id not in ship_status:
            ship_status[ship.id] = "exploring"
        
        if ship_status[ship.id] == "returning":
            if (game_map[ship.position].halite_amount + me.halite_amount + ship.halite_amount) >=5000 and not dropoffing:
                logging.info(f'making dropoff from ship at {ship.position}')
                dropoffing = True
                command_queue.append(ship.make_dropoff())
                continue
            elif ship.position == me.shipyard.position:
                ship_status[ship.id] = "exploring"
            else:
                move = game_map.naive_navigate(ship, me.shipyard.position)
                command_queue.append(ship.move(move))
                continue
        elif ship.halite_amount >= constants.MAX_HALITE / 4:
            ship_status[ship.id] = "returning"
#        command_queue.append(
#                ship.move('w'))
#        logging.info(f'ship {ship.id} status is {ship_status[ship.id]}')
        for dropoff in me.get_dropoffs():
            logging.info(f'd: {dropoff.position}')
        if game_map[ship.position].halite_amount < constants.MAX_HALITE / 10 or ship.is_full:
            desired_direction = random_dest()
            if not is_safe_occupy(ship, desired_direction, game_map):
                desired_direction = random_dest()
            command_queue.append(
                ship.move(desired_direction))
        else:
            command_queue.append(ship.stay_still())
        
    ship_want_to_go = {}

    # If you're on the first turn and have enough halite, spawn a ship.
    # Don't spawn a ship if you currently have a ship at port, though.
    if game.turn_number <= 1 and me.halite_amount >= constants.SHIP_COST and not game_map[me.shipyard].is_occupied:
        command_queue.append(game.me.shipyard.spawn())
    
    if len(me.get_ships()) < 2 and  game.turn_number > 5 and me.halite_amount >= constants.SHIP_COST and not game_map[me.shipyard].is_occupied:
        command_queue.append(game.me.shipyard.spawn())
        
    dropoffing = False

    # Send your moves back to the game environment, ending this turn.
    game.end_turn(command_queue)
