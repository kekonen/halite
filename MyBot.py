#!/usr/bin/env python3

# Import the Halite SDK, which will let you interact with the game.
import hlt
from hlt import constants, Direction, Position
from hlt.entity import Shipyard, Entity

import random
import logging
import re
import sys, os
stderr = sys.stderr
sys.stderr = open(os.devnull, 'w')

botName = sys.argv[1]


LOCAL_MACHINE=True
if LOCAL_MACHINE:
    logging.basicConfig(filename=f'app{botName}.log', filemode='w', format='%(name)s - %(levelname)s - %(message)s', level=logging.INFO)

# if LOCAL_MACHINE:
#     num = 0
#     for nme in os.listdir():
#         match = re.match(r'app(\d).log', nme)
#         if match:
#             num_candidate = int(match.group(1)) +1
#             if num_candidate > num:
#                 num = num_candidate
#     logging.basicConfig(filename=f'app{num}.log', filemode='w', format='%(name)s - %(levelname)s - %(message)s', level=logging.INFO)

import numpy as np



import keras


from keras.models import Model
from keras.layers import Input, Dense, Conv2D, MaxPooling2D, Flatten
from keras.optimizers import Adam


from collections import deque

import socket, pickle

class MemoryClient:
    def __init__(self, SERVER_IP="127.0.0.1", SERVER_PORT=1337, ME_IP="127.0.0.1" ,ME_PORT=1337):
        self.UDP_IP_SERVER = SERVER_IP
        self.UDP_PORT_SERVER = SERVER_PORT

        self.UDP_IP_ME = ME_IP
        self.UDP_PORT_ME = ME_PORT
        # self.UDP_PORT_IN  = 228


        self.sock = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
        self.sock.bind((self.UDP_IP_ME, self.UDP_PORT_ME))

        # self.sock = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)


    def send(self, data):
        self.sock.sendto(pickle.dumps(data), (self.UDP_IP_SERVER, self.UDP_PORT))
        answer = self.sock.recvfrom(1024)
        address = answer[1]
        data = answer[0]

        if data != b'kek' and data: 
            return pickle.loads(data)
        elif data == b'kek':
            return True
        # sock.sendto(message, (UDP_IP, UDP_PORT))

a = MemoryClient()

a.send(np.array([1,3,3,7]))



class DQNAgentClient:
    def __init__(self, SERVER_IP="127.0.0.1", SERVER_PORT=1337, ME_IP="127.0.0.1" ,ME_PORT=1338):
        self.UDP_IP_SERVER = SERVER_IP
        self.UDP_PORT_SERVER = SERVER_PORT

        self.UDP_IP_ME = ME_IP
        self.UDP_PORT_ME = ME_PORT
        self.PACKAGE_SIZE = 4096
        # self.UDP_PORT_IN  = 228


        self.sock = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
        self.sock.bind((self.UDP_IP_ME, self.UDP_PORT_ME))

    def _send(self, data):
        # Neural Net for Deep-Q learning Model
        self.sock.sendto(pickle.dumps(data), (self.UDP_IP_SERVER, self.UDP_PORT))
        answer = self.sock.recvfrom(self.PACKAGE_SIZE)
        address = answer[1]
        data = answer[0]

        if data != b'kek' and data: 
            return pickle.loads(data)
        elif data == b'kek':
            return True

    def remember(self, state, action, reward, next_state, done):
        self._send(['remember', [state, action, reward, next_state, done]])
    def act(self, state):
        # if np.random.rand() <= self.epsilon:
        #     return random.randrange(self.action_size)
        # act_values = self.model.predict(state)
        # return np.argmax(act_values[0])  # returns action
        return self._send(['act', state])
    def replay(self, batch_size): # TODO: adjust for model
        self._send(['replay', batch_size])


agent = DQNAgentClient()
sys.stderr = stderr

logging.warning(f'kek: 1')

# This game object contains the initial game state.
game = hlt.Game()
# Respond with your name.
game.ready("MyPythonBot")
logging.warning(f'kek: 2')
gap = 3

def dooo(ship, what):
    if what == 0:
        return ship.move(Direction.North), 'North'
    elif what == 1:
        return ship.move(Direction.South), 'South'
    elif what == 2:
        return ship.move(Direction.East), 'East'
    elif what == 3:
        return ship.move(Direction.West), 'West'
    elif what == 4:
        return ship.make_dropoff(), 'Dropoff'
    elif what == 5:
        return ship.stay_still(), 'Still'

def vision(ship, game_map, me):
    retina = np.zeros((gap*2+1, gap*2+1, 5)) #(7, 7, 5)  0:halite [0;1], 1:occupied by friend [bool], 2:occupied by enemy [bool], 3:drop point [bool], 4:shipyard [bool]
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

last_state_action = {}

while True:
    # Get the latest game state.
    game.update_frame()
    logging.info('Updating frame')
    # You extract player metadata and the updated map metadata here for convenience.
    me = game.me
    game_map = game.game_map

    # A command queue holds all the commands you will run this turn.
    command_queue = []
    
    
    
#    #
#    friend_ships = [ship for ship in me.get_ships()]
#    #
    for ship in me.get_ships():
        a_sight = vision(ship, game_map, me)
        state = [a_sight, np.array([ship.halite_amount, me.halite_amount])]
        logging.info(f'Ship {ship.id}, hal: {ship.halite_amount}, under: {game_map[ship.position].halite_amount}, base: {me.halite_amount}')
        
        if game.turn_number > 2:
            [previous_state, previous_action] = last_state_action[ship.id]
            reward = (state[1] - previous_state[1]).sum()
            logging.info(f'getting a reward: {reward}')
            # next_state, reward, done, _ = env.step(action)
            done = False
            agent.remember(previous_state, previous_action, reward, state, done)
        
        action = agent.act(state)
        
        last_state_action[ship.id] = [state, action]
        
    for ship in me.get_ships():
        command, command_name = dooo(ship, last_state_action[ship.id][1])
        logging.info(f'Command for ship {ship.id}, c: {command_name}')
        command_queue.append(command)
#        command_queue.append(ship.move(Destination.North))
        continue
        
    # If you're on the first turn and have enough halite, spawn a ship.
    # Don't spawn a ship if you currently have a ship at port, though.
    if game.turn_number <= 1 and me.halite_amount >= constants.SHIP_COST and not game_map[me.shipyard].is_occupied:
        command_queue.append(game.me.shipyard.spawn())


    # Send your moves back to the game environment, ending this turn.
    game.end_turn(command_queue)


# agent.replay(32)

