# STATUS: Not finished
'''
Readme:
The core of of this code is taken from tdw_physics

Possible improvements:
Shaking doesn't work yet
Freeze y-axis; probably not necessary with 'new' containment idea
'''
from typing import List
from random import choice, uniform
from tdw.tdw_utils import TDWUtils
from tdw.controller import Controller
from tdw.librarian import ModelLibrarian
from tdw_physics.rigidbodies_dataset import RigidbodiesDataset
from tdw_physics.physics_info import PHYSICS_INFO
from tdw_physics.util import get_args
from tdw.add_ons.third_person_camera import ThirdPersonCamera

from helpers.runner_main import Runner
from helpers.objects import CONTAINERS, CONTAINED
class Containment(Runner):
    """
    Create a set of "Containment" trials, where a container object holds a smaller target
    object and is shaken violently, causing the target object to move around and possibly fall out.
    """

    Controller.MODEL_LIBRARIANS["models_core.json"] = ModelLibrarian("models_core.json")
    
    O_X = -1.3
    O_Z = -2.15

    def __init__(self, port: int = 1071):
        super().__init__(port=port)

        self.controller_name = 'containment'

        for key in PHYSICS_INFO:
            # All containers have the same physics values. Set these manually.
            if key in Containment.CONTAINERS:
                PHYSICS_INFO[key].mass = 3

        # Commands to shake the container per frame.
        self._shake_commands: List[List[dict]] = []
        self._max_num_frames: int = 0

    def set_camera(self):
        # Add camera
        camera = ThirdPersonCamera(position={"x": -0.625, "y": 2.0, "z": -0.7},
                           look_at={"x": -1.0, "y": 1.0, "z": -1.5},
                           avatar_id=self.controller_name)
        self.add_ons.append(camera)

    def trial_initialization_commands(self):
        commands = []
        # Select a container.
        # Manually set the mass of the container.
        container_name = choice(CONTAINERS)
        container_scale = TDWUtils.get_unit_scale(PHYSICS_INFO[container_name].record) * 0.6
        container_id = self.get_unique_id()
        commands.extend(self.get_add_physics_object(model_name=container_name,
                                                    library="models_core.json",
                                                    object_id=container_id,
                                                    position={"x": Containment.O_X,
                                                              "y": 0.25,
                                                              "z": Containment.O_Z},
                                                    rotation=TDWUtils.VECTOR3_ZERO,
                                                    scale_factor={"x": container_scale,
                                                                  "y": container_scale,
                                                                  "z": container_scale}))
        
        # Add a random target object, with random size, mass, bounciness and initial orientation.
        object_name = choice(CONTAINED)
        o_id = self.get_unique_id()
        o_record = Controller.MODEL_LIBRARIANS["models_core.json"].get_record(object_name)
        o_scale = TDWUtils.get_unit_scale(o_record) * uniform(0.2, 0.3)
        self.o_ids = [o_id, container_id]
        commands.extend(self.get_add_physics_object(model_name=o_record.name,
                                                    library="models_core.json",
                                                    object_id=o_id,
                                                    position={"x": Containment.O_X,
                                                              "y": 0.6,
                                                              "z": Containment.O_Z},
                                                    rotation={"x": uniform(0, 360),
                                                              "y": uniform(0, 360),
                                                              "z": uniform(0, 360)},
                                                    default_physics_values=False,
                                                    scale_mass=False,
                                                    mass=uniform(0.1, 0.5),
                                                    dynamic_friction=uniform(0.1, 0.5),
                                                    static_friction=uniform(0.1, 0.5),
                                                    bounciness=uniform(0.5, 0.95),
                                                    scale_factor={"x": o_scale, "y": o_scale, "z": o_scale}))

        return commands

if __name__ == "__main__":
    c = Containment()
    success = c.run(num=5, pass_masks=['_img'] , room='empty', tot_frames=800, add_slope=False, trial_type='object')
    print(success)