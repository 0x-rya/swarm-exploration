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

print("Mod Loaded")

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
        _steps = 0,
		_client = nil
    },
    on_activate = function(self, staticdata, dtime_s)

		-- connect to the communication network server
		self._client = Sock.connect("127.0.0.1", 8000)
		local err = self._client:send("Connection Established")
		if err ~= nil then
			print("Connection Established")
		else
			print("Connection Failed")
		end
		print(self._client.object)

    end,

    on_step = function (self, dtime, moveresult)
        local range = 2
		local speed = 2
        local ent = self.object
		local entPos = ent:get_pos()
		local entDir = ent:get_yaw()
        local coll, dir = cast_ray(ent, range)
		if coll ~= nil then
        	local dist = vector.subtract(entPos, coll.intersection_point)

			-- data sending protocol

			self._client:send(
				string.format(
					"%d,%d,%d,%d/%.1f,%.1f,%.1f/%d",	-- d, d, d ent pos and f, f, f dist and d obj
					entPos.x,
					entPos.y,
					entPos.z,
					entDir,
					coll.intersection_point.x,
					coll.intersection_point.y,
					coll.intersection_point.z,
					1
				)
			)

        	print(dist)

            self.object:set_yaw(entDir + 1.71)
        else
			local end_pos = vector.add(entPos, vector.multiply(dir, range))
            self.object:move_to(vector.add(speed * dir * dtime, entPos))
			
			self._client:send(
				string.format(
					"%d,%d,%d,%d/%.1f,%.1f,%.1f/%d",	-- d, d, d ent pos and f, f, f dist and d no obj
					entPos.x,
					entPos.y,
					entPos.z,
					entDir,
					end_pos.x,
					end_pos.y,
					end_pos.z,
					0
				)
			)
		end
    end
})
