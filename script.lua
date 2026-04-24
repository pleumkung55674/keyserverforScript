-- 🔒 จุด 1
local a = hookfunction
if a then return end

local env = getfenv and getfenv() or _ENV
if env ~= _G then return end

-- 🔒 จุด 2
if debug and (debug.getinfo or debug.getupvalue or debug.setupvalue) then
    return
end

-- 🔒 จุด 3 (random trap)
if math.random(1,50) == 17 then return end

-- 🎮 loading notify
pcall(function()
    game.StarterGui:SetCore("SendNotification", {
        Title = "SlashHub",
        Text = "Loading...",
        Duration = 3
    })
end)

-- 🔒 จุด 4
if not game or not game.Players then return end

local ls = loadstring
if not ls or type(ls) ~= "function" then return end

-- 🔥 ===== เริ่มโค้ดจริง =====

print("🔥 SlashHub Loaded")

pcall(function()
    game.StarterGui:SetCore("SendNotification", {
        Title = "SlashHub",
        Text = "Welcome!",
        Duration = 5
    })
end)

print("🎮 Enjoy the game!")

for i = 1,5 do
    task.wait(0.2)
end



if hookfunction then
    while true do
        task.wait(1)
    end
end