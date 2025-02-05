# Swarm Exploration (Tentative Name)

## Simulation Setup in Luanti

The <main_exploration> code comes with a test-bed setup in [luanti](https://www.luanti.org/), which is an open-source voxel game-engine that allows easy mod configuration. The modding script is in Lua.

Having Lua and Luanti is a pre-requisite. Once both of them are downloaded, follow the steps below to properly setup the mod to test the <algorithm>.

1. Make the mods directory if it does not exist following the [Where are mods stored?](https://rubenwardy.com/minetest_modding_book/en/basics/getting_started.html) documentation. This dir will now be reffered to as the <mods_dir>
2. Create a symlink of sim folder to the <mods_dir> named as <lidar_sim>. On Unix systems it can be done via `ln -s <path_to_sim>/sim <mods_dir>/lidar_sim`. Please make sure to provide the absolute path to the sim directory.
3. As our mod uses external lua libraries, we need to either add our mod to the trusted mods list or disable mod security. This can be done via editing the minetest.cof file, which which is in the same dir as <mods_dir>. Add `secure.trusted_mods = lidar_sim` and only if that doesn't seem to work, disable mods security via `secure.enable_security = false`. NOTE: Disabling mod security runs the risk of running untrusted mods ANYTHING they would like to run. Make sure all the installed mods are trusted.
4. Our mod utliises the`LuaSocket` library to establish connection with the comms network. We can install it either using LuaRocks or install it directly. This tutorial assumes you choose to install it via LuaRocks.
    1. Install [LuaRocks](https://github.com/luarocks/luarocks/wiki/Download#installing)
    2. Install LuaSocket for the version of Lua that your Luanti runs on, via `luarocks install luasocket --lua-version=<your_lua_version>`.
        1. To check whether your Luanti runs on Lua or LuaJIT, run: `Luanti --version | grep Using`
        2. Depending on what it uses, run lua or luajit on your terminal and execute the following `print(_VERSION)` to know the version of your lua.
    3. Add <LUA_PATH> and <LUA_CPATH> to your environment variables and you're set to go.
        1. To find your <LUA_PATH> and <LUA_CPATH>, run `luarocks show luasocket --lua-version=<your_lua_version>`
         2. `LUA_PATH=<SOME/PATH>/share/lua/<VERSION>/?.lua` and `LUA_CPATH=<SOME/PATH>/lib/lua/<VERSION>/?.so`
