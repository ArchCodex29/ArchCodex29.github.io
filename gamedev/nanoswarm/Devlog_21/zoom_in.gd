var _zooming : bool = false

func _zoom_in_on_poi(poi: StaticBody2D) -> void:
	_zooming = true

    # This version makes it zoom in directly on the PoI, resulting in it being in the center of the screen
    # var target_position = poi.position

    # This version makes it zoom in on a place next to the PoI, resulting in it being on the right. Controllable with a Marker2D node
	var target_position = poi.position - (_zoom_marker.position - _center)

	var tween = get_tree().create_tween().set_parallel(true)
	tween.tween_property(_camera, "zoom", Vector2(2.0, 2.0), 0.25)
	tween.tween_property(_camera, "position", target_position, 0.25)
	tween.tween_callback(_level_card.show).set_delay(0.25)