-- Skullcannon Rework: deploy-mode <-> shot-type synchroniser.
-- Runs in every battle (script/battle/mod autoload). Polls each Skullcannon:
--   mode  = siege iff the deploy phase killed its speed (fast_speed ~ 0)
--   shot  = siege iff missile_range > 400 (siege shell range 500 vs assault 280)
-- and issues change_shot_type only on mismatch. Steady state = zero orders,
-- so player/AI control is never disturbed.
local SKC_UNIT = "wh3_main_kho_veh_skullcannon_0"
local SKC_SHOT_ASSAULT = "artillery_default"
local SKC_SHOT_SIEGE = "artillery_explosive"
local SKC_RANGE_CUT = 400
local SKC_SPEED_CUT = 2

local skc_wrapped = {} -- unique_ui_id -> script_unit

local function skc_sync_one(army, unit)
	if not unit:is_valid_target() then
		return
	end
	local uid = unit:unique_ui_id()
	local su = skc_wrapped[uid]
	if not su then
		su = script_unit:new(unit, "skc_" .. tostring(uid))
		skc_wrapped[uid] = su
	end
	local ok_speed, spd = pcall(function() return su.unit:fast_speed() end)
	local ok_range, rng = pcall(function() return su.unit:missile_range() end)
	if not ok_speed or not ok_range then
		return
	end
	local want = nil
	if spd < SKC_SPEED_CUT then
		if rng < SKC_RANGE_CUT then want = SKC_SHOT_SIEGE end
	else
		if rng > SKC_RANGE_CUT then want = SKC_SHOT_ASSAULT end
	end
	if want then
		bm:out("skc_rework: unit " .. tostring(uid) .. " switching shot to " .. want)
		pcall(function() su.uc:change_shot_type(want) end)
	end
end

local function skc_sync()
	if not bm:is_conflict_phase() then
		return
	end
	for _, alliance in model_pairs(bm:alliances()) do
		for _, army in model_pairs(alliance:armies()) do
			for _, unit in model_pairs(army:units()) do
				if unit:type() == SKC_UNIT then
					local ok, err = pcall(skc_sync_one, army, unit)
					if not ok then
						bm:out("skc_rework error: " .. tostring(err))
					end
				end
			end
		end
	end
end

bm:repeat_callback(skc_sync, 2000, "skc_rework_sync")
