local plain = require("classes.plain")

local class = pl.class(plain)
class._name = "slides"

--- Default configuration for slides presentation
local config = {
    hcolor = "black",
    ruleFolios = false,
    showTransitionSlides = true,
    printNotes = false,
    notesSize = "2.5ex",
    mainBG = nil,
    altBG = nil,
}

--- Bullet point markers for different nesting levels
local marks = { ">", "•", "–", "+", "o", "▶", "»", "›", "→" }

--- Runtime state tracking
local state = {
    sectionName = "Presentation",
    slideName = "",
    isNewSection = true,
    hasNotes = false,
    ilevel = 1,
    headers = {},
    totalPages = 1
}

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
        right  = "95%pw",
        top    =  "1%ph",
        bottom =  "5%ph"
    },
    root = {   -- used to display a background image
        left   =   "0%pw",
        right  = "100%pw",
        top    =    "0pt",
        bottom = "100%ph"
    }
}

class.firstContentFrame = "content"

logfile = (SILE.masterFilename or 'STDIN') .. '.out'

function class:_init(options)
    plain._init(self, options)
    self:loadPackage("color")
    self:loadPackage("frametricks")
    self:loadPackage("image")
    self:loadPackage("rules")
    self:loadPackage("url")
-- read file.out if exists
    fileID = io.open(logfile, "r")
    state.headers = {}
    if fileID ~= nil then
        for line in io.lines(logfile) do
            table.insert(state.headers,line)
        end
        io.close(fileID)
        state.totalPages = state.headers[#state.headers]
        table.remove(state.headers,#state.headers)
    end
-- then clear file.out
    fileID = io.open(logfile, "w")
    fileID:close()

    SILE.call("nofoliothispage")
    SILE.settings:set("document.lineskip", "6pt")
    SILE.settings:set("document.parskip", "6pt")
    SILE.settings:set("document.parindent", "0pt")
    SILE.call("set-counter", {id="folio", value=0})
    self:registerCommand("foliostyle", function(_, _) -- FIXME is this command name suitable?
        if not tonumber(state.totalPages) then return end
        if config.ruleFolios then
            SILE.call("noindent")
            local rwidth = string.format("%f", 100*plain.packages.counters:formatCounter(SILE.scratch.counters.folio) / state.totalPages).."%fw"
            SILE.call("color", { color=config.hcolor }, function()
                SILE.call("lower", {height="65%fh"}, function()
                    SILE.call("hrule", {width=rwidth, height="35%fh"})
                end)
            end)
        else
            SILE.typesetter:typeset(" ")
            SILE.typesetter:pushGlue(SILE.types.node.hfillglue())
            SILE.call("font", { size="1.5ex" }, function()
                SILE.call("color", { color=config.hcolor }, function()
                    SILE.typesetter:typeset(plain.packages.counters:formatCounter(SILE.scratch.counters.folio) .. "/" .. state.totalPages)
                end)
            end)
        end
    end)
end


function class:newPage()
    return plain.newPage(self)
end

function class:finish()  -- store the total number of slides for next run
    fileID = io.open(logfile, "a")
    fileID:write(plain.packages.counters:formatCounter(SILE.scratch.counters.folio) .. "\n")
    fileID:close()
    return plain.finish(class)
end


function class:registerCommands()
    plain.registerCommands(self)

    --- Register running header command
    -- Displays section headers across the top of slides with navigation links
    self:registerCommand("running-head", function(_, _)
        SILE.call("typeset-into", { frame="runningHead" }, function()
            SILE.call("font", { size="1ex" }, function()
                SILE.call("hbox")
                SILE.typesetter:pushGlue(SILE.types.node.hfillglue())
                for _, sectionHeader in ipairs(state.headers) do
                    SILE.typesetter:pushGlue(SILE.types.node.hfillglue())
                    if sectionHeader == state.sectionName then
                         -- Current section: highlight with theme color
--                      SILE.call("pdf:link", { dest=sectionHeader, border=1, borderstyle="underline" }, { val } )
--                      SILE.call("pdf:link", { dest=sectionHeader, borderwidth="0.2pt", borderstyle="underline", bordercolor=hcolor, borderoffset="0.5pt" }, function()
                        SILE.call("pdf:link", { dest=sectionHeader, borderstyle="none", bordercolor=config.hcolor, borderoffset="0.5pt" }, function()
                            SILE.call("color", { color=config.hcolor }, { sectionHeader })
                        end)
                    else
                        -- Other sections: gray color
                        SILE.call("pdf:link", { dest=sectionHeader }, function()
                            SILE.call("color", { color="gray" }, { sectionHeader })
                        end)
                    end
                end
                SILE.typesetter:pushGlue(SILE.types.node.hfillglue())
                SILE.call("hbox")
            end)
        end)
    end)

    --- Register section command
    -- Marks a new section and optionally displays a transition slide
    self:registerCommand("section", function(options, content)
        state.sectionName = options.name or content[1]
        state.isNewSection = true
        fileID = io.open(logfile, "a") -- for each section, add an entry in logfile
        fileID:write(state.sectionName .. "\n")
        fileID:close()
        if config.showTransitionSlides then
            SILE.call("transition", {}, content)
        end
    end)

    --- Register transition slide command
    -- Displays a full-slide transition with centered title
    self:registerCommand("transition", function(_, content)
        SILE.call("break")
        SILE.call("rootImage", { src=config.altBG })
        SILE.call("hbox")
        SILE.call("vfill") -- align slide vertically
        SILE.call("center", {}, function()
            SILE.call("title", {}, content)
        end)
        SILE.call("nofoliothispage")
        SILE.call("vfill") -- align slide vertically
    end)

    --- Register slide command
    -- Main slide content container with optional title, columns, and vertical centering
    -- @param options.columns number column count (default: 1)
    -- @param options.center boolean vertically center content (default: false)
    -- @param options.title string optional slide title
    self:registerCommand("slide", function(options, content)
        SILE.call("break")
        local cols = tonumber(options.columns) or 1
        local vCenter = options.center or false -- align slide vertically
        state.slideName = content[1] or state.sectionName
        SILE.call("rootImage", { src=config.mainBG })
        if options.title then
            SILE.call("title", {}, { options.title })
            SILE.call("breakframevertical")
        end
        if cols>1 then
            -- FIXME: Multi-column layout needs refinement
            SILE.call("makecolumns", { columns=cols, balanced=false }, {})
        end
        SILE.call("running-head")
        state.hasNotes = false
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
        if not state.hasNotes then
            SILE.call("notes")
        end
    end)

    --- Register notes command
    -- Adds speaker notes (printed separately if notes mode enabled)
    self:registerCommand("notes", function(_, content)
        if config.printNotes then
            SILE.call("break")
            SILE.call("font", { size=config.notesSize }, function()
                if content[1] then
                    SILE.process({ content[1] })
                else
                    -- Generate blank lines for handwritten notes
                    for _ = 1, 5 do
                        SILE.call("hrulefill")
                        SILE.call("skip")
                    end
                end
            end)
            state.hasNotes = true
        end
    end)

    --- Register title command
    -- Formats slide or section title with bold font and theme color
    -- @param options.size string font size (default: "3ex")
    self:registerCommand("title", function(options, content)
        local size = options.size or "3ex"
        SILE.call("font", { style="Bold", size=size }, function()
            SILE.call("color", { color=config.hcolor }, function()
                SILE.process(content)
            end)
        end)
        SILE.call("hfill")
        SILE.call("smallskip")
        SILE.call("hbox")
    end)

    --- Register table of contents command
    -- Displays clickable list of all sections
    self:registerCommand("toc", function()
        if #state.headers>0 then
            SILE.call("hbox")
            SILE.call("vfill")
            for _, sectionHeader in ipairs(state.headers) do
                SILE.call("litem", { level=1 }, function()
                    SILE.call("pdf:link", { dest=sectionHeader }, { sectionHeader })
                    SILE.call("vfill")
                end)
            end
            SILE.call("vfill")
        end
    end)

    --- Register theme color command
    -- Sets the primary color for titles, links, and highlights
    self:registerCommand("themeColor", function(options, _)
        if options.color then
            config.hcolor = options.color
        end
    end)

    --- Register no transition slides command
    -- Disables transition slides between sections
    self:registerCommand("noTransitionSlides", function(_, _)
        config.showTransitionSlides = false
    end)

    --- Register rule folios command
    -- Changes page numbers from text to progress bar format
    self:registerCommand("ruleFolios", function(_, _)
        config.ruleFolios = true
    end)

    --- Register print notes command
    -- Enables printing of speaker notes on separate pages
    -- @param options.size string font size for notes (default: "2.5ex")
    self:registerCommand("printNotes", function(options, _)
        config.notesSize = options.size or "2.5ex"
        config.printNotes = true
    end)

    --- Register background image command
    -- Sets the main background image for regular slides
    self:registerCommand("backgroundImage", function(options, _)
        if options.src then
            config.mainBG = options.src
            config.imageBG = options.src
            if not config.altBG then
                config.altBG = options.src
            end
            SILE.call("rootImage", { src=config.altBG })  -- a hack to place some image in the first slide
        end
    end)

    --- Register alternate image command
    -- Sets a different background image for transition slides
    self:registerCommand("alternateImage", function(options, _)
        if options.src then
            config.altBG = options.src
        end
    end)

    --- Register root image command (internal)
    -- Places background image and manages PDF bookmarks/destinations
    self:registerCommand("rootImage", function(options, _)
        local imagesrc = options.src
        SILE.typesetter:leaveHmode()
        SILE.call("typeset-into", { frame="root" }, function()
            local currentPage = plain.packages.counters:formatCounter(SILE.scratch.counters.folio)
            local slide = tostring(currentPage) .. " " .. state.slideName
            
            SILE.call("pdf:destination", { name=slide })
            if state.isNewSection then
                state.isNewSection = false
                SILE.call("pdf:destination", { name=state.sectionName })
                SILE.call("pdf:bookmark", { title=state.sectionName, dest=state.sectionName, level=1 })
                if not config.showTransitionSlides then
                    SILE.call("pdf:bookmark", { title=slide, dest=slide, level=2 })
                end
            else
                SILE.call("pdf:bookmark", { title=slide, dest=slide, level=2 })
            end
            if imagesrc then
                SILE.call("img", { src=imagesrc, width="100%pw", height="100%ph" })
            end
        end)
    end)

    --- Register list items container command
    -- Groups list items and manages nesting level
    self:registerCommand("litems", function(_, content)
        state.ilevel = state.ilevel + 1
        for i = 1, #content do
            if type(content[i]) == "table" then
                SILE.process({ content[i] })
            end
        end
        state.ilevel = state.ilevel - 1
    end)

    --- Register list item command
    -- Renders a single list item with appropriate bullet and indentation
    -- @param options.level number nesting level (uses state.ilevel if not specified)
    -- @param options.mark string custom bullet marker
    self:registerCommand("litem", function(options, content)
        local level = tonumber(options.level) or state.ilevel
        local mark = options.mark or marks[level] or "•"
        
        local indent = string.format("%f", 1.5*(level-1)).."em"
        SILE.typesetter:pushGlue(indent)
        local fontSize = string.format("%f", 0.75+0.5/level) .. "em"
        SILE.call("font", { size=fontSize }, function()
            SILE.call("color", { color=config.hcolor }, function()
                SILE.typesetter:typeset(mark.." ")
            end)
            SILE.process(content)
        end)
        SILE.typesetter:leaveHmode()
        SILE.typesetter:pushExplicitVglue("4pt plus 8pt minus 2pt") -- "Skip vertically by a huge amount"
    end)

end

return class
