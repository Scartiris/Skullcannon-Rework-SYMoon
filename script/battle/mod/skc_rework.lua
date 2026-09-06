-- Skullcannon Rework: transformation continuity bridge (ammo + HP).
-- Deploy/undeploy are native transformations (fresh unit entities). This script
-- runs every battle and carries ammo/HP across the swap so neither refills:
-- only EVER reduces the fresh form down to the recorded fraction (never buffs).
local SKC_ASSAULT = "wh3_main_kho_veh_skullcannon_0"
local SKC_SIEGE = "skc_rework_skullcannon_siege"
local SKC_TICK_MS = 2000
local SKC_PAIR_WINDOW_S = 8

local skc_known = {} -- "all:army:ui" -> {kind, ammo, hp, seen_tick}
local skc_tick = 0

local function skc_is_cannon(unit)
	local t = unit:type()
	return t == SKC_ASSAULT or t == SKC_SIEGE
end

local function skc_army_key(unit)
	return tostring(unit:alliance_index()) .. ":" .. tostring(unit:army_index())
end

local function skc_fractions(unit)
	local ammo, hp = 1, 1
	pcall(function()
		local max = unit:starting_ammo()
		if max and max > 0 then ammo = unit:ammo_left() / max end
	end)
	pcall(function() hp = unit:unary_hitpoints() end)
	return ammo, hp
end

local function skc_restore(unit, ammo, hp)
	pcall(function()
		local max = unit:starting_ammo()
		if max and max > 0 and unit:ammo_left() / max > ammo + 0.01 then
			unit:set_current_ammo_unary(ammo)
		end
	end)
	pcall(function()
		if unit:unary_hitpoints() > hp + 0.01 then
			unit:reduce_hitpoints_unary(1 - hp)
		end
	end)
end

local function skc_sync()
	skc_tick = skc_tick + 1
	if not bm:is_conflict_phase() then
		return
	end
	local ok, err = pcall(function()
		-- scan current cannons
		local current = {}
		for _, alliance in model_pairs(bm:alliances()) do
			for _, army in model_pairs(alliance:armies()) do
				for _, unit in model_pairs(army:units()) do
					if skc_is_cannon(unit) and unit:is_valid_target() then
						local id = skc_army_key(unit) .. ":" .. tostring(unit:unique_ui_id())
						local ammo, hp = skc_fractions(unit)
						current[id] = {kind = unit:type(), ammo = ammo, hp = hp, unit = unit}
					end
				end
			end
		end
		-- pair fresh arrivals with recent vanishings of the other form (same army)
		for id, cur in pairs(current) do
			local rec = skc_known[id]
			if not rec then
				local army_prefix = string.match(id, "^[^:]+:[^:]+:")
				local best_id, best_age = nil, SKC_PAIR_WINDOW_S + 1
				for vid, vrec in pairs(skc_known) do
					if not current[vid] and vrec.kind ~= cur.kind
						and string.sub(vid, 1, #army_prefix) == army_prefix then
						local age = (skc_tick - vrec.seen_tick) * SKC_TICK_MS / 1000
						if age < best_age then
							best_id, best_age = vid, age
						end
					end
				end
				if best_id then
					local donor = skc_known[best_id]
					bm:out("skc_rework: bridging " .. donor.kind .. " -> " .. cur.kind)
					skc_restore(cur.unit, donor.ammo, donor.hp)
					skc_known[best_id] = nil -- consume donor
				end
				skc_known[id] = {kind = cur.kind, ammo = cur.ammo, hp = cur.hp, seen_tick = skc_tick}
			else
				rec.ammo, rec.hp, rec.seen_tick = cur.ammo, cur.hp, skc_tick
			end
		end
	end)
	if not ok then
		bm:out("skc_rework error: " .. tostring(err))
	end
end

bm:repeat_callback(skc_sync, SKC_TICK_MS, "skc_rework_sync")
