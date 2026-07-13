-- mathpaste — convert LaTeX on the clipboard into native Word equations.
--
-- Hotkey: ⌘⌥C (left command + option + c).
-- Flow: copy LaTeX (e.g. from ChatGPT) with a normal Cmd+C, press ⌘⌥C to
-- convert the clipboard in place, then paste with Cmd+V. Cmd+C itself is never
-- intercepted, so ordinary copying is always safe.

local PYTHON = os.getenv("HOME") .. "/.mathpaste/.venv/bin/python"
local SCRIPT = os.getenv("HOME") .. "/.mathpaste/mathpaste.py"

hs.hotkey.bind({"cmd", "alt"}, "c", function()
    local task = hs.task.new(PYTHON, function(code, stdout, stderr)
        local msg = ((stdout or "") .. (stderr or "")):gsub("^%s+", ""):gsub("%s+$", "")
        if msg == "" then
            msg = (code == 0) and "clipboard converted" or "nothing to convert"
        end
        -- strip the "mathpaste: " prefix the CLI prints, for a cleaner toast
        msg = msg:gsub("^mathpaste:%s*", "")
        hs.notify.new({title = "mathpaste", informativeText = msg}):send()
    end, {SCRIPT})
    task:start()
end)
