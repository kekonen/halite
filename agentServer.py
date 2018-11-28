import socket
import pickle
import numpy as np
import logging
import re
import sys, os
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

        if f'botMemory.pkl' in os.listdir():
            self.memory = pickle.load(open(f'botMemory{botName}.pkl', 'rb'))
                
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
    def replay(self, batch_size): # TODO: adjust for model
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



class AgentServer:
    def __init__(self, IP="127.0.0.1", PORT=1337):
        self.UDP_IP = IP
        self.UDP_PORT = PORT
        self.PACKAGE_SIZE = 4096
        # self.UDP_PORT_IN  = 228


        self.sock = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
        self.sock.bind((self.UDP_IP, self.UDP_PORT))

        agent = DQNAgent((7, 7, 5), 2, 6)

        print(f'--- Server started at {(self.UDP_IP, self.UDP_PORT)}')

        # self.sock = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)

    def handle(self, requestObj):
        command = requestObj[0]
        data = requestObj[1]
        print(f'Command: {command}\n')

        if command == 'replay':
            agent.replay(data)
        elif command == 'act':
            return agent.act(data)
        elif command == 'remember':
            agent.remember(*data)


    def serve(self):
        while True:
            data = self.sock.recvfrom(self.PACKAGE_SIZE)
            address = data[1]
            data = data[0]#.decode('utf8')   keep as bytes for unpickle
            print(f'Received package from: {address}')
            

            if not data:
                break
            
            unpickled = pickle.loads(data)

            if unpickled[0]:
                answer = self.handle(unpickled)
                if answer:
                    pickled_answer = pickle.dumps(answer)
                    self.sock.sendto(pickled_answer, address) # .encode('utf8')

            # print(unpickled)
            # answer = f'KEK: lol'
            # # answer = f'KEK: {data}'

            # print('Received from:', address)
            # self.sock.sendto(answer.encode('utf8'), address)

        # sock.sendto(message, (UDP_IP, UDP_PORT))

s = AgentServer('127.0.0.1', 1337)

s.serve()
# ncat -v localhost 1337 -u
