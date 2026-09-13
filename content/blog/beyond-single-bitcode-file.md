+++
authors = ["Shengtuo Hu"]
title = "Beyond a Single Bitcode File"
description = "rllvm 0.5 keeps modules, provenance, and choices intact until an analysis is ready to use them."
date = 2026-09-13T18:00:00-07:00
[taxonomies]
tags = ["LLVM", "Rust", "Static Analysis"]
[extra]
styles = ["css/rllvm-substrate.css"]
toc = true
toc_sidebar = true
+++

## TL;DR

`rllvm` used to produce one answer: a merged whole-program `.bc` file. Version
0.5 can instead inventory the modules first, keep their identities and known
provenance in a catalog, select the ones an analysis needs, and only then copy,
archive, or merge them. It can acquire those modules from a wrapped build or
regenerate selected C and C++ compilations from `compile_commands.json`.

The original wrapper workflow still works. It now sits inside a larger model:
**acquire, catalog, select, materialize**.

## The `.bc` file was only the first output

In [my previous post](@/blog/whole-program-bitcode.md), I described `rllvm` as the
third tool in the `wllvm` and `gllvm` lineage: replace the compiler, build
normally, then recover one LLVM module from the linked program. I also wrote that
there was little urgency to switch if either older tool already worked for you.

That remains fair for the narrow job of producing one `.bc` file. It no longer
describes the whole project.

A merged module is useful, but merging is a poor first step. It collapses module
boundaries before a consumer can decide what belongs in an analysis. It also
hides useful distinctions: two compilations of the same source can use different
flags, a missing module is different from an unsupported one, and a module found
in an executable says something different from one regenerated from a compilation
database.

`rllvm` 0.5 makes the unmerged modules addressable. The whole-program file becomes
one possible output rather than the only interface.

## Modules before merging

`rllvm-info --json` now inventories bitcode, objects, executables, regular
archives, and existing catalogs without merging anything:

```bash
rllvm-info app --json > catalog.json
```

Each catalog entry has an opaque module ID and a content hash. Where available,
it also records source associations, target and data layout, compilation
configuration, debug-information presence, and diagnostics. A module can be
`available`, `missing`, `unsupported`, or `failed`; failure does not erase the
other evidence.

The catalog is deliberately careful about what it does not know. Finding a
source filename in debug information does not prove which compiler produced it.
Finding several modules in an archive does not prove that they form a complete
program. Those fields stay empty, and whole-program completeness stays unknown.

<figure class="substrate-fig substrate-acquire" aria-label="Two acquisition paths feed a module catalog: a wrapped build provides link membership, while a compilation database provides compilation configurations from the current source tree">
<div class="substrate-sources">
<div class="substrate-card">
<span class="substrate-kicker">live build</span>
<strong>object · archive · binary</strong>
<small>which modules reached the link</small>
</div>
<div class="substrate-card">
<span class="substrate-kicker">recorded build</span>
<strong>compile_commands.json</strong>
<small>how each source was compiled</small>
</div>
</div>
<div class="substrate-down" aria-hidden="true"><span></span><span></span></div>
<div class="substrate-catalog">
<span class="substrate-kicker">shared representation</span>
<strong>module catalog</strong>
<small>identity · integrity · provenance · uncertainty</small>
</div>
<figcaption>Both paths produce modules and the same catalog format, but they provide different evidence.</figcaption>
</figure>

## Two kinds of build evidence

The wrapper observes a real build. A path recorded in the finished executable is
evidence that the corresponding object participated in that link. This answers
the whole-program question, but the old path section does not record a complete
compiler identity, environment, or source snapshot.

A compilation database answers a different question. It preserves one command
per translation unit, so `rllvm-compdb` can list those entries and regenerate only
the current-tree modules an analysis asks for:

```bash
rllvm-compdb list build/ > compilations.json
rllvm-compdb generate build/ --source src/parser.c \
  --extra-arg=-O0 --output-dir analysis/parser
```

The importer keeps duplicate compilations distinct, records the original and
effective arguments, and puts failures beside successful modules. It does not
pretend to reconstruct the historical build. Generated headers must exist now,
the original environment is unknown, and a compile command says nothing about
which executable eventually used its object.

This distinction matters for analysis. Use wrapper capture when linked membership
is the fact you need. Use the compilation database when you want selected,
repeatable analysis compilations from the current tree.

## Select, then materialize

Catalogs can be filtered by module ID, source, or known configuration. Alternatives
within one selector are combined; different selector types intersect. An unmatched
selector is an error rather than an empty success.

```bash
rllvm-get-bc app --source src/parser.c --output-dir analysis/selected
rllvm-get-bc analysis/selected/catalog.json -o parser.bc
```

The first command copies separate, hash-checked modules into a new directory and
writes the catalog last. Its module paths are relative, so the directory can move
as a unit. The second command chooses to merge that collection. Archive and partial
merge strategies remain available when one large link is the wrong shape.

<figure class="substrate-fig substrate-materialize" aria-label="A module catalog is filtered before three possible outputs: a relocatable collection, a bitcode archive, or merged whole-program bitcode">
<div class="substrate-modules" aria-label="catalog modules">
<span><b>01</b> parse.c <i>debug</i></span>
<span><b>02</b> parse.c <i>release</i></span>
<span><b>03</b> lexer.c <i>release</i></span>
<span class="substrate-dim"><b>04</b> plugin.c <i>missing</i></span>
</div>
<div class="substrate-filter">
<span class="substrate-kicker">selection</span>
<strong>source + configuration</strong>
</div>
<div class="substrate-outputs">
<span>relocatable<br><b>collection</b></span>
<span>bitcode<br><b>archive</b></span>
<span>merged<br><b>.bc</b></span>
</div>
<figcaption>Selection preserves the useful boundary. Materialization can remain separate or merge only the chosen modules.</figcaption>
</figure>

## Real builds are mostly edge cases

The high-level model works only if acquisition survives actual compiler command
lines. Recent work therefore looks less glamorous and matters just as much.

Response files are expanded for classification while the real compiler still
receives the original arguments. Nested files, quoting, escapes, byte-order marks,
and relative paths follow Clang's rules. Commands generated by `rllvm` switch to
response files automatically when the operating system's argument limit would be
too small.

LTO needs separate handling because its “object” may already be bitcode. The
default marker mode covers full and ThinLTO on ELF and Mach-O; save-temps mode can
capture a full-LTO linker's optimized module. Rust needs crate-aware markers and
archive updates. Cross-target builds need architecture and sysroot choices to
survive secondary compilations.

eBPF was the pleasant counterexample. An eBPF object built through `rllvm-cc`
already carried the ordinary `.rllvm_bc` section. `libbpf` ignored that section
when loading the program and preserved it when linking objects. Supporting the
target required an integration test and documentation, not a new production
backend. A mechanism that composes with a tool it was not written for is a useful
kind of validation.

## Measuring the tax

Compiler wrappers are not free. C and C++ normally compile twice: once for the
native object and once for analysis bitcode. `rllvm` now has a reproducible
workflow harness that validates native behavior and extracted IR before accepting
a timing sample.

The first recorded baseline used an Apple M4, LLVM 22.1.8, eight build jobs, and
three repetitions. Clean build-only time relative to native compilation was:

| Workload | Cache off | Primed cache |
|---|---:|---:|
| nghttp2 C | 1.84× | 1.61× |
| nghttp2 C++ | 1.83× | 1.20× |
| Quiche | 1.59× | 1.50× |

The cache avoids repeated C/C++ bitcode compilation, but still preprocesses and
hashes current inputs before declaring a hit. It does not cache Rust compilation.
The measurements also had an uncontrolled filesystem cache and normal desktop
activity, so they are evidence for these workloads rather than a universal ratio.
They compare `rllvm` with native builds, not with `gllvm` or `wllvm`.

## The lineage now has a fork

`wllvm`, `gllvm`, and `rllvm` still share the same good trick: record sidecar
bitcode paths in object files and let the linker accumulate them. The older tools
center their interface on extracting a merged module or archive. `rllvm` now keeps
that workflow while adding another acquisition path and a representation between
capture and merge.

That does not make it a strict superset. `gllvm` supports Fortran and thin
archives; `wllvm` can drive GCC through dragonegg. But for Clang-based program
analysis, `rllvm` now exposes a much larger surface: Rust, WebAssembly and eBPF,
real LTO extraction, relocatable paths, validated caching, module catalogs,
selection, and compilation-database imports.

The meaningful difference is no longer implementation language or wrapper speed.
It is where the tool stops. The older workflow stops when it produces bitcode.
`rllvm` is starting to preserve the structure that the next tool will need.

## What comes next

[My previous post](@/blog/whole-program-bitcode.md#what-comes-next) ended with a
query interface for coding assistants: definitions, callers, callees,
reachability, possible indirect targets, and an inspectable path back to source.
The roadmap now gives that idea a clearer shape.

The first step is to make program facts easy to ask for. Scripts and coding
assistants should be able to query a catalog in source-level terms and receive
the locations and paths that support each answer. Missing modules, unresolved
calls, and unavailable mappings should remain visible rather than turning into
false certainty.

The second is to make the ask, edit, rebuild, ask loop practical. Unchanged work
should be reused without letting an answer from an older build appear current.
From there, simple reachability can grow into deeper security evidence when a
question needs it, and program facts can be compared across revisions or build
configurations. The useful result is still evidence a person can inspect, not an
automatic verdict.

The final direction is broader reach: following calls across Rust and C/C++
boundaries, and carrying a verified analysis snapshot to another machine after
the original build tree is gone.

The progression is from artifacts, to facts, to evidence. Extraction was the
prerequisite. The catalog is the substrate that keeps every later answer tied to
what was actually analyzed and what remains unknown.

---

`rllvm` is Apache-2.0 and available on
[GitHub](https://github.com/h1994st/rllvm). The repository includes the
[catalog schema](https://github.com/h1994st/rllvm/blob/main/docs/CATALOG.md) and
[benchmark evidence](https://github.com/h1994st/rllvm/tree/main/benchmarks/baselines/2026-09-12-apple-m4).
