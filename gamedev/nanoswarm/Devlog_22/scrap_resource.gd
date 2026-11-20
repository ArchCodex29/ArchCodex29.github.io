extends Resource
class_name Scrap

signal on_value_changed(new_value : int)

@export var value : int

func add(amount: int) -> void:
	value += amount
	on_value_changed.emit(value)

# create other methods as you see fit