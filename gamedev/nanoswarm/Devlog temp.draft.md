scaffold:
- ~~new "defenses" node in city scene for organization purposes~~
- ~~new "health", "enemy data" "turret data" resources. turret scene adapted; health_bar scene adapted~~
- ~~added "attack range" and "detection range" to turret (with some prop changes for isometric)~~****
- ~~(wip) copied look and shoot logic from dummy turret unto turret node~~
- tile set > new navigation layer for "road" tiles; test path follower using NavigationAgent2D
- testing out pathing with dummy path follower and repurposing original swarm unit
- small adjust to the swarm unit to use the basic avoidance option of the nav agent
- adjusted the ground tile's y sort origin to allow swarm unit to render behind buildings
- [test] two ground layers (one for road tiles, one for everything else) + two navigation layers to feed into two nav regionsfor better nav with cost in mind