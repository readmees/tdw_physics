from tdw.controller import Controller
from tdw.tdw_utils import TDWUtils
from tdw.add_ons.third_person_camera import ThirdPersonCamera
from typing import Dict
from tdw.add_ons.collision_manager import CollisionManager
from tdw.add_ons.object_manager import ObjectManager

# Added for video
from tdw.add_ons.image_capture import ImageCapture
from tdw.backend.paths import EXAMPLE_CONTROLLER_OUTPUT_PATH
from os import chdir, system
from subprocess import call
import shutil

# Added for collisions
import random
import numpy as np

# From &tdw_physics
from typing import List, Dict
from tdw.librarian import ModelLibrarian
from typing import Dict
from helpers import ObjectInfo, get_random_avatar_position

class Collision(Controller):
    """
    Per trial, create 2-3 objects. Apply a force to one of them, directed at another.
    Per frame, save object/physics metadata and image data.
    """

    def __init__(self):
        lib = ModelLibrarian('models_core.json')
        self.records = lib.records
        # self.records = {record.name:record for record in lib.records}
        self._target_id: int = 0
        super().__init__(port=1071)


    def collision_force(self, commands):
        num_objects = random.choice([2, 3])
        # Positions where objects will be placed (used to prevent interpenetration).
        objects_info = []

        # Randomize the order of the records and pick the first one.
        # This way, the objects are always different.
        random.shuffle(self.records)

        # Add 2-3 objects.
        for i in range(num_objects):
            o_id = Controller.get_unique_id()
            record = self.records[i]

            # Set randomized physics values and update the physics info.
            scale = TDWUtils.get_unit_scale(record) * random.uniform(0.8, 1.1)

            # Get a random position.
            o_pos = self._get_object_position(objects_info=objects_info)

            # Add the object and the radius, which is defined by its scale.
            objects_info.append(ObjectInfo(position=o_pos, radius=scale, id=o_id))

            commands.extend(self.get_add_physics_object(model_name=self.records[i].name,
                                                        library="models_full.json",
                                                        object_id=o_id,
                                                        position=self._get_object_position(
                                                            objects_info=objects_info),
                                                        rotation={"x": 0, "y": random.uniform(-90, 90), "z": 0},
                                                        default_physics_values=False,
                                                        mass=random.uniform(1, 5),
                                                        scale_mass=False,
                                                        dynamic_friction=random.uniform(0, 0.9),
                                                        static_friction=random.uniform(0, 0.9),
                                                        bounciness=random.uniform(0, 1),
                                                        scale_factor={"x": scale, "y": scale, "z": scale}))
        # Point one object at the center, and then offset the rotation.
        # Apply a force allow the forward directional vector.
        # Teleport the avatar and look at the object that will be hit. Then slightly rotate the camera randomly.
        # Listen for output data.
        force_id = objects_info[0].id
        self._target_id = objects_info[1].id 
        commands.extend([{"$type": "object_look_at",
                          "other_object_id": self._target_id,
                          "id": force_id},
                         {"$type": "rotate_object_by",
                          "angle": random.uniform(-5, 5),
                          "id": force_id,
                          "axis": "yaw",
                          "is_world": True},
                         {"$type": "apply_force_magnitude_to_object",
                          "magnitude": random.uniform(20, 60),
                          "id": force_id},
                         {"$type": "teleport_avatar_to",
                          "position": get_random_avatar_position(radius_min=0.9, radius_max=1.5, y_min=0.5,
                                                                      y_max=1.25, center=TDWUtils.VECTOR3_ZERO)},
                         {"$type": "look_at",
                          "object_id": self._target_id,
                          "use_centroid": True},
                         {"$type": "rotate_sensor_container_by",
                          "axis": "pitch",
                          "angle": random.uniform(-5, 5)},
                         {"$type": "rotate_sensor_container_by",
                          "axis": "yaw",
                          "angle": random.uniform(-5, 5)},
                         {"$type": "focus_on_object",
                          "object_id": self._target_id}])
        return commands

    @staticmethod
    def _get_object_position(objects_info: List[ObjectInfo], max_tries: int = 1000, radius: float = 2) -> \
            Dict[str, float]:
        """
        Try to get a valid random position that doesn't interpentrate with other objects.

        :param objects_info: The positions and radii of all objects so far that will be added to the scene.
        :param max_tries: Try this many times to get a valid position before giving up.
        :param radius: The radius to pick a position in.

        :return: A valid position that doesn't interpentrate with other objects.
        """

        o_pos = TDWUtils.array_to_vector3(TDWUtils.get_random_point_in_circle(center=np.array([0, 0, 0]),
                                                                              radius=radius))
        # Pick a position away from other objects.
        ok = False
        count = 0
        while not ok and count < max_tries:
            count += 1
            ok = True
            for o in objects_info:
                # If the object is too close to another object, try another position.
                if TDWUtils.get_distance(o.position, o_pos) <= o.radius:
                    ok = False
                    o_pos = TDWUtils.array_to_vector3(TDWUtils.get_random_point_in_circle(center=np.array([0, 0, 0]),
                                                                                          radius=radius))
        return o_pos


    def trial(self, path):
            '''
            param path: "Images will be save to here"'''
            # Clear the list of add-ons.
            self.add_ons.clear()

            # Add camera
            camera = ThirdPersonCamera(position={"x": 2, "y": 1.6, "z": -1},
                            look_at={"x": 0, "y": 0, "z": 0},
                            avatar_id="collision")
            self.add_ons.append(camera)
    
            # Remove previous images and videos
            try:
                shutil.rmtree(f'{path}collision/')
            except FileNotFoundError:
                pass
            
            # Save output images/frames for video
            self.add_ons.append(ImageCapture(path=path, avatar_ids=["collision"]))
            
            # Create room and set target framerate
            commands = [TDWUtils.create_empty_room(12, 12),
                        {"$type": "set_target_framerate",
                    "framerate": 30}]
            o_id1 = self.get_unique_id()
            o_id2 = self.get_unique_id()

            commands = self.collision_force(commands)
            print('hmm')
            for i, command in enumerate(commands[15:]):
                print('Command is ', i)
                print(command)
            self.communicate(commands[:15])
            print('hmm1')
            for i in range(400):
                self.communicate([])

            self.communicate({"$type": "terminate"})

if __name__ == "__main__":
    c = Collision()
    path = 'data/'
    success = c.trial(path)
    print('succes:', success)

    # Change directory.
    # chdir(str(path.joinpath("a").resolve()))

    # Call ffmpeg to make video
    call(["ffmpeg",
        "-i", f"{path}collision/"+"img_%04d.jpg",
        "-vcodec", "libx264",
        "-pix_fmt", "yuv420p",
        f"{path}collision/"+"image_only_video.mp4"])