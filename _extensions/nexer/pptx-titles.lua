--- Merge the two-tier title into one PowerPoint slide title.
---
--- The deck convention is `## kicker` then `### action title`. Reveal.js styles
--- them as two tiers, but PowerPoint has a single title placeholder, and
--- leaving the `###` in the body makes pandoc treat the slide as
--- "text then content" -- which splits any following columns block onto a
--- second, untitled slide.
---
--- So for pptx the action title becomes the slide title and the kicker is
--- dropped. That is also the better PowerPoint design: the title placeholder
--- should carry the takeaway, not the section label.

local function is_header(block, level)
  return block ~= nil and block.t == "Header" and block.level == level
end

function Blocks(blocks)
  local out = {}
  local i = 1
  while i <= #blocks do
    local this, next_ = blocks[i], blocks[i + 1]
    if is_header(this, 2) and is_header(next_, 3) then
      -- Keep the kicker's identifier and classes so cross-references and
      -- per-slide attributes still resolve.
      out[#out + 1] = pandoc.Header(2, next_.content, this.attr)
      i = i + 2
    else
      out[#out + 1] = this
      i = i + 1
    end
  end
  return out
end

--- Route the source rail and unit lines into speaker notes.
---
--- Pandoc cannot place any block after a figure or table on the same slide --
--- it starts a new, untitled one. So a `::: {.source}` under a chart becomes a
--- stray slide. PowerPoint has nowhere to put a bottom rail anyway, so the text
--- goes to the notes pane, where it stays with the slide and stays editable.
local function flatten(div, prefix)
  local inlines = {}
  for _, block in ipairs(div.content) do
    if block.t == "Para" or block.t == "Plain" then
      for _, inline in ipairs(block.content) do
        inlines[#inlines + 1] = inline
      end
      inlines[#inlines + 1] = pandoc.Space()
    end
  end
  table.insert(inlines, 1, pandoc.Str(prefix))
  table.insert(inlines, 2, pandoc.Space())
  return pandoc.Div({ pandoc.Para(inlines) }, pandoc.Attr("", { "notes" }))
end

function Div(el)
  if el.classes:includes("source") then
    return flatten(el, "[source]")
  elseif el.classes:includes("units") then
    return flatten(el, "[units]")
  end
end
