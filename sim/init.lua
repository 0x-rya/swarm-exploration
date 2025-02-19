Sock = require("socket")

local cast_ray = function(ent, range) -- end_pos = start_pos + dir (x, y, z) * range    entity should calculate this and send it here

	--[[ (x, y, z)
		x - sin
		z - cos
			360 -> (0, 0, 1)
			180 -> (0, 0, -1)
			90  -> (-1, 0, 0)
			270 -> (1, 0, 0)
	]]

	local entPos = ent:get_pos()
	local entDir = ent:get_yaw()

	local x, z = -1 * math.sin(entDir), math.cos(entDir)
	local dir = vector.new(x, 0, z)

    local end_pos = vector.add(entPos, vector.multiply(dir, range))
    local ray = minetest.raycast(vector.add(entPos, dir), end_pos, true, false)
    return ray:next(), dir

end

minetest.register_entity("lidar_sim:castor", {
    initial_properties = {
        physical = true,
        collide_with_objects = true,
        selectionbox = { -0.5, -0.5, -0.5, 0.5, 0.5, 0.5, rotate = true },
        pointable = true,
        visual = "cube",
        visual_size = {x = 1, y = 1, z = 1},
        is_visible = true,
        -- automatic_rotate = 0,
        automatic_rotate = 0,
        shaded = true,
        show_on_minimap = true,
        _steps = 0
    },
    on_activate = function(self, staticdata, dtime_s)

		-- spawn server and establish connection with that server

    end,

    on_step = function (self, dtime, moveresult)
        -- ent
        local range = 2
		local speed = 2
        local ent = self.object
		local entPos = ent:get_pos()
		local entDir = ent:get_yaw()
        local coll, dir = cast_ray(ent, range)
		if coll ~= nil then
        	local dist = vector.subtract(entPos, coll.intersection_point)
        	print(dist)
            self.object:set_yaw(entDir + 1.71)
        else
            self.object:move_to(vector.add(speed * dir * dtime, entPos))

		end

        print("dtime", dtime)
    end
})
