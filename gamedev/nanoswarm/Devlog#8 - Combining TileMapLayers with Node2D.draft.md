# Combining TileMapLayers with Node2D

scaffold: 
- new CityGen scene to isolate/move the test HUD logic out of the core City scene
- (sandbox) sample isometric turret with proper y sort with tilemaplayers
- further testing. looks like that, for taller turrets, it "needs" to be placed as child of the corresponding height
- configuring tileset's sample tiles with y sort; testing spawning turret instance via code
- changed approach for turret visual placement. position/spawn based (no longer need the per tile y sort)
- turret hitbox pos
- new "defenses" node in city scene for organization purposes