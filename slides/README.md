`slides.lua` is a class that allows to make simple presentations with SILE.
It may be adjusted through the following commands:

- `\slide` is used to create new slides.
    It accepts these arguments:

    - `title` to set a title for the slide (default=""),
    - `columns` to set the number of columns (default=1), and
    - `center` to position slide content vertically at 1/3 of the frame — it adds one `\vfill` before and two after contents (default=false).

- `\title` to print titles.

- `\transition` is used to place a slide with just one sentence in its middle.
    It is useful to highlight places in a presentation.

- `\section` is used to organize the slides.
    It accepts the option `name`, which defaults to the content of the command.
    Section names are displayed as links at the top of slides.
    Moreover, a transition slide can appear at the beginning of a new section.
    This behavior can be supressed by calling the `\noTransitionSlides` command.

- `\toc` is used to display a list of the sections in a presentation.

- `\litems` is a list environment in which each item is defined by calling a `\litem` command.

Besides `\noTransitionSlides`, the following commands may be used to customize presentations:

- `themeColor`: to change the color applied to titles and decorations (default=black)
- `ruleFolios`: to show the presentation progress with an horizontal bar at the bottom (default=false)
- `printNotes`: to print slide notes (default=true)
- `backgroundImage`: to set an image to be shown in the background of slides
- `alternateImage`: to set an image to be shown in transition slides
- `rootImage`: to show an image in the background of the current slide
