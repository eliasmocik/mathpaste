-- mathpaste — Hammerspoon clipboard watcher
-- Append this to your ~/.hammerspoon/init.lua (create the file if it doesn't
-- exist), then reload Hammerspoon (menu-bar hammer icon -> Reload Config).
--
-- Just press plain Cmd+C on a selection that contains LaTeX. A moment later the
-- clipboard is enriched so pasting into Word gives native equations. Normal
-- text copies and non-math copies are left completely untouched.

local MATHPASTE = os.getenv("HOME") .. "/Desktop/personal_projects/mathpaste/mathpaste"
local POLL = 0.4  -- seconds between clipboard checks

-- Quick pre-filter: only spawn the converter when the copied text could plausibly
-- contain LaTeX (a \command, or ^/_ ). Keeps Python off the path for normal copies.
local function looksLikeMath(t)
    if not t then return false end
    if t:find("\\%a") then return true end   -- \frac, \int, \ln, ...
    if t:find("[%^_]") then return true end   -- superscripts / subscripts
    return false
end

local lastCC = hs.pasteboard.changeCount()
local busy = false

mathpasteWatcher = hs.timer.doEvery(POLL, function()
    if busy then return end
    local cc = hs.pasteboard.changeCount()
    if cc == lastCC then return end
    lastCC = cc

    if not looksLikeMath(hs.pasteboard.readString()) then return end

    busy = true
    hs.task.new(MATHPASTE, function(code, stdout, _stderr)
        lastCC = hs.pasteboard.changeCount()  -- swallow our own write (loop guard)
        busy = false
        if code == 0 and stdout and stdout:find("ready") then
            hs.alert.show("mathpaste ✓")
        end
    end, { "--auto" }):start()
end)
