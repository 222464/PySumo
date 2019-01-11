import arcade
import os
import numpy as np
import pymunk
from copy import copy
from sumo import bot

class Arena:
    def __init__(self, windowSize=(640, 480)):
        self.viewRadius = 10.0
        self.arenaRadius = 8.0
        self.lineRadius = 1.5
        self.startRadius = 2.75
        self.damping = 0.0005

        minSize = np.minimum(windowSize[0], windowSize[1])

        self.camOffset = (windowSize[0] * 0.5, windowSize[1] * 0.5)

        self.mToP = minSize / (2.0 * self.viewRadius)

        self.reset()

    def reset(self):
        self.space = pymunk.Space()
        self.space.gravity = (0.0, 0.0)

        self.space.damping = self.damping

        self.bot0 = bot.Bot(self.space, arcade.color.RED)
        self.bot1 = bot.Bot(self.space, arcade.color.BLUE)

        self.bot0.body.position = (-self.startRadius, 0.0)
        self.bot0.body.angle = 0.0

        self.bot1.body.position = (self.startRadius, 0.0)
        self.bot1.body.angle = np.pi

    def update(self, dt, bot0LeftMotor, bot0RightMotor, bot0Boost, bot1LeftMotor, bot1RightMotor, bot1Boost):
        # Update bots
        self.bot0.update(dt, bot0LeftMotor, bot0RightMotor, bot0Boost)
        self.bot1.update(dt, bot1LeftMotor, bot1RightMotor, bot1Boost)

        # Update physics
        self.space.step(dt)

        # Scoring
        reward0 = 0.0
        reward1 = 0.0

        dist0 = np.sqrt(self.bot0.body.position[0] * self.bot0.body.position[0] + self.bot0.body.position[1] * self.bot0.body.position[1])
        dist1 = np.sqrt(self.bot1.body.position[0] * self.bot1.body.position[0] + self.bot1.body.position[1] * self.bot1.body.position[1])

        reset = False

        if dist0 > self.arenaRadius:
            reward0 = -1.0
            reward1 = 1.0

            reset = True

            self.reset()

        elif dist1 > self.arenaRadius:
            reward0 = 1.0
            reward1 = -1.0

            reset = True
            
            self.reset()

        return reward0, reward1, reset

    def draw(self):
        arcade.draw_circle_filled(self.camOffset[0], self.camOffset[1], self.arenaRadius * self.mToP, arcade.color.BLACK)
        arcade.draw_circle_outline(self.camOffset[0], self.camOffset[1], self.arenaRadius * self.mToP, arcade.color.WHITE, border_width=0.3 * self.mToP)

        arcade.draw_rectangle_filled(-self.lineRadius * self.mToP + self.camOffset[0], self.camOffset[1], 0.3 * self.mToP, 2.0 * self.mToP, arcade.color.WHITE)
        arcade.draw_rectangle_filled(self.lineRadius * self.mToP + self.camOffset[0], self.camOffset[1], 0.3 * self.mToP, 2.0 * self.mToP, arcade.color.WHITE)
        
        self.bot0.draw(self.mToP, self.camOffset)
        self.bot1.draw(self.mToP, self.camOffset)
        


