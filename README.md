# TDW Trials
Implements automated generation of object, agent and transition based videos in TDW
Note: internet connection needed

## Object based trials
- Collision trials (at least two objects collide)
- Permanence trials (object rolls behind occluder and then returns on other side)
- Containment trials (object is contained in larger container object and container is shaken -> object might or might not fall out of the container)
- Rolling down a slope

## Transition trials
- Object avoids collision ("moves out of the way")
- Permanence trials (after initial pause, object "hides behind occluder")
- Containment trials (object jumps out after a while "because it is too shaky")
- Rolling back up the slope after a while

## Agent trials
- agent seeks collision/touch (moves around obstacles in non-straight line to meet red target object)
- red target object moves behind occluder, agent follows after a while
- both red target object and agent are inside container, shaken. The agent tries to compensate for the shaking and seeks to touch the red target object. If the red target object leaves the container, so does the agent to follow.
- after initial pause, the agent rolls up a slope to meet the red target object at the top

Segmentation and other data available by specifying pass masks see: https://github.com/threedworld-mit/tdw/blob/master/Documentation/api/command_api.md#set_pass_masks

## Install and run tdw_trials
1. Create conda environment
```
conda create --name tdw_trials python=3.11
conda activate tdw_trials
```
3. Install requirements:
```pip install -r requirements.txt```
4. Download TDW.app
5. Run controller in controller folder
```
cd controllers
 open TDW.app;python <controller_name>.py
```
5. Might have to run again:
 ```open TDW.app;python occlusion.py```
## Copyright
A lot of this code is from the [tdw_physics](https://github.com/alters-mit/tdw_physics) repository, Copyright (c) 2021 Seth Alter

## Notes
- Not all the scenes are tested, trials are tested in empty room, so objects might spawn in walls etc. or empty frames mith be 

## TODO
- ~~Streamline platform~~
- Object based trials first version
- Transition based trials first version
- Agent based trials first version
- Chose better models
- Make a objectshower or use the TDW objectshower
- Implement rolling down controller
- Improve occlusion: don't stop behind object, but behind object in line with camera angle
- Improve occlusion: in objectbased, use force
- Improve containment: fix object
