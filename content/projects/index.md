+++
title = "Projects"
description = "Side projects by Shengtuo Hu: rllvm and rules_rllvm for whole-program LLVM bitcode, Grammar-Mutator for AFL++, Chromatron Remake, my-resume, cairn and Hack The Box notes."
template = "projects.html"

# Everything below is rendered by templates/projects.html. Cards appear in
# this order and pack into a three-column grid (`wide` cards take two). A card
# shows its `banner` if it has one, otherwise its `icon`, an SVG in this
# directory that is inlined so its parts can animate, plus an optional
# `mascot` SVG sitting beside it. `tags` drive the filter.
# `url`s starting with "@/" are internal and resolved with get_url.
[extra]
styles = ["css/projects.css"]
scripts = ["js/projects.js"]
intro = "Things I build on the side: compiler tooling, fuzzing, a game I loved as a kid, and notes from breaking things on purpose."
filters = [
  { id = "tools", label = "Tools" },
  { id = "security", label = "Security" },
  { id = "games", label = "Games" },
]
more = { url = "https://github.com/h1994st", title = "More on GitHub", text = "My playground, CTF scripts and older research code" }

[[extra.projects]]
id = "rllvm"
name = "rllvm & rules_rllvm"
years = "2022 – now"
brand = "#2a7bff"
tags = ["tools"]
wide = true
banner = "rllvm-banner.png"
banner_fit = "contain"
term = { cmd = "$ rllvm-get-bc ./server", out = "→ server.bc" }
summary = "Extract whole-program LLVM bitcode from any build: compiler wrappers for Make, CMake and Cargo, and Bazel rules that need no wrapper at all."
links = [
  { label = "rllvm", url = "https://shengtuo.me/rllvm/", primary = true },
  { label = "rules_rllvm", url = "https://shengtuo.me/rules_rllvm/", primary = true },
]
[extra.projects.detail]
kicker = "Rust · Starlark · 2022 – now"
body = "Static analysis wants the whole program as one LLVM module, but a real build spreads it across hundreds of compile commands. These two get it back out without changing how you build."
parts = [
  { name = "rllvm", text = "Compiler wrappers for any build system. On Homebrew and crates.io, with a Claude Code plugin.", links = [
    { label = "Site", url = "https://shengtuo.me/rllvm/" },
    { label = "Code", url = "https://github.com/h1994st/rllvm" },
  ] },
  { name = "rules_rllvm", text = "Bazel rules: one lazy bitcode action per translation unit, no wrapper.", links = [
    { label = "Site", url = "https://shengtuo.me/rules_rllvm/" },
    { label = "Code", url = "https://github.com/h1994st/rules_rllvm" },
  ] },
]

[[extra.projects]]
id = "grammar-mutator"
name = "Grammar-Mutator"
years = "2020 – now"
brand = "#5b45d6"
tags = ["tools", "security"]
icon = "grammar-mutator.svg"
stars = 276
summary = "Grammar-based mutator for AFL++. My Google Summer of Code 2020 project, which I still maintain."
links = [
  { label = "Code", url = "https://github.com/AFLplusplus/Grammar-Mutator" },
]
[extra.projects.detail]
kicker = "C · AFL++ · 2020 – now"
body = "A custom mutator that lets AFL++ fuzz highly structured inputs, like JSON or Ruby, by mutating parse trees instead of bytes."
facts = [
  "Tree-based mutation and trimming, after Nautilus and F1",
  "An ANTLR4 shim that parses test cases at runtime",
  "Started in Google Summer of Code 2020, mentored by Marc Heuse and Andrea Fioraldi",
]

[[extra.projects]]
id = "my-resume"
name = "my-resume"
years = "2026"
brand = "#64748b"
tags = ["tools"]
icon = "my-resume.svg"
mascot = "duna.svg"
summary = "A résumé you can `git diff`, tailored per job with Claude Code."
links = [
  { label = "Site", url = "https://shengtuo.me/my-resume/", primary = true },
  { label = "Code", url = "https://github.com/h1994st/my-resume" },
]
[extra.projects.detail]
kicker = "XeLaTeX · Claude Code · 2026"
image = "my-resume.jpg"
image_alt = "Three sample resume pages from the template"
body = "One canonical LaTeX resume, tailored variants per job, facts defined once so they can't drift, and a template tested like code."

[[extra.projects]]
id = "chromatron"
name = "Chromatron Remake"
years = "2026"
brand = "#ff2a55"
tags = ["games"]
wide = true
banner = "@/blog/chromatron-remake/banner.jpg"
sweep = true
summary = "Chromatron 1–4, rebuilt in Rust for Apple Silicon and the browser. The game I played with my dad in 2006."
links = [
  { label = "Play", url = "https://shengtuo.me/chromatron-remake/", primary = true },
  { label = "Code", url = "https://github.com/h1994st/chromatron-remake" },
  { label = "Blog post", url = "@/blog/chromatron-remake/index.md" },
]
[extra.projects.detail]
kicker = "Rust · WebAssembly · Ghidra · 2026"
image = "@/blog/chromatron-remake/chromatron1-modern.jpg"
image_alt = "Chromatron, level 46 solved, in the modern look"
body = "Sean Barrett's laser puzzle games, rebuilt from a decompilation of the PowerPC originals. Four native Mac apps and the browser share one engine."

[[extra.projects]]
id = "cairn"
name = "cairn"
years = "2026"
brand = "#a07a55"
tags = ["security"]
icon = "cairn.svg"
summary = "Public CVEs reproduced in Rust, one crate each."
links = [
  { label = "Code", url = "https://github.com/h1994st/cairn" },
]
[extra.projects.detail]
kicker = "Rust · 2026"
body = "A cairn is a stack of stones that marks a route. Each CVE I reproduce is one stone: a self-contained crate with the same layout, notes and verification steps."
facts = [
  "Two reproductions so far, including Copy Fail (CVE-2026-31431)",
  "Public, patched bugs only, credited to the original researchers",
]

[[extra.projects]]
id = "htb"
name = "HTB notes"
years = "2025 – now"
brand = "#6fb300"
tags = ["security"]
icon = "htb.svg"
summary = "Hack The Box machines, written up step by step."
links = [
  { label = "Writeups", url = "@/blog/htb/_index.md", primary = true },
  { label = "Code", url = "https://github.com/h1994st/HTB" },
]
[extra.projects.detail]
kicker = "Writeups · 2025 – now"
body = "Hack The Box machines I've solved, written up step by step on this blog, with the notebooks and scripts on GitHub."
+++
