-- 🔒 SlashHub Guard (Lite Protection)

-- กัน environment แปลก
if _G._SLASH_LOADED then return end
_G._SLASH_LOADED = true

-- เช็ค basic exploit env
local function isExploitEnv()
    if hookfunction or getgc or getrenv or getfenv ~= nil then
        return true
    end
    return false
end

if isExploitEnv() then
    warn("Exploit environment detected")
    return
end

-- ป้องกัน debug hook เบื้องต้น
pcall(function()
    if debug and debug.getinfo then
        local info = debug.getinfo(1)
        if info and info.what ~= "Lua" then
            return
        end
    end
end)

-- safety check
if not game or not game:IsLoaded() then
    return
end

if not game:FindFirstChild("Players") then
    return
end

-- โหลด function safe
local function safeLoad(str)
    local fn = loadstring or load
    if not fn then return end

    local success, result = pcall(fn(str))
    if not success then
        warn("Load failed")
    end
end

-- notify (safe)
pcall(function()
    game:GetService("StarterGui"):SetCore("SendNotification", {
        Title = "SlashHub",
        Text = "Loading...",
        Duration = 3
    })
end)

-- 🔥 ===== SCRIPT REAL START =====
-- ใส่โค้ดมึงตรงนี้

print("SlashHub Loaded")

task.spawn(function()
    wait(1)
    print("Ready")
end)

-- notify finish
pcall(function()
    game:GetService("StarterGui"):SetCore("SendNotification", {
        Title = "SlashHub",
        Text = "Welcome!",
        Duration = 5
    })
end)