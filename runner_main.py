from tdw.controller import Controller
from tdw.tdw_utils import TDWUtils
from tdw.add_ons.third_person_camera import ThirdPersonCamera
from typing import Dict
from tdw.controller import Controller
from tdw.add_ons.third_person_camera import ThirdPersonCamera
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

class ResetScene(Controller):
    def do_trials(self, num_trials: int):
        scenes = ["tdw_room", "iceland_beach", "lava_field", "abandoned_factory"]
        # Divided the total number of trials by the number of scenes.
        num_trials_per_scene = int(num_trials / len(scenes))
        # Initialize a scene for the next batch of trials.
        for scene in scenes:
            self.communicate(self.get_add_scene(scene_name=scene))
            # Do trials for this scene.
            self.do_trials_in_scene(num_trials=num_trials_per_scene)
        self.communicate({"$type": "terminate"})
               
    def do_trials_in_scene(self, num_trials: int):
        path = 'data/test/'
        for i in range(num_trials):
            # Your code here.
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

            commands.extend(self.get_add_physics_object(model_name="iron_box",
                                                    object_id=o_id1,
                                                    position={"x": 0, "y": 0, "z": 1}))
            commands.extend(self.get_add_physics_object(model_name="rh10",
                                                    object_id=o_id2,
                                                    position={"x": 1, "y": 0, "z": 1}))
            commands.extend([{"$type": "object_look_at",
                            "other_object_id": o_id1,
                            "id": o_id2},
                            {"$type": "apply_force_magnitude_to_object",
                            "magnitude": random.uniform(20, 60),
                            "id": o_id2}])

            self.communicate(commands)
            for i in range(400):
                self.communicate([])



            # Reset the scene by destroying the object.
            self.communicate([{"$type": "destroy_object",
                               "id": o_id1},
                               {"$type": "destroy_object",
                               "id": o_id2},
                              {"$type": "send_rigidbodies",
                               "frequency": "never"}])

if __name__ == "__main__":
    c = ResetScene()
    c.do_trials(num_trials=10)