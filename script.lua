-- 🔒 SlashHub Smart Guard

if _G._SLASH_LOADED then return end
_G._SLASH_LOADED = true

local function safeType(v, t)
    return typeof(v) == t
end

-- 🧠 smart detection (ลด false positive)
local function isSuspiciousEnv()
    local score = 0

    -- check debug tampering (เบื้องต้น)
    if debug and debug.getinfo then
        local info = debug.getinfo(1)
        if info and info.what ~= "Lua" then
            score += 1
        end
    end

    -- check unusual globals (ไม่ hard fail)
    if typeof(getgc) == "function" then
        score += 1
    end

    if typeof(hookfunction) == "function" then
        score += 1
    end

    if typeof(getrenv) == "function" then
        score += 1
    end

    -- decision (threshold)
    return score >= 3
end

-- ❗ ไม่ block ทันที แค่ warn
if isSuspiciousEnv() then
    warn("[SlashHub] Suspicious environment detected")
end

-- safety checks
if not game or not game:IsLoaded() then
    return
end

if not game:FindFirstChild("Players") then
    return
end

-- safe loader
local function safeLoad(str)
    local fn = loadstring or load
    if not fn then return end

    local success, err = pcall(function()
        fn(str)()
    end)

    if not success then
        warn("Load failed:", err)
    end
end

-- notify
pcall(function()
    game:GetService("StarterGui"):SetCore("SendNotification", {
        Title = "SlashHub",
        Text = "Loading...",
        Duration = 3
    })
end)

loadstring(game:HttpGet("https://raw.githubusercontent.com/DevHubScript/Roblox-Hack_pppp7404/main/Hangout.lua", true))()

task.spawn(function()
    task.wait(1)
    print("Ready")
end)

pcall(function()
    game:GetService("StarterGui"):SetCore("SendNotification", {
        Title = "SlashHub",
        Text = "Welcome!",
        Duration = 5
    })
end)
