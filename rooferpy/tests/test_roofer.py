# Copyright (c) 2018-2026 TU Delft 3D geoinformation group, Ravi Peters (3DGI),
# and Balazs Dukai (3DGI)
#
# This file is part of roofer (https://github.com/3DBAG/roofer)
#
# roofer is free software: you can redistribute it and/or modify it under the
# terms of the GNU General Public License as published by the Free Software
# Foundation, either version 3 of the License, or (at your option) any later
# version. roofer is distributed in the hope that it will be useful, but
# WITHOUT ANY WARRANTY; without even the implied warranty of MERCHANTABILITY or
# FITNESS FOR A PARTICULAR PURPOSE. See the GNU General Public License for more
# details. You should have received a copy of the GNU General Public License
# along with roofer. If not, see <https://www.gnu.org/licenses/>.

"""Reconstruct a synthetic gable roof house with the installed bindings."""

import random
import sys
import sysconfig
import unittest
from concurrent.futures import ThreadPoolExecutor

import roofer

WIDTH = 12.0  # along x, the ridge direction
DEPTH = 8.0  # along y
EAVE = 6.0
RIDGE = 9.0


def gable_house():
    """Roof points, ground points and the footprint of a gable roof house."""
    rng = random.Random(0)
    roof = []
    steps = 0.25
    for i in range(int(WIDTH / steps) + 1):
        for j in range(int(DEPTH / steps) + 1):
            x = i * steps
            y = j * steps
            z = RIDGE - (RIDGE - EAVE) * abs(y - DEPTH / 2) / (DEPTH / 2)
            roof.append([x, y, z + rng.uniform(-0.02, 0.02)])
    ground = []
    for i in range(-16, int(WIDTH / steps) + 17):
        for j in range(-16, int(DEPTH / steps) + 17):
            x = i * steps
            y = j * steps
            if -1 <= x <= WIDTH + 1 and -1 <= y <= DEPTH + 1:
                continue
            ground.append([x, y, rng.uniform(-0.02, 0.02)])
    footprint = [[[0.0, 0.0, 0.0], [WIDTH, 0.0, 0.0], [WIDTH, DEPTH, 0.0],
                  [0.0, DEPTH, 0.0]]]
    return roof, ground, footprint


def heights(meshes):
    return [p[2] for mesh in meshes for polygon in mesh for ring in polygon
            for p in ring]


def reconstruct(lod):
    roof, ground, footprint = gable_house()
    config = roofer.ReconstructionConfig()
    config.lod = lod
    return roofer.reconstruct(roof, ground, footprint, config)


class TestReconstruct(unittest.TestCase):

    def test_gil_stays_disabled(self):
        if sysconfig.get_config_var("Py_GIL_DISABLED"):
            self.assertFalse(sys._is_gil_enabled())

    def test_lod22_has_the_gable(self):
        meshes = reconstruct(22)
        self.assertEqual(len(meshes), 1)
        zs = heights(meshes)
        self.assertAlmostEqual(min(zs), 0.0, delta=0.1)
        self.assertAlmostEqual(max(zs), RIDGE, delta=0.2)
        eaves = [z for z in zs if abs(z - EAVE) < 0.2]
        self.assertTrue(eaves, "no vertex at the eaves")

    def test_lod12_and_lod13_are_flat(self):
        for lod in (12, 13):
            with self.subTest(lod=lod):
                meshes = reconstruct(lod)
                zs = heights(meshes)
                roof = {round(z, 3) for z in zs if z > 1.0}
                self.assertEqual(len(roof), 1, roof)
                self.assertTrue(EAVE < roof.pop() < RIDGE)

    def test_without_ground_points(self):
        roof, _, footprint = gable_house()
        meshes = roofer.reconstruct(roof, footprint)
        self.assertEqual(len(meshes), 1)
        self.assertAlmostEqual(max(heights(meshes)), RIDGE, delta=0.2)

    def test_triangulate_mesh(self):
        mesh = reconstruct(22)[0]
        vertices, faces = roofer.triangulate_mesh(mesh)
        self.assertGreater(len(faces), 0)
        for face in faces:
            self.assertEqual(len(set(face)), 3)
            for index in face:
                self.assertLess(index, len(vertices))

    def test_threads(self):
        # Plane detection seeds its region growing at random, so results may
        # differ slightly between calls: each is checked, not compared.
        with ThreadPoolExecutor(4) as pool:
            results = list(pool.map(reconstruct, [22] * 8))
        for meshes in results:
            self.assertEqual(len(meshes), 1)
            self.assertAlmostEqual(max(heights(meshes)), RIDGE, delta=0.2)


if __name__ == "__main__":
    unittest.main()
