local plain = require("classes.plain")

local class = pl.class(plain)
class._name = "slides"

local sectionName = "Presentation"
local slideName = ""
local isNewSection = true
local hasNotes = false

--defaults:
local hcolor = "black"
local ruleFolios = false
local showTransitionSlides = true
local printNotes = false
local marks = { ">", "•", "–", "+", "o", "▶", "»", "›", "→" }

--SILE.documentState.paperSize = SILE.paperSizeParser("5.04in x 3.78in")
class.defaultFrameset = {
    content = {
        left   =  "5%pw",
        right  = "95%pw",
        top    =  "7%ph",
        bottom = "97%ph"
    },
    folio = {
        left   =  "2%pw",
        right  = "98%pw",
        top    = "97%ph",
        bottom = "100%ph"
    },
    runningHead = {
        left   =  "5%pw",
        right  = "90%pw",
        top    =  "1%ph",
        bottom =  "5%ph"
    },
    root = {   -- used to display a background image
        left   =   "0%pw",
        right  = "100%pw",
        top    =    "0pt",  -- FIXME: 1st slide is displaced; using a 'cr' in each new one
        bottom = "100%ph"
    }
}

class.firstContentFrame = "content"

logfile = (SILE.masterFilename or 'STDIN') .. '.out'

function class:_init (options)
    plain._init(self, options)
    self:loadPackage("color")
    self:loadPackage("frametricks")
    self:loadPackage("image")
    self:loadPackage("rules")
    self:loadPackage("url")
-- read file.out if exists
    fileID = io.open(logfile, "r")
    headers = {}
    if fileID ~= nil then
        for line in io.lines(logfile) do
            table.insert(headers,line)
        end
        io.close(fileID)
        totalPages = headers[#headers]
        table.remove(headers,idx)
    end
-- then clear file.out
    fileID = io.open(logfile, "w")
    fileID:close()

    SILE.call("nofoliothispage")
    SILE.settings:set("document.lineskip","6pt") --"1ex")
    SILE.settings:set("document.parskip","6pt") --"1ex")
    SILE.settings:set("document.parindent","0pt")
    SILE.call("set-counter", {id="folio", value=0})
    self:registerCommand("foliostyle", function (_, content) -- FIXME
        if not tonumber(totalPages) then return end
        if ruleFolios then
            SILE.call("noindent")
            local rwidth = string.format("%f", 100*plain.packages.counters:formatCounter(SILE.scratch.counters.folio) / totalPages).."%fw"
            SILE.call("color", { color=hcolor }, function()
                SILE.call("lower", {height = "65%fh"}, function()
                    SILE.call("hrule", {width=rwidth, height="35%fh"})
                end)
            end)
        else
            SILE.typesetter:typeset(" ")
            SILE.typesetter:pushGlue(SILE.types.node.hfillglue())
            SILE.call("font", { size="1.5ex" }, function()
                SILE.call("color", { color=hcolor }, function()
                    SILE.typesetter:typeset(plain.packages.counters:formatCounter(SILE.scratch.counters.folio) .. "/" .. totalPages)
                end)
            end)
        end
    end)
end


function class:newPage()
--  SILE.call("rootImage")
    return plain.newPage(self)
end

function class:finish()  -- store the total number of slides
    fileID = io.open(logfile, "a")
    fileID:write(plain.packages.counters:formatCounter(SILE.scratch.counters.folio) .. "\n")
    fileID:close()
    return plain.finish(class)
end


function class:registerCommands ()
    plain.registerCommands(self)

    self:registerCommand("running-head", function (_, content)
        SILE.call("typeset-into", { frame="runningHead" }, function()
            SILE.call("font", { size="1ex" }, function()
                for id,val in ipairs(headers) do
                    SILE.typesetter:pushGlue(SILE.types.node.hfillglue())
                    if val == sectionName then
--                      SILE.call("pdf:link", { dest=val, border=1, borderstyle="underline" }, { val } )
--                      SILE.call("pdf:link", { dest=val, borderwidth="0.2pt", borderstyle="underline", bordercolor=hcolor, borderoffset="0.5pt" }, function()
                        SILE.call("pdf:link", { dest=val, borderstyle="none", bordercolor=hcolor, borderoffset="0.5pt" }, function()
                            SILE.call("color", { color=hcolor }, { val } )
                        end)
                    else
                        SILE.call("pdf:link", { dest=val }, function()
                            SILE.call("color", { color="gray" }, { val } )
                        end)
                    end
                    SILE.typesetter:pushGlue(SILE.types.node.hfillglue())
                    SILE.call("hbox")
                end
            end)
        end)
    end)

    self:registerCommand("section", function(options, content)
        sectionName = options.name or content[1]
        isNewSection = true
        fileID = io.open(logfile, "a") -- for each section, add an entry in logfile
        fileID:write(sectionName .. "\n")
        fileID:close()
        if showTransitionSlides then
            SILE.call("transition", {}, content)--eject")
        end
    end)

    self:registerCommand("transition", function(options, content)
        SILE.call("break")
        SILE.call("rootImage", { src=altBG } )
        SILE.call("hbox")
        SILE.call("vfill") -- align slide vertically
        SILE.call("center", {}, function()
            SILE.call("title", {}, content)
        end)
        SILE.call("nofoliothispage")
        SILE.call("vfill") -- align slide vertically
    end)

    self:registerCommand("slide", function(options, content)
        SILE.call("break")
        local cols = tonumber(options.columns) or 1
        local vCenter = options.center or false -- align slide vertically
        slideName = content[1] or sectionName
        SILE.call("rootImage", { src=mainBG } )
        if options.title ~= nil then
            SILE.call("title", {}, {options.title} )
            SILE.call("breakframevertical")
        end
        if cols > 1 then        -- FIXME
            SILE.call("makecolumns", { columns=cols , balanced=false } , {})
        end
        SILE.call("running-head")
        hasNotes = false
        if vCenter then
            SILE.call("hbox")
            SILE.call("vfill")
        end
        SILE.process(content)
        if vCenter then
            SILE.call("vfill")
            SILE.call("hbox")
            SILE.call("vfill") -- a second vfill at the botton displaces the contents towards the top, producing better(?) results
            SILE.call("hbox")
        end
        if hasNotes == false then
            SILE.call("notes")
        end
    end)

    self:registerCommand("notes", function (options, content)
        if printNotes then
            SILE.call("break")
            SILE.call("font", { size=notesSize }, function()
                if content[1] ~= nil then
                    SILE.process({ content[1] })
                else
                    SILE.call("hrulefill")
                    SILE.call("skip")
                    SILE.call("hrulefill")
                    SILE.call("skip")
                    SILE.call("hrulefill")
                    SILE.call("skip")
                    SILE.call("hrulefill")
                    SILE.call("skip")
                    SILE.call("hrulefill")
                    SILE.call("skip")
                end
            end)
            hasNotes = true
        end
    end)

    self:registerCommand("title", function(options, content)
        size = options.size or "3ex"
        SILE.call("font", { style="Bold", size=size }, function()
            SILE.call("color", { color=hcolor }, function()
                SILE.process(content)
            end)
        end)
        SILE.call("hfill")
        SILE.call("smallskip")
        SILE.call("hbox")
    end)

    self:registerCommand("toc", function()
        if #headers>0 then
            SILE.call("hbox")
            SILE.call("vfill")
            for id,val in ipairs(headers) do
                SILE.call("litem", { level=1 }, function()
                    SILE.call("pdf:link", { dest=val }, { val } )
                    SILE.call("vfill")
                end)
            end
            SILE.call("vfill")
        end
    end)

    self:registerCommand("themeColor", function(options, _)
        hcolor = options.color
    end)

    self:registerCommand("noTransitionSlides", function(_,_)
        showTransitionSlides=false
    end)

    self:registerCommand("ruleFolios", function(_,_)
        ruleFolios=true
    end)

    self:registerCommand("printNotes", function(options,_)
        notesSize = options.size or "2.5ex"
        printNotes=true
    end)

    self:registerCommand("backgroundImage", function(options, _)
        mainBG  = options.src
        imageBG = mainBG
        if not altBG then
            altBG = mainBG
        end
        SILE.call("rootImage", { src=altBG } )  -- a hack to place some image in the first slide
    end)

    self:registerCommand("alternateImage", function(options, _)
        altBG = options.src
    end)

    self:registerCommand("rootImage", function(options, _)
        local imagesrc = options.src
        SILE.typesetter:leaveHmode()
        SILE.call("typeset-into", { frame="root" }, function()  -- FIXME
            slide = tostring(plain.packages.counters:formatCounter(SILE.scratch.counters.folio)).." "..slideName
            SILE.call("pdf:destination", { name=slide })
            if isNewSection then
                isNewSection = false
                SILE.call("pdf:destination", { name=sectionName })
                SILE.call("pdf:bookmark", { title=sectionName, dest=sectionName, level = 1 })
                if showTransitionSlides == false then
                    SILE.call("pdf:bookmark", { title=slide, dest=slide, level = 2 })
                end
            else
                SILE.call("pdf:bookmark", { title=slide, dest=slide, level = 2 })
            end
            if imagesrc then
                SILE.call("img", {src=imagesrc, width="100%pw", height="100%ph"})
            end
        end)
    end)

    ilevel = 1
    class:registerCommand("litems", function(options,content)
        ilevel = ilevel + 1
        for i = 1, #content do
          if type(content[i]) == "table" then   -- ignore strings; process only \item{} commands
            SILE.process({ content[i] })
          end
        end
        ilevel = ilevel - 1
    end)

    class:registerCommand("litem", function(options,content)
        local level = tonumber(options.level) or ilevel
        local mark = options.mark or marks[level]
        SILE.typesetter:pushGlue(string.format("%f", 1.5*(level-1)).."em")
        size = string.format("%f", 0.75+0.5/level) .. "em"
        SILE.call("font", { size=size }, function()
            SILE.call("color", { color=hcolor }, function()
                SILE.typesetter:typeset(mark.." ")
            end)
            SILE.process(content)
        end)
        SILE.typesetter:leaveHmode()
        SILE.typesetter:pushExplicitVglue("4pt plus 8pt minus 2pt") -- "Skip vertically by a huge amount"
    end)

end

return class
