Sock = require("socket")

local cast_rays = function(ent, range, angle) -- end_pos = start_pos + dir (x, y, z) * range
    -- ent: entity object
    -- range: distance of the rays
    -- angle: view cone in radians

    -- temp
    local collFlag = false
    -- remove later

    local entPos = ent:get_pos()
    local entDir = ent:get_yaw()
    local half_angle = angle / 2
    local step = math.rad(3) -- Step size for raycasting (5 degrees in radians)
    local results = {}

    for offset = -half_angle, half_angle, step do
        local current_angle = entDir + offset

        local x, z = -1 * math.sin(current_angle), math.cos(current_angle)
        local dir = vector.new(x, 0, z)

        local end_pos = vector.add(entPos, vector.multiply(dir, range))
        local ray = minetest.raycast(vector.add(entPos, dir), end_pos, true, false)
        local coll = ray:next()

        -- temp
        if coll ~= nil then
            collFlag = true
            coll_new = { intersection_point = coll.intersection_point, coll_flag = 1 }
        else
            coll_new = { intersection_point = end_pos, coll_flag = 0 }
        end
        -- remove later

        table.insert(results, coll_new)
    end

    return results, collFlag
end

local format_data = function(entPos, entDir, data)
    -- Format the data in a / separated string to send over network
    local formatted_data = string.format("%d,%d,%d,%d/", entPos.x, entPos.y, entPos.z, entDir)
    -- Add the collision data
    for i, v in ipairs(data) do
        if v.coll_flag == 1 then
            print("Collision: " .. dump(v))
        end
        formatted_data = formatted_data .. string.format("%.1f,%.1f,%.1f,%d/", v.intersection_point.x, v.intersection_point.y, v.intersection_point.z, v.coll_flag)
    end

    return formatted_data
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
        local range = 1
		local speed = 5
        local ent = self.object
		local entPos = ent:get_pos()
		local entDir = ent:get_yaw()
        local res, collFlag = cast_rays(ent, range, math.rad(120)) -- 60 degrees view cone
		-- this entire condition will be removed later
        local dir = vector.new(-1 * math.sin(entDir), 0, math.cos(entDir))
        if collFlag then
            self.object:set_yaw(entDir + (2 * math.random() * math.pi))
        else
            self.object:move_to(vector.add(speed * dir * dtime, entPos))
        end
        -- send data to the server
        local formatted_data = format_data(entPos, entDir, res)
        local err = self._client:send(formatted_data)
        if err ~= nil then
            print("Data sent: " .. formatted_data)
        else
            print("Data send failed")
        end
        -- receive data from the server
        self._client:settimeout(0)
        local ready_to_read, _, err = Sock.select({self._client}, nil, 0)
        for _, sock in ipairs(ready_to_read) do
            print(dump(sock))
            if sock == self._client then
                local data, err, partial = self._client:receive()
                if data then
                    print("Data received: " .. data)
                elseif err ~= "timeout" then
                    print("Receive error:", err or "unknown")
                end
            end
        end

    end
})
