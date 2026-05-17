"""Tests unitaires — car.Player."""

import unittest
import settings as S

# pygame headless
import os
os.environ.setdefault("SDL_VIDEODRIVER", "dummy")

import pygame
pygame.init()

from car import Player


class TestPlayer(unittest.TestCase):
    def setUp(self):
        self.player = Player(S.ROAD_X, S.ROAD_WIDTH, 3, "cyan")

    def test_initial_position_in_road(self):
        self.assertGreaterEqual(self.player.x, S.ROAD_X)
        self.assertLessEqual(self.player.x + self.player.w, S.ROAD_X + S.ROAD_WIDTH)

    def test_nitro_activation_consumes_charge(self):
        self.player.nitro_charge = S.NITRO_MAX
        ok = self.player.activate_nitro()
        self.assertTrue(ok)
        self.assertTrue(self.player.nitro_active)
        self.assertLess(self.player.nitro_charge, S.NITRO_MAX)

    def test_take_hit_reduces_lives(self):
        lives_before = self.player.lives
        dead = self.player.take_hit()
        self.assertEqual(self.player.lives, lives_before - 1)
        self.assertFalse(dead)

    def test_get_lane(self):
        lane = self.player.get_lane(S.ROAD_X, S.ROAD_WIDTH // 3)
        self.assertGreaterEqual(lane, 0)
        self.assertLess(lane, 3)


if __name__ == "__main__":
    unittest.main()
