-- mathpaste — convert LaTeX on the clipboard into a native Word equation, and paste it.
--
-- Hotkey: ⌘⇧V (command + shift + V) — your "math paste".
-- Flow: copy LaTeX normally with Cmd+C, then press ⌘⇧V in Word (or Mail, etc.).
-- It converts the clipboard and pastes in one step. If the clipboard has no
-- math it just pastes as-is, so ⌘⇧V is always a safe paste. Cmd+C is never
-- intercepted, so ordinary copying is untouched.
--
-- Pasting synthesizes Cmd+V, which needs Accessibility permission for
-- Hammerspoon (System Settings > Privacy & Security > Accessibility).

local PYTHON = os.getenv("HOME") .. "/.mathpaste/.venv/bin/python"
local SCRIPT = os.getenv("HOME") .. "/.mathpaste/mathpaste.py"

hs.accessibilityState(true)  -- prompt for the permission if it isn't granted yet

hs.hotkey.bind({"cmd", "shift"}, "v", function()
    local task = hs.task.new(PYTHON, function()
        -- Clipboard is now converted (or left as-is if there was no math).
        -- Small delay so the physically-held ⌘⇧ have lifted before we send ⌘V,
        -- otherwise the shift can bleed in and fire Paste-Special instead.
        hs.timer.doAfter(0.06, function()
            hs.eventtap.keyStroke({"cmd"}, "v", 0)
        end)
    end, {SCRIPT})
    task:start()
end)
