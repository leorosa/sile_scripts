local plain = SILE.require("plain", "classes")
local article = plain { id="article" }

article.defaultFrameset = {
    content = {
        left   =        "2cm",
        right  = "100%pw-2cm",
        top    =        "2cm",
        bottom = "100%ph-2cm"
    },
    folio = {
        left   =        "2cm",
        right  = "100%pw-2cm",
        top    = "bottom(content)",
        height = "2cm"
    },
}

article.firstContentFrame = "content"

article.init = function (self)
    article:loadPackage("footnotes", { insertInto="footnotes", stealFrom = { "content" } })
    self:loadPackage("simpletable", {
        tableTag = "table",
        trTag    = "row",
        tdTag    = "col"
    })
    return plain.init(self)
end

article.newPage = function (self)
  return plain.newPage(self)
end

article.finish = function ()
  return plain.finish(article)
end

SILE.settings.set("document.parskip", "4pt plus 1pt")
SILE.settings.set("document.baselineskip", "3ex")

SILE.registerCommand("article:sectioning", function (options, content)
  if options.numbering == nil or options.numbering == "yes" then    -- test before increment counter
  local level = SU.required(options, "level", "article:sectioning")
  SILE.call("increment-multilevel-counter", { id="sectioning", level=level })
  local lang = SILE.settings.get("document.language")
    if options.prenumber then
      if SILE.Commands[options.prenumber .. ":"  .. lang] then
        options.prenumber = options.prenumber .. ":" .. lang
      end
      SILE.call(options.prenumber)
    end
    SILE.call("show-multilevel-counter", { id="sectioning" })
    if options.postnumber then
      if SILE.Commands[options.postnumber .. ":" .. lang] then
        options.postnumber = options.postnumber .. ":" .. lang
      end
      SILE.call(options.postnumber)
    end
  end
end)

article.registerCommands = function ()
  plain.registerCommands()
SILE.doTexlike([[%
\define[command=article:section:pre]{}%
\define[command=article:section:post]{. }%
\define[command=article:subsection:post]{ }%
\define[command=article:appendix:pre]{Appendix }%
\define[command=article:appendix:post]{. }%
\define[command=article:table:pre]{Table }%
\define[command=article:figure:pre]{Figure }%
\define[command=article:caption:post]{: }%
\define[command=abstract]{\quote{\bf{Abstract:} \process}}%
\define[command=litem]{\medskip{}• \process}%
\define[command=bf]{\strong{\process}}%
\define[command=nosection]{\section[numbering=no]{\process}}%
\define[command=nosubsection]{\subsection[numbering=no]{\process}}%
]])
end

SILE.registerCommand("title", function (options, content)
  SILE.typesetter:leaveHmode()
  SILE.call("noindent")
  SILE.call("center", {}, function ()
    SILE.settings.temporarily(function ()
      SILE.call("font", { weight=800, size="1.5em" }, content)
    end)
  end)
  SILE.call("bigskip")
end, "Title")

SILE.registerCommand("author", function (options, content)
  SILE.typesetter:leaveHmode()
--SILE.call("bigskip")
  SILE.call("noindent")
  SILE.call("center", {}, function ()
  SILE.process(
      SILE.call("font", { size = "1.2em" }, content )
  )
  end)
  SILE.call("bigskip")
end, "Author")

SILE.registerCommand("section", function (options, content)
  SILE.typesetter:leaveHmode()
  SILE.call("goodbreak")
  SILE.call("bigskip")
  SILE.call("noindent")
  SILE.call("article:sectionfont", {}, function ()
    SILE.call("article:sectioning", {
      numbering = options.numbering,
      level = 1,
      prenumber = "article:section:pre",
      postnumber = "article:section:post"
    }, content)
    SILE.process(content)
  end)
  SILE.call("novbreak")
  SILE.call("bigskip")
  SILE.call("novbreak")
  SILE.typesetter:inhibitLeading()
end, "Begin a new section")

SILE.registerCommand("subsection", function (options, content)
  SILE.typesetter:leaveHmode()
  SILE.call("goodbreak")
  SILE.call("noindent")
  SILE.call("medskip")
  SILE.call("article:subsectionfont", {}, function ()
    SILE.call("article:sectioning", {
          numbering = options.numbering,
          level = 2,
          postnumber = "article:subsection:post"
        }, content)
    SILE.process(content)
  end)
  SILE.typesetter:leaveHmode()
  SILE.call("novbreak")
  SILE.call("medskip")
  SILE.call("novbreak")
--SILE.typesetter:inhibitLeading()
end, "Begin a new subsection")

SILE.registerCommand("setappendix", function (options, content)
  SILE.scratch.counters['sectioning']['value'][1] = 0
  SILE.scratch.counters['sectioning']['display'][1] = 'Alpha'
  SILE.doTexlike([[\define[command=article:section:pre]{Appendix }]])
end, "Reset section counter to represent the appendix section")

SILE.registerCommand("appendix", function (options, content)
  SILE.typesetter:leaveHmode()
  SILE.call("goodbreak")
  SILE.call("bigskip")
  SILE.call("noindent")
  SILE.call("article:sectionfont", {}, function ()
    SILE.call("increment-counter", { id="appendix" })
    SILE.call("article:appendix:pre")
    SILE.call("show-counter", { id="appendix", display='Alpha' })
    SILE.call("article:appendix:post")
    SILE.process(content)
  end)
  SILE.call("novbreak")
  SILE.call("bigskip")
  SILE.call("novbreak")
  SILE.typesetter:inhibitLeading()
end, "Begin a new appendix section")

SILE.registerCommand("article:sectionfont", function (_, content)
  SILE.settings.temporarily(function ()
    SILE.call("font", { weight=800, size="1.5em" }, content)
  end)
end)

SILE.registerCommand("article:subsectionfont", function (_, content)
  SILE.settings.temporarily(function ()
    SILE.call("font", { weight=800, size="1.2em" }, content)
  end)
end)

SILE.registerCommand("article:captionfont", function (_, content)
  SILE.settings.temporarily(function ()
    SILE.call("font", { style="Italic", size="0.9em" }, content)
  end)
end)

SILE.registerCommand("article:caption", function (options, content)
--ctype=options.ctype
  SILE.typesetter:leaveHmode()
  SILE.call("increment-counter", { id=options.ctype })
  SILE.call("article:captionfont", {}, function ()
--  SILE.call("font", { weight = 800 }, function()
      SILE.call("article:"..options.ctype..":pre")
      SILE.call("show-counter", { id=options.ctype })
      SILE.call("article:caption:post")
--  end)
    SILE.typesetter:inhibitLeading()
    SILE.process(content)
  end)
end, "Increment and show a caption")

SILE.registerCommand("tcaption", function (options, content)
  SILE.call("article:caption", { ctype="table" }, function ()
    SILE.process(content)
  end)
--SILE.call("novbreak")
end, "Insert a table caption")

SILE.registerCommand("fcaption", function (options, content)
  SILE.call("novbreak")
  SILE.call("article:caption", { ctype="figure" }, function ()
    SILE.process(content)
  end)
end, "Insert a figure caption")

SILE.registerCommand("enum", function (options, content)
  if options.display then
    SILE.call("set-counter", { id="enum" , display=options.display })
  end
  SILE.call("set-counter", { id="enum" , value=0 })
  SILE.process(content)
  SILE.call("smallskip")
end, "Begin a numbered list")

SILE.registerCommand("eitem", function (_, _)
  SILE.call("smallskip")
  SILE.call("indent")
  SILE.call("increment-counter", { id="enum" })
  SILE.call("show-counter", { id="enum" })
  SILE.typesetter:typeset(".")
end, "Increment and add a numbered item")

return article
