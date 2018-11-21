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

def vision(ship, game_map, me):
    retina = np.zeros((gap*2+1, gap*2+1, 5)) #(7, 7, 4)  0:halite [0;1], 1:occupied by friend [bool], 2:occupied by enemy [bool], 3:drop point [bool], 4:shipyard [bool]
    for x in range(-gap, gap+1):
        for y in range(-gap, gap+1):

            check_position = ship.position + Position(x, y)
            retina[y+gap][x+gap][0] = game_map[check_position].halite_amount/1000

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

            if structure is Shipyard:
                retina[y+gap][x+gap][4] = 1

    return retina

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

        command_queue.append(ship.move(Destination.North))
        continue
        
    # If you're on the first turn and have enough halite, spawn a ship.
    # Don't spawn a ship if you currently have a ship at port, though.
    if game.turn_number <= 1 and me.halite_amount >= constants.SHIP_COST and not game_map[me.shipyard].is_occupied:
        command_queue.append(game.me.shipyard.spawn())


    # Send your moves back to the game environment, ending this turn.
    game.end_turn(command_queue)
