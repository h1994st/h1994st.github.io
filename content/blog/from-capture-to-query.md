+++
authors = ["Shengtuo Hu"]
title = "rllvm: From Capture to Query"
description = "rllvm-query adds an analysis step to the rllvm workflow. A real use-after-free in quiche shows what it can answer about a mixed C and Rust program, and what it still cannot."
date = 2026-09-21T18:00:00-07:00
[taxonomies]
tags = ["rllvm", "LLVM", "Rust", "Security", "Static Analysis"]
[extra]
styles = ["css/rllvm-ffi.css"]
toc = true
toc_sidebar = true
+++

## TL;DR

The first two posts in this series were about producing artifacts: extracting
[whole-program bitcode](@/blog/whole-program-bitcode.md), then keeping the
modules and their provenance in a
[catalog](@/blog/beyond-single-bitcode-file.md) instead of merging them away.
`rllvm-query` adds the step those were building toward. It reads a catalog and
answers questions in source terms: who defines this, who calls it, what does it
call, what path reaches it.

This post puts that step to work on a program written in two languages. The
example is CVE-2026-11941, a use-after-free in Cloudflare's quiche that is made
entirely of safe Rust and still hands C a pointer to freed memory. The queries
locate it, scan the rest of the library for the same shape, and then run out of
road in a place worth being precise about.

## A blind spot in mixed-language programs

Programs written in a single language are becoming the exception. A Rust crate
pulls in a `-sys` dependency and half of its real work happens in C. A C
codebase adopts Rust one module at a time.

The boundary between the two is the riskiest part of such a program. Ownership
stops being tracked there, error conventions stop matching, and who frees what
has to be written in a comment because no type carries it across. It is also the
one place that ordinary tooling does not look, for an understandable reason:
every ecosystem's index is scoped to its own build. `rust-analyzer` stops at the
`extern "C"` declaration, because Cargo compiled nothing past it. `clangd` never
heard of the Rust caller. `cargo audit` reasons over the dependency graph, which
suits crates and says nothing about the BoringSSL that a build script compiled
along the way. `unsafe` marks where Rust stops trusting itself, and stays silent
about the other side.

So the questions that matter most at the boundary are the ones nobody can ask.

## Getting both languages into one module

`rustc` and `clang` are both LLVM front ends. Once a call across the boundary
becomes an LLVM `call` instruction, the language has been erased: there is a
caller, a callee, and a source location for each. The boundary belongs to how we
build software rather than to the compiled program, so the whole job reduces to
capturing both halves at once. That used to take one environment variable. Now
it takes two.

```bash
export CC=rllvm-cc CXX=rllvm-cxx RUSTC_WRAPPER=rllvm-rustc
```

The [`examples/ffi`](https://github.com/h1994st/rllvm/tree/main/examples/ffi)
directory holds the smallest version of this I could write: two programs whose
call graphs cross the boundary, one led from each language, because the gap in
the tooling runs both ways.

<figure class="ffi-fig ffi-crossings" aria-label="Two small programs whose call graphs cross the FFI boundary, one led from Rust and one led from C">
<div class="ffi-group">
<span class="ffi-kicker">Rust-led</span>
<ol>
<li><span class="ffi-lang is-rust">Rust</span><span class="ffi-fn">main::main</span><span class="ffi-arrow">&#9656;</span><span class="ffi-lang is-c">C</span><span class="ffi-fn">c_double</span><span class="ffi-arrow">&#9656;</span><span class="ffi-lang is-rust">Rust</span><span class="ffi-fn">rust_add</span><span class="ffi-where">main.rs:12</span></li>
<li><span class="ffi-lang is-rust">Rust</span><span class="ffi-fn">main::main</span><span class="ffi-arrow">&#9656;</span><span class="ffi-lang is-cxx">C++</span><span class="ffi-fn">cxx_triple</span><span class="ffi-where">main.rs:13</span></li>
</ol>
</div>
<div class="ffi-group">
<span class="ffi-kicker">C-led</span>
<ol>
<li><span class="ffi-lang is-c">C</span><span class="ffi-fn">main</span><span class="ffi-arrow">&#9656;</span><span class="ffi-lang is-rust">Rust</span><span class="ffi-fn">rust_scale</span><span class="ffi-arrow">&#9656;</span><span class="ffi-lang is-c">C</span><span class="ffi-fn">c_offset</span><span class="ffi-where">c_main.c:8</span></li>
</ol>
</div>
<figcaption>One module holds all three languages, and each crossing is reported at the line that makes the call. Direction matters more than it looks: a Rust staticlib drags in a prebuilt <b>std</b> that never went through the wrapper, so whichever language leads decides how much of the program you can see.</figcaption>
</figure>

## A real bug where the languages meet

quiche is Cloudflare's QUIC and HTTP/3 library: a Cargo workspace that also
builds BoringSSL through a build script and exposes a C API behind a feature
flag. In June it published
[GHSA-mh64-ph39-mrc9](https://github.com/cloudflare/quiche/security/advisories/GHSA-mh64-ph39-mrc9),
CVE-2026-11941, a use-after-free in two of its FFI functions, fixed in 0.29.2.

The entire defect, from `quiche/src/ffi.rs` at 0.29.1:

```rust
impl<'a> Iterator for ConnectionIdIter<'a> {
    type Item = ConnectionId<'a>;

    fn next(&mut self) -> Option<Self::Item> {
        let v = self.cids.get(self.index)?;
        self.index += 1;
        Some(v.clone())            // an owned ConnectionId
    }
}

#[no_mangle]
pub extern "C" fn quiche_connection_id_iter_next(
    iter: &mut ConnectionIdIter,
    out: &mut *const u8,
    out_len: &mut size_t,
) -> bool {
    if let Some(conn_id) = iter.next() {   // owned; dropped below
        let id = conn_id.as_ref();
        *out = id.as_ptr();                // escapes to C
        *out_len = id.len();
        return true;
    }                                      // conn_id freed here

    false
}
```

There is no `unsafe` block. The borrow checker is satisfied and it is right to
be: `conn_id` is an owned value, dropped correctly at the end of its scope.
Every guarantee Rust makes holds.

What goes wrong is that a raw pointer into that value crossed an `extern "C"`
signature on the way out, and C reads it after the drop. Rust's ownership model
ends at the signature, and both halves of this program are correct on their own.

The C half is an ordinary loop. quiche's own C examples never touch this
iterator, so the caller below
([`cid_logger.c`](https://github.com/h1994st/rllvm/blob/main/examples/external/quiche/cid_logger.c))
ships with the rllvm example instead:

```c
static void log_source_ids(quiche_conn *conn) {
    quiche_connection_id_iter *iter = quiche_conn_source_ids(conn);

    const uint8_t *cid = NULL;
    size_t cid_len = 0;

    while (quiche_connection_id_iter_next(iter, &cid, &cid_len)) {
        for (size_t i = 0; i < cid_len; i++) {
            fprintf(stderr, "%02x", cid[i]);   // reads freed memory
        }
        fprintf(stderr, "\n");
    }

    quiche_connection_id_iter_free(iter);
}
```

<figure class="ffi-fig" aria-label="A timeline showing the ConnectionId being cloned, its pointer escaping to C, the value being dropped, and C reading the freed memory">
<div class="ffi-life">
<div class="ffi-step is-alive"><span class="ffi-side">Rust</span><span class="ffi-what">clone a <b>ConnectionId</b> out of the iterator<span class="ffi-at">ffi.rs:1157</span></span><span class="ffi-bar"></span></div>
<div class="ffi-step is-alive"><span class="ffi-side">Rust</span><span class="ffi-what">*out = id.as_ptr(), the pointer escapes<span class="ffi-at">ffi.rs:1158</span></span><span class="ffi-bar"></span></div>
<div class="ffi-step is-dead"><span class="ffi-side">Rust</span><span class="ffi-what">drop_glue::&lt;ConnectionId&gt;, the buffer is freed<span class="ffi-at">ffi.rs:1162</span></span><span class="ffi-bar"></span></div>
<div class="ffi-return">return to C, and out still holds the pointer</div>
<div class="ffi-step is-dead is-fault"><span class="ffi-side">C</span><span class="ffi-what">fprintf("%02x", cid[i])<span class="ffi-at">cid_logger.c:22</span></span><span class="ffi-bar"></span></div>
</div>
<figcaption>The solid bar is the value's lifetime; the dashed continuation is the pointer outliving it. Only the join between the two halves is wrong, and the join is what neither language's tooling reads.</figcaption>
</figure>

## Asking rllvm-query about it

What follows runs against quiche 0.29.1 with the FFI feature on, linked against
that C program.

```bash
git clone https://github.com/cloudflare/quiche && cd quiche
git checkout 0.29.1

export RUSTC_WRAPPER=rllvm-rustc CC=rllvm-cc
cargo build -p quiche --features ffi

MACOSX_DEPLOYMENT_TARGET=$(sw_vers -productVersion) \
  rllvm-cc -g -Iquiche/include cid_logger.c \
           target/debug/libquiche.a -o cid_logger

rllvm-get-bc cid_logger --output-dir cat
```

The deployment target is macOS housekeeping: the build script compiles
BoringSSL against the host SDK, and without it the link reports a few hundred
"built for newer macOS version" warnings. Plain `clang` does the same.

Every answer is JSON, so the readable form comes from `jq`:

```bash
CAT=cat/catalog.json
FN=quiche_connection_id_iter_next
```

The definition is Rust, and the caller is C, each reported at its own line:

```bash
rllvm-query --catalog $CAT defs $FN \
  | jq -r '.results[].location | "\(.file):\(.line)"'
#   quiche/src/ffi.rs:1154

rllvm-query --catalog $CAT callers $FN | jq -r '
  .results[] as $r | $r.call_sites[] | .location as $l
  | "\($r.function.symbol)  \($l.file|split("/")|last):\($l.line)"'
#   log_source_ids  cid_logger.c:20
```

`callees` on the FFI function is the bug in three lines. Rust symbols are
demangled into the envelope's `symbols` table, so the filter looks each one up
there and drops the panic-handling edges:

```bash
rllvm-query --catalog $CAT callees $FN | jq -r '
  .symbols as $s | .results[]
  | select(.target.kind == "direct")
  | ($s[.target.callee.symbol] // .target.callee.symbol) as $n
  | select($n | test("panic") | not)
  | .location as $l
  | "\($l.file|split("/")|last):\($l.line)  \($n)"'
```

```txt
ffi.rs:1157  <quiche::ffi::ConnectionIdIter as ...Iterator>::next
ffi.rs:1158  <quiche::packet::ConnectionId as ...AsRef<[u8]>>::as_ref
ffi.rs:1162  core::ptr::drop_glue::<quiche::packet::ConnectionId>
ffi.rs:1162  core::ptr::drop_glue::<quiche::packet::ConnectionId>
```

Clone, take a pointer, free. Run the same query against 0.29.2 and the
`drop_glue` lines are gone, because the fix stopped owning anything:

```txt
ffi.rs:1146  <alloc::vec::Vec<...ConnectionId> as ...Deref>::deref
ffi.rs:1146  <[quiche::packet::ConnectionId]>::get::<usize>
ffi.rs:1147  <quiche::packet::ConnectionId as ...AsRef<[u8]>>::as_ref
```

`reach` walks from the C entry point to the Rust function, and records the
crossing as its own kind of step:

```bash
rllvm-query --catalog $CAT reach main $FN | jq -r '.results[]
  | if .kind == "call" then "call     \(.function.symbol)"
    else "binding  \(.symbol)  (\(.status))" end'
```

```txt
call     main
call     log_source_ids
binding  quiche_connection_id_iter_next  (unique)
```

Two ordinary calls inside C, then a `binding`: a C declaration that resolved to
one candidate definition in a Rust module. The answer distinguishes a call it
observed from a link it resolved, and says which one carries the path.

## Scanning the whole FFI surface

Everything above starts from knowing the answer. The more useful question is
whether the bug has a shape you can search for, stated without reference to the
CVE:

> An `extern "C"` entry point hands C a raw pointer into a value, and then drops
> that value before returning.

In call-graph terms that is two conditions on one function's callees: something
that takes a pointer into `T`, and `drop_glue::<T>`. Both already appear in the
output, so the scan is a loop.

```bash
llvm-nm target/debug/libquiche.a 2>/dev/null \
  | awk '$2=="T" && $3 ~ /^_quiche_/ { print substr($3, 2) }' \
  | sort -u > surface.txt
wc -l < surface.txt        # 169 entry points

for fn in $(cat surface.txt); do
  rllvm-query --catalog $CAT callees "$fn" | jq -r --arg fn "$fn" '
    .symbols as $s
    | [ .results[] | (.target.callee.symbol // "") as $y
                   | ($s[$y] // $y) ] as $n
    | select(($n | any(test("drop_glue")))
         and ($n | any(test("::(as_ref|as_ptr|as_slice)$"))))
    | $fn'
done
```

Three details bite here. It has to be LLVM's `llvm-nm`, because rustc ships
`std` and `core` into the archive with embedded bitcode and a system `nm` built
on an older LLVM rejects it with `Unknown attribute kind`. Its stderr carries
harmless "no symbols" notes for empty members. And the `substr` drops Mach-O's
leading underscore, which the queries do not want; an ELF build matches
`/^quiche_/` and keeps the whole name.
Both quirks, and the fact that this step reaches outside the tool at all, are a
gap: the catalog already knows which functions a Rust module exported to C, so
`rllvm-query` should be able to list them itself
([#243](https://github.com/h1994st/rllvm/issues/243)).

169 entry points reduce to 7 candidates, and both functions the advisory names
are among them:

| Candidate | Reading it |
|---|---|
| `quiche_connection_id_iter_next` | **CVE-2026-11941** |
| `quiche_conn_retired_scid_next` | **CVE-2026-11941** |
| `quiche_conn_source_id` | safe: the dropped `ConnectionId` is the borrowed variant |
| `quiche_conn_destination_id` | safe: the same |
| `quiche_accept` | filter noise: the match was `Option::as_ref` |
| `quiche_conn_new_with_tls` | filter noise: the same |
| `quiche_h3_take_last_priority_update` | safe *if* the C callback behaves |

One caveat on how much this proves. I wrote the filter after reading the
advisory. The shape is general, since handing C a pointer into something you
then drop is a whole class of FFI bug. This run still does not establish that I
would have picked it blind. What it does establish is that the class fits in two
predicates over ordinary output, that it ranks both real defects into seven of a
hundred and sixty-nine, and that the signal disappears when the bug is fixed.

## Does it affect my build?

`cargo audit` gives one answer for any quiche below 0.29.2: vulnerable. The
advisory is more careful, and names the thing that actually decides it.

> Only applications using those FFI functions are affected. The FFI API is
> disabled by default by a build-time feature flag.

That is a whole-program question, with four different true answers depending on
how the program was built.

| Build | Definition present | Callers | What is true |
|---|---|---|---|
| default features | no | n/a | the code was never compiled |
| `--features ffi`, quiche's own `client.c` | yes | 0 | linked in, never called |
| `--features ffi`, a C app that iterates CIDs | yes | 1 | reachable |
| 0.29.2, same C app | yes | 1 | fixed |

The second row is worth sitting with. `nm` confirms
`_quiche_connection_id_iter_next` is in that binary as a defined symbol, and
`callers` still returns zero. Present and reachable are different facts, and
only one of them describes your risk.

For a caller that does exist, `callees` on it gives the order of operations, so
you can see what happens after the crossing:

```txt
blk 0 #7   line 15   quiche_conn_source_ids
blk 1 #1   line 20   quiche_connection_id_iter_next   <- the crossing
blk 4 #6   line 22   fprintf                          <- after it
blk 6 #1   line 24   fprintf                          <- after it
blk 7 #1   line 27   quiche_connection_id_iter_free
```

Anything sequenced after the crossing is a candidate consumer of a pointer that
Rust has already freed. The two `fprintf` calls are a three-line reading window.

<figure class="ffi-fig ffi-funnel" aria-label="Each step narrows the search: 169 FFI entry points, 7 candidates, 1 caller, 3 lines of C to read">
<div class="ffi-rung"><span class="ffi-count">169</span><span class="ffi-track"><span class="ffi-fill" style="--w:100%"></span></span><span class="ffi-label"><b>FFI entry points</b>, listed by nm</span></div>
<div class="ffi-rung"><span class="ffi-count">7</span><span class="ffi-track"><span class="ffi-fill" style="--w:34%"></span></span><span class="ffi-label"><b>candidates</b>: callees take a pointer into T and drop T</span></div>
<div class="ffi-rung"><span class="ffi-count">1</span><span class="ffi-track"><span class="ffi-fill" style="--w:16%"></span></span><span class="ffi-label"><b>caller</b>, with a file and a line</span></div>
<div class="ffi-rung"><span class="ffi-count">3</span><span class="ffi-track"><span class="ffi-fill" style="--w:7%"></span></span><span class="ffi-label"><b>lines of C</b> left to read</span></div>
<figcaption>The bars are illustrative rather than to scale. Every step is mechanical except the last one, which is the point: the tool decides where to look and a person decides what is there.</figcaption>
</figure>

## Where the answers stop

Five of those seven candidates are safe, for two different kinds of reason.

`ConnectionId` is a Cow-like type: `enum { Vec(Vec<u8>), Ref(&'a [u8]) }`.
`quiche_conn_source_id` drops one, but it drops the *borrowed* variant, so the
drop frees nothing and the pointer stays valid. The call graph sees
`drop_glue::<ConnectionId>` either way and cannot separate the two.

`quiche_accept` and `quiche_conn_new_with_tls` are the cheaper kind of wrong.
Both call `Option::as_ref`, a borrow helper that hands out no raw pointer at
all, and my filter matched on the method name. Neither function gives C a
pointer into anything it later drops, so the pattern never applied to them.

`quiche_h3_take_last_priority_update` is more interesting. It takes a pointer
into an owned `Vec<u8>`, passes it to a callback supplied by C, and frees the
buffer when the callback returns. Whether that is safe depends on what the C
callback does with the pointer, and the contract lives in a header comment that
nothing enforces. I called it safe above by reading the Rust and assuming the C
behaves. That was an assumption rather than an analysis.

The Cow case and the callback case ask the same question: does this pointer
outlive the value behind it? `rllvm-query` does not perform data-flow analysis,
so it cannot answer either.
The same limit shows up at indirect calls, where `indirect-targets` reports a
target set when LLVM recorded one and reports the callback above as unresolved.
Tracking a value through a store, which is how the C side would retain that
pointer, is outside what a call graph describes at all.

## What comes next

Two things, in the order I care about them.

The queries in this post form a short procedure: is the function here, does
anything call it, what happens after the crossing. Two of those steps can end
the investigation early. That belongs in tooling rather than in a blog post.
[Issue #188](https://github.com/h1994st/rllvm/issues/188) is a Claude Code
plugin bundling the MCP server with two skills: how to capture bitcode for the
build in front of you, and how to read an answer without over-claiming it. An
assistant reading source approximates a call graph by matching names, and across
an FFI boundary it cannot even approximate. The early exits matter most, because
"the version range matches, therefore you are affected" is the failure an agent
would otherwise reproduce at scale.

The second is the data flow this post kept needing. I would rather borrow that
than build it. [PhASAR](https://github.com/secure-software-engineering/phasar)
and [SVF](https://github.com/SVF-tools/SVF) have solved pointer and value
analysis for years, and have always taken whole-program C and C++ bitcode.
Getting that file out of a real build was the awkward step they were waiting on.
A module with Rust in it too is new input for tools that already work. Running
them behind the same query contract
([#149](https://github.com/h1994st/rllvm/issues/149),
[#242](https://github.com/h1994st/rllvm/issues/242)) is what would separate a
borrowed `ConnectionId` from an owned one, and say whether a pointer escapes
past a drop. The output should stay evidence: sources, sinks, and the path. A
tool that reports "vulnerable" without showing its work has only moved the
guessing somewhere else.

Indirect calls remain the hard problem they have always been. I do not expect
that to change soon, and the honest move is to keep saying so in the answer.

---

`rllvm` is Apache-2.0 and available on
[GitHub](https://github.com/h1994st/rllvm), including the
[FFI example](https://github.com/h1994st/rllvm/tree/main/examples/ffi) and
[notes on quiche](https://github.com/h1994st/rllvm/tree/main/examples/external/quiche)
used here. Measurements were taken on arm64 macOS against quiche 0.29.1 and
0.29.2, built with rustc 1.98.0 and read with LLVM 23.1.1.
