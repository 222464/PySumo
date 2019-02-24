import arcade
import os
import numpy as np
import pymunk
from copy import copy

radToDeg = 180.0 / np.pi
degToRad = np.pi / 180.0

class Bot:
    def __init__(self, space: pymunk.Space, color: arcade.Color):
        self.space = space
        self.color = color

        self.mass = 1.0
        self.size = (2.0, 2.0)
        self.rotationDamping = 0.7
        
        moment = pymunk.moment_for_box(self.mass, self.size)

        self.body = pymunk.Body(self.mass, moment)

        self.shape = pymunk.Poly.create_box(self.body, size=self.size)

        self.space.add(self.body, self.shape)

        self.motorForce = 300.0
        self.maxMotorSpeed = 0.2

        self.boost = 1.0
        self.boostRegen = 0.1
        self.boostDeplete = 1.0
        self.boostSpeedMul = 1.5

        self.globalLeftMotorPosPrev = None
        self.globalRightMotorPosPrev = None

    def update(self, dt, leftMotor, rightMotor, boost):
        localLeftMotorPos = (0.0, self.size[1] * 0.5)
        localRightMotorPos = (0.0, -self.size[1] * 0.5)

        c = np.cos(self.body.angle)
        s = np.sin(self.body.angle)

        v = (c, s)

        globalLeftMotorPos = (localLeftMotorPos[0] * c - localLeftMotorPos[1] * s + self.body.position[0], localLeftMotorPos[1] * s + localLeftMotorPos[0] * c + self.body.position[1])
        globalRightMotorPos = (localRightMotorPos[0] * c - localRightMotorPos[1] * s + self.body.position[0], localRightMotorPos[1] * s + localRightMotorPos[0] * c + self.body.position[1])

        driveLeft = True
        driveRight = True
        speedMulLeft = 1.0
        speedMulRight = 1.0

        if self.globalLeftMotorPosPrev is not None:
            vel = (globalLeftMotorPos[0] - self.globalLeftMotorPosPrev[0], globalLeftMotorPos[1] - self.globalLeftMotorPosPrev[1])

            mag = np.sqrt(vel[0] * vel[0] + vel[1] * vel[1])

            if mag >= self.maxMotorSpeed:
                driveLeft = False
            else:
                speedMulLeft = 1.0 - mag / self.maxMotorSpeed

        if self.globalRightMotorPosPrev is not None:
            vel = (globalRightMotorPos[0] - self.globalRightMotorPosPrev[0], globalRightMotorPos[1] - self.globalRightMotorPosPrev[1])

            mag = np.sqrt(vel[0] * vel[0] + vel[1] * vel[1])

            if mag >= self.maxMotorSpeed:
                driveRight = False
            else:
                speedMulRight = 1.0 - mag / self.maxMotorSpeed

        if boost and self.boost >= self.boostDeplete * dt:
            speedMulLeft *= self.boostSpeedMul
            speedMulRight *= self.boostSpeedMul

            self.boost = np.maximum(0.0, self.boost - self.boostDeplete * dt)
        else:
            # Regen
            self.boost = np.minimum(1.0, self.boost + self.boostRegen * dt)

        if driveLeft:
            self.body.apply_force_at_local_point((self.motorForce * leftMotor * speedMulLeft, 0.0), localLeftMotorPos)

        if driveRight:
            self.body.apply_force_at_local_point((self.motorForce * rightMotor * speedMulRight, 0.0), localRightMotorPos)

        self.body.angular_velocity *= self.rotationDamping

        self.globalLeftMotorPosPrev = globalLeftMotorPos
        self.globalRightMotorPosPrev = globalRightMotorPos

    def draw(self, mToP, camOffset):
        arcade.draw_rectangle_outline(self.body.position[0] * mToP + camOffset[0], self.body.position[1] * mToP + camOffset[1], self.size[0] * mToP, self.size[1] * mToP, self.color, 0.01 * mToP, self.body.angle * radToDeg)

        arcade.draw_arc_outline(self.body.position[0] * mToP + camOffset[0], self.body.position[1] * mToP + camOffset[1], self.size[0] * 0.5 * mToP, self.size[1] * 0.5 * mToP, self.color, 0.0, np.pi * radToDeg, 0.01 * mToP, (self.body.angle - np.pi * 0.5) * radToDeg)
        
        arcade.draw_arc_filled(self.body.position[0] * mToP + camOffset[0], self.body.position[1] * mToP + camOffset[1], self.size[0] * 0.25 * mToP, self.size[1] * 0.25 * mToP, self.color, 0.0, np.pi * 2.0 * self.boost * radToDeg, (self.body.angle - np.pi * 0.5) * radToDeg)
        