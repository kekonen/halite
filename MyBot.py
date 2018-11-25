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

LOCAL_MACHINE=True

if LOCAL_MACHINE:
    num = 0
    for nme in os.listdir():
        match = re.match(r'app(\d).log', nme)
        if match:
            num_candidate = int(match.group(1)) +1
            if num_candidate > num:
                num = num_candidate

    logging.basicConfig(filename=f'app{num}.log', filemode='w', format='%(name)s - %(levelname)s - %(message)s', level=logging.INFO)

import numpy as np



import keras


from keras.models import Model
from keras.layers import Input, Dense, Conv2D, MaxPooling2D, Flatten
from keras.optimizers import Adam


from collections import deque

class DQNAgent:
    def __init__(self, vision_size, tabular_size, action_size):
        self.vision_size = vision_size
        self.tabular_size = tabular_size

        logging.info(f'Agent: {self.vision_size}, {self.tabular_size}')
        self.action_size = action_size
        self.memory = deque(maxlen=2000)
        self.gamma = 0.95    # discount rate
        self.epsilon = 1.0  # exploration rate
        self.epsilon_min = 0.01
        self.epsilon_decay = 0.995
        self.learning_rate = 0.001
        self.model = self._build_model()
    def _build_model(self):
        # Neural Net for Deep-Q learning Model
        vision_input = Input(shape=self.vision_size)
        tabluar_input = Input(shape=[self.tabular_size])
        
        conv1 = Conv2D(25, (3, 3), padding='same', activation='selu')(vision_input)
        pool1 = MaxPooling2D((2, 2), strides=(1, 1), padding='same')(conv1)
        
        conv2 = Conv2D(16, (3, 3), padding='same', activation='selu')(pool1)
        pool2 = MaxPooling2D((2, 2), strides=(1, 1), padding='same')(conv2)
        
        vision_out = Flatten()(pool2)
        
        concat = keras.layers.concatenate([vision_out, tabluar_input], axis=1)
        
        x = Dense(16, activation='selu')(concat)
        x = Dense(16, activation='selu')(x)
        
        main_output = Dense(self.action_size, activation='softmax')(x)
        model = Model(inputs=[vision_input, tabluar_input], outputs=main_output)
        
#        model = Sequential()
#        model.add(Dense(24, input_dim=self.state_size, activation='relu'))
#        model.add(Dense(24, activation='relu'))
#        model.add(Dense(self.action_size, activation='linear'))
        model.compile(loss='categorical_crossentropy',
                      optimizer=Adam(lr=self.learning_rate))
        return model
    def remember(self, state, action, reward, next_state, done):
        self.memory.append((state, action, reward, next_state, done))
    def act(self, state):
        if np.random.rand() <= self.epsilon:
            return random.randrange(self.action_size)
        act_values = self.model.predict(state)
        return np.argmax(act_values[0])  # returns action
    def replay(self, batch_size):
        minibatch = random.sample(self.memory, batch_size)
        for state, action, reward, next_state, done in minibatch:
            target = reward
            if not done:
              target = reward + self.gamma * \
                       np.amax(self.model.predict(next_state)[0])
            target_f = self.model.predict(state)
            target_f[0][action] = target
            self.model.fit(state, target_f, epochs=1, verbose=0)
        if self.epsilon > self.epsilon_min:
            self.epsilon *= self.epsilon_decay


agent = DQNAgent((7, 7, 5), 2, 6)
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

predicted_command = {}

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
            [previous_state, previous_action] = predicted_command[ship.id]
            reward = (state[1] - previous_state[1]).sum()
            logging.info(f'getting a reward: {reward}')
            # next_state, reward, done, _ = env.step(action)
            done = False
            agent.remember(previous_state, previous_action, reward, state, done)
        
        action = agent.act(state)
        
        predicted_command[ship.id] = [state, action]
        
    for ship in me.get_ships():
        command, command_name = dooo(ship, predicted_command[ship.id][1])
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

