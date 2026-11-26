# Architecture of application code

Good practice for code written in this repo: the `.github/` tooling, and any project whose
author wants to follow it. It is not a rule and no CI checks it. The principles come from
the `ub-mode` skill next to this file; this file wins where they differ, and a project's own
rules apply on top of it. In this repo:

- *Push to the main line* becomes a pull request to `main`, merged once its CODEOWNERS approve.
- *Worktree Cleanup* happens after the merge, never before.

## Layers

| Layer | Holds | Imports |
|---|---|---|
| Domain | business types and pure functions: what to count, decide, write; the steps that call the ports | ports, utils, constants |
| Ports | every `Protocol` (or `interface`) the domain needs, in `ports.py`, and their errors | domain types |
| Adapters | one module per external system: CLI, API, database, CI platform, a file another process reads | ports, domain types, utils, constants |
| Utils | small helpers with no business rule and no vendor error (the clock, a `git` call) | constants |
| Entry point | builds the adapters, calls the domain, maps the outcome to outputs and exit code | everything |

- The domain does no I/O: `subprocess`, HTTP, SDKs, the clock, the filesystem, the
  environment and console output are reached through a port or an injected util.
- The domain writes no vendor format: command lines and flags, refs, status codes,
  platform Markdown, HTML markers, `owner/name`, file layouts. It decides the content and
  hands it over as a value; the vendor's adapter renders it.
- A port is named after a capability (`PaymentGateway`) and its methods after business
  actions (`charge`, `find_open`), never after vendor calls or storage verbs. Its
  arguments, values and errors are domain types. A port filters nothing: what to accept
  is a domain rule.
- An adapter holds no business rule, translates every vendor error into its port's
  error, and masks every secret in the errors it raises. It imports the domain types,
  never the rules or the steps. `TYPE_CHECKING` imports count.
- The domain types live in a module without the steps, so an adapter can import them
  without importing the code that calls it.
- The entry point holds no business decision. An option the program cannot run without
  is required. It receives its adapter factories as a parameter, so its tests pass fakes
  of the ports.
- Smallest design that holds these rules: a type exists when it carries a rule or a
  validation, a module when it has its own role.

```text
billing/invoice.py        Invoice, InvoiceLine, the outcomes
billing/rules.py          pure rules
billing/steps.py          plan the charge, run it, return the outcome
ports.py                  PaymentGateway, InvoiceArchive (Protocol) and their errors
adapters/stripe.py        StripePaymentGateway; Stripe errors -> PaymentRefused
adapters/stripe_bodies.py the Stripe payloads, used by adapters/stripe.py only
utils/clock.py            today in the team's timezone
cli.py                    builds the adapters, calls the steps, writes the outputs
constants.py              limits, labels, prefixes
```

## Rules

1. One decision lives in one place. When a rule needs two writes, the domain decides
   both; the adapter executes them. A partial failure is a state the domain names.
2. Dependencies are injected. Tests pass fakes of the ports; patching a module global
   means an injection is missing.
3. Outside data is parsed once, at the boundary, into domain types. A missing or null
   field is handled there, so one bad record cannot stop the run.
4. A rerun is idempotent: running twice, or after a crash halfway, ends in the same
   state. Look for the result first, then create it. A marker used to find an earlier
   result is matched exactly, at a fixed place.
5. A vendor list read with a limit that comes back full may miss records: the domain
   names that case in its outcome instead of truncating silently.
6. Types make illegal states impossible. A value with a format or a bound (an
   identifier, a number of days) is a type checked in its constructor. Distinct cases
   are a union of types, not optional fields.
7. A domain step returns its outcome as a value: done, refused with a reason, or a named
   partial state. The entry point reads the value and never parses an error message.
8. Outputs and exit codes follow the spec. A case the spec does not define takes the
   closest behavior the spec defines, and the report names it.
9. A self-contained tool with no business rule can stay a single module. The PR says
   why.

## Code

These apply to what a PR adds or renames; older code follows through its own ticket.

- Names say what the function does or returns, in business terms and full words. One
  concept has one name in every layer, and one name means one concept.
- At most two positional parameters, `self` and `cls` excluded; the others after `*`.
  Tests, `Protocol` implementations and dataclasses are exempt.
- Docstrings in full sentences on every public function and type: what it receives,
  returns or refuses, and why when the code does not show it.
- Meaningful literals go in the package's `constants.py`.

## Tests

- Domain tests use fakes of the ports. Vendor fakes (fake HTTP, fake CLI, scratch repo)
  serve adapter tests only.
- A rule is tested once, at its layer, its cases in one parametrized test. Entry point
  tests check the wiring with port fakes: outputs and exit code, one case per outcome.
- Each rerunnable step has a test that runs it twice and one after a failure halfway.

## Design before code

Write the plan before coding, as a table of layer, module and role. Before opening the PR,
check the imports against the layer table, grep the domain for vendor formats, list the
functions with more than two positional parameters, and run the quality gates.

## Quality gates

From the root of the project, on the files the branch changed, with the script of the
`ub-mode` skill:

```bash
uv run --script "$(git rev-parse --show-toplevel)/.claude/skills/ub-mode/scripts/quality.py" \
  --base origin/<target branch> --tests <pytest path of the changed package>
```

- **CRAP < 10** (`crap` gate) for every function of a changed file.
- **No duplicate pair ≥ 0.8** (`dry` gate) that involves a changed file.
- **Mutation** (`--gate mutate`): optional until it gives reliable results on uv
  projects. A surviving mutant the agent saw is killed or explained in the PR.

A failing gate is fixed, or the PR explains the exception (generated code, a function
the PR only moved). Code the branch does not touch never blocks.

## Review

A review that is asked to check this file reports a breach introduced by the PR as a
finding to fix, and a pre-existing breach in a touched file as a note.
