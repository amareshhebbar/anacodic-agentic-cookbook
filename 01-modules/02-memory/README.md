# 02 · Memory

**In → out, in 5 lines:** a conversation and a set of past decisions go in. What
the agent will actually carry into the next turn — and into the next session —
comes out. This stage is about the one thing a stateless model cannot do for
you: nothing is remembered unless the caller writes it down and sends it back.
Everything else here is a choice about *what* to write down, *where*, and *how
to find it again*.

Every notebook runs end to end with no API key.

## Short-term and long-term are different problems

| | Short-term | Long-term |
|---|---|---|
| Scope | one conversation | across sessions, indefinitely |
| Lives in | a list in the caller's process | a file on disk |
| Bounded by | the context window — a hard token ceiling | disk, and a retention policy |
| Fails by | dropping a fact that was stated too early | remembering a decision that should have been revised |
| Question it forces | what do I drop? | how do I find the right one again? |

The first two notebooks are those two columns. The third is the answer to the
long-term column's question, and it turns out to be machinery this repo already
has.

## Notebooks

| Notebook | What it proves | Needs a key? |
|---|---|---|
| [`01-short-term.ipynb`](01-short-term.ipynb) | A finite window forces a truncation policy, and the policy has a cost: a fact stated in turn 1 falls out of the window and the agent recommends a dish the user is allergic to. Ported from SafeBite's `_truncate_history`, flaws intact. | No. An optional Groq step re-runs the two prompts through a real model; without a key it says so and skips. |
| [`02-long-term.ipynb`](02-long-term.ipynb) | A decision written to a local JSON file is recovered by a genuinely separate `subprocess`, and the same mistake costs the same marks in a later session. Ported from TerrierTA's deduction memory. | No — stdlib `json` and the filesystem, nothing else. |
| [`03-semantic-recall.ipynb`](03-semantic-recall.ipynb) | Recall by meaning rather than recency, using `hash_embed` from `01-tools/03-embed` unchanged — and an honest demonstration of what a hash embedding cannot do. | No. An optional OpenAI step runs the same store on real embeddings. |

## Run it

```bash
pip install -r requirements.txt                      # from the repo root
jupyter notebook 01-modules/02-memory/01-short-term.ipynb
```

`02-long-term.ipynb` writes to `runs/memory/<course>/deductions.json` under the
repo root, resolved through `nbio.runs_dir()`. `runs/` is gitignored. Nothing
in this stage writes to S3, to a database, or to any cloud store — the whole
stage runs with no account anywhere, and that is a constraint, not a default.

## Design notes

**The donors.** `01-short-term.ipynb` ports SafeBite's `_truncate_history`
(`src/safe_bite/pipeline/orchestrator.py`) — keep the last 4 messages, cap
assistant messages at 150 characters. It is ported as written, including three
flaws that are demonstrated rather than fixed: the cut is by message count so a
verbose user is still over budget afterwards (Step 10), the 150-character cap
severs sentences mid-clause and can lose the operative half of a warning
(Step 11), and the earliest turns — where people state the things that matter
most — are exactly what goes first (Steps 5–8). A budget-aware alternative with
pinned facts appears in Step 12 as a *contrast*, not as a patch to the port.

`02-long-term.ipynb` ports TerrierTA's `services/deduction_memory.py` and the
consistency check from `services/memory_hooks.py`. This is the strongest memory
in the lab because it solves a real problem precisely: an LLM grader asked cold
will deduct 2 marks for a missing unit today and 5 tomorrow, confidently both
times. Writing the first decision down and reading it back before the second is
what makes grading consistent across a semester. Its three limits are also
shown: the consistency warning is advisory and the new value overwrites the old
one anyway (so the memory enforces agreement with the *most recent* decision,
not the first), the `items[-cap:]` eviction drops the oldest entry rather than
the least used even though `count` is stored, and `find_similar_deductions` is a
substring match despite its name.

**That last flaw is the bridge.** A paraphrase of a remembered mistake returns
`[]`, which is indistinguishable from "never seen before," so the grader falls
through to a cold default and the inconsistency happens anyway.
`03-semantic-recall.ipynb` picks it up.

**Memory and retrieval are the same mechanism.** `03-semantic-recall.ipynb`
exists to make that concrete rather than to introduce anything new. It copies
`hash_embed` out of
[`01-tools/03-embed/01-offline-embeddings.ipynb`](../01-tools/03-embed/01-offline-embeddings.ipynb)
without modification and points it at the agent's own past instead of at
document chunks. The ranking loop is the same three lines either way; Step 12
runs it over both corpora side by side. If you have read `03-embed` and
`04-retrieve`, you already know how semantic memory works.

**And it is honest about the hash.** A hash embedding is not semantically
meaningful. The notebook asserts only what it can actually guarantee — exact
self-recall scores 1.0, and a query sharing tokens with a memory outranks one
that does not — and then demonstrates the boundary with real output: a true
paraphrase (*"omitted dimensional annotation"* vs *"forgot the units"*) scores
exactly **0.0** against the memory it paraphrases and ranks an unrelated memory
first. Two unrelated memories score **0.52** against each other purely on shared
boilerplate, which drops to 0.0 once the filler words are stripped. A real
embedding model is what makes semantic recall work; the hash proves the
plumbing, not the semantics, and the optional Step 11 is where a real model
plugs in.

**No framework.** No LangChain `ConversationBufferMemory`, no LangGraph
checkpointer, no Strands session store. A reader should finish this stage able
to say exactly what those libraries are doing on their behalf — because all
three notebooks are plain lists, plain dicts, plain `json`, and one dot product.

## Files

```
02-memory/
├── README.md
├── 01-short-term.ipynb      truncation in one conversation, and what it costs
├── 02-long-term.ipynb       a decision that survives the process that made it
├── 03-semantic-recall.ipynb recall by meaning -- retrieval, pointed at the past
└── requirements.txt
```

## Not in scope

- **Deciding what is worth remembering.** Every memory in `03` is handed in
  ready-made. Summarising a conversation into durable facts — salience,
  deduplication against what is already stored, contradiction handling — is the
  hardest unsolved part of agent memory and is not attempted anywhere here.
- **Forgetting.** No decay, no relevance-weighted eviction. `02`'s Step 12 shows
  the cap TerrierTA actually ships and says plainly why it is the wrong one;
  nothing better is implemented.
- **A persistent vector index.** `03`'s `MemoryStore` is a Python list and a
  linear scan, rebuilt on every kernel start. Combining it with `02`'s file
  store and
  [`01-tools/03-embed/05-local-vector-store.ipynb`](../01-tools/03-embed/05-local-vector-store.ipynb)
  is the obvious next step this stage does not take.
- **Concurrency and multi-tenancy.** `save_deduction` is read-modify-write with
  no lock; two writers lose one write. The tenant scoping in the donor is
  replaced by a plain `course_id`.
