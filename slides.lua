-- TODO: hyperlinks to sections
-- 2021-10-01   using a big stretchable skip instead of vfills in lists
-- 2021-09-30   insert a vfill before the first \litem of a slide
-- 2021-09-27   hyperlinks in header, TOC, bookmarks/outline
-- 2021-09-24   breakframevertical fix slides with a title and more than one column
-- 2021-09-13   fixes in slides with multiple columns
-- 2021-06-30   fixed frames; changed ruleFolios size and position
-- 2020-01-19   bg and header fixes
-- 2020-01-18   ruleFolios, section altnames
-- 2020-01-17   litems, title, color, -slide2 (use makecolumns)
-- 2020-01-16   slide2(=2cols), header, folio, background
-- 2020-01-15   slide0(=section), slide1(=slide), logfile

local plain = SILE.require("plain", "classes")
local slides = plain { id = "slides" }

local sectionName = "Presentation"
local slideName = ""
local isNewSection = true
local isNewSlide   = true

SILE.require("packages/color")
SILE.require("packages/folio")
SILE.require("packages/frametricks")
SILE.require("packages/image")
SILE.require("packages/rules")
SILE.require("packages/url")

--defaults:
--  ruleFolios=false
--  noTransitionSlides=false

--SILE.documentState.paperSize = SILE.paperSizeParser("5.04in x 3.78in")

slides.defaultFrameset = {
    content = {
        left   =  "5%pw",
        right  = "95%pw",
        top    =  "5%ph",
        bottom = "97%ph"
    },
    folio = {
        left   =  "5%pw",
        right  = "95%pw",
        top    = "98%ph",
        bottom = "100%ph"
    },
    runningHead = {
        left   =  "5%pw",
        right  = "95%pw",
        top    =  "1%ph",
        bottom =  "5%ph"
    },
    root = {   -- used to display a background image
        left   =   "0%pw",
        right  = "100%pw",
        top    =   "-6pt",  -- FIXME: 1st slide is displaced; using a 'cr' in each new one
        bottom = "100%ph"
    }
}

--slides.pageTemplate.firstContentFrame = slides.pageTemplate.frames["content"]
slides.firstContentFrame = "content"

logfile = SILE.masterFilename .. '.out'

slides.init = function (self)
-- read file.out if exists
    fileID = io.open(logfile, "r")
    headers = {}
    if fileID  ~= nil then
        for line in io.lines(logfile) do
            table.insert(headers,line)
        end
        io.close(fileID)
        totalPages = headers[#headers]
        table.remove(headers,idx)
    end
-- clear file.out
    fileID = io.open(logfile, "w")
    fileID:close()

    SILE.call("nofoliosthispage")
    SILE.settings.set("document.lineskip","1ex")
    SILE.settings.set("document.parskip","1ex")
    SILE.settings.set("document.parindent","0pt")
    return plain.init(self)
end


slides.newPage = function (self)
--  SILE.call("rootImage")
    return plain.newPage(self)
end

slides.finish = function ()
    fileID = io.open(logfile, "a")
    fileID:write(SILE.formatCounter(SILE.scratch.counters.folio) .. "\n")
    fileID:close()
    return plain.finish(slides)
end

SILE.registerCommand("running-head", function (_, content)
    SILE.call("typeset-into", { frame="runningHead" }, function()
        SILE.call("font", { size="1ex" }, function()
            for id,val in ipairs(headers) do
                SILE.typesetter:pushGlue(SILE.nodefactory.hfillglue())
                if val == sectionName then
                    SILE.call("pdf:link", { dest=val, border=1, borderstyle="underline" }, { val } )
                else
                    SILE.call("pdf:link", { dest=val, border=0 }, function()
                        SILE.call("color", { color="gray" }, { val } )
                    end)
                end
                SILE.typesetter:pushGlue(SILE.nodefactory.hfillglue())
            end
        end)
    end)
end)

SILE.registerCommand("foliostyle", function (_, content)
    if not tonumber(totalPages) then return end
    if ruleFolios then
        SILE.call("noindent")
        local rwidth = string.format("%f", 100*SILE.formatCounter(SILE.scratch.counters.folio) / totalPages).."%fw"
        SILE.call("color", { color=hcolor }, function()
            SILE.call("lower", {height = "65%fh"}, function()
                SILE.call("hrule", {width=rwidth, height="35%fh"})
            end)
        end)
    else
        SILE.typesetter:typeset(" ")
        SILE.typesetter:pushGlue(SILE.nodefactory.hfillglue())
        SILE.call("font", { size="1ex" }, function()
            SILE.typesetter:typeset(SILE.formatCounter(SILE.scratch.counters.folio) .. "/" .. totalPages)
        end)
    end
end)


SILE.registerCommand("section", function(options, content)
-- each section, populate out file
    sectionName = options.name or content[1]
    isNewSection = true
    fileID = io.open(logfile, "a")
    fileID:write(sectionName .. "\n")
    fileID:close()
    if noTransitionSlides then
        return
    end
--  SILE.call("running-head")
    SILE.call("pagebreak")--eject")
    SILE.call("rootImage", { src=altBG } )
    SILE.call("hbox")
    SILE.call("vfill")
    SILE.call("center", {}, function()
        SILE.call("title", {}, content)
    end)
    SILE.call("vfill")
    SILE.call("glue")
    SILE.call("nofoliosthispage")
end)

SILE.registerCommand("slide", function(options, content)
    local cols = tonumber(options.columns) or 1
    slideName = content[1] or sectionName
    SILE.call("pagebreak")--eject")
    SILE.call("rootImage", { src=mainBG } )
    if content[1] ~= nil then
        SILE.call("title", {}, content)
        SILE.call("medskip")
        SILE.call("breakframevertical")
    end
    if cols > 1 then
        SILE.call("makecolumns", { columns=cols } , {})
    end
    SILE.call("running-head")
    isNewSlide = true
end)

SILE.registerCommand("title", function(_, content)
    SILE.call("font", { style="Bold", size="3ex" }, function()
        SILE.call("color", { color=hcolor }, function()
            SILE.process(content)
        end)
    end)
end)

SILE.registerCommand("noTransitionSlides", function(_,_)
    noTransitionSlides=true
end)

SILE.registerCommand("ruleFolios", function(_,_)
    ruleFolios=true
end)

SILE.registerCommand("backgroundImage", function(options, _)
    mainBG  = options.src
    imageBG = mainBG
    if not altBG then
        altBG = mainBG
    end
    SILE.call("rootImage", { src=altBG } )  -- a hack to place some image in the first slide
end)

SILE.registerCommand("alternateImage", function(options, _)
    altBG = options.src
end)

SILE.registerCommand("rootImage", function(options, _)
    local imagesrc = options.src
    SILE.typesetter:leaveHmode()
    SILE.call("typeset-into", { frame="root" }, function()
        slide = tostring(SILE.formatCounter(SILE.scratch.counters.folio)).." "..slideName
        SILE.call("pdf:destination", { name=slide })
        if isNewSection then
            isNewSection = false
            SILE.call("pdf:destination", { name=sectionName })
            SILE.call("pdf:bookmark", { title=sectionName, dest=sectionName, level = 1 })
            if noTransitionSlides then
                SILE.call("pdf:bookmark", { title=slide, dest=slide, level = 2 })
            end
        else
            SILE.call("pdf:bookmark", { title=slide, dest=slide, level = 2 })
        end
        if imagesrc then
            SILE.call("cr") -- FIXME: the root frame discounts the extra space of the first slide; here a space is added to the remaining slides
--          SILE.call("noindent")
            SILE.call("img", {src=imagesrc, width="100%pw", height="100%ph"})
        end
    end)
end)

hcolor = "black"
SILE.registerCommand("themeColor", function(options, _)
    hcolor = options.color
end)

marks = { "•", "–", "o", "▶", "»", "›", "→" }
SILE.registerCommand("litem", function(options,content)
    local level = tonumber(options.level) or 1
    if level == 1 and isNewSlide then
        SILE.call("glue")
        SILE.call("itemskip")
        isNewSlide = false
    end
    size = string.format("%f", 1.5+0.5/level) .. "ex"
    SILE.typesetter:pushGlue(string.format("%d", 1.5*level-1).."em")
    SILE.call("font", { size=size }, function()
        SILE.call("color", { color=hcolor }, function()
            SILE.typesetter:typeset(marks[level].." ")
        end)
        SILE.process(content)
    end)
    SILE.call("itemskip")
end)

SILE.registerCommand("toc", function()
    for id,val in ipairs(headers) do
        SILE.call("litem", { level=1 }, function()
            SILE.call("pdf:link", { dest=val }, { val } )
        end)
    end
end)

SILE.registerCommand("itemskip", function (_, _)
    SILE.typesetter:leaveHmode()
    SILE.typesetter:pushExplicitVglue("6pt plus 18pt minus 18pt")
end, "Skip vertically by a huge amount")

return slides
