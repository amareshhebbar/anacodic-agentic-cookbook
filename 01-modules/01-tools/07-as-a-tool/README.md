# 07 · As a Tool

**In → out, in 5 lines:** an ordinary Python function goes in. A tool spec — a
name, a description, and a JSON argument schema — comes out, along with the
loop that chooses between two of them, calls one, and survives it failing.
This is where stages `01`–`06` stop being a pipeline and become one callable
thing, and where a second callable thing is added next to it. That second tool
is the line: with one tool there is no choice to make; with two there is, and
something has to make it.

## Why this stage is the keystone

`01-extract` through `06-bench` build one tool. They just don't call it one.
Six stages of extraction, chunking, embedding, retrieval, gating and
measurement collapse into this, which is everything an agent ever sees of
them:

```json
{"name": "search_documents",
 "description": "Search the indexed document corpus and return the passages most relevant to a query. ...",
 "parameters": {"type": "object",
                "properties": {"query": {"type": "string"}, "k": {"type": "integer", "default": 5}},
                "required": ["query"]}}
```

Everything after this stage — `02-memory`, `03-guardrails`, `04-orchestrate`,
`05-observe` — exists because of the choice point that appears in
`03-a-second-tool.ipynb`. A pipeline with one entry point needs none of them.

## Notebooks

| Notebook | Needs a key? |
|---|---|
| [`01-function-as-tool.ipynb`](01-function-as-tool.ipynb) | No. The spec builder, the registry, and the vague-vs-sharp description demo are stdlib only. The last cell sends the same two specs to a real model if `GROQ_API_KEY` or `OPENAI_API_KEY` is loaded; without one it says so and the deterministic chooser's result stands. |
| [`02-pipeline-as-tool.ipynb`](02-pipeline-as-tool.ipynb) | No, and it makes no network call of any kind. Extract → chunk → embed → retrieve → gate run in miniature over three documents written for the notebook, using the same hash embedding as `03-embed/01-offline-embeddings.ipynb`. |
| [`03-a-second-tool.ipynb`](03-a-second-tool.ipynb) | No. The tool choice comes from a deterministic word-overlap chooser. With a key loaded, the final cell asks a real model to make the same three choices and prints both answers side by side. |
| [`04-tool-failure.ipynb`](04-tool-failure.ipynb) | No. Every failure comes from a scripted service — no randomness, no network, no sleeping. With a key loaded, the final cell hands a real error message back to a real model and prints the call it makes next. |

Run them in order. `01` builds the spec that `02` puts a pipeline behind, `03`
adds the second tool, and `04` is what the loop in `03` needs before it can be
trusted with anything.

## Design notes

**No framework, on purpose.** No Strands, LangGraph, LangChain, or Bedrock
anywhere in this stage. Everything a framework's `@tool` decorator does is
about forty lines of `inspect` and `typing`, and it is all in
`01-function-as-tool.ipynb` where you can read it. Pick a framework afterwards
if you want one — but pick it knowing what it took over.

**The docstring is the input, not the documentation.** `01` proves this with
a swap: the same function, the same body, the same code object, one rewritten
`__doc__` — and the tool goes from never being picked to being picked. The
assertions in that notebook check that nothing executable changed.

**The stand-in chooser is not a model, and the notebooks say so every time.**
Word overlap with a crude plural fold, ties broken alphabetically. It is
reproducible, it needs no key, and it is honest about being cruder than the
thing it stands in for. `nbio.show_environment()` in the second cell of every
notebook tells the reader which path the output they are reading came from.

**The hash embedding's limits are shown, not hidden.** In `02`, an off-topic
query about quarterly revenue clears the score floor on the strength of the
shared words "in" and "the", and the notebook prints exactly that overlap. In
`03`, the retrieval tool ranks the shipping passage above the return-window
passage for a question about the return window, and the composing code has to
scan the shortlist rather than trust rank one. Both are real output from a
real run, left in because a score floor over vectors with no semantics is a
floor on a number and not a check on meaning.

**One question in `03` cannot be answered.** "My order shipped on 2026-08-02.
Is it too late to return it on 2026-09-04?" needs the handbook *and* the date
tool. A router that picks one tool returns the policy and stops. The notebook
composes both calls by hand and points at the hand-written part: deciding that
sequence automatically is `04-orchestrate`, not this stage.

**Retryable versus fatal is a judgement made at the raise site.** `04` keeps
`FatalToolError` outside the `ToolFailure` hierarchy so `safe_call` cannot
accidentally catch it, and measures the cost of getting it wrong: 12 turns
against an error that could never change, versus 1 and a halt. The third case
— a call that succeeds and returns a delivery date in 2125 — raises nothing at
all, and only a post-condition catches it.

## How to run

```bash
pip install -r ../../../requirements.txt   # repo root: jupyter, nbformat, python-dotenv
pip install -r requirements.txt            # this stage (optional SDKs only)
jupyter notebook 01-function-as-tool.ipynb
```

Every notebook runs end to end with no key, no account, and no network.

## Not in scope

- **Orchestration.** More than one tool call, in a decided sequence, with the
  result of the first shaping the second. `03` shows the question that needs
  it and stops there; it is `04-orchestrate`.
- **Memory.** Nothing here remembers a previous turn. The loop in `03` is
  question → tool → result, once, with no message history — which is why it
  cannot react to what a tool returned. That is `02-memory`.
- **Guardrails.** Nothing decides whether a tool is *allowed* to be called
  with the arguments it was given. `04` validates arguments against a schema;
  it does not authorize them. That is `03-guardrails`.
- **Tracing.** Every envelope in `04` is printed and dropped. Which tool was
  chosen, how often it failed, and what it cost is `05-observe`.
- **Real tool quality at scale.** Two tools with disjoint vocabularies is the
  smallest interesting number, not a realistic one. Choice quality degrades as
  tools multiply and their descriptions start to overlap, and nothing here
  measures that.
- **Provider differences.** The specs are emitted in the OpenAI-compatible
  `{"type": "function", "function": {...}}` shape that Groq also accepts.
  Other providers nest the same three fields differently; translating between
  them is mechanical and not taught here.
