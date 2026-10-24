---
name: Ofertas de empleo
description: A private job-search dashboard set as the classified-ads section of a newspaper.
colors:
  band-yellow: "#ffd200"
  band-ink: "#16130f"
  link-blue: "#1d4fd7"
  vermilion: "#c8321e"
  amber: "#8f5400"
  ledger-green: "#1f6b3a"
  paper: "#f4f3ef"
  paper-2: "#eae8e1"
  sheet: "#ffffff"
  ink: "#16130f"
  ink-2: "#4a443b"
  ink-3: "#686256"
  hair: "#c9c5ba"
  fit-high: "#16130f"
  fit-medium: "#8a8478"
  fit-low: "#cfcabf"
  on-state: "#ffffff"
  dark-paper: "#12110e"
  dark-paper-2: "#1b1915"
  dark-sheet: "#1f1d18"
  dark-ink: "#ecebe4"
  dark-ink-2: "#c4c0b5"
  dark-ink-3: "#a19c90"
  dark-hair: "#3b372f"
  dark-link-blue: "#93b1ff"
  dark-vermilion: "#ff6b55"
  dark-amber: "#f0b44c"
  dark-ledger-green: "#74d394"
  dark-fit-medium: "#8f897d"
  dark-fit-low: "#4a463e"
  dark-on-state: "#16130f"
typography:
  display:
    fontFamily: "Archivo, system-ui, sans-serif"
    fontSize: "128px"
    fontWeight: 900
    lineHeight: 0.8
    letterSpacing: "-0.03em"
    fontVariation: "'wdth' 62"
  headline:
    fontFamily: "Archivo, system-ui, sans-serif"
    fontSize: "38px"
    fontWeight: 900
    lineHeight: 1.02
    letterSpacing: "-0.005em"
    fontVariation: "'wdth' 75"
  section:
    fontFamily: "Archivo, system-ui, sans-serif"
    fontSize: "28px"
    fontWeight: 900
    lineHeight: 1.05
    fontVariation: "'wdth' 62"
  lead-in:
    fontFamily: "Archivo, system-ui, sans-serif"
    fontSize: "16.5px"
    fontWeight: 900
    letterSpacing: "0.005em"
    fontVariation: "'wdth' 75"
  body:
    fontFamily: "Archivo, system-ui, sans-serif"
    fontSize: "15px"
    fontWeight: 400
    lineHeight: 1.45
    fontFeature: "'tnum'"
    fontVariation: "'wdth' 100"
  label:
    fontFamily: "Archivo, system-ui, sans-serif"
    fontSize: "13.5px"
    fontWeight: 700
  display-phone:
    fontFamily: "Archivo, system-ui, sans-serif"
    fontSize: "88px"
    fontWeight: 900
    lineHeight: 0.8
    fontVariation: "'wdth' 62"
  tally:
    fontFamily: "Archivo, system-ui, sans-serif"
    fontSize: "60px"
    fontWeight: 900
    lineHeight: 0.9
    fontVariation: "'wdth' 62"
  masthead:
    fontFamily: "Archivo, system-ui, sans-serif"
    fontSize: "34px"
    fontWeight: 900
    lineHeight: 1
    letterSpacing: "-0.01em"
    fontVariation: "'wdth' 62"
  headline-phone:
    fontFamily: "Archivo, system-ui, sans-serif"
    fontSize: "30px"
    fontWeight: 900
    lineHeight: 1.02
    fontVariation: "'wdth' 75"
  dialog-title:
    fontFamily: "Archivo, system-ui, sans-serif"
    fontSize: "30px"
    fontWeight: 900
    lineHeight: 1
    fontVariation: "'wdth' 62"
  row-score:
    fontFamily: "Archivo, system-ui, sans-serif"
    fontSize: "30px"
    fontWeight: 900
    lineHeight: 1
    fontVariation: "'wdth' 62"
  row-score-phone:
    fontFamily: "Archivo, system-ui, sans-serif"
    fontSize: "26px"
    fontWeight: 900
    lineHeight: 1
    fontVariation: "'wdth' 62"
  masthead-phone:
    fontFamily: "Archivo, system-ui, sans-serif"
    fontSize: "24px"
    fontWeight: 900
    lineHeight: 1
    fontVariation: "'wdth' 62"
  empty-title:
    fontFamily: "Archivo, system-ui, sans-serif"
    fontSize: "20px"
    fontWeight: 900
    fontVariation: "'wdth' 75"
  company:
    fontFamily: "Archivo, system-ui, sans-serif"
    fontSize: "18px"
    fontWeight: 600
  rail-head:
    fontFamily: "Archivo, system-ui, sans-serif"
    fontSize: "16px"
    fontWeight: 900
    fontVariation: "'wdth' 75"
  group-head:
    fontFamily: "Archivo, system-ui, sans-serif"
    fontSize: "15px"
    fontWeight: 900
    fontVariation: "'wdth' 75"
  button:
    fontFamily: "Archivo, system-ui, sans-serif"
    fontSize: "14px"
    fontWeight: 700
  small:
    fontFamily: "Archivo, system-ui, sans-serif"
    fontSize: "13px"
    fontWeight: 600
  caption:
    fontFamily: "Archivo, system-ui, sans-serif"
    fontSize: "12.5px"
    fontWeight: 400
  meta-phone:
    fontFamily: "Archivo, system-ui, sans-serif"
    fontSize: "12px"
    fontWeight: 600
    lineHeight: 1.3
  chart:
    fontFamily: "Archivo, system-ui, sans-serif"
    fontSize: "10.5px"
    fontWeight: 600
  mark:
    fontFamily: "Archivo, system-ui, sans-serif"
    fontSize: "11px"
    fontWeight: 800
    lineHeight: 1.4
    letterSpacing: "0.05em"
rounded:
  none: "0px"
spacing:
  xs: "4px"
  sm: "8px"
  md: "12px"
  lg: "16px"
  xl: "24px"
  section: "34px"
  gutter: "40px"
components:
  button-primary:
    backgroundColor: "{colors.ink}"
    textColor: "{colors.paper}"
    typography: "{typography.button}"
    rounded: "{rounded.none}"
    padding: "8px 16px"
    height: "40px"
  button-primary-hover:
    backgroundColor: "transparent"
    textColor: "{colors.ink}"
  button-ghost:
    backgroundColor: "transparent"
    textColor: "{colors.ink}"
    rounded: "{rounded.none}"
    padding: "8px 16px"
    height: "40px"
  button-band:
    backgroundColor: "{colors.band-ink}"
    textColor: "{colors.band-yellow}"
    rounded: "{rounded.none}"
    padding: "8px 16px"
    height: "40px"
  tab-active:
    backgroundColor: "{colors.band-ink}"
    textColor: "{colors.band-yellow}"
    padding: "8px 12px"
    height: "38px"
  toggle:
    backgroundColor: "transparent"
    textColor: "{colors.ink-2}"
    rounded: "{rounded.none}"
    padding: "6px 11px"
    height: "38px"
  input:
    backgroundColor: "{colors.sheet}"
    textColor: "{colors.ink}"
    rounded: "{rounded.none}"
    padding: "7px 10px"
    height: "38px"
  featured-ad:
    backgroundColor: "{colors.sheet}"
    textColor: "{colors.ink}"
    rounded: "{rounded.none}"
    padding: "22px 24px"
  mark-new:
    backgroundColor: "{colors.vermilion}"
    textColor: "{colors.on-state}"
    typography: "{typography.mark}"
    padding: "1px 5px"
  segment-soft-checked:
    backgroundColor: "{colors.amber}"
    textColor: "{colors.on-state}"
    padding: "6px 10px"
    height: "34px"
  segment-hard-checked:
    backgroundColor: "{colors.vermilion}"
    textColor: "{colors.on-state}"
    padding: "6px 10px"
    height: "34px"
---

# Design System: Ofertas de empleo

## Overview

**Creative North Star: "The Classifieds Page"**

The dashboard is set like the "Ofertas de empleo" section of a newspaper: a process-yellow section band with a heavy ink rule on top, cool off-white newsprint below, and every posting composed as a classified ad whose job title is a bold condensed caps lead-in with the company, place and alerts run in after it. Hierarchy comes from size contrast and the width axis of a single variable family, not from boxes, cards, colour fills or charts. Numbers are set as type (score numerals, tallies) and charts are small, monochrome and secondary in the rail.

Density is high and calm: rows are separated by hairlines, groups by 3px ink rules, and only one element on the page, the featured ad, is framed. Colour is spent on meaning only: blue for links and actions, vermilion for new and hard discards, amber for penalized, green for matched salary and keywords. The dark theme swaps the paper for ink and keeps the yellow band unchanged.

The world explicitly refuses the generic SaaS dashboard arrangement of KPI cards, rounded panels and blue charts.

**Key Characteristics:**
- One family (Archivo variable), the width axis doing the hierarchy: 62% for display and numerals, 75% for lead-ins and sub-heads, 100% for text.
- Square corners everywhere; rules instead of boxes.
- A yellow section band with a 3px ink bottom rule as the shell, reused as the dialog head.
- Exactly one framed element per view: the featured ad (3px ink border).
- Tabular numerals throughout.
- Motion limited to 180ms expand and dim.

## Colors

Newsprint neutrals carrying one process yellow and a handful of semantic inks.

### Primary
- **Process Yellow** (band-yellow): the section band behind the title, tabs, folio and band actions, and the requirements dialog head. Also the text-selection colour. Never used for content surfaces or state.
- **Band Ink** (band-ink): text, rules, active tab fill and buttons on the yellow band. Identical in both themes so the band never changes.

### Secondary
- **Press Blue** (link-blue): links, "CV ATS" and "Abrir" row actions, focus outlines. Dark theme: #93b1ff.

### Tertiary (semantic only)
- **Vermilion** (vermilion): the NUEVA mark, the "Última/Hoy" run mark, "No cumple" outline mark, hard-discard requirement labels ("descarta"), the hard segment in the dialog, failed runs and errors. Dark theme: #ff6b55.
- **On-state text** (--on-state): text set on a vermilion or amber fill (NUEVA mark, checked Penalizar/Descartar segments). #ffffff in light, band ink #16130f in dark, where the fills turn light.
- **Burnt Amber** (amber): penalized state: PENALIZADA mark, soft alerts, "penaliza" labels, missing keywords. Dark theme: #f0b44c.
- **Ledger Green** (ledger-green): positive alerts (salary in range, "en tu zona") and matched keywords. Dark theme: #74d394.

### Neutral
- **Newsprint** (paper): page ground; dark theme #12110e.
- **Newsprint Shade** (paper-2): skeleton loaders; dark #1b1915.
- **Sheet** (sheet): featured ad, inputs, checked options; dark #1f1d18.
- **Press Ink** (ink): text, 3px rules, primary buttons; dark #ecebe4.
- **Ink 2** (ink-2): run-in text, secondary copy; dark #c4c0b5.
- **Ink 3** (ink-3): captions, help text, input strokes, dotted leaders; dark #a19c90.
- **Hairline** (hair): 1px row dividers and inactive toggle borders; dark #3b372f.
- **Fit ramp** (fit-high, fit-medium, fit-low): an ink-to-paper ramp for fit level in swatches and the "Publicadas por día" bars; dark #ecebe4 / #8f897d / #4a463e.

### Named Rules
**The Spent Colour Rule.** Vermilion, amber and green appear only as state; a coloured element must mean new, discarded, penalized or matched. Decoration is done with ink and rules.

**The Monochrome Data Rule.** Charts use the fit ramp of inks, never a hue palette.

## Typography

**Display Font:** Archivo variable (with system-ui, sans-serif), self-hosted at /fonts/archivo-latin.woff2, weights 100-900, widths 62-125%
**Body Font:** Archivo at 100% width
**Label/Mono Font:** none; labels are Archivo, numerals tabular

**Character:** A grotesque that condenses into newspaper-headline black at narrow widths and relaxes into a plain reading face at normal width; one family means the page reads as one publication.

### Hierarchy
- **Display** (900, 62% width, 128px, line-height 0.8): the featured ad's score numeral only; 88px on phone (display-phone). The same cut sets the rail tally at 60px and row scores at 30px (26px on phone): one numeral at three fixed desktop sizes.
- **Masthead** (900, 62%, 34px, uppercase): the band title; 24px on phone (masthead-phone). The dialog head title uses the same cut at 30px.
- **Headline** (900, 75%, 38px, line-height 1.02, uppercase, balanced): featured ad title; 30px on phone (headline-phone).
- **Section** (900, 62%, 28px, uppercase): day-group headings ("Última búsqueda", "Publicadas el 22 oct") over a 3px rule.
- **Empty title** (900, 75%, 20px, uppercase): the heading of an empty-list message.
- **Company** (600, 18px): the company · place line under the featured title.
- **Lead-in** (900, 75%, 16.5px, uppercase): the job title opening every classified row, followed by a period and run-in text. Rail headings (16px) and dialog group headings (15px) use the same cut.
- **Body** (400, 100%, 15px, line-height 1.45, tabular numerals): run-in text, snippets capped at 68-78ch.
- **Button** (700, 14px): buttons, tabs, facts row, requirement rows; 13px for band buttons on phone.
- **Label** (600-700, 13.5px): filter toggles, alerts, row actions, tab labels on phone.
- **Small** (600, 13px): band meta, section counts, mode and date, run list, preset note.
- **Caption** (400-600, 12.5px): help text, rail descriptions, featured note, keyword tags, legends, tooltip.
- **Phone meta** (600, 12px, line-height 1.3): band meta line on phone and run details.
- **Mark** (800, 11px, letter-spacing 0.05em, uppercase): state marks; small uppercase captions under numerals (11px, 700, 0.04em).
- **Chart** (600, 10.5px): axis labels in the rail's day chart.

### Named Rules
**The Width Axis Rule.** Hierarchy is made by width and size, not by new families or colours: 62% for numerals and section heads, 75% for titles and lead-ins, 100% for reading.

**The Lead-In Rule.** Every posting row begins with its title in 75% black caps, then runs in company, place and alerts in regular text on the same line.

## Layout

A centred column, max 1400px, 24px side padding (16px on phone). Under the band, a filter row separated by a hairline; below it a two-column grid: content `minmax(0, 1fr)` and a 320px rail, 40px gap. At 1040px the rail drops below the list (32px gap). At 760px the band wraps into two lines (title and tabs, then folio and actions), the filter toggles become one horizontally scrolling row, the featured ad stacks with its actions side by side, and rows collapse to a 40px numeral column with text, then mode · date and links on one line.

Classified rows use a four-column grid: 52px numeral, flexible text, 150px mode/date, auto actions, 16px column gap, 12px vertical padding. Groups are spaced 34px apart. The spacing rhythm steps 4 / 8 / 12 / 16 / 24 / 40px.

## Elevation & Depth

The page is flat. Depth on the page is made with rule weight: 1px hairlines between rows, 3px ink rules under section heads and the band, a 3px ink frame on the featured ad. Only floating layers that leave the page plane (tooltip, toast, dialog) carry a soft, diffuse black shadow, plus a 55% ink backdrop for the dialog.

### Shadow Vocabulary
- **Tooltip** (`box-shadow: 0 6px 18px rgba(0,0,0,.18)`): chart hover tooltip.
- **Toast** (`box-shadow: 0 8px 24px rgba(0,0,0,.2)`): bottom-centre confirmation.
- **Dialog** (`box-shadow: 0 18px 50px rgba(0,0,0,.3)`): requirements dialog.

### Named Rules
**The One Frame Rule.** Only the featured ad is boxed on the page. Everything else is separated by rules, not containers.

## Shapes

Square corners throughout (0px): buttons, inputs, toggles, marks, dialog, swatches. The only circle is the loading spinner. Borders carry state: 1px for resting controls, 2px for pressed toggles, buttons and segmented controls, 3px for rules and frames. Dashed borders mark expired postings; a dotted leader joins label and value in rail tallies.

## Components

### Buttons
Solid ink blocks that invert on hover.
- **Shape:** square (0px), 2px ink border, min-height 40px, 8px 16px padding, 14px weight 700, optional 16px stroke icon at 8px gap.
- **Primary:** ink fill, paper text; hover becomes transparent with ink text (150ms colour transition).
- **Ghost:** transparent with ink border; hover fills with ink.
- **On the band:** band-ink fill with yellow text, ghost variant outlined in band-ink; same inversion on hover. On phone the band buttons shrink to 36px and drop the long label.
- **Busy:** a 14px spinning ring replaces the icon; disabled at 0.6 opacity.

### Tabs
Text buttons in the band (14px, 700, min-height 38px); the active tab is a solid band-ink block with yellow text, hover is an 8% ink wash. Counts sit inside at weight 500.

### Chips (filter toggles)
- **Style:** transparent, 1px ink-3 border, 13.5px weight 600, min-height 38px; fit toggles carry a 10px square swatch.
- **State:** pressed is a 2px ink border with weight 800; unpressed fades to hairline border and ink-3 text.

### Cards / Containers (featured ad)
- **Corner Style:** square.
- **Background:** sheet.
- **Border:** 3px ink.
- **Internal Padding:** 22px 24px (18px phone).
- **Structure:** three columns: display score with caption, title block (headline, 18px company line, snippet, facts row), and an action column (190px) holding "Descargar CV ATS" primary, "Abrir oferta" ghost and a 12.5px note explaining why it is featured. Facts are set over a 2px top rule, coloured by state.

### Inputs / Fields
- **Style:** sheet fill, 1px ink-3 stroke, square, 7px 10px padding, min-height 38px.
- **Focus:** global 2px press-blue outline at 2px offset.
- **Segmented hardness control:** a 2px ink frame of labels divided by 1px ink; checked "No filtrar" fills ink, "Penalizar" fills amber, "Descartar" fills vermilion.

### Navigation
The yellow band is the only navigation: masthead, tabs, uppercase folio date (800, 0.03em) and the last-search line right-aligned, then Requisitos and Buscar ahora.

### Classified Row (signature)
Score numeral with uppercase fit caption, lead-in plus run-in text with inline state marks and coloured alerts, mode and date with real age, then "CV ATS" and "Abrir" blue links with 14px icons. Clicking the lead-in expands detail in place (180ms rise) and dims sibling rows to 0.42 opacity until hovered.

### State Marks
11px uppercase tags before the lead-in, one defined form per state: NUEVA solid vermilion, EVALUADA ink-2 outline, PENALIZADA amber outline, NO CUMPLE vermilion outline, DESCARTADA ink-3 fill with strike-through, CADUCADA dashed ink-3 outline.

### Rail Tallies
Rail sections open with a 75% caps heading over a 3px rule. Lists are label, dotted leader, 75% black numeral; the requirement count uses a 60px condensed numeral.

## Do's and Don'ts

### Do:
- **Do** open every posting row with a 75%-width, weight-900 uppercase lead-in and run the rest of the ad in on the same line.
- **Do** separate content with rules (1px hairline between items, 3px ink under headings) instead of boxes.
- **Do** keep the yellow band and its 3px band-ink rule identical in light and dark themes.
- **Do** set numerals in Archivo 62% black at the fixed sizes (128px, 60px, 30px) with tabular figures.
- **Do** state why a posting is hidden or penalized with a mark and coloured alert text.
- **Do** keep motion to the 180ms expand and dim, and drop it under prefers-reduced-motion.

### Don't:
- **Don't** introduce rounded corners, KPI cards or panel containers; the only framed element is the featured ad.
- **Don't** use vermilion, amber or green decoratively; they mean discarded/new, penalized and matched.
- **Don't** add a second type family; change width and weight on Archivo instead.
- **Don't** colour charts with a hue palette; use the fit ramp of inks.
- **Don't** put shadows on page-plane elements; only tooltip, toast and dialog float.
