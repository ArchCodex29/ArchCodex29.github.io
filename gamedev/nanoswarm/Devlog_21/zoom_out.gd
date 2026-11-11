# on click event, binded to the close button on the LevelInfoCard
func _on_city_level_cancel() -> void:
	if !_zooming: return
	
	_zoom_out_to_map()

func _zoom_out_to_map() -> void:
	_zooming = false

    # _center = original camera position. stored in _ready() function

	var tween = get_tree().create_tween().set_parallel(true)
	tween.tween_property(_camera, "zoom", Vector2(1.0, 1.0), 0.25)
	tween.tween_property(_camera, "position", _center, 0.25)
	tween.tween_callback(_level_card.hide).set_delay(0.25)