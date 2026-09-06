-- Skullcannon Rework: foundry bonus reconciler (campaign).
-- T4 vehicle works (wh3_main_kho_vehicle_2) and T5 (wh3_main_kho_vehicle_3) grant
-- hidden bundles to the owning faction. Exactly ONE bundle ever applies per faction
-- (T5 wins over T4), so multiple buildings can never stack the bonus.
local SKC_BUNDLE_T4 = "skc_rework_foundry_t4"
local SKC_BUNDLE_T5 = "skc_rework_foundry_t5"
local SKC_BLD_T4 = "wh3_main_kho_vehicle_2"
local SKC_BLD_T5 = "wh3_main_kho_vehicle_3"

local skc_state = {} -- faction key -> "t4" / "t5" / nil

local function skc_has_building(faction, building_key)
	local ok, found = pcall(function()
		local region_list = faction:region_list()
		for i = 0, region_list:num_items() - 1 do
			local region = region_list:item_at(i)
			local rok, has = pcall(function() return region:building_exists(building_key) end)
			if rok and has then
				return true
			end
		end
		return false
	end)
	return ok and found
end

local function skc_reconcile(faction)
	if faction == nil or faction:is_null_interface() or faction:is_dead() then
		return
	end
	local fname = faction:name()
	local want = nil
	if skc_has_building(faction, SKC_BLD_T5) then
		want = "t5"
	elseif skc_has_building(faction, SKC_BLD_T4) then
		want = "t4"
	end
	if want == skc_state[fname] then
		return
	end
	pcall(function() cm:remove_effect_bundle(SKC_BUNDLE_T4, fname) end)
	pcall(function() cm:remove_effect_bundle(SKC_BUNDLE_T5, fname) end)
	if want == "t4" then
		pcall(function() cm:apply_effect_bundle(SKC_BUNDLE_T4, fname, 0) end)
	elseif want == "t5" then
		pcall(function() cm:apply_effect_bundle(SKC_BUNDLE_T5, fname, 0) end)
	end
	skc_state[fname] = want
end

core:add_listener(
	"skc_rework_foundry",
	"FactionTurnStart",
	function(context)
		local faction = context:faction()
		return faction ~= nil and not faction:is_null_interface()
	end,
	function(context)
		local ok, err = pcall(skc_reconcile, context:faction())
		if not ok and cm ~= nil then
			cm:out("skc_rework foundry error: " .. tostring(err))
		end
	end,
	true
)
