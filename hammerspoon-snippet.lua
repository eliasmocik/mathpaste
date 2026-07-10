-- mathpaste — Hammerspoon binding
-- Append this to your ~/.hammerspoon/init.lua (create the file if it doesn't
-- exist), then reload Hammerspoon (menu-bar icon -> Reload Config).
--
-- Copy LaTeX  ->  press Cmd+Alt+M  ->  paste into Word.

local MATHPASTE = os.getenv("HOME") .. "/Desktop/personal_projects/mathpaste/mathpaste"

hs.hotkey.bind({"cmd", "alt"}, "M", function()
    local out, ok = hs.execute(MATHPASTE, true) -- true = run in a login shell
    if ok then
        hs.alert.show("mathpaste ✓  paste into Word")
    else
        hs.alert.show("mathpaste failed:\n" .. (out or "unknown error"))
    end
end)
