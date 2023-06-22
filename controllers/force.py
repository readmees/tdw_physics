import h5py
from enum import Enum
import random
from typing import List, Dict, Tuple
from weighted_collection import WeightedCollection
from tdw.controller import Controller
from tdw.tdw_utils import TDWUtils
from tdw.librarian import ModelRecord, ModelLibrarian
from tdw_physics.dataset import Dataset
from tdw_physics.rigidbodies_dataset import RigidbodiesDataset
from tdw_physics.util import get_args
import numpy as np
# bowl
# cone
# cube
# cylinder
# dumbbell
# octahedron
# pentagon
# pipe
# platonic
# pyramid
# sphere
# torus
# triangular_prism


class Force(RigidbodiesDataset):
    def __init__(self, port: int = 1071):
        Controller.MODEL_LIBRARIANS["models_core.json"] = ModelLibrarian("models_core.json")
        self.obj_names = []
        for record in Controller.MODEL_LIBRARIANS["models_core.json"].records:
            self.obj_names.append(record.name)
        self.obj_names = self.obj_names
        super().__init__(port=port)
        
    def get_field_of_view(self) -> float:
        ''' '''
        return 55

    def get_scene_initialization_commands(self) -> List[dict]:
        return [self.get_add_scene(scene_name="box_room_2018"),
                {"$type": "set_aperture",
                 "aperture": 4.8},
                {"$type": "set_post_exposure",
                 "post_exposure": 0.4},
                {"$type": "set_ambient_occlusion_intensity",
                 "intensity": 0.175},
                {"$type": "set_ambient_occlusion_thickness_modifier",
                 "thickness": 3.5}]

    def get_trial_initialization_commands(self) -> List[dict]:
        commands = []
        # Your code here.
        model_name = random.choice(["cube", "cylinder", "pentagon"])
        o_id = self.get_unique_id()
        scale = 1
    
        # Add the object with random physics values.
        commands = []
        commands.extend(self.get_add_physics_object(model_name=model_name,
                                                    library="models_flex.json",
                                                    object_id=o_id,
                                                    position={"x": random.uniform(-0.02, 0.02),
                                                              "y": 0,
                                                              "z": random.uniform(-0.02, 0.02)},
                                                    rotation={"x": 0,
                                                              "y": random.uniform(0, 360),
                                                              "z": 0},
                                                    default_physics_values=False,
                                                    scale_mass=False,
                                                    mass=random.uniform(2, 7),
                                                    dynamic_friction=random.uniform(0, 0.9),
                                                    static_friction=random.uniform(0, 0.9),
                                                    bounciness=random.uniform(0, 1),
                                                    scale_factor={"x": scale, "y": scale, "z": scale}))
        # Set a random color.
        a_pos = np.array([1, 1, 1])
        commands.extend([{"$type": "teleport_avatar_to",
                          "position": TDWUtils.array_to_vector3(a_pos)},
                         {"$type": "look_at_position",
                          "position": TDWUtils.array_to_vector3(np.array([0,0,0]))}])
        

    def get_per_frame_commands(self, resp: List[bytes], frame: int) -> List[dict]:
        return []

    def is_done(self, resp: List[bytes], frame: int) -> bool:
        return frame > 500


if __name__ == "__main__":
    args = get_args("force")
    Force().run(num=args.num, output_dir=args.dir, temp_path=args.temp, width=args.width, height=args.height)
