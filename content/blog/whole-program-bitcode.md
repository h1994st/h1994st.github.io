+++
authors = ["Shengtuo Hu"]
title = "Two Ways to Extract Whole-Program Bitcode"
description = "rllvm and rules_rllvm solve the same problem from opposite ends: one poses as your compiler, the other asks the build system."
date = 2026-09-07T18:00:00-07:00
[taxonomies]
tags = ["LLVM", "Bazel", "Rust"]
[extra]
styles = ["css/diagrams.css"]
toc = true
toc_sidebar = true
+++

A compiler sees one source file at a time. That is the whole design: hand it a file,
get back an object file, repeat, and let the linker staple the results together. It
works so well that we forget it is a constraint.

It becomes a constraint the moment you want to analyze a program instead of build it.
Checking a property that spans function boundaries, running a custom compiler pass
over everything at once, auditing every call site of a risky API — each of these needs
the whole program in one piece, in a form built for analysis rather than for
execution. LLVM bitcode is that form: what the compiler works in after it has
understood your code but before it has turned it into machine instructions.

Getting bitcode for one file is easy. Getting it for a whole program, out of a real
build, is not. The difficulty is not that the information is missing but that the
build throws it away. After `make` finishes, nothing on disk records which source
files went into which binary, or how each one was compiled. The linker knew, briefly,
and did not write it down.

I have built two tools that recover it. They share a name, a goal, and almost no code,
because they come at the problem from opposite ends.

## rllvm: pose as the compiler

[rllvm](https://shengtuo.me/rllvm/) is a set of compiler wrappers written in Rust. You
point your build at them and build normally:

```bash
export CC=rllvm-cc CXX=rllvm-cxx
./configure && make
rllvm-get-bc ./myprogram      # produces myprogram.bc
```

### How it works

Underneath, each source file compiles twice: once to the object file your build
expects, and once to bitcode written off to the side. The second copy then has to be
findable again, and that is the interesting part. Every object file carries a small
extra section — a labelled region of bytes that object files can hold alongside code
and data — recording the path to that file's bitcode. The linker has no idea what that
section means, so it does the one thing linkers do with sections they do not
recognize: it concatenates them. The finished binary ends up carrying a complete list
of the bitcode files that make it up, assembled by a tool that does not know it is
helping.

<figure class="bc-fig bc-ledger" aria-label="Five source files each record one bitcode path, and the linker concatenates them into a single section naming the whole program">
<ol>
<li style="--i:0"><span class="src">parse.c</span><span class="tie" aria-hidden="true"></span><span class="bc">parse.bc</span></li>
<li style="--i:1"><span class="src">lexer.c</span><span class="tie" aria-hidden="true"></span><span class="bc">lexer.bc</span></li>
<li style="--i:2"><span class="src">codegen.c</span><span class="tie" aria-hidden="true"></span><span class="bc">codegen.bc</span></li>
<li style="--i:3"><span class="src">util.c</span><span class="tie" aria-hidden="true"></span><span class="bc">util.bc</span></li>
<li style="--i:4"><span class="src">main.c</span><span class="tie" aria-hidden="true"></span><span class="bc">main.bc</span></li>
</ol>
<figcaption>Each object file carries one line. The linker concatenates them into <b>__RLLVM,__rllvm_bc</b>, so the finished binary holds the whole list, and <b>rllvm-get-bc</b> reads it back out as <b>prog.bc</b>.</figcaption>
</figure>

I still think that is a good trick. It borrows the linker as an accumulator, and it
asks nothing of your project except permission to be its compiler — a knob every build
system already has.

### Where the idea came from

The trick is not mine. [wllvm](https://github.com/travitch/whole-program-llvm)
established it years ago with Python wrappers that build each file normally, build it
again as bitcode, and record where that bitcode landed in a section called `.llvm_bc`;
a companion tool, `extract-bc`, reads the section back out of the finished binary and
links the pieces together. [gllvm](https://github.com/SRI-CSL/gllvm) is the same
design rewritten in Go, and it runs faster for an unglamorous reason: it generates
bitcode in parallel where the Python wrappers fork and wait. The two differ mostly in
reach, as wllvm can drive gcc through the dragonegg plugin while gllvm is clang-only
and its README rules out combining it with link-time optimization.

rllvm is the third entry in that lineage, and the naming says so: `w` for
whole-program, `g` for Go, `r` for Rust. If gllvm or wllvm already work for you, there
is no urgency to switch.

### What rllvm adds

What rllvm adds, above all, is records that survive being moved. The original design
writes down where each bitcode file landed as an absolute path, which holds up exactly
as long as nothing moves. Rename the directory, run the build inside a container and
read the results outside it, or reuse a cached object file that another machine
compiled, and every recorded path names a directory that does not exist. What makes
this particular failure unpleasant is that extraction does not stop; it simply
resolves fewer files than it should and hands you a smaller program than you asked
for. rllvm can record those paths relative to a root you name at extraction time
instead. Because the section is plain text, both forms can appear in the same binary
and objects built before the change keep working.

The rest of what rllvm adds is reach. Turning on link-time optimization removes the
object file that the original mechanism needs to write into, so rllvm records the path
another way and hides the difference behind the same interface. Its rustc wrapper
copes with cargo naming outputs its own way, so a cargo build gives back bitcode with
dependency crates included. It produces whole-program bitcode for a linked WebAssembly
module rather than only for the pieces that went into it. For projects too large to
link in one pass it can stage the merge directory by directory, or produce an archive
instead. And `rllvm-info` reports what a module actually contains, which is worth more
than it sounds when the characteristic failure is an empty result.

### What it costs

The weaknesses follow from the same trick as the strengths. The section holds a path,
not the bitcode, so the binary is not self-contained: `make clean` breaks it, moving
the directory breaks it, and copying the binary to another machine breaks it. Storing
the bitcode itself would fix this, and I have a working prototype, but bitcode is
comparable to or larger than the object code it would ride along with, and I have not
been willing to pay that in binary size. Compiling every file twice is a real tax on a
large C++ project. And because a wrapper has to understand the compiler's command line
well enough to know what is being built, one misread flag is enough to make bitcode
stop appearing.

Linkers supply the rest of the difficulty, and each lesson arrived the hard way.
Nothing in the program references that extra section, so a linker that discards
unreferenced data throws it away unless it is explicitly marked to keep. The
WebAssembly linker deletes sections with certain LLVM-standard names while faithfully
keeping every other custom section, which is exactly why rllvm's sections are not
named after LLVM's.

## rules_rllvm: ask the build system

[rules_rllvm](https://shengtuo.me/rules_rllvm/) answers the same question for Bazel
builds, and it does not use rllvm to do it.

### Why I stopped wrapping rllvm

I did not start from scratch. I started by wrapping rllvm inside Bazel rules — keep
the wrappers, keep the sections, let Bazel drive them — and spent a while on it before
concluding it could not be made to work properly.

The obstacles were not details. Bazel keeps only the files an action declares in
advance as its outputs, so bitcode written off to the side gets discarded when the
action finishes and never comes back at all when the build runs on another machine.
The absolute paths recorded in those sections are wrong on any machine but the one
that compiled them, which quietly breaks a shared cache. Extraction afterwards is a
separate pass Bazel knows nothing about, so none of it is incremental or cached. And
depending on the rllvm binary tied the whole thing to one processor architecture,
which meant it would not run on my own laptop. Working around all of that meant asking
Bazel to stop doing the things people use Bazel for.

So I stopped wrapping and started again on a better premise. Bazel already knows the
dependency graph, and it already knows the exact command it used to compile every
file, because it built that command itself. A wrapper under Bazel spends all its
ingenuity recovering information that was never lost.

### How it works

These rules ask instead. They use a Bazel *aspect* — a piece of code that walks over
the targets you already have and attaches extra work to them, without you editing a
single build file. For each source file it finds, the aspect asks the toolchain for
the compile command Bazel was going to run anyway, changes where the output goes, and
declares the result as a proper build output. There is no compiler wrapper, nothing
hidden inside object files, and no absolute path anywhere in the results.

```bash
bazel build //:app_bc
```

### What living in the graph buys

The first thing this buys is that extraction costs nothing until somebody asks for it.
The bitcode files are not part of what a target normally produces; they sit in a
separate group you request by name, and Bazel runs work only when something needs its
output. An ordinary build runs none of it. That is what makes it reasonable to leave
these rules switched on in a repository other people share, because the people who
never wanted bitcode never pay for it.

The second is that every point in the dependency graph becomes an extraction point.
The bitcode travels up the graph node by node, which makes a library just as
addressable as a finished program. "Give me the bitcode for this one library, not
linked into anything" is a request the wrapper approach cannot express at all, because
reading those sections starts at the final binary.

Handling shared dependencies is where this earns its keep: each point in the graph
collects only its own source files, never its dependencies'. Folding a dependency's
bitcode into everything that uses it would include a shared library twice, and merging
then fails on the duplicate definitions. Instead the bitcode travels in a set that
treats the same file as the same file, so when two libraries both depend on a third,
the shared one contributes exactly one copy.

<figure class="bc-fig bc-graph" aria-label="A diamond dependency graph in which two libraries both depend on a third, which contributes one copy of its bitcode">
<svg viewBox="0 0 420 300" role="img">
<g class="edges">
<line x1="172" y1="66" x2="112" y2="128"/>
<line x1="248" y1="66" x2="308" y2="128"/>
<line x1="112" y1="172" x2="172" y2="234"/>
<line x1="308" y1="172" x2="248" y2="234"/>
</g>
<g class="node" style="--i:0">
<rect x="155" y="22" width="110" height="44" rx="8"/>
<text class="target" x="210" y="41">//:diamond</text>
<text class="bc" x="210" y="57">diamond.bc</text>
</g>
<g class="node" style="--i:1">
<rect x="37" y="128" width="110" height="44" rx="8"/>
<text class="target" x="92" y="147">//:lib_a</text>
<text class="bc" x="92" y="163">lib_a.bc</text>
</g>
<g class="node" style="--i:1">
<rect x="273" y="128" width="110" height="44" rx="8"/>
<text class="target" x="328" y="147">//:lib_b</text>
<text class="bc" x="328" y="163">lib_b.bc</text>
</g>
<g class="node shared" style="--i:2">
<rect x="155" y="234" width="110" height="44" rx="8"/>
<text class="target" x="210" y="253">//:lib_c</text>
<text class="bc" x="210" y="269">lib_c.bc</text>
</g>
</svg>
<figcaption>Both paths down from <b>//:diamond</b> arrive at <b>//:lib_c</b>. Because the bitcode travels in a set keyed on file identity, <b>lib_c.bc</b> is built once and merged once. The edges are dashed because they are declared during analysis and run nothing until an output group asks for them.</figcaption>
</figure>

The third is that the bitcode always matches the real compile. The aspect never
interprets a command line; it asks the toolchain for the command Bazel had already
built and changes only where the output goes. A wrapper has to understand flags it did
not write, and anything it misreads becomes bitcode that quietly differs from the
object that actually shipped. Here there is nothing to misread. For the same reason,
the work behaves like every other step in the build: scheduled, parallelized, cached,
and distributed across machines, with no special case for a shared cache because there
are no absolute paths to go stale.

### What it costs

The cost of all this is that it works with Bazel and nothing else, and with a recent
Bazel at that, since older-style workspace configuration is no longer supported. What
makes the approach clean is exactly what makes it narrow.

The smaller costs are worth naming too. A rule cannot mark itself as "do not build me
by default," so bitcode targets get swept up by a build-everything command unless
whoever writes them opts out. Running a one-off extraction without editing build files
works, but the incantation is clumsy and easy to get subtly wrong. Because the aspect
reuses the toolchain's own machinery, it is coupled to the internals of the LLVM and
Rust rule sets, and an upstream release can require changes here; I took that deal
deliberately, since deriving those commands independently would drift out of sync
silently, which is worse. It is also early software: not yet in Bazel's central
package registry, so depending on it takes an extra line. Objective-C works only on
macOS and needs an extra flag, and Swift does not work yet because the bitcode it
emits is newer than what the toolchain's LLVM tools will read.

## Which one to use

If you build with Bazel, use rules_rllvm. If you build with anything else, use rllvm.
That is the honest short answer, and the second half covers most existing C and C++
software.

| | rllvm | rules_rllvm |
|---|---|---|
| Build system | Any | Bazel only |
| How you adopt it | Set `CC` and build | Point an aspect at existing targets |
| Extract from | The finished binary | Any library or binary in the graph |
| Cost when unused | Every file compiles twice | Nothing runs |
| Result | Points at bitcode by path | Ordinary build outputs |
| Portability | The entire point | Not a goal |

The more useful question is what each tool assumes about your situation. Reach for
rllvm when you do not control the build — third-party source, a vendored tree,
reproducing somebody else's build — or when you need one method that behaves the same
across many projects that share no build system. Reach for rules_rllvm when you are
already using Bazel, and especially when you want bitcode for individual libraries,
when your builds are cached or spread across machines, or when you cannot afford to
double the cost of a build people run all day.

Neither is a strict upgrade on the other. rllvm buys portability with a second compile
and a result that points at files instead of containing them. rules_rllvm buys
precision and costs nothing when idle, by giving up every build system but one.

## What building both taught me

Where you get into the build decides everything else. Both tools answer the same
question, and nearly every difference between them follows from one choice about where
to intervene. rllvm intervenes at the compiler, which every build system can be told
to swap out, so it works everywhere and understands nothing about the project it sits
inside. rules_rllvm intervenes at the build system, which understands everything and
exists in exactly one place. Portability, cost, robustness, and what you can even
extract were not four decisions. They were one, and I did not see that clearly until I
had built the second tool.

Recovering what somebody already knows is a losing game when you have the option of
asking. rllvm's central trick reconstructs, after the fact, something the build never
bothered to record. That is satisfying to make work, and it is also labor that exists
only because nobody wrote the answer down. Under Bazel the answer is written down, and
reconstructing it anyway means maintaining a careful parser for command lines that the
build system generated itself. This does not make reconstruction bad. With make or
autotools there is nobody to ask, and reconstruction is the only approach that works
at all. It makes noticing which situation you are in the actual skill, because the
answer is a property of the environment rather than of the problem.

Trying to get both sets of benefits got me neither, which is what the pivot taught me.
Wrapping rllvm inside Bazel rules looked like reuse: one mechanism, one codebase, a
thin adapter. What it produced was the fragility of reconstruction plus a constant
fight with the guarantees that make Bazel worth using. The two designs are not layers.
They are alternatives, and the honest move was to stop making one wear the other as a
costume.

## What comes next

Extraction is a means, not an end. A `.bc` file matters only because something else
reads it, and plenty of things already do: symbolic execution engines like KLEE, and
static analysis frameworks like SVF and Phasar, all take whole-program bitcode as
their input. Getting that file out of a real build has always been the awkward step,
which is why tools like these exist at all.

The direction I find most interesting now is handing those facts to a coding
assistant. An assistant reading your source approximates the call graph by matching
names and patterns. It cannot know what actually reaches what once everything is
linked, and indirect calls make the guess worse. Bitcode knows. A small query
interface over a whole-program module — who calls this function, whether anything can
reach that one, what an indirect call might actually target — turns a guess into a
lookup. The answers have to come back as file and line numbers rather than as compiler
IR, because that is where the work happens.

For security review the useful output is evidence, not a verdict. Asking whether
attacker-controlled input can reach a risky function is a reachability question, and
the honest answer is the path itself, so a person can read those particular functions
and decide. Static analysis over-approximates. A tool that reports "vulnerable"
without showing its work has only moved the guessing somewhere else.

None of this is built yet, and two things would decide whether it works. The bitcode
has to be compiled with debug information and little optimization, or there is nothing
to map back to source. Indirect calls remain the hard problem they have always been.
But extraction that works per library and costs nothing when idle is a good substrate
for a loop that asks a question, changes a file, and asks again.

---

Both projects are Apache-2.0 and take issues and patches:
[rllvm](https://github.com/h1994st/rllvm) ·
[rules_rllvm](https://github.com/h1994st/rules_rllvm)