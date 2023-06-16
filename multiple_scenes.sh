#!/bin/bash
for i in {1..20}
do
    open TDW.app;
    python occlusion_transition.py;
    sleep 5;
done