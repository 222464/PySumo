import random
import arcade
import os
import sumo.arena
import numpy as np
import pyswarm
from copy import copy

#####################################################################

screenWidth = 800
screenHeight = 600

class Sumo(arcade.Window):
    def __init__(self):
        super().__init__(screenWidth, screenHeight, "Sumo")
        file_path = os.path.dirname(os.path.abspath(__file__))
        os.chdir(file_path)

        arcade.set_background_color(arcade.color.GRAY_BLUE)

        self.a = sumo.arena.Arena((screenWidth, screenHeight))

        self.tDown = False
        self.speedMode = False

        self.bot0LeftMotor = 0.0
        self.bot0RightMotor = 0.0
        self.bot0Boost = False

        self.bot1LeftMotor = 0.0
        self.bot1RightMotor = 0.0
        self.bot1Boost = False

        ########################### Create Agents ###########################

        # Sensors: arena distance from center, angle relative to center, distance from opponent, angle to opponent, angle between opponents, boost
        # Actions: Left motor, right motor, boost

        self.cs = pyswarm.PyComputeSystem(16)

        numInputs = 6
        numActions = 3

        numLayers = 2

        inputSize = pyswarm.PyInt3(1, 1, numInputs)

        lds = []

        for i in range(numLayers):
            l = pyswarm.PyLayerDesc()

            l._layerType = "conv"
            l._filterRadius = 0
            l._numMaps = numActions if i == numLayers - 1 else 24
            l._recurrent = False if i == numLayers - 1 else True
            l._actScalar = 6.0

            lds.append(l)

        self.h0 = pyswarm.PyHierarchy(self.cs, inputSize, lds, 32)
        self.h1 = pyswarm.PyHierarchy(self.cs, inputSize, lds, 32)

        self.h0.setOptAlpha(0.001)

        self.h1.setOptAlpha(0.001)

        self.rewardNoise = 0.0

    def on_draw(self):
        arcade.start_render()
        
        self.a.draw()

    def on_key_press(self, key, modifiers):
        if key == arcade.key.T:
            if not self.tDown:
                self.speedMode = not self.speedMode

            self.tDown = True

    def on_key_release(self, key, modifiers):
        if key == arcade.key.T:
            self.tDown = False

    def botAct(self, botIndex, reward):
        if botIndex == 0:
            # Gather sensors (all in [0, 1] range)
            sensors = []

            distToCenter = np.sqrt(self.a.bot0.body.position[0] * self.a.bot0.body.position[0] + self.a.bot0.body.position[1] * self.a.bot0.body.position[1])

            sensors.append(distToCenter / self.a.arenaRadius)

            toCenter = (-self.a.bot0.body.position[0], -self.a.bot0.body.position[1])

            angleToCenter = (np.arctan2(toCenter[1], toCenter[0]) - self.a.bot0.body.angle) % (2.0 * np.pi)

            if angleToCenter < 0.0:
                angleToCenter += 2.0 * np.pi

            sensors.append(angleToCenter / (2.0 * np.pi))

            deltaPos = (self.a.bot1.body.position[0] - self.a.bot0.body.position[0], self.a.bot1.body.position[1] - self.a.bot0.body.position[1])

            distToOpponent = np.sqrt(deltaPos[0] * deltaPos[0] + deltaPos[1] * deltaPos[1])

            sensors.append(distToOpponent / (self.a.arenaRadius * 2.0))

            angleToOpponent = (np.arctan2(deltaPos[1], deltaPos[0]) - self.a.bot0.body.angle) % (2.0 * np.pi)

            if angleToOpponent < 0.0:
                angleToOpponent += 2.0 * np.pi

            sensors.append(angleToOpponent / (2.0 * np.pi))

            angleBetween = (self.a.bot1.body.angle - self.a.bot0.body.angle) % (2.0 * np.pi)

            if angleBetween < 0.0:
                angleBetween += 2.0 * np.pi

            sensors.append(angleBetween / (2.0 * np.pi))

            sensors.append(self.a.bot0.boost)

            self.h0.step(self.cs, sensors, reward - 0.01 * distToOpponent + self.rewardNoise * np.random.randn(), True)

            actions = self.h0.getOutputStates()

            # Actions
            self.bot0LeftMotor = actions[0]
            self.bot0RightMotor = actions[1]

            self.bot0Boost = actions[2] > 0.1

        elif botIndex == 1:
            # Gather sensors (all in [0, 1] range)
            sensors = []

            distToCenter = np.sqrt(self.a.bot1.body.position[0] * self.a.bot1.body.position[0] + self.a.bot1.body.position[1] * self.a.bot1.body.position[1])

            sensors.append(distToCenter / self.a.arenaRadius)

            toCenter = (-self.a.bot1.body.position[0], -self.a.bot1.body.position[1])

            angleToCenter = (np.arctan2(toCenter[1], toCenter[0]) - self.a.bot1.body.angle) % (2.0 * np.pi)

            if angleToCenter < 0.0:
                angleToCenter += 2.0 * np.pi

            sensors.append(angleToCenter / (2.0 * np.pi))

            deltaPos = (self.a.bot0.body.position[0] - self.a.bot1.body.position[0], self.a.bot0.body.position[1] - self.a.bot1.body.position[1])

            distToOpponent = np.sqrt(deltaPos[0] * deltaPos[0] + deltaPos[1] * deltaPos[1])

            sensors.append(distToOpponent / (self.a.arenaRadius * 2.0))

            angleToOpponent = (np.arctan2(deltaPos[1], deltaPos[0]) - self.a.bot1.body.angle) % (2.0 * np.pi)

            if angleToOpponent < 0.0:
                angleToOpponent += 2.0 * np.pi

            sensors.append(angleToOpponent / (2.0 * np.pi))

            angleBetween = (self.a.bot0.body.angle - self.a.bot1.body.angle) % (2.0 * np.pi)

            if angleBetween < 0.0:
                angleBetween += 2.0 * np.pi

            sensors.append(angleBetween / (2.0 * np.pi))

            sensors.append(self.a.bot1.boost)

            self.h1.step(self.cs, sensors, reward - 0.01 * distToOpponent + self.rewardNoise * np.random.randn(), True)

            actions = self.h1.getOutputStates()

            # Actions
            self.bot1LeftMotor = actions[0]
            self.bot1RightMotor = actions[1]

            self.bot1Boost = actions[2] > 0.1

    def update(self, dt):
        fixedDt = 0.017
        
        if self.speedMode:
            for i in range(100): 
                reward0, reward1, reset = self.a.update(fixedDt, self.bot0LeftMotor, self.bot0RightMotor, self.bot0Boost, self.bot1LeftMotor, self.bot1RightMotor, self.bot1Boost)

                if reset:
                    print("Episode terminated with " + str(reward0) + " " + str(reward1))

                # If reset, copy bot of better player to worse player
                # if reset:
                #     if reward0 > reward1:
                #         self.h1 = copy(self.h0)
                #     else:
                #         self.h0 = copy(self.h1)

                self.botAct(0, reward0)
                self.botAct(1, reward1)
        else:
            reward0, reward1, reset = self.a.update(fixedDt, self.bot0LeftMotor, self.bot0RightMotor, self.bot0Boost, self.bot1LeftMotor, self.bot1RightMotor, self.bot1Boost)

            if reset:
                print("Episode terminated with " + str(reward0) + " " + str(reward1))

            # If reset, copy bot of better player to worse player
            # if reset:
            #     if reward0 > reward1:
            #         self.h1 = copy(self.h0)
            #     else:
            #         self.h0 = copy(self.h1)

            self.botAct(0, reward0)
            self.botAct(1, reward1)

def main():
    window = Sumo()
    arcade.run()

if __name__ == "__main__":
    main()