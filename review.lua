require("packages/rules")
require("packages/color")

-- TODO line numbers!

SILE.registerCommand("sout", function (_, content)
-- check if the underline code in rules package is different
    local hbox = SILE.call("hbox", {}, content)
    local gl = SILE.length() - hbox.width
    SILE.call("raise", {height = "0.5ex"}, function()
        SILE.call("hrule", {width = gl.length, height = "0.5pt"})
    end)
    SILE.typesetter:pushGlue({width = hbox.width})
end, "Strickeout some content (badly)")

SILE.registerCommand("hl", function (_, content)
    SILE.call("color", {color = "yellow"}, function()
        local hbox = SILE.call("hbox", {}, content)
        local gl = SILE.length() - hbox.width
        SILE.call("hrule", {width = gl.length, height = "1.5ex"})
    end)
    SILE.call("hbox", {}, content)
end, "Highlight content (badly)")

SILE.registerCommand("red", function (_, content)
    SILE.call("color", {color = "red"}, function()
        SILE.process(content)
    end)
end, "Color content red")

