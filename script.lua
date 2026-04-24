-- 🔒 SlashHub Smart Guard

if _G._SLASH_LOADED then return end
_G._SLASH_LOADED = true

local function safeType(v, t)
    return typeof(v) == t
end

-- 🧠 smart detection (ลด false positive)
-- 🧠 smart detection (no false positive version)
local function isSuspiciousEnv()
    local score = 0

    -- 🔹 check debug integrity only (safe)
    if debug and debug.getinfo then
        local ok, info = pcall(function()
            return debug.getinfo(1)
        end)

        if ok and info and info.what ~= "Lua" then
            score += 1
        end
    end

    -- 🔹 check if game environment broken
    if not game or not game:IsLoaded() then
        score += 1
    end

    if not game:GetService("Players") then
        score += 1
    end

    -- 🔹 optional: weird execution timing check
    if tick and os.clock and math.abs(tick() - os.clock()) > 100000 then
        score += 1
    end

    -- threshold สูงขึ้น ลด false positive
    return score >= 3
end

-- ❗ soft warning only
local suspicious = isSuspiciousEnv()

if suspicious then
    warn("[SlashHub] Suspicious environment detected (soft flag)")
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
end)-- 🔒 SlashHub Smart Guard

if _G._SLASH_LOADED then return end
_G._SLASH_LOADED = true

local function safeType(v, t)
    return typeof(v) == t
end

-- 🧠 smart detection (ลด false positive)
-- 🧠 smart detection (no false positive version)
local function isSuspiciousEnv()
    local score = 0

    -- 🔹 check debug integrity only (safe)
    if debug and debug.getinfo then
        local ok, info = pcall(function()
            return debug.getinfo(1)
        end)

        if ok and info and info.what ~= "Lua" then
            score += 1
        end
    end

    -- 🔹 check if game environment broken
    if not game or not game:IsLoaded() then
        score += 1
    end

    if not game:GetService("Players") then
        score += 1
    end

    -- 🔹 optional: weird execution timing check
    if tick and os.clock and math.abs(tick() - os.clock()) > 100000 then
        score += 1
    end

    -- threshold สูงขึ้น ลด false positive
    return score >= 3
end

-- ❗ soft warning only
local suspicious = isSuspiciousEnv()

if suspicious then
    warn("[SlashHub] Suspicious environment detected (soft flag)")
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
