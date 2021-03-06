
from __future__ import division
from math import tan, radians

from OpenGL.GL import *
from OpenGL.GLU import *

from base import Entity, Container

class HedgeEntity(Entity):
    '''
    The center of the hedge is directly between the top point of the vertical
    poles.
    '''

    def __init__(self, *args, **kwargs):
        super(HedgeEntity, self).__init__(*args, **kwargs)

    def draw(self):
        self.pre_draw()
        glColor(0, 1, 0)
        glMatrixMode(GL_MODELVIEW)

        # Right Pole
        glPushMatrix()
        glTranslate(0, 3, -4)
        gluCylinder(gluNewQuadric(), 0.2, 0.2, 1, 10, 1)
        glPopMatrix()

        # Center Pole
        glColor(1,0,0)
        glPushMatrix()
        glTranslate(0,0,-4)
        gluCylinder(gluNewQuadric(), 0.2, 0.2, 4, 10, 1)
        glPopMatrix()

        # Left Pole
        glColor(0,1,0)
        glPushMatrix()
        glTranslate(0, -3, -4)
        gluCylinder(gluNewQuadric(), 0.2, 0.2, 1, 10, 1)
        glPopMatrix()

        # Bottom Pole
        glPushMatrix()
        glTranslate(0, 3, -4)
        glRotate(90, 1, 0, 0)
        gluCylinder(gluNewQuadric(), 0.2, 0.2, 6, 10, 1)
        glPopMatrix()

        self.post_draw()

    def find(self, robot):

        c = Container()
        c.left_pole = robot.find_point("forward", self.absolute_point((0, 3)))
        c.right_pole = robot.find_point("forward", self.absolute_point((0, -3)))
        c.center_pole = robot.find_point("forward", self.absolute_point((0,0)))
        bottom_pole = robot.find_point("forward", self.absolute_point((0, 0, -4)))[1]

        if c.left_pole:
            c.left_pole *= robot.get_camera_fov("forward")/2
        if c.right_pole:
            c.right_pole *= robot.get_camera_fov("forward")/2
        if c.center_pole:
            c.center_pole *= robot.get_camera_fov("forward")/2
        if bottom_pole:
            bottom_pole *= robot.get_camera_fov("forward", vertical=True)/2

        if c.left_pole and c.right_pole:
            theta = abs(c.left_pole - c.right_pole)
            c.r = 3 / tan(radians(theta/2))
        elif c.center_pole:
            theta = abs(c.center_pole)
            c.r = 3 / tan(radians(theta/2))
        else:
            c.r = None

        if c.r and bottom_pole:
            c.crossbar_depth = -1 * c.r * tan(radians(bottom_pole))
        else:
            c.crossbar_depth = None

        hedge_found = False
        if c.left_pole is not None or c.right_pole is not None or c.center_pole is not None:
            hedge_found = True

        return hedge_found, c
