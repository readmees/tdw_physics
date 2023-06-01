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


class Empty(RigidbodiesDataset):
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
      
        return commands

    def get_per_frame_commands(self, resp: List[bytes], frame: int) -> List[dict]:
        return []

    def is_done(self, resp: List[bytes], frame: int) -> bool:
        return frame > 500


if __name__ == "__main__":
    args = get_args("empty")
    Empty().run(num=args.num, output_dir=args.dir, temp_path=args.temp, width=args.width, height=args.height)
