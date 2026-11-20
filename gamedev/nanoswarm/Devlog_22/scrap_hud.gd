extends PanelContainer
class_name ScrapResourceHUD

var _scrap_ref : Scrap
@onready var value_lbl : Label = %ValueLbl

func _ready() -> void:
    # utility resource that holds all "unique" properties I want for now
	var campaign_data = GameManager.get_campaign_data()

	if campaign_data == null :
		push_error("Scrap HUD used outside of campaign context")
		return

	_scrap_ref = campaign_data.scrap
	_scrap_ref.on_value_changed.connect(on_resource_value_changed)
	
	_set_value(_scrap_ref.value)

func _set_value(value : int) -> void:
	value_lbl.text = "%s" % value

func on_resource_value_changed(new_value : int) -> void:
	_set_value(new_value)
