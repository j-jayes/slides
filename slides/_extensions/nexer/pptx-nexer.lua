--- Build the Nexer slide components as native PowerPoint shapes.
---
--- Reveal.js gets `.stats`, `.takeaway`, `.chip` and the source rail from
--- nexer.scss. PowerPoint has no stylesheet, so pandoc flattens all of them
--- into plain paragraphs in one placeholder -- a four-figure stat row becomes
--- four bare lines. This filter emits the same components as raw OpenXML
--- shapes instead, which land in the deck as ordinary editable text boxes and
--- rectangles: a colleague can retype the number or drag the box.
---
--- Three facts about pandoc's pptx writer shape everything below (all read
--- from Text.Pandoc.Writers.Powerpoint, pandoc 3.6.3):
---
---  1. A RawBlock "openxml" is spliced verbatim into <p:spTree> and claims no
---     placeholder, so it is a free-floating shape and must carry its own
---     absolute geometry. RawInline "openxml" is spliced into <a:p> as a run.
---  2. Layout choice is `break notText` over the slide's blocks: text then
---     non-text picks "Content with Caption", whose content box is smaller.
---     A raw block counts as *text*, so every shape this filter builds has to
---     be appended AFTER any image or table, or a full-page chart silently
---     shrinks.
---  3. Every TextBox on a slide binds to the same placeholder and only
---     *adjacent* ones merge. A raw block left between two text blocks
---     therefore splits the body into two placeholders drawn on top of each
---     other. Hence the same rule: raw shapes go last.
---
--- A columns div is the exception to "last": any block beside it at slide
--- level starts a new slide, so the shapes go inside its first column. They
--- are absolutely positioned, so which column holds them does not matter.

local stringify = pandoc.utils.stringify

-- --------------------------------------------------------------------------
-- Geometry. EMU, on the reference deck's 12192000 x 6858000 canvas; every
-- number is read off nexer-reference.pptx rather than chosen.
-- --------------------------------------------------------------------------

local MARGIN = 838200
local BODY_W = 10515600
local BODY_Y = 1822267
local BODY_H = 4352400

local COL_X = { 833648, 6313323 }   -- "Two Content" left / right
local COL_W = 5040000

local KICKER_Y, KICKER_H = 330000, 300000
local RULE_Y, RULE_H = 640000, 12700

local STAT_Y, STAT_H, STAT_GAP = BODY_Y, 1300000, 300000

local TAKE_H = 900000
local TAKE_BAR_W = 60000
local TAKE_STATS_Y = STAT_Y + STAT_H + 150000      -- tucked under a stat row
local TAKE_BODY_Y = BODY_Y + BODY_H - TAKE_H       -- bottom band of the body

-- The rail stops short of the master's logo, which sits at x = 10800521.
local RAIL_Y, RAIL_H, RAIL_W = 6250000, 330000, 9800000

-- --------------------------------------------------------------------------
-- XML helpers
-- --------------------------------------------------------------------------

--- Integer-only formatting. Lua 5.4's `/` yields a float, and PowerPoint
--- rejects "2628900.0" as a coordinate -- with a repair prompt, not an error.
local function n(x) return string.format("%d", math.floor(x)) end

local function esc(s)
  return (tostring(s):gsub("&", "&amp;"):gsub("<", "&lt;"):gsub(">", "&gt;"))
end

local function esc_attr(s) return (esc(s):gsub('"', "&quot;")) end

local function scheme(v) return '<a:schemeClr val="' .. v .. '"/>' end
local function srgb(v) return '<a:srgbClr val="' .. v .. '"/>' end
local function white(alpha)
  return '<a:srgbClr val="FFFFFF"><a:alpha val="' .. n(alpha) .. '"/></a:srgbClr>'
end

-- Brand colours come from the theme, so recolouring nexer-reference.pptx
-- recolours these shapes too. tx2 = dk2 = Nexer purple, accent3 = orange,
-- accent2 = pale blue, bg2 = lt2 = pale grey.
local PURPLE, PURPLE_LIGHT = scheme("tx2"), scheme("accent1")
local ORANGE, CHIP_BG, PANEL = scheme("accent3"), scheme("accent2"), scheme("bg2")
local INK, GREY, RAIL_GREY = scheme("tx1"), srgb("555555"), srgb("6B6B6B")

local HEAD, BODY_FACE = "+mj-lt", "+mn-lt"   -- Bw Gradual / FK Grotesk

--- One <a:r>. `o` carries sz (hundredths of a point), b, i, caps, spc, fill,
--- highlight and face.
local function run(text, o)
  local attrs = { 'lang="en-GB"', 'sz="' .. n(o.sz) .. '"' }
  if o.b then attrs[#attrs + 1] = 'b="1"' end
  if o.i then attrs[#attrs + 1] = 'i="1"' end
  if o.caps then attrs[#attrs + 1] = 'cap="all"' end
  if o.spc then attrs[#attrs + 1] = 'spc="' .. n(o.spc) .. '"' end
  -- Child order is fixed by the schema: fill, then highlight, then latin.
  local props = "<a:solidFill>" .. o.fill .. "</a:solidFill>"
  if o.highlight then props = props .. "<a:highlight>" .. o.highlight .. "</a:highlight>" end
  props = props .. '<a:latin typeface="' .. (o.face or BODY_FACE) .. '"/>'
  return "<a:r><a:rPr " .. table.concat(attrs, " ") .. ">" .. props ..
      "</a:rPr><a:t>" .. esc(text) .. "</a:t></a:r>"
end

local function with(o, extra)
  local copy = {}
  for k, v in pairs(o) do copy[k] = v end
  for k, v in pairs(extra) do copy[k] = v end
  return copy
end

--- Inlines to runs, keeping bold, italic and `.label` emphasis.
local function runs_of(inlines, base)
  local parts = {}
  local function walk(ils, o)
    for _, il in ipairs(ils) do
      local t = il.t
      if t == "Str" then
        parts[#parts + 1] = run(il.text, o)
      elseif t == "Space" or t == "SoftBreak" then
        parts[#parts + 1] = run(" ", o)
      elseif t == "LineBreak" then
        parts[#parts + 1] = "<a:br/>"
      elseif t == "Strong" then
        walk(il.content, with(o, { b = true }))
      elseif t == "Emph" then
        walk(il.content, with(o, { i = true }))
      elseif t == "Span" then
        walk(il.content, il.classes:includes("label") and
          with(o, { b = true, caps = true, spc = 80 }) or o)
      elseif t == "Code" then
        parts[#parts + 1] = run(il.text, o)
      elseif il.content then
        walk(il.content, o)
      else
        local s = stringify(il)
        if s ~= "" then parts[#parts + 1] = run(s, o) end
      end
    end
  end
  walk(inlines, base)
  return table.concat(parts)
end

local function para(runs, o)
  o = o or {}
  local pr = '<a:pPr marL="0" indent="0"'
  if o.algn then pr = pr .. ' algn="' .. o.algn .. '"' end
  pr = pr .. ">"
  -- Schema order inside a:pPr: spacing before the bullet declaration.
  if o.spc_before then
    pr = pr .. '<a:spcBef><a:spcPts val="' .. n(o.spc_before) .. '"/></a:spcBef>'
  end
  pr = pr .. "<a:buNone/></a:pPr>"
  return "<a:p>" .. pr .. runs .. "</a:p>"
end

local next_id = 1000   -- pandoc uses 0, 1, 6 and the layout's own ids

--- A text box. `o`: fill (default none), anchor, lIns.
local function textbox(name, x, y, cx, cy, paras, o)
  o = o or {}
  next_id = next_id + 1
  return table.concat {
    '<p:sp><p:nvSpPr><p:cNvPr id="', n(next_id), '" name="', esc_attr(name), '"/>',
    '<p:cNvSpPr txBox="1"/><p:nvPr/></p:nvSpPr>',
    '<p:spPr><a:xfrm><a:off x="', n(x), '" y="', n(y), '"/>',
    '<a:ext cx="', n(cx), '" cy="', n(cy), '"/></a:xfrm>',
    '<a:prstGeom prst="rect"><a:avLst/></a:prstGeom>',
    o.fill and ("<a:solidFill>" .. o.fill .. "</a:solidFill>") or "<a:noFill/>",
    '<a:ln><a:noFill/></a:ln></p:spPr>',
    '<p:txBody><a:bodyPr wrap="square" lIns="', n(o.lIns or 0),
    '" tIns="0" rIns="0" bIns="0" anchor="', o.anchor or "t",
    '"><a:normAutofit/></a:bodyPr><a:lstStyle/>',
    paras, "</p:txBody></p:sp>",
  }
end

--- A filled rectangle with no text: the kicker rule, the takeaway bar.
local function rect(name, x, y, cx, cy, fill)
  next_id = next_id + 1
  return table.concat {
    '<p:sp><p:nvSpPr><p:cNvPr id="', n(next_id), '" name="', esc_attr(name), '"/>',
    "<p:cNvSpPr/><p:nvPr/></p:nvSpPr>",
    '<p:spPr><a:xfrm><a:off x="', n(x), '" y="', n(y), '"/>',
    '<a:ext cx="', n(cx), '" cy="', n(cy), '"/></a:xfrm>',
    '<a:prstGeom prst="rect"><a:avLst/></a:prstGeom>',
    "<a:solidFill>", fill, "</a:solidFill><a:ln><a:noFill/></a:ln></p:spPr>",
    '<p:txBody><a:bodyPr/><a:lstStyle/><a:p><a:endParaRPr lang="en-GB"/></a:p>',
    "</p:txBody></p:sp>",
  }
end

local function raw(xml) return pandoc.RawBlock("openxml", xml) end

-- --------------------------------------------------------------------------
-- The components
-- --------------------------------------------------------------------------

local function kicker_shapes(text, dark)
  return {
    raw(textbox("Nexer kicker", MARGIN, KICKER_Y, BODY_W, KICKER_H,
      para(run(text, {
        sz = 1100, b = true, caps = true, spc = 300,
        fill = dark and PURPLE_LIGHT or PURPLE, face = HEAD,
      })), { anchor = "b" })),
    raw(rect("Nexer rule", MARGIN, RULE_Y, BODY_W, RULE_H,
      dark and white(22000) or PANEL)),
  }
end

--- One text box per `.stat`, spread across the body width.
local function stats_shapes(div, dark)
  local stats = {}
  for _, blk in ipairs(div.content) do
    if blk.t == "Div" and blk.classes:includes("stat") then
      local figure, label = {}, {}
      for _, inner in ipairs(blk.content) do
        if inner.content then
          for _, il in ipairs(inner.content) do
            if il.t == "Span" and il.classes:includes("figure") then
              figure[#figure + 1] = stringify(il)
            elseif il.t == "Span" and il.classes:includes("label") then
              label[#label + 1] = stringify(il)
            end
          end
        end
      end
      stats[#stats + 1] = {
        figure = table.concat(figure, " "),
        label = table.concat(label, " "),
      }
    end
  end
  if #stats == 0 then return {} end

  local width = (BODY_W - STAT_GAP * (#stats - 1)) // #stats
  local out = {}
  for i, stat in ipairs(stats) do
    out[i] = raw(textbox("Nexer stat " .. i,
      MARGIN + (i - 1) * (width + STAT_GAP), STAT_Y, width, STAT_H,
      para(run(stat.figure, {
        sz = 4400, b = true, spc = -100,
        fill = dark and PURPLE_LIGHT or PURPLE, face = HEAD,
      })) .. para(run(stat.label, {
        sz = 1100, caps = true, spc = 200,
        fill = dark and white(72000) or GREY, face = BODY_FACE,
      }), { spc_before = 600 })))
  end
  return out
end

--- The bold lead-in: a panel with an orange bar down its left edge. Two flat
--- shapes rather than a group, because a <p:grpSp> needs a child coordinate
--- space and gets one more chance to be malformed.
local function takeaway_shapes(div, x, y, w, dark)
  local first = div.content[1]
  local text = runs_of(first and first.content or {}, {
    sz = 1600, fill = dark and white(100000) or INK, face = BODY_FACE,
  })
  return {
    raw(textbox("Nexer takeaway", x, y, w, TAKE_H, para(text), {
      fill = dark and white(8000) or PANEL,
      anchor = "ctr",
      lIns = TAKE_BAR_W + 120000,
    })),
    raw(rect("Nexer takeaway bar", x, y, TAKE_BAR_W, TAKE_H, ORANGE)),
  }
end

--- The bottom-left rail: `.units` first, then whatever `.source` said. In the
--- HTML these are two lines in different places; PowerPoint has room for one.
local function rail_shape(units, sources, dark)
  local base = {
    sz = 900, fill = dark and white(60000) or RAIL_GREY, face = BODY_FACE,
  }
  local parts = {}
  for _, u in ipairs(units) do
    parts[#parts + 1] = run("Units: ", with(base, { b = true, caps = true, spc = 80 })) ..
        runs_of(u, base) .. run("   ", base)
  end
  for _, s in ipairs(sources) do
    parts[#parts + 1] = runs_of(s, base)
  end
  if #parts == 0 then return nil end
  return raw(textbox("Nexer source", MARGIN, RAIL_Y, RAIL_W, RAIL_H,
    para(table.concat(parts))))
end

-- --------------------------------------------------------------------------
-- Slide assembly
-- --------------------------------------------------------------------------

local function is_dark(hex)
  local r = tonumber(hex:sub(1, 2), 16) or 0
  local g = tonumber(hex:sub(3, 4), 16) or 0
  local b = tonumber(hex:sub(5, 6), 16) or 0
  -- The same luminance test reveal.js uses for .has-dark-background.
  return (299 * r + 587 * g + 114 * b) / 1000 < 128
end

--- Solid-colour slide backgrounds ship as PNG tiles: pandoc honours
--- `background-image` on a slide heading but ignores `background-color`.
local function background_tile(hex)
  local path = quarto.utils.resolve_path("bg/" .. hex:lower() .. ".png")
  local handle = io.open(path, "rb")
  if not handle then return nil end
  handle:close()
  return path
end

--- Every inline in a div's paragraphs, flattened to one line.
local function inlines_of(div)
  local out = {}
  for _, blk in ipairs(div.content) do
    if blk.content then
      if #out > 0 then out[#out + 1] = pandoc.Space() end
      for _, il in ipairs(blk.content) do out[#out + 1] = il end
    end
  end
  return out
end

--- Rewrite one container's blocks, collecting the shapes they become.
---
--- `column` is nil at slide level, or 1/2 inside a `.column`, which decides
--- where a takeaway's band goes.
local function convert(blocks, ctx, column)
  local out = pandoc.List()
  local after_stats = false
  for _, blk in ipairs(blocks) do
    local handled = false
    local was_stats = false

    if blk.t == "Div" then
      if blk.classes:includes("stats") then
        for _, s in ipairs(stats_shapes(blk, ctx.dark)) do
          ctx.shapes[#ctx.shapes + 1] = s
        end
        handled, was_stats = true, true
      elseif blk.classes:includes("takeaway") then
        local x, y, w
        if after_stats then
          x, y, w = MARGIN, TAKE_STATS_Y, BODY_W
        elseif column then
          x, y, w = COL_X[column], TAKE_BODY_Y, COL_W
        else
          x, y, w = MARGIN, TAKE_BODY_Y, BODY_W
        end
        for _, s in ipairs(takeaway_shapes(blk, x, y, w, ctx.dark)) do
          ctx.shapes[#ctx.shapes + 1] = s
        end
        handled = true
      elseif blk.classes:includes("source") then
        ctx.sources[#ctx.sources + 1] = inlines_of(blk)
        handled = true
      elseif blk.classes:includes("units") then
        ctx.units[#ctx.units + 1] = inlines_of(blk)
        handled = true
      elseif blk.classes:includes("columns") then
        local i = 0
        blk.content = blk.content:map(function(col)
          if col.t == "Div" and col.classes:includes("column") then
            i = i + 1
            col.content = convert(col.content, ctx, math.min(i, #COL_X))
          end
          return col
        end)
        ctx.columns = blk
      end
    elseif blk.t == "Table" then
      -- Figure-wrapping is what keeps an exhibit and its rail on one slide:
      -- pandoc splits before a bare Table or image paragraph, never before a
      -- Figure. Inside a column it matters even more -- only the first chunk
      -- of a split column survives, so anything after the chart is dropped.
      blk = pandoc.Figure({ blk }, nil, pandoc.Attr())
    elseif (blk.t == "Para" or blk.t == "Plain") and
        #blk.content == 1 and blk.content[1].t == "Image" then
      blk = pandoc.Figure({ blk }, nil, pandoc.Attr())
    end

    if not handled then out:insert(blk) end
    after_stats = was_stats
  end
  return out
end

--- Turn `## kicker` + `### action title` + body into one PowerPoint slide.
---
--- The title merge is not cosmetic: PowerPoint has a single title
--- placeholder, and leaving the `###` in the body makes pandoc read the slide
--- as "text then content" and split any following columns onto a second,
--- untitled slide. The action title is also the better thing to put there.
local function build_slide(header, body)
  local kicker = nil
  if body[1] and body[1].t == "Header" and body[1].level == 3 then
    kicker = stringify(header)
    header = pandoc.Header(2, body[1].content, header.attr)
    table.remove(body, 1)
  end

  local colour = header.attributes["background-color"]
  local dark = false
  if colour then
    local hex = colour:gsub("^#", "")
    dark = is_dark(hex)
    local tile = background_tile(hex)
    if tile then
      header.attributes["background-image"] = tile
    else
      quarto.log.warning("nexer: no background tile for " .. colour ..
        " -- add one with tools/build_bg_pngs.py")
    end
    header.attributes["background-color"] = nil
  elseif header.attributes["background-image"] or
      header.attributes["data-background-image"] then
    dark = true
  end

  if dark then
    -- The title placeholder inherits ink from the layout, which is invisible
    -- on a dark fill; a raw run is the only way to recolour it.
    header.content = { pandoc.RawInline("openxml", run(stringify(header), {
      sz = 2600, spc = -30, fill = white(100000), face = HEAD,
    })) }
  end

  next_id = 1000
  local ctx = { shapes = {}, sources = {}, units = {}, dark = dark, columns = nil }
  local blocks = convert(body, ctx, nil)

  local shapes = {}
  if kicker then
    for _, s in ipairs(kicker_shapes(kicker, dark)) do shapes[#shapes + 1] = s end
  end
  for _, s in ipairs(ctx.shapes) do shapes[#shapes + 1] = s end
  local rail = rail_shape(ctx.units, ctx.sources, dark)
  if rail then shapes[#shapes + 1] = rail end

  -- Last, always: see the header comment. Inside the columns div when there
  -- is one, because a sibling block there would start a new slide.
  if ctx.columns then
    for _, col in ipairs(ctx.columns.content) do
      if col.t == "Div" and col.classes:includes("column") then
        for _, s in ipairs(shapes) do col.content:insert(s) end
        break
      end
    end
  else
    for _, s in ipairs(shapes) do blocks:insert(s) end
  end

  local out = pandoc.List({ header })
  out:extend(blocks)
  return out
end

-- --------------------------------------------------------------------------
-- Entry point
-- --------------------------------------------------------------------------

--- Inline styling that survives inside a placeholder, applied after the slide
--- walk so that the spans consumed by `.stats` and `.source` are already gone.
local function style_inlines(doc)
  return doc:walk {
    Span = function(el)
      if el.classes:includes("chip") then
        local accent = el.classes:includes("accent")
        return pandoc.RawInline("openxml", run(" " .. stringify(el) .. " ", {
          sz = 1100, b = true, caps = true, spc = 80,
          fill = accent and white(100000) or INK,
          highlight = accent and ORANGE or CHIP_BG,
        }))
      elseif el.classes:includes("figure") then
        return pandoc.RawInline("openxml", run(stringify(el), {
          sz = 3200, b = true, spc = -100, fill = PURPLE, face = HEAD,
        }))
      elseif el.classes:includes("label") then
        return pandoc.RawInline("openxml", run(stringify(el), {
          sz = 1100, b = true, caps = true, spc = 200, fill = GREY,
        }))
      end
    end,
    Header = function(el)
      -- A `####` subhead inside the body. Pandoc already renders it bold with
      -- space above; this only recolours it, so the block stays a Header.
      if el.level >= 4 then
        el.content = { pandoc.RawInline("openxml", run(stringify(el), {
          sz = 1400, b = true, caps = true, spc = 80, fill = PURPLE, face = HEAD,
        })) }
        return el
      end
    end,
  }
end

function Pandoc(doc)
  local out = pandoc.List()
  local blocks, i = doc.blocks, 1
  while i <= #blocks do
    local blk = blocks[i]
    if blk.t == "Header" and blk.level == 2 then
      local body, j = {}, i + 1
      while j <= #blocks and
          not (blocks[j].t == "Header" and blocks[j].level <= 2) do
        body[#body + 1] = blocks[j]
        j = j + 1
      end
      out:extend(build_slide(blk, body))
      i = j
    else
      if blk.t == "Header" and blk.level == 1 then
        -- Section dividers are already dark with the swirl artwork, from the
        -- layout. Honouring the attribute too embeds a second copy of it.
        blk.attributes["background-image"] = nil
        blk.attributes["data-background-image"] = nil
        blk.attributes["background-color"] = nil
      end
      out:insert(blk)
      i = i + 1
    end
  end
  doc.blocks = out
  return style_inlines(doc)
end
