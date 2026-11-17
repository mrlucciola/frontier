<!-- docfmt: ignore -- the bytes between file markers are extracted verbatim; do not normalize them. -->
# Portable Software Engineering Knowledge Base

This is a **single-file, copy/paste transport** for the current CLI-first knowledge base. It consolidates the original and CLI archives without duplicating superseded routes: 219 original row files are preserved; the old nested `AGENTS.md` files are replaced by the current `INDEX.md` routes. This is not a ZIP file and needs no download, archive utility, or Git.

## Installation (Python 3.9+, standard library only)

1. This document lives at `~/projects/frontier-clean/swe-kb/swe-kb-portable.md`, one directory *above* the extraction target `~/projects/frontier-clean/swe-kb/kb/`. Keep the HTML file markers intact. Do not wrap the document in an extra Markdown code fence.
2. In your terminal, run `mkdir -p ~/projects/frontier-clean/swe-kb/kb && cd ~/projects/frontier-clean/swe-kb/kb`.
3. Paste and run the following extractor block. It reads **only** `<!-- SWE-KB:FILE ... -->` / `<!-- SWE-KB:END -->` sections, writes only their indicated relative files, and refuses to overwrite different existing files. File permissions are restored for executable scripts.

```bash
python3 - <<'PY'
from pathlib import Path, PurePosixPath
import re

root = Path.cwd().resolve()  # Run from ~/projects/frontier-clean/swe-kb/kb/
bundle = root.parent / 'swe-kb-portable.md'
start = re.compile(rb'<!-- SWE-KB:FILE ([A-Za-z0-9._/-]+)(?: mode=(755))? -->\r?\n?')
end = b'<!-- SWE-KB:END -->'
entries = []
current = None
body = bytearray()

for line in bundle.read_bytes().splitlines(keepends=True):
    match = start.fullmatch(line)
    if match:
        if current is not None:
            raise SystemExit('Unclosed file section')
        relative = match.group(1).decode('ascii')
        p = PurePosixPath(relative)
        if (relative != p.as_posix() or p.is_absolute() or
            any(s in ('', '.', '..') for s in p.parts)):
            raise SystemExit(f'Unsafe relative path: {relative}')
        current = (relative, bool(match.group(2)))
        body = bytearray()
    elif line.rstrip(b'\r\n') == end:
        if current is None:
            raise SystemExit('Unexpected end marker')
        entries.append((*current, bytes(body)))
        current = None
    elif current is not None:
        body.extend(line)
if current is not None or not entries:
    raise SystemExit('Incomplete bundle or no file sections')

# Preflight the entire bundle before creating or updating anything.
seen = set()
planned = []
for relative, executable, contents in entries:
    if relative in seen:
        raise SystemExit(f'Duplicate file: {relative}')
    seen.add(relative)
    destination = (root / relative).resolve()
    if not destination.is_relative_to(root):
        raise SystemExit(f'Path escapes destination: {relative}')
    if destination.exists() and destination.read_bytes() != contents:
        raise SystemExit(f'Existing file differs; refusing overwrite: {relative}')
    planned.append((destination, executable, contents))

written = 0
for destination, executable, contents in planned:
    destination.parent.mkdir(parents=True, exist_ok=True)
    if not destination.exists():
        destination.write_bytes(contents)
        written += 1
    if executable:
        destination.chmod(0o755)
print(f'Files in bundle: {len(entries)}; created: {written}; already present: {len(entries) - written}')
PY
```

4. Optional verification from `~/projects/frontier-clean/swe-kb/kb/`:

```bash
python3 scripts/build-index.py --check
python3 -m unittest discover -s tests -v
./scripts/kb get DI
./scripts/kb search 'legacy migration'
```

The bundle is kept **outside** `kb/` because the KB index generator scans Markdown files inside that directory; otherwise the transport file would be mistaken for a knowledge entry. The extractor does not execute any extracted code.

## Files

Every section has a filepath marker. The bytes between the start and end markers become that file's exact contents. The only optional marker metadata is `mode=755` for executable scripts. No checksums, archive metadata, or redundant copies are included.

<!-- SWE-KB:FILE AGENTS.md -->
# Software Engineering Knowledge Base — Agent Entry Point

## Operating rules

- Work from the repository root for the commands shown below.
- **Exact lookup first:** `./scripts/kb get dependency-injection` (aliases including `DI` supported).
- **Discovery:** `./scripts/kb search "legacy migration"` or `rg -i "legacy" catalog.tsv aliases.tsv`.
- **Category navigation:** `./scripts/kb category design-patterns`.
- **Relations:** `./scripts/kb related dependency-injection`.
- **Direct path:** `./scripts/kb path strangler-fig`.
- **Metadata-only lookup:** `awk -F "\t" '$1=="strangler-fig" {print $5; exit}' catalog.tsv`.
- Read only the necessary concept files; do not bulk-load the catalog.
- Source files are **seed** data, not verified classifications or an exhaustive ontology.
- Never treat category placement or provisional relationship labels as independently validated facts.
- Preserve source rows, record IDs, and canonical concept IDs when adding knowledge.
- `cross-category-relationships/` contains source relationship records, **not canonical concepts**.
- Keep `AGENTS.md` procedural. Every category and table has a generated `INDEX.md`.
- Regenerate indexes: `python3 scripts/build-index.py`; verify: `python3 scripts/build-index.py --check`.

## Category routes

| Section | Command |
|---|---|
| `architectural-patterns` | `cat architectural-patterns/INDEX.md` |
| `cross-category-relationships` | `cat cross-category-relationships/INDEX.md` |
| `design-patterns` | `cat design-patterns/INDEX.md` |
| `implementation-techniques` | `cat implementation-techniques/INDEX.md` |
| `integration-patterns` | `cat integration-patterns/INDEX.md` |
| `software-design-principles` | `cat software-design-principles/INDEX.md` |

## Read without a helper CLI

```sh
awk -F "\t" '$1=="strangler-fig" {print $5; exit}' catalog.tsv
cat architectural-patterns/migration-and-modernization/strangler-fig.md
rg -in "dependency injection" catalog.tsv aliases.tsv
```

## Data contract

- `catalog.tsv`: one canonical entry per concept ID.
- `aliases.tsv`: exact, case-insensitive alternate-name resolution.
- `records.tsv`: all original source rows, including duplicates and relationship records.
- `relationships.tsv`: source-attributed **seed** edges; blank IDs mean unresolved references.
- `INDEX.md`: generated human-readable parent → child routes.
- Markdown leaf frontmatter: source of truth for identity, status, and category provenance.

## Pattern Language skill integration

- The skill invokes lookup and reads targeted Markdown; avoid embedding the knowledge base in its entrypoint.
- Concept selection, comparison, and reasoning remain with the skill, not this CLI.
- Run the index builder after changing leaf files; never manually edit TSV or INDEX outputs.

**Original source:** `Organize Software Concepts.txt`.
<!-- SWE-KB:END -->

<!-- SWE-KB:FILE README.md -->
# Software Engineering Knowledge Base (CLI-first)

A source-preserving Markdown inventory for progressive discovery and retrieval by CLI-based agents (including a future Pattern Language skill integration).

## First commands

From this directory:

```sh
./scripts/kb get dependency-injection
./scripts/kb get DI
./scripts/kb path strangler-fig
./scripts/kb search 'legacy migration'
./scripts/kb related DI
./scripts/kb category design-patterns
./scripts/kb sources dependency-injection-container
./scripts/kb check
```

Use `cat AGENTS.md` for the agent routing contract. Any category/table's `INDEX.md` links to its child folders and individual row files. All paths are relative to this repository root.

The CLI is a Python 3 standard-library executable with no third-party dependencies. It resolves the knowledge-base root from the executable location, so calling it from another working directory also works.

## Files and ownership

| File | Role | Edited manually? |
|---|---|---|
| `AGENTS.md` | Minimal agent entrypoint + deterministic commands | No (generated) |
| `*/INDEX.md` | Progressive hierarchical route map for every parent | No (generated) |
| `catalog.tsv` | One canonical row per concept ID | No (generated) |
| `aliases.tsv` | Unambiguous aliases, acronym resolution, and canonical IDs | No (generated) |
| `records.tsv` | Every original source row and its route | No (generated) |
| `relationships.tsv` | Source-attributed, provisional relationship rows | No (generated) |
| Concept `.md` | Source-preserving seed document and future discovery material | Yes |
| `scripts/build-index.py` | Deterministic index generator and checker | Yes |
| `scripts/kb` | Read-only lookup interface | Yes |

The original **219 row files** remain intact, including **14 cross-category relationship source records**. Of the other 205 source rows, one `concept_id` occurs in two tables; the lookup index therefore contains **204 canonical concepts**. Canonicalization here means selecting a primary lookup path, **not** merging or deleting row files. `kb sources <id>` lists all copies. Concept IDs are not renamed.

Original table classifications, definitions, and row text are treated as **unverified seed data**. The index does not claim to be an exhaustive ontology. Related concepts and common-pattern columns are only *source-attributed suggestions*. A blank `subject_id` or `object_id` in `relationships.tsv` means no unambiguous canonical match was found; it is **not** an error to be guessed away.

## Update workflow

1. Edit/add the relevant concept Markdown file, retaining its existing `record_id`/`concept_id` and source attribution. For new concepts, assign a unique stable ID. For alternate names, add an `aliases: Name, Another Name` frontmatter field (optional).
2. Rebuild derived files: `python3 scripts/build-index.py`.
3. Check consistency: `python3 scripts/build-index.py --check`.
4. Run tests: `python3 -m unittest discover -s tests -v`.

Do not manually edit generated TSVs, `INDEX.md` files, or root `AGENTS.md`. Add richer context/forces/tradeoffs/examples/references only when supported. The Pattern Language skill should retrieve these documents, and own interpretation and pattern selection rather than embedding the entire catalog in its instructions.

## Direct lookup without the helper

```sh
# Exact canonical ID → source path:
awk -F '\t' '$1=="strangler-fig" {print $5; exit}' catalog.tsv

# Directly read that concept:
cat architectural-patterns/migration-and-modernization/strangler-fig.md

# Discover an alias or name:
grep -inF 'DI' aliases.tsv
rg -i 'legacy migration|strangler' catalog.tsv
```

**Provenance:** `Organize Software Concepts.txt`, preserved in its original row-file arrangement.
<!-- SWE-KB:END -->

<!-- SWE-KB:FILE aliases.tsv -->
alias	id	normalized	origin
abstract-factory	abstract-factory	abstract-factory	id
active-record	active-record	active-record	id
Acyclic Dependencies Principle	acyclic-dependencies-principle-adp	acyclic-dependencies-principle	title-variant
acyclic-dependencies-principle-adp	acyclic-dependencies-principle-adp	acyclic-dependencies-principle-adp	id
adapter	adapter	adapter	id
adapter-wrappers	adapter-wrappers	adapter-wrappers	id
ADP	acyclic-dependencies-principle-adp	adp	acronym
aggregate	aggregate	aggregate	id
algebraic-data-types	algebraic-data-types	algebraic-data-types	id
anti-corruption-layer	anti-corruption-layer	anti-corruption-layer	id
api-composition	api-composition	api-composition	id
api-gateway	api-gateway	api-gateway	id
at-least-once-delivery	at-least-once-delivery	at-least-once-delivery	id
at-most-once-delivery	at-most-once-delivery	at-most-once-delivery	id
automated-refactoring	automated-refactoring	automated-refactoring	id
Backend for Frontend	backend-for-frontend-bff	backend-for-frontend	title-variant
backend-for-frontend-bff	backend-for-frontend-bff	backend-for-frontend-bff	id
backpressure	backpressure	backpressure	id
BFF	backend-for-frontend-bff	bff	acronym
Blue–Green Deployment	bluegreen-deployment	blue-green-deployment	title
bluegreen-deployment	bluegreen-deployment	bluegreen-deployment	id
branch-by-abstraction	branch-by-abstraction	branch-by-abstraction	id
bridge	bridge	bridge	id
builder	builder	builder	id
bulkhead	bulkhead	bulkhead	id
cache-aside	cache-aside	cache-aside	id
callback	callback	callback	id
canary-deployment	canary-deployment	canary-deployment	id
CCP	common-closure-principle-ccp	ccp	acronym
CDC	change-data-capture-cdc	cdc	acronym
cell-based-architecture	cell-based-architecture	cell-based-architecture	id
chain-of-responsibility	chain-of-responsibility	chain-of-responsibility	id
Change Data Capture	change-data-capture-cdc	change-data-capture	title-variant
change-data-capture-cdc	change-data-capture-cdc	change-data-capture-cdc	id
circuit-breaker	circuit-breaker	circuit-breaker	id
claim-check	claim-check	claim-check	id
clean-architecture	clean-architecture	clean-architecture	id
closures	closures	closures	id
code-generation	code-generation	code-generation	id
command	command	command	id
Command–Query Separation	commandquery-separation-cqs	command-query-separation	title-variant
Command–Query Separation (CQS)	commandquery-separation-cqs	command-query-separation-cqs	title
commandquery-separation-cqs	commandquery-separation-cqs	commandquery-separation-cqs	id
Common Closure Principle	common-closure-principle-ccp	common-closure-principle	title-variant
common-closure-principle-ccp	common-closure-principle-ccp	common-closure-principle-ccp	id
Common Reuse Principle	common-reuse-principle-crp	common-reuse-principle	title-variant
common-reuse-principle-crp	common-reuse-principle-crp	common-reuse-principle-crp	id
competing-consumers	competing-consumers	competing-consumers	id
composite	composite	composite	id
composition-over-inheritance	composition-over-inheritance	composition-over-inheritance	id
composition-root	composition-root	composition-root	id
constructor-injection	constructor-injection	constructor-injection	id
contract-testing	contract-testing	contract-testing	id
convention-over-configuration	convention-over-configuration	convention-over-configuration	id
copy-on-write	copy-on-write	copy-on-write	id
cqrs	cqrs	cqrs	id
CQS	commandquery-separation-cqs	cqs	acronym
CRP	common-reuse-principle-crp	crp	acronym
D — Dependency Inversion	d-dependency-inversion-dip	d-dependency-inversion	title-variant
d-dependency-inversion-dip	d-dependency-inversion-dip	d-dependency-inversion-dip	id
data-lakehouse	data-lakehouse	data-lakehouse	id
data-mapper	data-mapper	data-mapper	id
data-mesh	data-mesh	data-mesh	id
Data Transfer Object	data-transfer-object-dto	data-transfer-object	title-variant
data-transfer-object-dto	data-transfer-object-dto	data-transfer-object-dto	id
database-migrations	database-migrations	database-migrations	id
DbC	design-by-contract-dbc	dbc	acronym
dead-letter-queue	dead-letter-queue	dead-letter-queue	id
decorator	decorator	decorator	id
defense-in-depth	defense-in-depth	defense-in-depth	id
defensive-programming	defensive-programming	defensive-programming	id
delegation	delegation	delegation	id
dependency-abstraction	dependency-abstraction	dependency-abstraction	id
Dependency Injection	dependency-injection-di	dependency-injection	title-variant
dependency-injection-container	dependency-injection-container	dependency-injection-container	id
dependency-injection-di	dependency-injection-di	dependency-injection-di	id
Dependency Inversion	d-dependency-inversion-dip	dependency-inversion	title-variant
Dependency Inversion (DIP)	d-dependency-inversion-dip	dependency-inversion-dip	title-variant
dependency-mocking	dependency-mocking	dependency-mocking	id
Design by Contract	design-by-contract-dbc	design-by-contract	title-variant
design-by-contract-dbc	design-by-contract-dbc	design-by-contract-dbc	id
DI	dependency-injection-di	di	acronym
DIP	d-dependency-inversion-dip	dip	acronym
discriminated-unions	discriminated-unions	discriminated-unions	id
distributed-lock	distributed-lock	distributed-lock	id
domain-event	domain-event	domain-event	id
domain-service	domain-service	domain-service	id
dry	dry	dry	id
DTO	data-transfer-object-dto	dto	acronym
dual-write	dual-write	dual-write	id
dynamic-dispatch	dynamic-dispatch	dynamic-dispatch	id
EDA	event-driven-architecture-eda	eda	acronym
encapsulation	encapsulation	encapsulation	id
end-to-end-principle	end-to-end-principle	end-to-end-principle	id
entity	entity	entity	id
Event-Driven Architecture	event-driven-architecture-eda	event-driven-architecture	title-variant
event-driven-architecture-eda	event-driven-architecture-eda	event-driven-architecture-eda	id
event-sourcing	event-sourcing	event-sourcing	id
eventual-consistency	eventual-consistency	eventual-consistency	id
expand-and-contract	expand-and-contract	expand-and-contract	id
explicit-over-implicit	explicit-over-implicit	explicit-over-implicit	id
facade	facade	facade	id
factory-method	factory-method	factory-method	id
fail-fast	fail-fast	fail-fast	id
fault-isolation	fault-isolation	fault-isolation	id
favor-immutability	favor-immutability	favor-immutability	id
feature-flags	feature-flags	feature-flags	id
feature-toggles	feature-toggles	feature-toggles	id
flyweight	flyweight	flyweight	id
functional-core-imperative-shell	functional-core-imperative-shell	functional-core-imperative-shell	id
generics-parametric-polymorphism	generics-parametric-polymorphism	generics-parametric-polymorphism	id
graceful-degradation	graceful-degradation	graceful-degradation	id
health-check	health-check	health-check	id
heartbeat	heartbeat	heartbeat	id
Hexagonal / Ports & Adapters	hexagonal-ports-and-adapters	hexagonal-ports-adapters	title
hexagonal-ports-and-adapters	hexagonal-ports-and-adapters	hexagonal-ports-and-adapters	id
high-cohesion	high-cohesion	high-cohesion	id
higher-order-functions	higher-order-functions	higher-order-functions	id
I — Interface Segregation	i-interface-segregation-isp	i-interface-segregation	title-variant
i-interface-segregation-isp	i-interface-segregation-isp	i-interface-segregation-isp	id
idempotency	idempotency	idempotency	id
idempotent-consumer	idempotent-consumer	idempotent-consumer	id
identity-map	identity-map	identity-map	id
immutable-data-structures	immutable-data-structures	immutable-data-structures	id
information-hiding	information-hiding	information-hiding	id
interface-based-programming	interface-based-programming	interface-based-programming	id
interface-extraction	interface-extraction	interface-extraction	id
interface-injection	interface-injection	interface-injection	id
Interface Segregation	i-interface-segregation-isp	interface-segregation	title-variant
Interface Segregation (ISP)	i-interface-segregation-isp	interface-segregation-isp	title-variant
interpreter	interpreter	interpreter	id
Inversion of Control	inversion-of-control-ioc	inversion-of-control	title-variant
inversion-of-control-ioc	inversion-of-control-ioc	inversion-of-control-ioc	id
IoC	inversion-of-control-ioc	ioc	acronym
ISP	i-interface-segregation-isp	isp	acronym
iterator	iterator	iterator	id
kappa-architecture	kappa-architecture	kappa-architecture	id
kiss	kiss	kiss	id
L — Liskov Substitution	l-liskov-substitution-lsp	l-liskov-substitution	title-variant
l-liskov-substitution-lsp	l-liskov-substitution-lsp	l-liskov-substitution-lsp	id
lambda-architecture	lambda-architecture	lambda-architecture	id
layered-n-tier	layered-n-tier	layered-n-tier	id
lazy-evaluation	lazy-evaluation	lazy-evaluation	id
lazy-initialization	lazy-initialization	lazy-initialization	id
leader-election	leader-election	leader-election	id
Leader–Follower	leaderfollower	leader-follower	title
leaderfollower	leaderfollower	leaderfollower	id
lease	lease	lease	id
least-astonishment	least-astonishment	least-astonishment	id
linting	linting	linting	id
Liskov Substitution	l-liskov-substitution-lsp	liskov-substitution	title-variant
Liskov Substitution (LSP)	l-liskov-substitution-lsp	liskov-substitution-lsp	title-variant
load-balancer	load-balancer	load-balancer	id
low-coupling	low-coupling	low-coupling	id
LSP	l-liskov-substitution-lsp	lsp	acronym
manual-dependency-wiring	manual-dependency-wiring	manual-dependency-wiring	id
materialized-view	materialized-view	materialized-view	id
mediator	mediator	mediator	id
memento	memento	memento	id
memoization	memoization	memoization	id
message-broker	message-broker	message-broker	id
method-injection	method-injection	method-injection	id
microkernel-plugin	microkernel-plugin	microkernel-plugin	id
microservices	microservices	microservices	id
middleware-interceptor	middleware-interceptor	middleware-interceptor	id
modular-monolith	modular-monolith	modular-monolith	id
monolithic	monolithic	monolithic	id
null-object	null-object	null-object	id
O — Open/Closed	o-open-closed-ocp	o-open-closed	title-variant
o-open-closed-ocp	o-open-closed-ocp	o-open-closed-ocp	id
object-pool	object-pool	object-pool	id
observer	observer	observer	id
OCP	o-open-closed-ocp	ocp	acronym
onion-architecture	onion-architecture	onion-architecture	id
Open/Closed	o-open-closed-ocp	open-closed	title-variant
Open/Closed (OCP)	o-open-closed-ocp	open-closed-ocp	title-variant
orthogonality	orthogonality	orthogonality	id
parallel-run	parallel-run	parallel-run	id
peer-to-peer	peer-to-peer	peer-to-peer	id
pipes-and-filters	pipes-and-filters	pipes-and-filters	id
plugin	plugin	plugin	id
policy-object	policy-object	policy-object	id
Primary–Replica	primaryreplica	primary-replica	title
primaryreplica	primaryreplica	primaryreplica	id
principle-of-least-authority	principle-of-least-authority	principle-of-least-authority	id
principle-of-least-knowledge-law-of-demeter	principle-of-least-knowledge-law-of-demeter	principle-of-least-knowledge-law-of-demeter	id
principle-of-least-privilege	principle-of-least-privilege	principle-of-least-privilege	id
principle-of-reversibility	principle-of-reversibility	principle-of-reversibility	id
program-to-an-interface	program-to-an-interface	program-to-an-interface	id
property-based-testing	property-based-testing	property-based-testing	id
protected-variations	protected-variations	protected-variations	id
prototype	prototype	prototype	id
proxy	proxy	proxy	id
Publish–Subscribe	publishsubscribe	publish-subscribe	title
publishsubscribe	publishsubscribe	publishsubscribe	id
pure-functions	pure-functions	pure-functions	id
rate-limiter	rate-limiter	rate-limiter	id
read-through-cache	read-through-cache	read-through-cache	id
referential-transparency	referential-transparency	referential-transparency	id
registry	registry	registry	id
REP	reuse-release-equivalence-principle-rep	rep	acronym
repository	repository	repository	id
Request–Reply	requestreply	request-reply	title
requestreply	requestreply	requestreply	id
result-either	result-either	result-either	id
retry	retry	retry	id
retry-with-backoff	retry-with-backoff	retry-with-backoff	id
Reuse/Release Equivalence Principle	reuse-release-equivalence-principle-rep	reuse-release-equivalence-principle	title-variant
reuse-release-equivalence-principle-rep	reuse-release-equivalence-principle-rep	reuse-release-equivalence-principle-rep	id
S — Single Responsibility	s-single-responsibility-srp	s-single-responsibility	title-variant
s-single-responsibility-srp	s-single-responsibility-srp	s-single-responsibility-srp	id
saga	saga	saga	id
SAP	stable-abstractions-principle-sap	sap	acronym
Scatter–Gather	scattergather	scatter-gather	title
scattergather	scattergather	scattergather	id
schema-versioning	schema-versioning	schema-versioning	id
SDP	stable-dependencies-principle-sdp	sdp	acronym
self-contained-systems	self-contained-systems	self-contained-systems	id
Separation of Concerns	separation-of-concerns-soc	separation-of-concerns	title-variant
separation-of-concerns-soc	separation-of-concerns-soc	separation-of-concerns-soc	id
serverless	serverless	serverless	id
service-layer	service-layer	service-layer	id
service-locator	service-locator	service-locator	id
Service-Oriented Architecture	service-oriented-architecture-soa	service-oriented-architecture	title-variant
service-oriented-architecture-soa	service-oriented-architecture-soa	service-oriented-architecture-soa	id
setter-injection	setter-injection	setter-injection	id
shadow-traffic	shadow-traffic	shadow-traffic	id
sharding-partitioning	sharding-partitioning	sharding-partitioning	id
shared-nothing-architecture	shared-nothing-architecture	shared-nothing-architecture	id
sidecar	sidecar	sidecar	id
Single Responsibility	s-single-responsibility-srp	single-responsibility	title-variant
Single Responsibility (SRP)	s-single-responsibility-srp	single-responsibility-srp	title-variant
single-source-of-truth	single-source-of-truth	single-source-of-truth	id
singleton	singleton	singleton	id
SOA	service-oriented-architecture-soa	soa	acronym
SoC	separation-of-concerns-soc	soc	acronym
space-based-architecture	space-based-architecture	space-based-architecture	id
specification	specification	specification	id
SRP	s-single-responsibility-srp	srp	acronym
Stable Abstractions Principle	stable-abstractions-principle-sap	stable-abstractions-principle	title-variant
stable-abstractions-principle-sap	stable-abstractions-principle-sap	stable-abstractions-principle-sap	id
Stable Dependencies Principle	stable-dependencies-principle-sdp	stable-dependencies-principle	title-variant
stable-dependencies-principle-sdp	stable-dependencies-principle-sdp	stable-dependencies-principle-sdp	id
state	state	state	id
static-analysis	static-analysis	static-analysis	id
static-dispatch	static-dispatch	static-dispatch	id
strangler-fig	strangler-fig	strangler-fig	id
strategy	strategy	strategy	id
strong-consistency	strong-consistency	strong-consistency	id
tell-don-t-ask	tell-don-t-ask	tell-don-t-ask	id
template-method	template-method	template-method	id
test-doubles	test-doubles	test-doubles	id
timeout	timeout	timeout	id
timeout-budgeting	timeout-budgeting	timeout-budgeting	id
transactional-inbox	transactional-inbox	transactional-inbox	id
transactional-outbox	transactional-outbox	transactional-outbox	id
type-guards-refinement	type-guards-refinement	type-guards-refinement	id
unit-of-work	unit-of-work	unit-of-work	id
value-object	value-object	value-object	id
visitor	visitor	visitor	id
write-behind-cache	write-behind-cache	write-behind-cache	id
write-through-cache	write-through-cache	write-through-cache	id
yagni	yagni	yagni	id
zero-trust	zero-trust	zero-trust	id
<!-- SWE-KB:END -->

<!-- SWE-KB:FILE architectural-patterns/INDEX.md -->
# Architectural Patterns — Index

> Generated from source rows. Use the paths below from the repository root.

- **Back:** `cat AGENTS.md`
- **Search:** `./scripts/kb search "<term>"`

## Child routes

| Folder | Command |
|---|---|
| `data-and-communication/` | `cat architectural-patterns/data-and-communication/INDEX.md` |
| `migration-and-modernization/` | `cat architectural-patterns/migration-and-modernization/INDEX.md` |
| `system-structure/` | `cat architectural-patterns/system-structure/INDEX.md` |
<!-- SWE-KB:END -->

<!-- SWE-KB:FILE architectural-patterns/data-and-communication/INDEX.md -->
# Architectural Patterns/Data And Communication — Index

> Generated from source rows. Use the paths below from the repository root.

- **Back:** `cat architectural-patterns/INDEX.md`
- **Search:** `./scripts/kb search "<term>"`

## Source rows (17)

| Row | Direct command |
|---|---|
| API Gateway | `cat architectural-patterns/data-and-communication/api-gateway.md` |
| CQRS | `cat architectural-patterns/data-and-communication/cqrs.md` |
| Data Lakehouse | `cat architectural-patterns/data-and-communication/data-lakehouse.md` |
| Data Mesh | `cat architectural-patterns/data-and-communication/data-mesh.md` |
| Event Sourcing | `cat architectural-patterns/data-and-communication/event-sourcing.md` |
| Event-Driven Architecture (EDA) | `cat architectural-patterns/data-and-communication/event-driven-architecture-eda.md` |
| Kappa Architecture | `cat architectural-patterns/data-and-communication/kappa-architecture.md` |
| Lambda Architecture | `cat architectural-patterns/data-and-communication/lambda-architecture.md` |
| Leader–Follower | `cat architectural-patterns/data-and-communication/leaderfollower.md` |
| Message Broker | `cat architectural-patterns/data-and-communication/message-broker.md` |
| Peer-to-Peer | `cat architectural-patterns/data-and-communication/peer-to-peer.md` |
| Pipes and Filters | `cat architectural-patterns/data-and-communication/pipes-and-filters.md` |
| Primary–Replica | `cat architectural-patterns/data-and-communication/primaryreplica.md` |
| Publish–Subscribe | `cat architectural-patterns/data-and-communication/publishsubscribe.md` |
| Sharding / Partitioning | `cat architectural-patterns/data-and-communication/sharding-partitioning.md` |
| Shared-Nothing Architecture | `cat architectural-patterns/data-and-communication/shared-nothing-architecture.md` |
| Sidecar | `cat architectural-patterns/data-and-communication/sidecar.md` |
<!-- SWE-KB:END -->

<!-- SWE-KB:FILE architectural-patterns/data-and-communication/api-gateway.md -->
---
record_id: architectural-patterns--data-and-communication--api-gateway
concept_id: api-gateway
status: seed
source_table: architectural-patterns/data-and-communication
---

# API Gateway

> Seed record from `Organize Software Concepts.txt`. Classification and terminology are preserved from the source table; not independently verified.

| Field | Source value |
|---|---|
| Pattern | API Gateway |
| Purpose | Centralize API entry and cross-cutting concerns |
| Typical use | Microservices |

## Discovery extension

Add supporting references, context, tradeoffs, limitations, and validated relationships when reviewed; keep original source fields intact.
<!-- SWE-KB:END -->

<!-- SWE-KB:FILE architectural-patterns/data-and-communication/cqrs.md -->
---
record_id: architectural-patterns--data-and-communication--cqrs
concept_id: cqrs
status: seed
source_table: architectural-patterns/data-and-communication
---

# CQRS

> Seed record from `Organize Software Concepts.txt`. Classification and terminology are preserved from the source table; not independently verified.

| Field | Source value |
|---|---|
| Pattern | CQRS |
| Purpose | Separate read and write models |
| Typical use | Complex data access |

## Discovery extension

Add supporting references, context, tradeoffs, limitations, and validated relationships when reviewed; keep original source fields intact.
<!-- SWE-KB:END -->

<!-- SWE-KB:FILE architectural-patterns/data-and-communication/data-lakehouse.md -->
---
record_id: architectural-patterns--data-and-communication--data-lakehouse
concept_id: data-lakehouse
status: seed
source_table: architectural-patterns/data-and-communication
---

# Data Lakehouse

> Seed record from `Organize Software Concepts.txt`. Classification and terminology are preserved from the source table; not independently verified.

| Field | Source value |
|---|---|
| Pattern | Data Lakehouse |
| Purpose | Combine lake and warehouse capabilities |
| Typical use | Analytics platforms |

## Discovery extension

Add supporting references, context, tradeoffs, limitations, and validated relationships when reviewed; keep original source fields intact.
<!-- SWE-KB:END -->

<!-- SWE-KB:FILE architectural-patterns/data-and-communication/data-mesh.md -->
---
record_id: architectural-patterns--data-and-communication--data-mesh
concept_id: data-mesh
status: seed
source_table: architectural-patterns/data-and-communication
---

# Data Mesh

> Seed record from `Organize Software Concepts.txt`. Classification and terminology are preserved from the source table; not independently verified.

| Field | Source value |
|---|---|
| Pattern | Data Mesh |
| Purpose | Decentralize ownership of data products |
| Typical use | Enterprise analytics |

## Discovery extension

Add supporting references, context, tradeoffs, limitations, and validated relationships when reviewed; keep original source fields intact.
<!-- SWE-KB:END -->

<!-- SWE-KB:FILE architectural-patterns/data-and-communication/event-driven-architecture-eda.md -->
---
record_id: architectural-patterns--data-and-communication--event-driven-architecture-eda
concept_id: event-driven-architecture-eda
status: seed
source_table: architectural-patterns/data-and-communication
---

# Event-Driven Architecture (EDA)

> Seed record from `Organize Software Concepts.txt`. Classification and terminology are preserved from the source table; not independently verified.

| Field | Source value |
|---|---|
| Pattern | Event-Driven Architecture (EDA) |
| Purpose | Decouple components through events |
| Typical use | Async systems |

## Discovery extension

Add supporting references, context, tradeoffs, limitations, and validated relationships when reviewed; keep original source fields intact.
<!-- SWE-KB:END -->

<!-- SWE-KB:FILE architectural-patterns/data-and-communication/event-sourcing.md -->
---
record_id: architectural-patterns--data-and-communication--event-sourcing
concept_id: event-sourcing
status: seed
source_table: architectural-patterns/data-and-communication
---

# Event Sourcing

> Seed record from `Organize Software Concepts.txt`. Classification and terminology are preserved from the source table; not independently verified.

| Field | Source value |
|---|---|
| Pattern | Event Sourcing |
| Purpose | Persist state changes as events |
| Typical use | Audit-heavy domains |

## Discovery extension

Add supporting references, context, tradeoffs, limitations, and validated relationships when reviewed; keep original source fields intact.
<!-- SWE-KB:END -->

<!-- SWE-KB:FILE architectural-patterns/data-and-communication/kappa-architecture.md -->
---
record_id: architectural-patterns--data-and-communication--kappa-architecture
concept_id: kappa-architecture
status: seed
source_table: architectural-patterns/data-and-communication
---

# Kappa Architecture

> Seed record from `Organize Software Concepts.txt`. Classification and terminology are preserved from the source table; not independently verified.

| Field | Source value |
|---|---|
| Pattern | Kappa Architecture |
| Purpose | Process data primarily as streams |
| Typical use | Streaming systems |

## Discovery extension

Add supporting references, context, tradeoffs, limitations, and validated relationships when reviewed; keep original source fields intact.
<!-- SWE-KB:END -->

<!-- SWE-KB:FILE architectural-patterns/data-and-communication/lambda-architecture.md -->
---
record_id: architectural-patterns--data-and-communication--lambda-architecture
concept_id: lambda-architecture
status: seed
source_table: architectural-patterns/data-and-communication
---

# Lambda Architecture

> Seed record from `Organize Software Concepts.txt`. Classification and terminology are preserved from the source table; not independently verified.

| Field | Source value |
|---|---|
| Pattern | Lambda Architecture |
| Purpose | Combine batch and stream processing |
| Typical use | Big data |

## Discovery extension

Add supporting references, context, tradeoffs, limitations, and validated relationships when reviewed; keep original source fields intact.
<!-- SWE-KB:END -->

<!-- SWE-KB:FILE architectural-patterns/data-and-communication/leaderfollower.md -->
---
record_id: architectural-patterns--data-and-communication--leaderfollower
concept_id: leaderfollower
status: seed
source_table: architectural-patterns/data-and-communication
---

# Leader–Follower

> Seed record from `Organize Software Concepts.txt`. Classification and terminology are preserved from the source table; not independently verified.

| Field | Source value |
|---|---|
| Pattern | Leader–Follower |
| Purpose | Coordinate replicated services |
| Typical use | Database replication |

## Discovery extension

Add supporting references, context, tradeoffs, limitations, and validated relationships when reviewed; keep original source fields intact.
<!-- SWE-KB:END -->

<!-- SWE-KB:FILE architectural-patterns/data-and-communication/message-broker.md -->
---
record_id: architectural-patterns--data-and-communication--message-broker
concept_id: message-broker
status: seed
source_table: architectural-patterns/data-and-communication
---

# Message Broker

> Seed record from `Organize Software Concepts.txt`. Classification and terminology are preserved from the source table; not independently verified.

| Field | Source value |
|---|---|
| Pattern | Message Broker |
| Purpose | Mediate asynchronous communication |
| Typical use | Distributed services |

## Discovery extension

Add supporting references, context, tradeoffs, limitations, and validated relationships when reviewed; keep original source fields intact.
<!-- SWE-KB:END -->

<!-- SWE-KB:FILE architectural-patterns/data-and-communication/peer-to-peer.md -->
---
record_id: architectural-patterns--data-and-communication--peer-to-peer
concept_id: peer-to-peer
status: seed
source_table: architectural-patterns/data-and-communication
---

# Peer-to-Peer

> Seed record from `Organize Software Concepts.txt`. Classification and terminology are preserved from the source table; not independently verified.

| Field | Source value |
|---|---|
| Pattern | Peer-to-Peer |
| Purpose | Distribute responsibility among peers |
| Typical use | Blockchain, file sharing |

## Discovery extension

Add supporting references, context, tradeoffs, limitations, and validated relationships when reviewed; keep original source fields intact.
<!-- SWE-KB:END -->

<!-- SWE-KB:FILE architectural-patterns/data-and-communication/pipes-and-filters.md -->
---
record_id: architectural-patterns--data-and-communication--pipes-and-filters
concept_id: pipes-and-filters
status: seed
source_table: architectural-patterns/data-and-communication
---

# Pipes and Filters

> Seed record from `Organize Software Concepts.txt`. Classification and terminology are preserved from the source table; not independently verified.

| Field | Source value |
|---|---|
| Pattern | Pipes and Filters |
| Purpose | Process data through independent stages |
| Typical use | ETL, compilers |

## Discovery extension

Add supporting references, context, tradeoffs, limitations, and validated relationships when reviewed; keep original source fields intact.
<!-- SWE-KB:END -->

<!-- SWE-KB:FILE architectural-patterns/data-and-communication/primaryreplica.md -->
---
record_id: architectural-patterns--data-and-communication--primaryreplica
concept_id: primaryreplica
status: seed
source_table: architectural-patterns/data-and-communication
---

# Primary–Replica

> Seed record from `Organize Software Concepts.txt`. Classification and terminology are preserved from the source table; not independently verified.

| Field | Source value |
|---|---|
| Pattern | Primary–Replica |
| Purpose | Replicate data from an authoritative node |
| Typical use | Read scaling |

## Discovery extension

Add supporting references, context, tradeoffs, limitations, and validated relationships when reviewed; keep original source fields intact.
<!-- SWE-KB:END -->

<!-- SWE-KB:FILE architectural-patterns/data-and-communication/publishsubscribe.md -->
---
record_id: architectural-patterns--data-and-communication--publishsubscribe
concept_id: publishsubscribe
status: seed
source_table: architectural-patterns/data-and-communication
---

# Publish–Subscribe

> Seed record from `Organize Software Concepts.txt`. Classification and terminology are preserved from the source table; not independently verified.

| Field | Source value |
|---|---|
| Pattern | Publish–Subscribe |
| Purpose | Broadcast messages to subscribers |
| Typical use | Messaging systems |

## Discovery extension

Add supporting references, context, tradeoffs, limitations, and validated relationships when reviewed; keep original source fields intact.
<!-- SWE-KB:END -->

<!-- SWE-KB:FILE architectural-patterns/data-and-communication/sharding-partitioning.md -->
---
record_id: architectural-patterns--data-and-communication--sharding-partitioning
concept_id: sharding-partitioning
status: seed
source_table: architectural-patterns/data-and-communication
---

# Sharding / Partitioning

> Seed record from `Organize Software Concepts.txt`. Classification and terminology are preserved from the source table; not independently verified.

| Field | Source value |
|---|---|
| Pattern | Sharding / Partitioning |
| Purpose | Distribute data across partitions |
| Typical use | Large datasets |

## Discovery extension

Add supporting references, context, tradeoffs, limitations, and validated relationships when reviewed; keep original source fields intact.
<!-- SWE-KB:END -->

<!-- SWE-KB:FILE architectural-patterns/data-and-communication/shared-nothing-architecture.md -->
---
record_id: architectural-patterns--data-and-communication--shared-nothing-architecture
concept_id: shared-nothing-architecture
status: seed
source_table: architectural-patterns/data-and-communication
---

# Shared-Nothing Architecture

> Seed record from `Organize Software Concepts.txt`. Classification and terminology are preserved from the source table; not independently verified.

| Field | Source value |
|---|---|
| Pattern | Shared-Nothing Architecture |
| Purpose | Minimize shared infrastructure and state |
| Typical use | Distributed databases |

## Discovery extension

Add supporting references, context, tradeoffs, limitations, and validated relationships when reviewed; keep original source fields intact.
<!-- SWE-KB:END -->

<!-- SWE-KB:FILE architectural-patterns/data-and-communication/sidecar.md -->
---
record_id: architectural-patterns--data-and-communication--sidecar
concept_id: sidecar
status: seed
source_table: architectural-patterns/data-and-communication
---

# Sidecar

> Seed record from `Organize Software Concepts.txt`. Classification and terminology are preserved from the source table; not independently verified.

| Field | Source value |
|---|---|
| Pattern | Sidecar |
| Purpose | Attach supporting functionality to a workload |
| Typical use | Service meshes |

## Discovery extension

Add supporting references, context, tradeoffs, limitations, and validated relationships when reviewed; keep original source fields intact.
<!-- SWE-KB:END -->

<!-- SWE-KB:FILE architectural-patterns/migration-and-modernization/INDEX.md -->
# Architectural Patterns/Migration And Modernization — Index

> Generated from source rows. Use the paths below from the repository root.

- **Back:** `cat architectural-patterns/INDEX.md`
- **Search:** `./scripts/kb search "<term>"`

## Source rows (11)

| Row | Direct command |
|---|---|
| Anti-Corruption Layer | `cat architectural-patterns/migration-and-modernization/anti-corruption-layer.md` |
| Blue–Green Deployment | `cat architectural-patterns/migration-and-modernization/bluegreen-deployment.md` |
| Branch by Abstraction | `cat architectural-patterns/migration-and-modernization/branch-by-abstraction.md` |
| Canary Deployment | `cat architectural-patterns/migration-and-modernization/canary-deployment.md` |
| Change Data Capture (CDC) | `cat architectural-patterns/migration-and-modernization/change-data-capture-cdc.md` |
| Dual Write | `cat architectural-patterns/migration-and-modernization/dual-write.md` |
| Expand and Contract | `cat architectural-patterns/migration-and-modernization/expand-and-contract.md` |
| Feature Toggles | `cat architectural-patterns/migration-and-modernization/feature-toggles.md` |
| Parallel Run | `cat architectural-patterns/migration-and-modernization/parallel-run.md` |
| Shadow Traffic | `cat architectural-patterns/migration-and-modernization/shadow-traffic.md` |
| Strangler Fig | `cat architectural-patterns/migration-and-modernization/strangler-fig.md` |
<!-- SWE-KB:END -->

<!-- SWE-KB:FILE architectural-patterns/migration-and-modernization/anti-corruption-layer.md -->
---
record_id: architectural-patterns--migration-and-modernization--anti-corruption-layer
concept_id: anti-corruption-layer
status: seed
source_table: architectural-patterns/migration-and-modernization
---

# Anti-Corruption Layer

> Seed record from `Organize Software Concepts.txt`. Classification and terminology are preserved from the source table; not independently verified.

| Field | Source value |
|---|---|
| Pattern | Anti-Corruption Layer |
| Purpose | Translate between incompatible domain models |
| Typical use | Legacy integrations |

## Discovery extension

Add supporting references, context, tradeoffs, limitations, and validated relationships when reviewed; keep original source fields intact.
<!-- SWE-KB:END -->

<!-- SWE-KB:FILE architectural-patterns/migration-and-modernization/bluegreen-deployment.md -->
---
record_id: architectural-patterns--migration-and-modernization--bluegreen-deployment
concept_id: bluegreen-deployment
status: seed
source_table: architectural-patterns/migration-and-modernization
---

# Blue–Green Deployment

> Seed record from `Organize Software Concepts.txt`. Classification and terminology are preserved from the source table; not independently verified.

| Field | Source value |
|---|---|
| Pattern | Blue–Green Deployment |
| Purpose | Switch traffic between environments |
| Typical use | Deployment migration |

## Discovery extension

Add supporting references, context, tradeoffs, limitations, and validated relationships when reviewed; keep original source fields intact.
<!-- SWE-KB:END -->

<!-- SWE-KB:FILE architectural-patterns/migration-and-modernization/branch-by-abstraction.md -->
---
record_id: architectural-patterns--migration-and-modernization--branch-by-abstraction
concept_id: branch-by-abstraction
status: seed
source_table: architectural-patterns/migration-and-modernization
---

# Branch by Abstraction

> Seed record from `Organize Software Concepts.txt`. Classification and terminology are preserved from the source table; not independently verified.

| Field | Source value |
|---|---|
| Pattern | Branch by Abstraction |
| Purpose | Replace implementations behind stable interfaces |
| Typical use | Continuous migration |

## Discovery extension

Add supporting references, context, tradeoffs, limitations, and validated relationships when reviewed; keep original source fields intact.
<!-- SWE-KB:END -->

<!-- SWE-KB:FILE architectural-patterns/migration-and-modernization/canary-deployment.md -->
---
record_id: architectural-patterns--migration-and-modernization--canary-deployment
concept_id: canary-deployment
status: seed
source_table: architectural-patterns/migration-and-modernization
---

# Canary Deployment

> Seed record from `Organize Software Concepts.txt`. Classification and terminology are preserved from the source table; not independently verified.

| Field | Source value |
|---|---|
| Pattern | Canary Deployment |
| Purpose | Gradually expose users to new implementations |
| Typical use | Risk-controlled rollout |

## Discovery extension

Add supporting references, context, tradeoffs, limitations, and validated relationships when reviewed; keep original source fields intact.
<!-- SWE-KB:END -->

<!-- SWE-KB:FILE architectural-patterns/migration-and-modernization/change-data-capture-cdc.md -->
---
record_id: architectural-patterns--migration-and-modernization--change-data-capture-cdc
concept_id: change-data-capture-cdc
status: seed
source_table: architectural-patterns/migration-and-modernization
---

# Change Data Capture (CDC)

> Seed record from `Organize Software Concepts.txt`. Classification and terminology are preserved from the source table; not independently verified.

| Field | Source value |
|---|---|
| Pattern | Change Data Capture (CDC) |
| Purpose | Replicate database changes |
| Typical use | Data migration |

## Discovery extension

Add supporting references, context, tradeoffs, limitations, and validated relationships when reviewed; keep original source fields intact.
<!-- SWE-KB:END -->

<!-- SWE-KB:FILE architectural-patterns/migration-and-modernization/dual-write.md -->
---
record_id: architectural-patterns--migration-and-modernization--dual-write
concept_id: dual-write
status: seed
source_table: architectural-patterns/migration-and-modernization
---

# Dual Write

> Seed record from `Organize Software Concepts.txt`. Classification and terminology are preserved from the source table; not independently verified.

| Field | Source value |
|---|---|
| Pattern | Dual Write |
| Purpose | Write to multiple systems during transition |
| Typical use | Storage migration |

## Discovery extension

Add supporting references, context, tradeoffs, limitations, and validated relationships when reviewed; keep original source fields intact.
<!-- SWE-KB:END -->

<!-- SWE-KB:FILE architectural-patterns/migration-and-modernization/expand-and-contract.md -->
---
record_id: architectural-patterns--migration-and-modernization--expand-and-contract
concept_id: expand-and-contract
status: seed
source_table: architectural-patterns/migration-and-modernization
---

# Expand and Contract

> Seed record from `Organize Software Concepts.txt`. Classification and terminology are preserved from the source table; not independently verified.

| Field | Source value |
|---|---|
| Pattern | Expand and Contract |
| Purpose | Evolve schemas and APIs compatibly |
| Typical use | Zero-downtime migration |

## Discovery extension

Add supporting references, context, tradeoffs, limitations, and validated relationships when reviewed; keep original source fields intact.
<!-- SWE-KB:END -->

<!-- SWE-KB:FILE architectural-patterns/migration-and-modernization/feature-toggles.md -->
---
record_id: architectural-patterns--migration-and-modernization--feature-toggles
concept_id: feature-toggles
status: seed
source_table: architectural-patterns/migration-and-modernization
---

# Feature Toggles

> Seed record from `Organize Software Concepts.txt`. Classification and terminology are preserved from the source table; not independently verified.

| Field | Source value |
|---|---|
| Pattern | Feature Toggles |
| Purpose | Enable or disable behavior dynamically |
| Typical use | Incremental releases |

## Discovery extension

Add supporting references, context, tradeoffs, limitations, and validated relationships when reviewed; keep original source fields intact.
<!-- SWE-KB:END -->

<!-- SWE-KB:FILE architectural-patterns/migration-and-modernization/parallel-run.md -->
---
record_id: architectural-patterns--migration-and-modernization--parallel-run
concept_id: parallel-run
status: seed
source_table: architectural-patterns/migration-and-modernization
---

# Parallel Run

> Seed record from `Organize Software Concepts.txt`. Classification and terminology are preserved from the source table; not independently verified.

| Field | Source value |
|---|---|
| Pattern | Parallel Run |
| Purpose | Execute old and new implementations together |
| Typical use | Migration validation |

## Discovery extension

Add supporting references, context, tradeoffs, limitations, and validated relationships when reviewed; keep original source fields intact.
<!-- SWE-KB:END -->

<!-- SWE-KB:FILE architectural-patterns/migration-and-modernization/shadow-traffic.md -->
---
record_id: architectural-patterns--migration-and-modernization--shadow-traffic
concept_id: shadow-traffic
status: seed
source_table: architectural-patterns/migration-and-modernization
---

# Shadow Traffic

> Seed record from `Organize Software Concepts.txt`. Classification and terminology are preserved from the source table; not independently verified.

| Field | Source value |
|---|---|
| Pattern | Shadow Traffic |
| Purpose | Replay production requests without affecting responses |
| Typical use | System validation |

## Discovery extension

Add supporting references, context, tradeoffs, limitations, and validated relationships when reviewed; keep original source fields intact.
<!-- SWE-KB:END -->

<!-- SWE-KB:FILE architectural-patterns/migration-and-modernization/strangler-fig.md -->
---
record_id: architectural-patterns--migration-and-modernization--strangler-fig
concept_id: strangler-fig
status: seed
source_table: architectural-patterns/migration-and-modernization
---

# Strangler Fig

> Seed record from `Organize Software Concepts.txt`. Classification and terminology are preserved from the source table; not independently verified.

| Field | Source value |
|---|---|
| Pattern | Strangler Fig |
| Purpose | Incrementally replace an existing system |
| Typical use | Legacy modernization |

## Discovery extension

Add supporting references, context, tradeoffs, limitations, and validated relationships when reviewed; keep original source fields intact.
<!-- SWE-KB:END -->

<!-- SWE-KB:FILE architectural-patterns/system-structure/INDEX.md -->
# Architectural Patterns/System Structure — Index

> Generated from source rows. Use the paths below from the repository root.

- **Back:** `cat architectural-patterns/INDEX.md`
- **Search:** `./scripts/kb search "<term>"`

## Source rows (14)

| Row | Direct command |
|---|---|
| Backend for Frontend (BFF) | `cat architectural-patterns/system-structure/backend-for-frontend-bff.md` |
| Cell-Based Architecture | `cat architectural-patterns/system-structure/cell-based-architecture.md` |
| Clean Architecture | `cat architectural-patterns/system-structure/clean-architecture.md` |
| Hexagonal / Ports & Adapters | `cat architectural-patterns/system-structure/hexagonal-ports-and-adapters.md` |
| Layered / N-Tier | `cat architectural-patterns/system-structure/layered-n-tier.md` |
| Microkernel / Plugin | `cat architectural-patterns/system-structure/microkernel-plugin.md` |
| Microservices | `cat architectural-patterns/system-structure/microservices.md` |
| Modular Monolith | `cat architectural-patterns/system-structure/modular-monolith.md` |
| Monolithic | `cat architectural-patterns/system-structure/monolithic.md` |
| Onion Architecture | `cat architectural-patterns/system-structure/onion-architecture.md` |
| Self-Contained Systems | `cat architectural-patterns/system-structure/self-contained-systems.md` |
| Serverless | `cat architectural-patterns/system-structure/serverless.md` |
| Service-Oriented Architecture (SOA) | `cat architectural-patterns/system-structure/service-oriented-architecture-soa.md` |
| Space-Based Architecture | `cat architectural-patterns/system-structure/space-based-architecture.md` |
<!-- SWE-KB:END -->

<!-- SWE-KB:FILE architectural-patterns/system-structure/backend-for-frontend-bff.md -->
---
record_id: architectural-patterns--system-structure--backend-for-frontend-bff
concept_id: backend-for-frontend-bff
status: seed
source_table: architectural-patterns/system-structure
---

# Backend for Frontend (BFF)

> Seed record from `Organize Software Concepts.txt`. Classification and terminology are preserved from the source table; not independently verified.

| Field | Source value |
|---|---|
| Pattern | Backend for Frontend (BFF) |
| Purpose | Tailor backend interfaces to clients |
| Typical use | Multi-client applications |

## Discovery extension

Add supporting references, context, tradeoffs, limitations, and validated relationships when reviewed; keep original source fields intact.
<!-- SWE-KB:END -->

<!-- SWE-KB:FILE architectural-patterns/system-structure/cell-based-architecture.md -->
---
record_id: architectural-patterns--system-structure--cell-based-architecture
concept_id: cell-based-architecture
status: seed
source_table: architectural-patterns/system-structure
---

# Cell-Based Architecture

> Seed record from `Organize Software Concepts.txt`. Classification and terminology are preserved from the source table; not independently verified.

| Field | Source value |
|---|---|
| Pattern | Cell-Based Architecture |
| Purpose | Isolate workloads into independent cells |
| Typical use | Fault containment |

## Discovery extension

Add supporting references, context, tradeoffs, limitations, and validated relationships when reviewed; keep original source fields intact.
<!-- SWE-KB:END -->

<!-- SWE-KB:FILE architectural-patterns/system-structure/clean-architecture.md -->
---
record_id: architectural-patterns--system-structure--clean-architecture
concept_id: clean-architecture
status: seed
source_table: architectural-patterns/system-structure
---

# Clean Architecture

> Seed record from `Organize Software Concepts.txt`. Classification and terminology are preserved from the source table; not independently verified.

| Field | Source value |
|---|---|
| Pattern | Clean Architecture |
| Purpose | Enforce inward dependency direction |
| Typical use | Domain-centric systems |

## Discovery extension

Add supporting references, context, tradeoffs, limitations, and validated relationships when reviewed; keep original source fields intact.
<!-- SWE-KB:END -->

<!-- SWE-KB:FILE architectural-patterns/system-structure/hexagonal-ports-and-adapters.md -->
---
record_id: architectural-patterns--system-structure--hexagonal-ports-and-adapters
concept_id: hexagonal-ports-and-adapters
status: seed
source_table: architectural-patterns/system-structure
---

# Hexagonal / Ports & Adapters

> Seed record from `Organize Software Concepts.txt`. Classification and terminology are preserved from the source table; not independently verified.

| Field | Source value |
|---|---|
| Pattern | Hexagonal / Ports & Adapters |
| Purpose | Isolate domain logic from infrastructure |
| Typical use | Testable backends |

## Discovery extension

Add supporting references, context, tradeoffs, limitations, and validated relationships when reviewed; keep original source fields intact.
<!-- SWE-KB:END -->

<!-- SWE-KB:FILE architectural-patterns/system-structure/layered-n-tier.md -->
---
record_id: architectural-patterns--system-structure--layered-n-tier
concept_id: layered-n-tier
status: seed
source_table: architectural-patterns/system-structure
---

# Layered / N-Tier

> Seed record from `Organize Software Concepts.txt`. Classification and terminology are preserved from the source table; not independently verified.

| Field | Source value |
|---|---|
| Pattern | Layered / N-Tier |
| Purpose | Separate responsibilities into layers |
| Typical use | Enterprise applications |

## Discovery extension

Add supporting references, context, tradeoffs, limitations, and validated relationships when reviewed; keep original source fields intact.
<!-- SWE-KB:END -->

<!-- SWE-KB:FILE architectural-patterns/system-structure/microkernel-plugin.md -->
---
record_id: architectural-patterns--system-structure--microkernel-plugin
concept_id: microkernel-plugin
status: seed
source_table: architectural-patterns/system-structure
---

# Microkernel / Plugin

> Seed record from `Organize Software Concepts.txt`. Classification and terminology are preserved from the source table; not independently verified.

| Field | Source value |
|---|---|
| Pattern | Microkernel / Plugin |
| Purpose | Extend a minimal core through plugins |
| Typical use | Extensible platforms |

## Discovery extension

Add supporting references, context, tradeoffs, limitations, and validated relationships when reviewed; keep original source fields intact.
<!-- SWE-KB:END -->

<!-- SWE-KB:FILE architectural-patterns/system-structure/microservices.md -->
---
record_id: architectural-patterns--system-structure--microservices
concept_id: microservices
status: seed
source_table: architectural-patterns/system-structure
---

# Microservices

> Seed record from `Organize Software Concepts.txt`. Classification and terminology are preserved from the source table; not independently verified.

| Field | Source value |
|---|---|
| Pattern | Microservices |
| Purpose | Split systems into independently deployable services |
| Typical use | Distributed platforms |

## Discovery extension

Add supporting references, context, tradeoffs, limitations, and validated relationships when reviewed; keep original source fields intact.
<!-- SWE-KB:END -->

<!-- SWE-KB:FILE architectural-patterns/system-structure/modular-monolith.md -->
---
record_id: architectural-patterns--system-structure--modular-monolith
concept_id: modular-monolith
status: seed
source_table: architectural-patterns/system-structure
---

# Modular Monolith

> Seed record from `Organize Software Concepts.txt`. Classification and terminology are preserved from the source table; not independently verified.

| Field | Source value |
|---|---|
| Pattern | Modular Monolith |
| Purpose | Preserve module boundaries within one deployment |
| Typical use | Growing applications |

## Discovery extension

Add supporting references, context, tradeoffs, limitations, and validated relationships when reviewed; keep original source fields intact.
<!-- SWE-KB:END -->

<!-- SWE-KB:FILE architectural-patterns/system-structure/monolithic.md -->
---
record_id: architectural-patterns--system-structure--monolithic
concept_id: monolithic
status: seed
source_table: architectural-patterns/system-structure
---

# Monolithic

> Seed record from `Organize Software Concepts.txt`. Classification and terminology are preserved from the source table; not independently verified.

| Field | Source value |
|---|---|
| Pattern | Monolithic |
| Purpose | Deploy an application as one unit |
| Typical use | Small to medium systems |

## Discovery extension

Add supporting references, context, tradeoffs, limitations, and validated relationships when reviewed; keep original source fields intact.
<!-- SWE-KB:END -->

<!-- SWE-KB:FILE architectural-patterns/system-structure/onion-architecture.md -->
---
record_id: architectural-patterns--system-structure--onion-architecture
concept_id: onion-architecture
status: seed
source_table: architectural-patterns/system-structure
---

# Onion Architecture

> Seed record from `Organize Software Concepts.txt`. Classification and terminology are preserved from the source table; not independently verified.

| Field | Source value |
|---|---|
| Pattern | Onion Architecture |
| Purpose | Organize dependencies around domain models |
| Typical use | DDD applications |

## Discovery extension

Add supporting references, context, tradeoffs, limitations, and validated relationships when reviewed; keep original source fields intact.
<!-- SWE-KB:END -->

<!-- SWE-KB:FILE architectural-patterns/system-structure/self-contained-systems.md -->
---
record_id: architectural-patterns--system-structure--self-contained-systems
concept_id: self-contained-systems
status: seed
source_table: architectural-patterns/system-structure
---

# Self-Contained Systems

> Seed record from `Organize Software Concepts.txt`. Classification and terminology are preserved from the source table; not independently verified.

| Field | Source value |
|---|---|
| Pattern | Self-Contained Systems |
| Purpose | Build autonomous vertical application slices |
| Typical use | Large web platforms |

## Discovery extension

Add supporting references, context, tradeoffs, limitations, and validated relationships when reviewed; keep original source fields intact.
<!-- SWE-KB:END -->

<!-- SWE-KB:FILE architectural-patterns/system-structure/serverless.md -->
---
record_id: architectural-patterns--system-structure--serverless
concept_id: serverless
status: seed
source_table: architectural-patterns/system-structure
---

# Serverless

> Seed record from `Organize Software Concepts.txt`. Classification and terminology are preserved from the source table; not independently verified.

| Field | Source value |
|---|---|
| Pattern | Serverless |
| Purpose | Execute workloads through managed infrastructure |
| Typical use | Event-driven applications |

## Discovery extension

Add supporting references, context, tradeoffs, limitations, and validated relationships when reviewed; keep original source fields intact.
<!-- SWE-KB:END -->

<!-- SWE-KB:FILE architectural-patterns/system-structure/service-oriented-architecture-soa.md -->
---
record_id: architectural-patterns--system-structure--service-oriented-architecture-soa
concept_id: service-oriented-architecture-soa
status: seed
source_table: architectural-patterns/system-structure
---

# Service-Oriented Architecture (SOA)

> Seed record from `Organize Software Concepts.txt`. Classification and terminology are preserved from the source table; not independently verified.

| Field | Source value |
|---|---|
| Pattern | Service-Oriented Architecture (SOA) |
| Purpose | Integrate services through defined contracts |
| Typical use | Enterprise integration |

## Discovery extension

Add supporting references, context, tradeoffs, limitations, and validated relationships when reviewed; keep original source fields intact.
<!-- SWE-KB:END -->

<!-- SWE-KB:FILE architectural-patterns/system-structure/space-based-architecture.md -->
---
record_id: architectural-patterns--system-structure--space-based-architecture
concept_id: space-based-architecture
status: seed
source_table: architectural-patterns/system-structure
---

# Space-Based Architecture

> Seed record from `Organize Software Concepts.txt`. Classification and terminology are preserved from the source table; not independently verified.

| Field | Source value |
|---|---|
| Pattern | Space-Based Architecture |
| Purpose | Distribute processing and state across nodes |
| Typical use | High-throughput systems |

## Discovery extension

Add supporting references, context, tradeoffs, limitations, and validated relationships when reviewed; keep original source fields intact.
<!-- SWE-KB:END -->

<!-- SWE-KB:FILE catalog.tsv -->
id	kind	category	name	path	summary	status
abstract-factory	design-pattern	design-patterns	Abstract Factory	design-patterns/creational-gang-of-four/abstract-factory.md	Create related families of objects	seed
active-record	design-pattern	design-patterns	Active Record	design-patterns/additional-application-design-patterns/active-record.md	Combine domain data and persistence behavior	seed
acyclic-dependencies-principle-adp	principle	software-design-principles	Acyclic Dependencies Principle (ADP)	software-design-principles/additional-object-oriented-and-modularity-principles/acyclic-dependencies-principle-adp.md	Prevent dependency cycles	seed
adapter	design-pattern	design-patterns	Adapter	design-patterns/structural-gang-of-four/adapter.md	Convert one interface into another	seed
adapter-wrappers	technique	implementation-techniques	Adapter Wrappers	implementation-techniques/adapter-wrappers.md	Normalize incompatible interfaces	seed
aggregate	design-pattern	design-patterns	Aggregate	design-patterns/additional-application-design-patterns/aggregate.md	Enforce consistency boundaries	seed
algebraic-data-types	technique	implementation-techniques	Algebraic Data Types	implementation-techniques/algebraic-data-types.md	Represent structured alternatives	seed
anti-corruption-layer	architectural-pattern	architectural-patterns	Anti-Corruption Layer	architectural-patterns/migration-and-modernization/anti-corruption-layer.md	Translate between incompatible domain models	seed
api-composition	integration-pattern	integration-patterns	API Composition	integration-patterns/distributed-coordination-and-resilience/api-composition.md	Aggregate data from multiple services	seed
api-gateway	architectural-pattern	architectural-patterns	API Gateway	architectural-patterns/data-and-communication/api-gateway.md	Centralize API entry and cross-cutting concerns	seed
at-least-once-delivery	principle	software-design-principles	At-Least-Once Delivery	software-design-principles/distributed-systems-principles/at-least-once-delivery.md	Ensure delivery with possible duplicates	seed
at-most-once-delivery	principle	software-design-principles	At-Most-Once Delivery	software-design-principles/distributed-systems-principles/at-most-once-delivery.md	Avoid duplicate delivery with possible loss	seed
automated-refactoring	technique	implementation-techniques	Automated Refactoring	implementation-techniques/automated-refactoring.md	Change code structure while preserving behavior	seed
backend-for-frontend-bff	architectural-pattern	architectural-patterns	Backend for Frontend (BFF)	architectural-patterns/system-structure/backend-for-frontend-bff.md	Tailor backend interfaces to clients	seed
backpressure	principle	software-design-principles	Backpressure	software-design-principles/distributed-systems-principles/backpressure.md	Prevent producers from overwhelming consumers	seed
bluegreen-deployment	architectural-pattern	architectural-patterns	Blue–Green Deployment	architectural-patterns/migration-and-modernization/bluegreen-deployment.md	Switch traffic between environments	seed
branch-by-abstraction	architectural-pattern	architectural-patterns	Branch by Abstraction	architectural-patterns/migration-and-modernization/branch-by-abstraction.md	Replace implementations behind stable interfaces	seed
bridge	design-pattern	design-patterns	Bridge	design-patterns/structural-gang-of-four/bridge.md	Separate abstraction from implementation	seed
builder	design-pattern	design-patterns	Builder	design-patterns/creational-gang-of-four/builder.md	Construct complex objects step by step	seed
bulkhead	integration-pattern	integration-patterns	Bulkhead	integration-patterns/distributed-coordination-and-resilience/bulkhead.md	Isolate resource pools and failures	seed
cache-aside	integration-pattern	integration-patterns	Cache-Aside	integration-patterns/distributed-coordination-and-resilience/cache-aside.md	Load cache entries on demand	seed
callback	design-pattern	design-patterns	Callback	design-patterns/additional-application-design-patterns/callback.md	Delegate behavior to a supplied function	seed
canary-deployment	architectural-pattern	architectural-patterns	Canary Deployment	architectural-patterns/migration-and-modernization/canary-deployment.md	Gradually expose users to new implementations	seed
cell-based-architecture	architectural-pattern	architectural-patterns	Cell-Based Architecture	architectural-patterns/system-structure/cell-based-architecture.md	Isolate workloads into independent cells	seed
chain-of-responsibility	design-pattern	design-patterns	Chain of Responsibility	design-patterns/behavioral-gang-of-four/chain-of-responsibility.md	Pass requests through handlers	seed
change-data-capture-cdc	architectural-pattern	architectural-patterns	Change Data Capture (CDC)	architectural-patterns/migration-and-modernization/change-data-capture-cdc.md	Replicate database changes	seed
circuit-breaker	integration-pattern	integration-patterns	Circuit Breaker	integration-patterns/distributed-coordination-and-resilience/circuit-breaker.md	Stop repeated calls to failing dependencies	seed
claim-check	integration-pattern	integration-patterns	Claim Check	integration-patterns/distributed-coordination-and-resilience/claim-check.md	Store large payloads separately from messages	seed
clean-architecture	architectural-pattern	architectural-patterns	Clean Architecture	architectural-patterns/system-structure/clean-architecture.md	Enforce inward dependency direction	seed
closures	technique	implementation-techniques	Closures	implementation-techniques/closures.md	Capture state in function environments	seed
code-generation	technique	implementation-techniques	Code Generation	implementation-techniques/code-generation.md	Produce repetitive code from definitions	seed
command	design-pattern	design-patterns	Command	design-patterns/behavioral-gang-of-four/command.md	Encapsulate an operation as an object	seed
commandquery-separation-cqs	principle	software-design-principles	Command–Query Separation (CQS)	software-design-principles/additional-object-oriented-and-modularity-principles/commandquery-separation-cqs.md	Distinguish state-changing commands from queries	seed
common-closure-principle-ccp	principle	software-design-principles	Common Closure Principle (CCP)	software-design-principles/additional-object-oriented-and-modularity-principles/common-closure-principle-ccp.md	Group elements that change together	seed
common-reuse-principle-crp	principle	software-design-principles	Common Reuse Principle (CRP)	software-design-principles/additional-object-oriented-and-modularity-principles/common-reuse-principle-crp.md	Group elements reused together	seed
competing-consumers	integration-pattern	integration-patterns	Competing Consumers	integration-patterns/distributed-coordination-and-resilience/competing-consumers.md	Scale processing through multiple consumers	seed
composite	design-pattern	design-patterns	Composite	design-patterns/structural-gang-of-four/composite.md	Treat individual objects and groups uniformly	seed
composition-over-inheritance	principle	software-design-principles	Composition over Inheritance	software-design-principles/general-engineering-principles/composition-over-inheritance.md	Prefer assembling behavior to inheritance hierarchies	seed
composition-root	technique	implementation-techniques	Composition Root	implementation-techniques/composition-root.md	Centralize object graph assembly	seed
constructor-injection	technique	implementation-techniques	Constructor Injection	implementation-techniques/constructor-injection.md	Pass dependencies through constructors	seed
contract-testing	technique	implementation-techniques	Contract Testing	implementation-techniques/contract-testing.md	Verify compatibility across boundaries	seed
convention-over-configuration	principle	software-design-principles	Convention over Configuration	software-design-principles/general-engineering-principles/convention-over-configuration.md	Use defaults to reduce explicit setup	seed
copy-on-write	technique	implementation-techniques	Copy-on-Write	implementation-techniques/copy-on-write.md	Defer copying until modification	seed
cqrs	architectural-pattern	architectural-patterns	CQRS	architectural-patterns/data-and-communication/cqrs.md	Separate read and write models	seed
d-dependency-inversion-dip	principle	software-design-principles	D — Dependency Inversion (DIP)	software-design-principles/solid-principles/d-dependency-inversion-dip.md	High-level policy should not depend directly on low-level implementation details	seed
data-lakehouse	architectural-pattern	architectural-patterns	Data Lakehouse	architectural-patterns/data-and-communication/data-lakehouse.md	Combine lake and warehouse capabilities	seed
data-mapper	design-pattern	design-patterns	Data Mapper	design-patterns/additional-application-design-patterns/data-mapper.md	Map domain objects to persistence structures	seed
data-mesh	architectural-pattern	architectural-patterns	Data Mesh	architectural-patterns/data-and-communication/data-mesh.md	Decentralize ownership of data products	seed
data-transfer-object-dto	design-pattern	design-patterns	Data Transfer Object (DTO)	design-patterns/additional-application-design-patterns/data-transfer-object-dto.md	Transfer structured data across boundaries	seed
database-migrations	technique	implementation-techniques	Database Migrations	implementation-techniques/database-migrations.md	Evolve persisted schemas	seed
dead-letter-queue	integration-pattern	integration-patterns	Dead Letter Queue	integration-patterns/distributed-coordination-and-resilience/dead-letter-queue.md	Isolate messages that cannot be processed	seed
decorator	design-pattern	design-patterns	Decorator	design-patterns/structural-gang-of-four/decorator.md	Add behavior through composition	seed
defense-in-depth	principle	software-design-principles	Defense in Depth	software-design-principles/distributed-systems-principles/defense-in-depth.md	Apply multiple independent security controls	seed
defensive-programming	principle	software-design-principles	Defensive Programming	software-design-principles/general-engineering-principles/defensive-programming.md	Guard against invalid inputs and states	seed
delegation	technique	implementation-techniques	Delegation	implementation-techniques/delegation.md	Forward behavior to collaborators	seed
dependency-abstraction	principle	software-design-principles	Dependency Abstraction	software-design-principles/additional-object-oriented-and-modularity-principles/dependency-abstraction.md	Depend on stable contracts	seed
dependency-injection-container	design-pattern	design-patterns	Dependency Injection Container	design-patterns/additional-application-design-patterns/dependency-injection-container.md	Automate dependency resolution	seed
dependency-injection-di	design-pattern	design-patterns	Dependency Injection (DI)	design-patterns/additional-application-design-patterns/dependency-injection-di.md	Supply dependencies externally	seed
dependency-mocking	technique	implementation-techniques	Dependency Mocking	implementation-techniques/dependency-mocking.md	Replace collaborators during tests	seed
design-by-contract-dbc	principle	software-design-principles	Design by Contract (DbC)	software-design-principles/additional-object-oriented-and-modularity-principles/design-by-contract-dbc.md	Specify preconditions, postconditions, and invariants	seed
discriminated-unions	technique	implementation-techniques	Discriminated Unions	implementation-techniques/discriminated-unions.md	Model variants with explicit tags	seed
distributed-lock	integration-pattern	integration-patterns	Distributed Lock	integration-patterns/distributed-coordination-and-resilience/distributed-lock.md	Coordinate mutually exclusive operations	seed
domain-event	design-pattern	design-patterns	Domain Event	design-patterns/additional-application-design-patterns/domain-event.md	Represent meaningful domain occurrences	seed
domain-service	design-pattern	design-patterns	Domain Service	design-patterns/additional-application-design-patterns/domain-service.md	Encapsulate domain behavior outside entities	seed
dry	principle	software-design-principles	DRY	software-design-principles/general-engineering-principles/dry.md	Don't Repeat Yourself	seed
dual-write	architectural-pattern	architectural-patterns	Dual Write	architectural-patterns/migration-and-modernization/dual-write.md	Write to multiple systems during transition	seed
dynamic-dispatch	technique	implementation-techniques	Dynamic Dispatch	implementation-techniques/dynamic-dispatch.md	Select implementations at runtime	seed
encapsulation	principle	software-design-principles	Encapsulation	software-design-principles/general-engineering-principles/encapsulation.md	Protect state and behavior behind boundaries	seed
end-to-end-principle	principle	software-design-principles	End-to-End Principle	software-design-principles/distributed-systems-principles/end-to-end-principle.md	Place certain correctness guarantees at endpoints	seed
entity	design-pattern	design-patterns	Entity	design-patterns/additional-application-design-patterns/entity.md	Model objects with persistent identity	seed
event-driven-architecture-eda	architectural-pattern	architectural-patterns	Event-Driven Architecture (EDA)	architectural-patterns/data-and-communication/event-driven-architecture-eda.md	Decouple components through events	seed
event-sourcing	architectural-pattern	architectural-patterns	Event Sourcing	architectural-patterns/data-and-communication/event-sourcing.md	Persist state changes as events	seed
eventual-consistency	principle	software-design-principles	Eventual Consistency	software-design-principles/distributed-systems-principles/eventual-consistency.md	Allow replicas to converge asynchronously	seed
expand-and-contract	architectural-pattern	architectural-patterns	Expand and Contract	architectural-patterns/migration-and-modernization/expand-and-contract.md	Evolve schemas and APIs compatibly	seed
explicit-over-implicit	principle	software-design-principles	Explicit over Implicit	software-design-principles/general-engineering-principles/explicit-over-implicit.md	Make behavior and dependencies visible	seed
facade	design-pattern	design-patterns	Facade	design-patterns/structural-gang-of-four/facade.md	Simplify access to a complex subsystem	seed
factory-method	design-pattern	design-patterns	Factory Method	design-patterns/creational-gang-of-four/factory-method.md	Delegate object creation to subclasses	seed
fail-fast	principle	software-design-principles	Fail Fast	software-design-principles/general-engineering-principles/fail-fast.md	Detect invalid states early	seed
fault-isolation	principle	software-design-principles	Fault Isolation	software-design-principles/distributed-systems-principles/fault-isolation.md	Prevent failures from propagating	seed
favor-immutability	principle	software-design-principles	Favor Immutability	software-design-principles/additional-object-oriented-and-modularity-principles/favor-immutability.md	Reduce mutable shared state	seed
feature-flags	technique	implementation-techniques	Feature Flags	implementation-techniques/feature-flags.md	Control behavior without redeployment	seed
feature-toggles	architectural-pattern	architectural-patterns	Feature Toggles	architectural-patterns/migration-and-modernization/feature-toggles.md	Enable or disable behavior dynamically	seed
flyweight	design-pattern	design-patterns	Flyweight	design-patterns/structural-gang-of-four/flyweight.md	Share reusable intrinsic state	seed
functional-core-imperative-shell	design-pattern	design-patterns	Functional Core, Imperative Shell	design-patterns/additional-application-design-patterns/functional-core-imperative-shell.md	Isolate pure logic from side effects	seed
generics-parametric-polymorphism	technique	implementation-techniques	Generics / Parametric Polymorphism	implementation-techniques/generics-parametric-polymorphism.md	Reuse behavior across types	seed
graceful-degradation	principle	software-design-principles	Graceful Degradation	software-design-principles/distributed-systems-principles/graceful-degradation.md	Preserve reduced functionality under failure	seed
health-check	integration-pattern	integration-patterns	Health Check	integration-patterns/distributed-coordination-and-resilience/health-check.md	Expose service health	seed
heartbeat	integration-pattern	integration-patterns	Heartbeat	integration-patterns/distributed-coordination-and-resilience/heartbeat.md	Detect unavailable participants	seed
hexagonal-ports-and-adapters	architectural-pattern	architectural-patterns	Hexagonal / Ports & Adapters	architectural-patterns/system-structure/hexagonal-ports-and-adapters.md	Isolate domain logic from infrastructure	seed
high-cohesion	principle	software-design-principles	High Cohesion	software-design-principles/general-engineering-principles/high-cohesion.md	Keep closely related responsibilities together	seed
higher-order-functions	technique	implementation-techniques	Higher-Order Functions	implementation-techniques/higher-order-functions.md	Pass or return behavior as functions	seed
i-interface-segregation-isp	principle	software-design-principles	I — Interface Segregation (ISP)	software-design-principles/solid-principles/i-interface-segregation-isp.md	Avoid forcing consumers to depend on unused operations	seed
idempotency	principle	software-design-principles	Idempotency	software-design-principles/distributed-systems-principles/idempotency.md	Make repeated operations safe	seed
idempotent-consumer	integration-pattern	integration-patterns	Idempotent Consumer	integration-patterns/distributed-coordination-and-resilience/idempotent-consumer.md	Safely handle duplicate messages	seed
identity-map	design-pattern	design-patterns	Identity Map	design-patterns/additional-application-design-patterns/identity-map.md	Maintain one in-memory object per entity identity	seed
immutable-data-structures	technique	implementation-techniques	Immutable Data Structures	implementation-techniques/immutable-data-structures.md	Prevent in-place mutation	seed
information-hiding	principle	software-design-principles	Information Hiding	software-design-principles/general-engineering-principles/information-hiding.md	Hide implementation decisions behind interfaces	seed
interface-based-programming	principle	software-design-principles	Interface-Based Programming	software-design-principles/additional-object-oriented-and-modularity-principles/interface-based-programming.md	Program against contracts	seed
interface-extraction	technique	implementation-techniques	Interface Extraction	implementation-techniques/interface-extraction.md	Separate contracts from implementations	seed
interface-injection	technique	implementation-techniques	Interface Injection	implementation-techniques/interface-injection.md	Define a contract for supplying dependencies	seed
interpreter	design-pattern	design-patterns	Interpreter	design-patterns/behavioral-gang-of-four/interpreter.md	Evaluate expressions in a language	seed
inversion-of-control-ioc	principle	software-design-principles	Inversion of Control (IoC)	software-design-principles/additional-object-oriented-and-modularity-principles/inversion-of-control-ioc.md	Delegate control to an external mechanism	seed
iterator	design-pattern	design-patterns	Iterator	design-patterns/behavioral-gang-of-four/iterator.md	Traverse collections	seed
kappa-architecture	architectural-pattern	architectural-patterns	Kappa Architecture	architectural-patterns/data-and-communication/kappa-architecture.md	Process data primarily as streams	seed
kiss	principle	software-design-principles	KISS	software-design-principles/general-engineering-principles/kiss.md	Keep It Simple	seed
l-liskov-substitution-lsp	principle	software-design-principles	L — Liskov Substitution (LSP)	software-design-principles/solid-principles/l-liskov-substitution-lsp.md	Subtypes must preserve their base type's behavioral contracts	seed
lambda-architecture	architectural-pattern	architectural-patterns	Lambda Architecture	architectural-patterns/data-and-communication/lambda-architecture.md	Combine batch and stream processing	seed
layered-n-tier	architectural-pattern	architectural-patterns	Layered / N-Tier	architectural-patterns/system-structure/layered-n-tier.md	Separate responsibilities into layers	seed
lazy-evaluation	technique	implementation-techniques	Lazy Evaluation	implementation-techniques/lazy-evaluation.md	Delay computation	seed
lazy-initialization	design-pattern	design-patterns	Lazy Initialization	design-patterns/additional-application-design-patterns/lazy-initialization.md	Delay creation until needed	seed
leader-election	integration-pattern	integration-patterns	Leader Election	integration-patterns/distributed-coordination-and-resilience/leader-election.md	Select a coordinator among nodes	seed
leaderfollower	architectural-pattern	architectural-patterns	Leader–Follower	architectural-patterns/data-and-communication/leaderfollower.md	Coordinate replicated services	seed
lease	integration-pattern	integration-patterns	Lease	integration-patterns/distributed-coordination-and-resilience/lease.md	Grant temporary ownership	seed
least-astonishment	principle	software-design-principles	Least Astonishment	software-design-principles/general-engineering-principles/least-astonishment.md	Behavior should match reasonable expectations	seed
linting	technique	implementation-techniques	Linting	implementation-techniques/linting.md	Enforce code conventions and detect suspicious patterns	seed
load-balancer	integration-pattern	integration-patterns	Load Balancer	integration-patterns/distributed-coordination-and-resilience/load-balancer.md	Distribute requests across instances	seed
low-coupling	principle	software-design-principles	Low Coupling	software-design-principles/general-engineering-principles/low-coupling.md	Minimize dependencies between components	seed
manual-dependency-wiring	technique	implementation-techniques	Manual Dependency Wiring	implementation-techniques/manual-dependency-wiring.md	Assemble dependencies without a container	seed
materialized-view	integration-pattern	integration-patterns	Materialized View	integration-patterns/distributed-coordination-and-resilience/materialized-view.md	Precompute read-optimized representations	seed
mediator	design-pattern	design-patterns	Mediator	design-patterns/behavioral-gang-of-four/mediator.md	Centralize interactions among components	seed
memento	design-pattern	design-patterns	Memento	design-patterns/behavioral-gang-of-four/memento.md	Capture and restore state	seed
memoization	technique	implementation-techniques	Memoization	implementation-techniques/memoization.md	Cache function results	seed
message-broker	architectural-pattern	architectural-patterns	Message Broker	architectural-patterns/data-and-communication/message-broker.md	Mediate asynchronous communication	seed
method-injection	technique	implementation-techniques	Method Injection	implementation-techniques/method-injection.md	Pass dependencies to individual operations	seed
microkernel-plugin	architectural-pattern	architectural-patterns	Microkernel / Plugin	architectural-patterns/system-structure/microkernel-plugin.md	Extend a minimal core through plugins	seed
microservices	architectural-pattern	architectural-patterns	Microservices	architectural-patterns/system-structure/microservices.md	Split systems into independently deployable services	seed
middleware-interceptor	design-pattern	design-patterns	Middleware / Interceptor	design-patterns/additional-application-design-patterns/middleware-interceptor.md	Process requests through reusable stages	seed
modular-monolith	architectural-pattern	architectural-patterns	Modular Monolith	architectural-patterns/system-structure/modular-monolith.md	Preserve module boundaries within one deployment	seed
monolithic	architectural-pattern	architectural-patterns	Monolithic	architectural-patterns/system-structure/monolithic.md	Deploy an application as one unit	seed
null-object	design-pattern	design-patterns	Null Object	design-patterns/additional-application-design-patterns/null-object.md	Replace null checks with neutral behavior	seed
o-open-closed-ocp	principle	software-design-principles	O — Open/Closed (OCP)	software-design-principles/solid-principles/o-open-closed-ocp.md	Extend behavior without modifying stable existing code	seed
object-pool	design-pattern	design-patterns	Object Pool	design-patterns/additional-application-design-patterns/object-pool.md	Reuse expensive objects	seed
observer	design-pattern	design-patterns	Observer	design-patterns/behavioral-gang-of-four/observer.md	Notify dependents about changes	seed
onion-architecture	architectural-pattern	architectural-patterns	Onion Architecture	architectural-patterns/system-structure/onion-architecture.md	Organize dependencies around domain models	seed
orthogonality	principle	software-design-principles	Orthogonality	software-design-principles/general-engineering-principles/orthogonality.md	Keep independent concerns independently changeable	seed
parallel-run	architectural-pattern	architectural-patterns	Parallel Run	architectural-patterns/migration-and-modernization/parallel-run.md	Execute old and new implementations together	seed
peer-to-peer	architectural-pattern	architectural-patterns	Peer-to-Peer	architectural-patterns/data-and-communication/peer-to-peer.md	Distribute responsibility among peers	seed
pipes-and-filters	architectural-pattern	architectural-patterns	Pipes and Filters	architectural-patterns/data-and-communication/pipes-and-filters.md	Process data through independent stages	seed
plugin	design-pattern	design-patterns	Plugin	design-patterns/additional-application-design-patterns/plugin.md	Extend functionality through contracts	seed
policy-object	design-pattern	design-patterns	Policy Object	design-patterns/additional-application-design-patterns/policy-object.md	Encapsulate configurable rules	seed
primaryreplica	architectural-pattern	architectural-patterns	Primary–Replica	architectural-patterns/data-and-communication/primaryreplica.md	Replicate data from an authoritative node	seed
principle-of-least-authority	principle	software-design-principles	Principle of Least Authority	software-design-principles/general-engineering-principles/principle-of-least-authority.md	Minimize accessible capabilities	seed
principle-of-least-knowledge-law-of-demeter	principle	software-design-principles	Principle of Least Knowledge / Law of Demeter	software-design-principles/general-engineering-principles/principle-of-least-knowledge-law-of-demeter.md	Minimize knowledge of other objects' internals	seed
principle-of-least-privilege	principle	software-design-principles	Principle of Least Privilege	software-design-principles/general-engineering-principles/principle-of-least-privilege.md	Grant only necessary permissions	seed
principle-of-reversibility	principle	software-design-principles	Principle of Reversibility	software-design-principles/general-engineering-principles/principle-of-reversibility.md	Favor decisions that are inexpensive to undo	seed
program-to-an-interface	principle	software-design-principles	Program to an Interface	software-design-principles/additional-object-oriented-and-modularity-principles/program-to-an-interface.md	Avoid unnecessary dependence on concrete types	seed
property-based-testing	technique	implementation-techniques	Property-Based Testing	implementation-techniques/property-based-testing.md	Validate properties across generated inputs	seed
protected-variations	principle	software-design-principles	Protected Variations	software-design-principles/additional-object-oriented-and-modularity-principles/protected-variations.md	Isolate elements likely to change	seed
prototype	design-pattern	design-patterns	Prototype	design-patterns/creational-gang-of-four/prototype.md	Create objects by cloning	seed
proxy	design-pattern	design-patterns	Proxy	design-patterns/structural-gang-of-four/proxy.md	Control access to another object	seed
publishsubscribe	architectural-pattern	architectural-patterns	Publish–Subscribe	architectural-patterns/data-and-communication/publishsubscribe.md	Broadcast messages to subscribers	seed
pure-functions	technique	implementation-techniques	Pure Functions	implementation-techniques/pure-functions.md	Avoid observable side effects	seed
rate-limiter	integration-pattern	integration-patterns	Rate Limiter	integration-patterns/distributed-coordination-and-resilience/rate-limiter.md	Restrict request frequency	seed
read-through-cache	integration-pattern	integration-patterns	Read-Through Cache	integration-patterns/distributed-coordination-and-resilience/read-through-cache.md	Load data through a cache abstraction	seed
referential-transparency	technique	implementation-techniques	Referential Transparency	implementation-techniques/referential-transparency.md	Make expressions replaceable by their values	seed
registry	design-pattern	design-patterns	Registry	design-patterns/additional-application-design-patterns/registry.md	Centralize lookup of components	seed
repository	design-pattern	design-patterns	Repository	design-patterns/additional-application-design-patterns/repository.md	Abstract persistence operations	seed
requestreply	integration-pattern	integration-patterns	Request–Reply	integration-patterns/distributed-coordination-and-resilience/requestreply.md	Correlate requests with responses	seed
result-either	design-pattern	design-patterns	Result / Either	design-patterns/additional-application-design-patterns/result-either.md	Represent success and failure explicitly	seed
retry	integration-pattern	integration-patterns	Retry	integration-patterns/distributed-coordination-and-resilience/retry.md	Repeat transiently failed operations	seed
retry-with-backoff	principle	software-design-principles	Retry with Backoff	software-design-principles/distributed-systems-principles/retry-with-backoff.md	Recover from transient failures	seed
reuse-release-equivalence-principle-rep	principle	software-design-principles	Reuse/Release Equivalence Principle (REP)	software-design-principles/additional-object-oriented-and-modularity-principles/reuse-release-equivalence-principle-rep.md	Align reusable units with release units	seed
s-single-responsibility-srp	principle	software-design-principles	S — Single Responsibility (SRP)	software-design-principles/solid-principles/s-single-responsibility-srp.md	A module should have one reason to change	seed
saga	integration-pattern	integration-patterns	Saga	integration-patterns/distributed-coordination-and-resilience/saga.md	Coordinate distributed transactions through local transactions and compensation	seed
scattergather	integration-pattern	integration-patterns	Scatter–Gather	integration-patterns/distributed-coordination-and-resilience/scattergather.md	Aggregate responses from parallel recipients	seed
schema-versioning	technique	implementation-techniques	Schema Versioning	implementation-techniques/schema-versioning.md	Manage compatibility across versions	seed
self-contained-systems	architectural-pattern	architectural-patterns	Self-Contained Systems	architectural-patterns/system-structure/self-contained-systems.md	Build autonomous vertical application slices	seed
separation-of-concerns-soc	principle	software-design-principles	Separation of Concerns (SoC)	software-design-principles/general-engineering-principles/separation-of-concerns-soc.md	Isolate distinct responsibilities	seed
serverless	architectural-pattern	architectural-patterns	Serverless	architectural-patterns/system-structure/serverless.md	Execute workloads through managed infrastructure	seed
service-layer	design-pattern	design-patterns	Service Layer	design-patterns/additional-application-design-patterns/service-layer.md	Define application operations	seed
service-locator	design-pattern	design-patterns	Service Locator	design-patterns/additional-application-design-patterns/service-locator.md	Retrieve dependencies from a registry	seed
service-oriented-architecture-soa	architectural-pattern	architectural-patterns	Service-Oriented Architecture (SOA)	architectural-patterns/system-structure/service-oriented-architecture-soa.md	Integrate services through defined contracts	seed
setter-injection	technique	implementation-techniques	Setter Injection	implementation-techniques/setter-injection.md	Configure dependencies after construction	seed
shadow-traffic	architectural-pattern	architectural-patterns	Shadow Traffic	architectural-patterns/migration-and-modernization/shadow-traffic.md	Replay production requests without affecting responses	seed
sharding-partitioning	architectural-pattern	architectural-patterns	Sharding / Partitioning	architectural-patterns/data-and-communication/sharding-partitioning.md	Distribute data across partitions	seed
shared-nothing-architecture	architectural-pattern	architectural-patterns	Shared-Nothing Architecture	architectural-patterns/data-and-communication/shared-nothing-architecture.md	Minimize shared infrastructure and state	seed
sidecar	architectural-pattern	architectural-patterns	Sidecar	architectural-patterns/data-and-communication/sidecar.md	Attach supporting functionality to a workload	seed
single-source-of-truth	principle	software-design-principles	Single Source of Truth	software-design-principles/general-engineering-principles/single-source-of-truth.md	Establish one authoritative source for each fact	seed
singleton	design-pattern	design-patterns	Singleton	design-patterns/creational-gang-of-four/singleton.md	Ensure one instance within a defined scope	seed
space-based-architecture	architectural-pattern	architectural-patterns	Space-Based Architecture	architectural-patterns/system-structure/space-based-architecture.md	Distribute processing and state across nodes	seed
specification	design-pattern	design-patterns	Specification	design-patterns/additional-application-design-patterns/specification.md	Encapsulate business predicates	seed
stable-abstractions-principle-sap	principle	software-design-principles	Stable Abstractions Principle (SAP)	software-design-principles/additional-object-oriented-and-modularity-principles/stable-abstractions-principle-sap.md	Balance stability with abstraction	seed
stable-dependencies-principle-sdp	principle	software-design-principles	Stable Dependencies Principle (SDP)	software-design-principles/additional-object-oriented-and-modularity-principles/stable-dependencies-principle-sdp.md	Depend toward more stable components	seed
state	design-pattern	design-patterns	State	design-patterns/behavioral-gang-of-four/state.md	Change behavior according to internal state	seed
static-analysis	technique	implementation-techniques	Static Analysis	implementation-techniques/static-analysis.md	Detect issues without executing code	seed
static-dispatch	technique	implementation-techniques	Static Dispatch	implementation-techniques/static-dispatch.md	Select implementations at compile time	seed
strangler-fig	architectural-pattern	architectural-patterns	Strangler Fig	architectural-patterns/migration-and-modernization/strangler-fig.md	Incrementally replace an existing system	seed
strategy	design-pattern	design-patterns	Strategy	design-patterns/behavioral-gang-of-four/strategy.md	Swap interchangeable algorithms	seed
strong-consistency	principle	software-design-principles	Strong Consistency	software-design-principles/distributed-systems-principles/strong-consistency.md	Enforce defined consistency guarantees	seed
tell-don-t-ask	principle	software-design-principles	Tell, Don't Ask	software-design-principles/additional-object-oriented-and-modularity-principles/tell-don-t-ask.md	Put behavior near the data it operates on	seed
template-method	design-pattern	design-patterns	Template Method	design-patterns/behavioral-gang-of-four/template-method.md	Define an algorithm skeleton	seed
test-doubles	technique	implementation-techniques	Test Doubles	implementation-techniques/test-doubles.md	Substitute dependencies for test isolation	seed
timeout	integration-pattern	integration-patterns	Timeout	integration-patterns/distributed-coordination-and-resilience/timeout.md	Bound operation duration	seed
timeout-budgeting	principle	software-design-principles	Timeout Budgeting	software-design-principles/distributed-systems-principles/timeout-budgeting.md	Bound waiting and resource consumption	seed
transactional-inbox	integration-pattern	integration-patterns	Transactional Inbox	integration-patterns/distributed-coordination-and-resilience/transactional-inbox.md	Deduplicate and track consumed messages	seed
transactional-outbox	integration-pattern	integration-patterns	Transactional Outbox	integration-patterns/distributed-coordination-and-resilience/transactional-outbox.md	Reliably publish events alongside database updates	seed
type-guards-refinement	technique	implementation-techniques	Type Guards / Refinement	implementation-techniques/type-guards-refinement.md	Narrow types through runtime or static checks	seed
unit-of-work	design-pattern	design-patterns	Unit of Work	design-patterns/additional-application-design-patterns/unit-of-work.md	Coordinate persistence changes	seed
value-object	design-pattern	design-patterns	Value Object	design-patterns/additional-application-design-patterns/value-object.md	Model immutable values by attributes	seed
visitor	design-pattern	design-patterns	Visitor	design-patterns/behavioral-gang-of-four/visitor.md	Add operations across object structures	seed
write-behind-cache	integration-pattern	integration-patterns	Write-Behind Cache	integration-patterns/distributed-coordination-and-resilience/write-behind-cache.md	Persist cached writes asynchronously	seed
write-through-cache	integration-pattern	integration-patterns	Write-Through Cache	integration-patterns/distributed-coordination-and-resilience/write-through-cache.md	Update cache during writes	seed
yagni	principle	software-design-principles	YAGNI	software-design-principles/general-engineering-principles/yagni.md	You Aren't Gonna Need It	seed
zero-trust	principle	software-design-principles	Zero Trust	software-design-principles/distributed-systems-principles/zero-trust.md	Verify access rather than trusting network location	seed
<!-- SWE-KB:END -->

<!-- SWE-KB:FILE cross-category-relationships/INDEX.md -->
# Cross Category Relationships — Index

> Generated from source rows. Use the paths below from the repository root.

- **Back:** `cat AGENTS.md`
- **Search:** `./scripts/kb search "<term>"`

## Source rows (14)

| Row | Direct command |
|---|---|
| Data Consistency | `cat cross-category-relationships/data-consistency.md` |
| DIP | `cat cross-category-relationships/dip.md` |
| DRY | `cat cross-category-relationships/dry.md` |
| Fault Isolation | `cat cross-category-relationships/fault-isolation.md` |
| High Cohesion | `cat cross-category-relationships/high-cohesion.md` |
| Idempotency | `cat cross-category-relationships/idempotency.md` |
| Incremental Migration | `cat cross-category-relationships/incremental-migration.md` |
| IoC | `cat cross-category-relationships/ioc.md` |
| ISP | `cat cross-category-relationships/isp.md` |
| Low Coupling | `cat cross-category-relationships/low-coupling.md` |
| LSP | `cat cross-category-relationships/lsp.md` |
| OCP | `cat cross-category-relationships/ocp.md` |
| Separation of Concerns | `cat cross-category-relationships/separation-of-concerns.md` |
| SRP | `cat cross-category-relationships/srp.md` |
<!-- SWE-KB:END -->

<!-- SWE-KB:FILE cross-category-relationships/data-consistency.md -->
---
record_id: cross-category-relationships--main--data-consistency
concept_id: data-consistency
status: seed
source_table: cross-category-relationships
---

# Data Consistency

> Seed record from `Organize Software Concepts.txt`. Classification and terminology are preserved from the source table; not independently verified.

| Field | Source value |
|---|---|
| Principle / Goal | Data Consistency |
| Common patterns | Saga, Outbox |
| Implementation techniques | Transactions, deduplication |

## Discovery extension

Add supporting references, context, tradeoffs, limitations, and validated relationships when reviewed; keep original source fields intact.
<!-- SWE-KB:END -->

<!-- SWE-KB:FILE cross-category-relationships/dip.md -->
---
record_id: cross-category-relationships--main--dip
concept_id: dip
status: seed
source_table: cross-category-relationships
---

# DIP

> Seed record from `Organize Software Concepts.txt`. Classification and terminology are preserved from the source table; not independently verified.

| Field | Source value |
|---|---|
| Principle / Goal | DIP |
| Common patterns | DI, Adapter, Strategy |
| Implementation techniques | Constructor injection, interfaces |

## Discovery extension

Add supporting references, context, tradeoffs, limitations, and validated relationships when reviewed; keep original source fields intact.
<!-- SWE-KB:END -->

<!-- SWE-KB:FILE cross-category-relationships/dry.md -->
---
record_id: cross-category-relationships--main--dry
concept_id: dry
status: seed
source_table: cross-category-relationships
---

# DRY

> Seed record from `Organize Software Concepts.txt`. Classification and terminology are preserved from the source table; not independently verified.

| Field | Source value |
|---|---|
| Principle / Goal | DRY |
| Common patterns | Template Method, Strategy |
| Implementation techniques | Shared abstractions, code generation |

## Discovery extension

Add supporting references, context, tradeoffs, limitations, and validated relationships when reviewed; keep original source fields intact.
<!-- SWE-KB:END -->

<!-- SWE-KB:FILE cross-category-relationships/fault-isolation.md -->
---
record_id: cross-category-relationships--main--fault-isolation
concept_id: fault-isolation
status: seed
source_table: cross-category-relationships
---

# Fault Isolation

> Seed record from `Organize Software Concepts.txt`. Classification and terminology are preserved from the source table; not independently verified.

| Field | Source value |
|---|---|
| Principle / Goal | Fault Isolation |
| Common patterns | Bulkhead, Cell-Based |
| Implementation techniques | Separate resource pools |

## Discovery extension

Add supporting references, context, tradeoffs, limitations, and validated relationships when reviewed; keep original source fields intact.
<!-- SWE-KB:END -->

<!-- SWE-KB:FILE cross-category-relationships/high-cohesion.md -->
---
record_id: cross-category-relationships--main--high-cohesion
concept_id: high-cohesion
status: seed
source_table: cross-category-relationships
---

# High Cohesion

> Seed record from `Organize Software Concepts.txt`. Classification and terminology are preserved from the source table; not independently verified.

| Field | Source value |
|---|---|
| Principle / Goal | High Cohesion |
| Common patterns | Aggregate, Modular Monolith |
| Implementation techniques | Module boundaries |

## Discovery extension

Add supporting references, context, tradeoffs, limitations, and validated relationships when reviewed; keep original source fields intact.
<!-- SWE-KB:END -->

<!-- SWE-KB:FILE cross-category-relationships/idempotency.md -->
---
record_id: cross-category-relationships--main--idempotency
concept_id: idempotency
status: seed
source_table: cross-category-relationships
---

# Idempotency

> Seed record from `Organize Software Concepts.txt`. Classification and terminology are preserved from the source table; not independently verified.

| Field | Source value |
|---|---|
| Principle / Goal | Idempotency |
| Common patterns | Idempotent Consumer, Inbox |
| Implementation techniques | Idempotency keys |

## Discovery extension

Add supporting references, context, tradeoffs, limitations, and validated relationships when reviewed; keep original source fields intact.
<!-- SWE-KB:END -->

<!-- SWE-KB:FILE cross-category-relationships/incremental-migration.md -->
---
record_id: cross-category-relationships--main--incremental-migration
concept_id: incremental-migration
status: seed
source_table: cross-category-relationships
---

# Incremental Migration

> Seed record from `Organize Software Concepts.txt`. Classification and terminology are preserved from the source table; not independently verified.

| Field | Source value |
|---|---|
| Principle / Goal | Incremental Migration |
| Common patterns | Strangler Fig, Branch by Abstraction |
| Implementation techniques | Routing, feature flags |

## Discovery extension

Add supporting references, context, tradeoffs, limitations, and validated relationships when reviewed; keep original source fields intact.
<!-- SWE-KB:END -->

<!-- SWE-KB:FILE cross-category-relationships/ioc.md -->
---
record_id: cross-category-relationships--main--ioc
concept_id: ioc
status: seed
source_table: cross-category-relationships
---

# IoC

> Seed record from `Organize Software Concepts.txt`. Classification and terminology are preserved from the source table; not independently verified.

| Field | Source value |
|---|---|
| Principle / Goal | IoC |
| Common patterns | DI, Template Method, Observer |
| Implementation techniques | Callbacks, containers |

## Discovery extension

Add supporting references, context, tradeoffs, limitations, and validated relationships when reviewed; keep original source fields intact.
<!-- SWE-KB:END -->

<!-- SWE-KB:FILE cross-category-relationships/isp.md -->
---
record_id: cross-category-relationships--main--isp
concept_id: isp
status: seed
source_table: cross-category-relationships
---

# ISP

> Seed record from `Organize Software Concepts.txt`. Classification and terminology are preserved from the source table; not independently verified.

| Field | Source value |
|---|---|
| Principle / Goal | ISP |
| Common patterns | Adapter, Facade |
| Implementation techniques | Small interfaces |

## Discovery extension

Add supporting references, context, tradeoffs, limitations, and validated relationships when reviewed; keep original source fields intact.
<!-- SWE-KB:END -->

<!-- SWE-KB:FILE cross-category-relationships/low-coupling.md -->
---
record_id: cross-category-relationships--main--low-coupling
concept_id: low-coupling
status: seed
source_table: cross-category-relationships
---

# Low Coupling

> Seed record from `Organize Software Concepts.txt`. Classification and terminology are preserved from the source table; not independently verified.

| Field | Source value |
|---|---|
| Principle / Goal | Low Coupling |
| Common patterns | Mediator, Observer, DI |
| Implementation techniques | Event dispatch, interfaces |

## Discovery extension

Add supporting references, context, tradeoffs, limitations, and validated relationships when reviewed; keep original source fields intact.
<!-- SWE-KB:END -->

<!-- SWE-KB:FILE cross-category-relationships/lsp.md -->
---
record_id: cross-category-relationships--main--lsp
concept_id: lsp
status: seed
source_table: cross-category-relationships
---

# LSP

> Seed record from `Organize Software Concepts.txt`. Classification and terminology are preserved from the source table; not independently verified.

| Field | Source value |
|---|---|
| Principle / Goal | LSP |
| Common patterns | Strategy, Template Method |
| Implementation techniques | Contract tests |

## Discovery extension

Add supporting references, context, tradeoffs, limitations, and validated relationships when reviewed; keep original source fields intact.
<!-- SWE-KB:END -->

<!-- SWE-KB:FILE cross-category-relationships/ocp.md -->
---
record_id: cross-category-relationships--main--ocp
concept_id: ocp
status: seed
source_table: cross-category-relationships
---

# OCP

> Seed record from `Organize Software Concepts.txt`. Classification and terminology are preserved from the source table; not independently verified.

| Field | Source value |
|---|---|
| Principle / Goal | OCP |
| Common patterns | Strategy, Decorator, Plugin |
| Implementation techniques | Polymorphism, composition |

## Discovery extension

Add supporting references, context, tradeoffs, limitations, and validated relationships when reviewed; keep original source fields intact.
<!-- SWE-KB:END -->

<!-- SWE-KB:FILE cross-category-relationships/separation-of-concerns.md -->
---
record_id: cross-category-relationships--main--separation-of-concerns
concept_id: separation-of-concerns
status: seed
source_table: cross-category-relationships
---

# Separation of Concerns

> Seed record from `Organize Software Concepts.txt`. Classification and terminology are preserved from the source table; not independently verified.

| Field | Source value |
|---|---|
| Principle / Goal | Separation of Concerns |
| Common patterns | Hexagonal, CQRS, MVC |
| Implementation techniques | Layering, ports |

## Discovery extension

Add supporting references, context, tradeoffs, limitations, and validated relationships when reviewed; keep original source fields intact.
<!-- SWE-KB:END -->

<!-- SWE-KB:FILE cross-category-relationships/srp.md -->
---
record_id: cross-category-relationships--main--srp
concept_id: srp
status: seed
source_table: cross-category-relationships
---

# SRP

> Seed record from `Organize Software Concepts.txt`. Classification and terminology are preserved from the source table; not independently verified.

| Field | Source value |
|---|---|
| Principle / Goal | SRP |
| Common patterns | Repository, Service Layer |
| Implementation techniques | Module extraction |

## Discovery extension

Add supporting references, context, tradeoffs, limitations, and validated relationships when reviewed; keep original source fields intact.
<!-- SWE-KB:END -->

<!-- SWE-KB:FILE design-patterns/INDEX.md -->
# Design Patterns — Index

> Generated from source rows. Use the paths below from the repository root.

- **Back:** `cat AGENTS.md`
- **Search:** `./scripts/kb search "<term>"`

## Child routes

| Folder | Command |
|---|---|
| `additional-application-design-patterns/` | `cat design-patterns/additional-application-design-patterns/INDEX.md` |
| `behavioral-gang-of-four/` | `cat design-patterns/behavioral-gang-of-four/INDEX.md` |
| `creational-gang-of-four/` | `cat design-patterns/creational-gang-of-four/INDEX.md` |
| `structural-gang-of-four/` | `cat design-patterns/structural-gang-of-four/INDEX.md` |
<!-- SWE-KB:END -->

<!-- SWE-KB:FILE design-patterns/additional-application-design-patterns/INDEX.md -->
# Design Patterns/Additional Application Design Patterns — Index

> Generated from source rows. Use the paths below from the repository root.

- **Back:** `cat design-patterns/INDEX.md`
- **Search:** `./scripts/kb search "<term>"`

## Source rows (26)

| Row | Direct command |
|---|---|
| Active Record | `cat design-patterns/additional-application-design-patterns/active-record.md` |
| Aggregate | `cat design-patterns/additional-application-design-patterns/aggregate.md` |
| Callback | `cat design-patterns/additional-application-design-patterns/callback.md` |
| Data Mapper | `cat design-patterns/additional-application-design-patterns/data-mapper.md` |
| Data Transfer Object (DTO) | `cat design-patterns/additional-application-design-patterns/data-transfer-object-dto.md` |
| Dependency Injection (DI) | `cat design-patterns/additional-application-design-patterns/dependency-injection-di.md` |
| Dependency Injection Container | `cat design-patterns/additional-application-design-patterns/dependency-injection-container.md` |
| Domain Event | `cat design-patterns/additional-application-design-patterns/domain-event.md` |
| Domain Service | `cat design-patterns/additional-application-design-patterns/domain-service.md` |
| Entity | `cat design-patterns/additional-application-design-patterns/entity.md` |
| Functional Core, Imperative Shell | `cat design-patterns/additional-application-design-patterns/functional-core-imperative-shell.md` |
| Identity Map | `cat design-patterns/additional-application-design-patterns/identity-map.md` |
| Lazy Initialization | `cat design-patterns/additional-application-design-patterns/lazy-initialization.md` |
| Middleware / Interceptor | `cat design-patterns/additional-application-design-patterns/middleware-interceptor.md` |
| Null Object | `cat design-patterns/additional-application-design-patterns/null-object.md` |
| Object Pool | `cat design-patterns/additional-application-design-patterns/object-pool.md` |
| Plugin | `cat design-patterns/additional-application-design-patterns/plugin.md` |
| Policy Object | `cat design-patterns/additional-application-design-patterns/policy-object.md` |
| Registry | `cat design-patterns/additional-application-design-patterns/registry.md` |
| Repository | `cat design-patterns/additional-application-design-patterns/repository.md` |
| Result / Either | `cat design-patterns/additional-application-design-patterns/result-either.md` |
| Service Layer | `cat design-patterns/additional-application-design-patterns/service-layer.md` |
| Service Locator | `cat design-patterns/additional-application-design-patterns/service-locator.md` |
| Specification | `cat design-patterns/additional-application-design-patterns/specification.md` |
| Unit of Work | `cat design-patterns/additional-application-design-patterns/unit-of-work.md` |
| Value Object | `cat design-patterns/additional-application-design-patterns/value-object.md` |
<!-- SWE-KB:END -->

<!-- SWE-KB:FILE design-patterns/additional-application-design-patterns/active-record.md -->
---
record_id: design-patterns--additional-application-design-patterns--active-record
concept_id: active-record
status: seed
source_table: design-patterns/additional-application-design-patterns
---

# Active Record

> Seed record from `Organize Software Concepts.txt`. Classification and terminology are preserved from the source table; not independently verified.

| Field | Source value |
|---|---|
| Pattern | Active Record |
| Purpose | Combine domain data and persistence behavior |

## Discovery extension

Add supporting references, context, tradeoffs, limitations, and validated relationships when reviewed; keep original source fields intact.
<!-- SWE-KB:END -->

<!-- SWE-KB:FILE design-patterns/additional-application-design-patterns/aggregate.md -->
---
record_id: design-patterns--additional-application-design-patterns--aggregate
concept_id: aggregate
status: seed
source_table: design-patterns/additional-application-design-patterns
---

# Aggregate

> Seed record from `Organize Software Concepts.txt`. Classification and terminology are preserved from the source table; not independently verified.

| Field | Source value |
|---|---|
| Pattern | Aggregate |
| Purpose | Enforce consistency boundaries |

## Discovery extension

Add supporting references, context, tradeoffs, limitations, and validated relationships when reviewed; keep original source fields intact.
<!-- SWE-KB:END -->

<!-- SWE-KB:FILE design-patterns/additional-application-design-patterns/callback.md -->
---
record_id: design-patterns--additional-application-design-patterns--callback
concept_id: callback
status: seed
source_table: design-patterns/additional-application-design-patterns
---

# Callback

> Seed record from `Organize Software Concepts.txt`. Classification and terminology are preserved from the source table; not independently verified.

| Field | Source value |
|---|---|
| Pattern | Callback |
| Purpose | Delegate behavior to a supplied function |

## Discovery extension

Add supporting references, context, tradeoffs, limitations, and validated relationships when reviewed; keep original source fields intact.
<!-- SWE-KB:END -->

<!-- SWE-KB:FILE design-patterns/additional-application-design-patterns/data-mapper.md -->
---
record_id: design-patterns--additional-application-design-patterns--data-mapper
concept_id: data-mapper
status: seed
source_table: design-patterns/additional-application-design-patterns
---

# Data Mapper

> Seed record from `Organize Software Concepts.txt`. Classification and terminology are preserved from the source table; not independently verified.

| Field | Source value |
|---|---|
| Pattern | Data Mapper |
| Purpose | Map domain objects to persistence structures |

## Discovery extension

Add supporting references, context, tradeoffs, limitations, and validated relationships when reviewed; keep original source fields intact.
<!-- SWE-KB:END -->

<!-- SWE-KB:FILE design-patterns/additional-application-design-patterns/data-transfer-object-dto.md -->
---
record_id: design-patterns--additional-application-design-patterns--data-transfer-object-dto
concept_id: data-transfer-object-dto
status: seed
source_table: design-patterns/additional-application-design-patterns
---

# Data Transfer Object (DTO)

> Seed record from `Organize Software Concepts.txt`. Classification and terminology are preserved from the source table; not independently verified.

| Field | Source value |
|---|---|
| Pattern | Data Transfer Object (DTO) |
| Purpose | Transfer structured data across boundaries |

## Discovery extension

Add supporting references, context, tradeoffs, limitations, and validated relationships when reviewed; keep original source fields intact.
<!-- SWE-KB:END -->

<!-- SWE-KB:FILE design-patterns/additional-application-design-patterns/dependency-injection-container.md -->
---
record_id: design-patterns--additional-application-design-patterns--dependency-injection-container
concept_id: dependency-injection-container
status: seed
source_table: design-patterns/additional-application-design-patterns
---

# Dependency Injection Container

> Seed record from `Organize Software Concepts.txt`. Classification and terminology are preserved from the source table; not independently verified.

| Field | Source value |
|---|---|
| Pattern | Dependency Injection Container |
| Purpose | Automate dependency resolution |

## Discovery extension

Add supporting references, context, tradeoffs, limitations, and validated relationships when reviewed; keep original source fields intact.
<!-- SWE-KB:END -->

<!-- SWE-KB:FILE design-patterns/additional-application-design-patterns/dependency-injection-di.md -->
---
record_id: design-patterns--additional-application-design-patterns--dependency-injection-di
concept_id: dependency-injection-di
status: seed
source_table: design-patterns/additional-application-design-patterns
---

# Dependency Injection (DI)

> Seed record from `Organize Software Concepts.txt`. Classification and terminology are preserved from the source table; not independently verified.

| Field | Source value |
|---|---|
| Pattern | Dependency Injection (DI) |
| Purpose | Supply dependencies externally |

## Discovery extension

Add supporting references, context, tradeoffs, limitations, and validated relationships when reviewed; keep original source fields intact.
<!-- SWE-KB:END -->

<!-- SWE-KB:FILE design-patterns/additional-application-design-patterns/domain-event.md -->
---
record_id: design-patterns--additional-application-design-patterns--domain-event
concept_id: domain-event
status: seed
source_table: design-patterns/additional-application-design-patterns
---

# Domain Event

> Seed record from `Organize Software Concepts.txt`. Classification and terminology are preserved from the source table; not independently verified.

| Field | Source value |
|---|---|
| Pattern | Domain Event |
| Purpose | Represent meaningful domain occurrences |

## Discovery extension

Add supporting references, context, tradeoffs, limitations, and validated relationships when reviewed; keep original source fields intact.
<!-- SWE-KB:END -->

<!-- SWE-KB:FILE design-patterns/additional-application-design-patterns/domain-service.md -->
---
record_id: design-patterns--additional-application-design-patterns--domain-service
concept_id: domain-service
status: seed
source_table: design-patterns/additional-application-design-patterns
---

# Domain Service

> Seed record from `Organize Software Concepts.txt`. Classification and terminology are preserved from the source table; not independently verified.

| Field | Source value |
|---|---|
| Pattern | Domain Service |
| Purpose | Encapsulate domain behavior outside entities |

## Discovery extension

Add supporting references, context, tradeoffs, limitations, and validated relationships when reviewed; keep original source fields intact.
<!-- SWE-KB:END -->

<!-- SWE-KB:FILE design-patterns/additional-application-design-patterns/entity.md -->
---
record_id: design-patterns--additional-application-design-patterns--entity
concept_id: entity
status: seed
source_table: design-patterns/additional-application-design-patterns
---

# Entity

> Seed record from `Organize Software Concepts.txt`. Classification and terminology are preserved from the source table; not independently verified.

| Field | Source value |
|---|---|
| Pattern | Entity |
| Purpose | Model objects with persistent identity |

## Discovery extension

Add supporting references, context, tradeoffs, limitations, and validated relationships when reviewed; keep original source fields intact.
<!-- SWE-KB:END -->

<!-- SWE-KB:FILE design-patterns/additional-application-design-patterns/functional-core-imperative-shell.md -->
---
record_id: design-patterns--additional-application-design-patterns--functional-core-imperative-shell
concept_id: functional-core-imperative-shell
status: seed
source_table: design-patterns/additional-application-design-patterns
---

# Functional Core, Imperative Shell

> Seed record from `Organize Software Concepts.txt`. Classification and terminology are preserved from the source table; not independently verified.

| Field | Source value |
|---|---|
| Pattern | Functional Core, Imperative Shell |
| Purpose | Isolate pure logic from side effects |

## Discovery extension

Add supporting references, context, tradeoffs, limitations, and validated relationships when reviewed; keep original source fields intact.
<!-- SWE-KB:END -->

<!-- SWE-KB:FILE design-patterns/additional-application-design-patterns/identity-map.md -->
---
record_id: design-patterns--additional-application-design-patterns--identity-map
concept_id: identity-map
status: seed
source_table: design-patterns/additional-application-design-patterns
---

# Identity Map

> Seed record from `Organize Software Concepts.txt`. Classification and terminology are preserved from the source table; not independently verified.

| Field | Source value |
|---|---|
| Pattern | Identity Map |
| Purpose | Maintain one in-memory object per entity identity |

## Discovery extension

Add supporting references, context, tradeoffs, limitations, and validated relationships when reviewed; keep original source fields intact.
<!-- SWE-KB:END -->

<!-- SWE-KB:FILE design-patterns/additional-application-design-patterns/lazy-initialization.md -->
---
record_id: design-patterns--additional-application-design-patterns--lazy-initialization
concept_id: lazy-initialization
status: seed
source_table: design-patterns/additional-application-design-patterns
---

# Lazy Initialization

> Seed record from `Organize Software Concepts.txt`. Classification and terminology are preserved from the source table; not independently verified.

| Field | Source value |
|---|---|
| Pattern | Lazy Initialization |
| Purpose | Delay creation until needed |

## Discovery extension

Add supporting references, context, tradeoffs, limitations, and validated relationships when reviewed; keep original source fields intact.
<!-- SWE-KB:END -->

<!-- SWE-KB:FILE design-patterns/additional-application-design-patterns/middleware-interceptor.md -->
---
record_id: design-patterns--additional-application-design-patterns--middleware-interceptor
concept_id: middleware-interceptor
status: seed
source_table: design-patterns/additional-application-design-patterns
---

# Middleware / Interceptor

> Seed record from `Organize Software Concepts.txt`. Classification and terminology are preserved from the source table; not independently verified.

| Field | Source value |
|---|---|
| Pattern | Middleware / Interceptor |
| Purpose | Process requests through reusable stages |

## Discovery extension

Add supporting references, context, tradeoffs, limitations, and validated relationships when reviewed; keep original source fields intact.
<!-- SWE-KB:END -->

<!-- SWE-KB:FILE design-patterns/additional-application-design-patterns/null-object.md -->
---
record_id: design-patterns--additional-application-design-patterns--null-object
concept_id: null-object
status: seed
source_table: design-patterns/additional-application-design-patterns
---

# Null Object

> Seed record from `Organize Software Concepts.txt`. Classification and terminology are preserved from the source table; not independently verified.

| Field | Source value |
|---|---|
| Pattern | Null Object |
| Purpose | Replace null checks with neutral behavior |

## Discovery extension

Add supporting references, context, tradeoffs, limitations, and validated relationships when reviewed; keep original source fields intact.
<!-- SWE-KB:END -->

<!-- SWE-KB:FILE design-patterns/additional-application-design-patterns/object-pool.md -->
---
record_id: design-patterns--additional-application-design-patterns--object-pool
concept_id: object-pool
status: seed
source_table: design-patterns/additional-application-design-patterns
---

# Object Pool

> Seed record from `Organize Software Concepts.txt`. Classification and terminology are preserved from the source table; not independently verified.

| Field | Source value |
|---|---|
| Pattern | Object Pool |
| Purpose | Reuse expensive objects |

## Discovery extension

Add supporting references, context, tradeoffs, limitations, and validated relationships when reviewed; keep original source fields intact.
<!-- SWE-KB:END -->

<!-- SWE-KB:FILE design-patterns/additional-application-design-patterns/plugin.md -->
---
record_id: design-patterns--additional-application-design-patterns--plugin
concept_id: plugin
status: seed
source_table: design-patterns/additional-application-design-patterns
---

# Plugin

> Seed record from `Organize Software Concepts.txt`. Classification and terminology are preserved from the source table; not independently verified.

| Field | Source value |
|---|---|
| Pattern | Plugin |
| Purpose | Extend functionality through contracts |

## Discovery extension

Add supporting references, context, tradeoffs, limitations, and validated relationships when reviewed; keep original source fields intact.
<!-- SWE-KB:END -->

<!-- SWE-KB:FILE design-patterns/additional-application-design-patterns/policy-object.md -->
---
record_id: design-patterns--additional-application-design-patterns--policy-object
concept_id: policy-object
status: seed
source_table: design-patterns/additional-application-design-patterns
---

# Policy Object

> Seed record from `Organize Software Concepts.txt`. Classification and terminology are preserved from the source table; not independently verified.

| Field | Source value |
|---|---|
| Pattern | Policy Object |
| Purpose | Encapsulate configurable rules |

## Discovery extension

Add supporting references, context, tradeoffs, limitations, and validated relationships when reviewed; keep original source fields intact.
<!-- SWE-KB:END -->

<!-- SWE-KB:FILE design-patterns/additional-application-design-patterns/registry.md -->
---
record_id: design-patterns--additional-application-design-patterns--registry
concept_id: registry
status: seed
source_table: design-patterns/additional-application-design-patterns
---

# Registry

> Seed record from `Organize Software Concepts.txt`. Classification and terminology are preserved from the source table; not independently verified.

| Field | Source value |
|---|---|
| Pattern | Registry |
| Purpose | Centralize lookup of components |

## Discovery extension

Add supporting references, context, tradeoffs, limitations, and validated relationships when reviewed; keep original source fields intact.
<!-- SWE-KB:END -->

<!-- SWE-KB:FILE design-patterns/additional-application-design-patterns/repository.md -->
---
record_id: design-patterns--additional-application-design-patterns--repository
concept_id: repository
status: seed
source_table: design-patterns/additional-application-design-patterns
---

# Repository

> Seed record from `Organize Software Concepts.txt`. Classification and terminology are preserved from the source table; not independently verified.

| Field | Source value |
|---|---|
| Pattern | Repository |
| Purpose | Abstract persistence operations |

## Discovery extension

Add supporting references, context, tradeoffs, limitations, and validated relationships when reviewed; keep original source fields intact.
<!-- SWE-KB:END -->

<!-- SWE-KB:FILE design-patterns/additional-application-design-patterns/result-either.md -->
---
record_id: design-patterns--additional-application-design-patterns--result-either
concept_id: result-either
status: seed
source_table: design-patterns/additional-application-design-patterns
---

# Result / Either

> Seed record from `Organize Software Concepts.txt`. Classification and terminology are preserved from the source table; not independently verified.

| Field | Source value |
|---|---|
| Pattern | Result / Either |
| Purpose | Represent success and failure explicitly |

## Discovery extension

Add supporting references, context, tradeoffs, limitations, and validated relationships when reviewed; keep original source fields intact.
<!-- SWE-KB:END -->

<!-- SWE-KB:FILE design-patterns/additional-application-design-patterns/service-layer.md -->
---
record_id: design-patterns--additional-application-design-patterns--service-layer
concept_id: service-layer
status: seed
source_table: design-patterns/additional-application-design-patterns
---

# Service Layer

> Seed record from `Organize Software Concepts.txt`. Classification and terminology are preserved from the source table; not independently verified.

| Field | Source value |
|---|---|
| Pattern | Service Layer |
| Purpose | Define application operations |

## Discovery extension

Add supporting references, context, tradeoffs, limitations, and validated relationships when reviewed; keep original source fields intact.
<!-- SWE-KB:END -->

<!-- SWE-KB:FILE design-patterns/additional-application-design-patterns/service-locator.md -->
---
record_id: design-patterns--additional-application-design-patterns--service-locator
concept_id: service-locator
status: seed
source_table: design-patterns/additional-application-design-patterns
---

# Service Locator

> Seed record from `Organize Software Concepts.txt`. Classification and terminology are preserved from the source table; not independently verified.

| Field | Source value |
|---|---|
| Pattern | Service Locator |
| Purpose | Retrieve dependencies from a registry |

## Discovery extension

Add supporting references, context, tradeoffs, limitations, and validated relationships when reviewed; keep original source fields intact.
<!-- SWE-KB:END -->

<!-- SWE-KB:FILE design-patterns/additional-application-design-patterns/specification.md -->
---
record_id: design-patterns--additional-application-design-patterns--specification
concept_id: specification
status: seed
source_table: design-patterns/additional-application-design-patterns
---

# Specification

> Seed record from `Organize Software Concepts.txt`. Classification and terminology are preserved from the source table; not independently verified.

| Field | Source value |
|---|---|
| Pattern | Specification |
| Purpose | Encapsulate business predicates |

## Discovery extension

Add supporting references, context, tradeoffs, limitations, and validated relationships when reviewed; keep original source fields intact.
<!-- SWE-KB:END -->

<!-- SWE-KB:FILE design-patterns/additional-application-design-patterns/unit-of-work.md -->
---
record_id: design-patterns--additional-application-design-patterns--unit-of-work
concept_id: unit-of-work
status: seed
source_table: design-patterns/additional-application-design-patterns
---

# Unit of Work

> Seed record from `Organize Software Concepts.txt`. Classification and terminology are preserved from the source table; not independently verified.

| Field | Source value |
|---|---|
| Pattern | Unit of Work |
| Purpose | Coordinate persistence changes |

## Discovery extension

Add supporting references, context, tradeoffs, limitations, and validated relationships when reviewed; keep original source fields intact.
<!-- SWE-KB:END -->

<!-- SWE-KB:FILE design-patterns/additional-application-design-patterns/value-object.md -->
---
record_id: design-patterns--additional-application-design-patterns--value-object
concept_id: value-object
status: seed
source_table: design-patterns/additional-application-design-patterns
---

# Value Object

> Seed record from `Organize Software Concepts.txt`. Classification and terminology are preserved from the source table; not independently verified.

| Field | Source value |
|---|---|
| Pattern | Value Object |
| Purpose | Model immutable values by attributes |

## Discovery extension

Add supporting references, context, tradeoffs, limitations, and validated relationships when reviewed; keep original source fields intact.
<!-- SWE-KB:END -->

<!-- SWE-KB:FILE design-patterns/behavioral-gang-of-four/INDEX.md -->
# Design Patterns/Behavioral Gang Of Four — Index

> Generated from source rows. Use the paths below from the repository root.

- **Back:** `cat design-patterns/INDEX.md`
- **Search:** `./scripts/kb search "<term>"`

## Source rows (11)

| Row | Direct command |
|---|---|
| Chain of Responsibility | `cat design-patterns/behavioral-gang-of-four/chain-of-responsibility.md` |
| Command | `cat design-patterns/behavioral-gang-of-four/command.md` |
| Interpreter | `cat design-patterns/behavioral-gang-of-four/interpreter.md` |
| Iterator | `cat design-patterns/behavioral-gang-of-four/iterator.md` |
| Mediator | `cat design-patterns/behavioral-gang-of-four/mediator.md` |
| Memento | `cat design-patterns/behavioral-gang-of-four/memento.md` |
| Observer | `cat design-patterns/behavioral-gang-of-four/observer.md` |
| State | `cat design-patterns/behavioral-gang-of-four/state.md` |
| Strategy | `cat design-patterns/behavioral-gang-of-four/strategy.md` |
| Template Method | `cat design-patterns/behavioral-gang-of-four/template-method.md` |
| Visitor | `cat design-patterns/behavioral-gang-of-four/visitor.md` |
<!-- SWE-KB:END -->

<!-- SWE-KB:FILE design-patterns/behavioral-gang-of-four/chain-of-responsibility.md -->
---
record_id: design-patterns--behavioral-gang-of-four--chain-of-responsibility
concept_id: chain-of-responsibility
status: seed
source_table: design-patterns/behavioral-gang-of-four
---

# Chain of Responsibility

> Seed record from `Organize Software Concepts.txt`. Classification and terminology are preserved from the source table; not independently verified.

| Field | Source value |
|---|---|
| Pattern | Chain of Responsibility |
| Purpose | Pass requests through handlers |

## Discovery extension

Add supporting references, context, tradeoffs, limitations, and validated relationships when reviewed; keep original source fields intact.
<!-- SWE-KB:END -->

<!-- SWE-KB:FILE design-patterns/behavioral-gang-of-four/command.md -->
---
record_id: design-patterns--behavioral-gang-of-four--command
concept_id: command
status: seed
source_table: design-patterns/behavioral-gang-of-four
---

# Command

> Seed record from `Organize Software Concepts.txt`. Classification and terminology are preserved from the source table; not independently verified.

| Field | Source value |
|---|---|
| Pattern | Command |
| Purpose | Encapsulate an operation as an object |

## Discovery extension

Add supporting references, context, tradeoffs, limitations, and validated relationships when reviewed; keep original source fields intact.
<!-- SWE-KB:END -->

<!-- SWE-KB:FILE design-patterns/behavioral-gang-of-four/interpreter.md -->
---
record_id: design-patterns--behavioral-gang-of-four--interpreter
concept_id: interpreter
status: seed
source_table: design-patterns/behavioral-gang-of-four
---

# Interpreter

> Seed record from `Organize Software Concepts.txt`. Classification and terminology are preserved from the source table; not independently verified.

| Field | Source value |
|---|---|
| Pattern | Interpreter |
| Purpose | Evaluate expressions in a language |

## Discovery extension

Add supporting references, context, tradeoffs, limitations, and validated relationships when reviewed; keep original source fields intact.
<!-- SWE-KB:END -->

<!-- SWE-KB:FILE design-patterns/behavioral-gang-of-four/iterator.md -->
---
record_id: design-patterns--behavioral-gang-of-four--iterator
concept_id: iterator
status: seed
source_table: design-patterns/behavioral-gang-of-four
---

# Iterator

> Seed record from `Organize Software Concepts.txt`. Classification and terminology are preserved from the source table; not independently verified.

| Field | Source value |
|---|---|
| Pattern | Iterator |
| Purpose | Traverse collections |

## Discovery extension

Add supporting references, context, tradeoffs, limitations, and validated relationships when reviewed; keep original source fields intact.
<!-- SWE-KB:END -->

<!-- SWE-KB:FILE design-patterns/behavioral-gang-of-four/mediator.md -->
---
record_id: design-patterns--behavioral-gang-of-four--mediator
concept_id: mediator
status: seed
source_table: design-patterns/behavioral-gang-of-four
---

# Mediator

> Seed record from `Organize Software Concepts.txt`. Classification and terminology are preserved from the source table; not independently verified.

| Field | Source value |
|---|---|
| Pattern | Mediator |
| Purpose | Centralize interactions among components |

## Discovery extension

Add supporting references, context, tradeoffs, limitations, and validated relationships when reviewed; keep original source fields intact.
<!-- SWE-KB:END -->

<!-- SWE-KB:FILE design-patterns/behavioral-gang-of-four/memento.md -->
---
record_id: design-patterns--behavioral-gang-of-four--memento
concept_id: memento
status: seed
source_table: design-patterns/behavioral-gang-of-four
---

# Memento

> Seed record from `Organize Software Concepts.txt`. Classification and terminology are preserved from the source table; not independently verified.

| Field | Source value |
|---|---|
| Pattern | Memento |
| Purpose | Capture and restore state |

## Discovery extension

Add supporting references, context, tradeoffs, limitations, and validated relationships when reviewed; keep original source fields intact.
<!-- SWE-KB:END -->

<!-- SWE-KB:FILE design-patterns/behavioral-gang-of-four/observer.md -->
---
record_id: design-patterns--behavioral-gang-of-four--observer
concept_id: observer
status: seed
source_table: design-patterns/behavioral-gang-of-four
---

# Observer

> Seed record from `Organize Software Concepts.txt`. Classification and terminology are preserved from the source table; not independently verified.

| Field | Source value |
|---|---|
| Pattern | Observer |
| Purpose | Notify dependents about changes |

## Discovery extension

Add supporting references, context, tradeoffs, limitations, and validated relationships when reviewed; keep original source fields intact.
<!-- SWE-KB:END -->

<!-- SWE-KB:FILE design-patterns/behavioral-gang-of-four/state.md -->
---
record_id: design-patterns--behavioral-gang-of-four--state
concept_id: state
status: seed
source_table: design-patterns/behavioral-gang-of-four
---

# State

> Seed record from `Organize Software Concepts.txt`. Classification and terminology are preserved from the source table; not independently verified.

| Field | Source value |
|---|---|
| Pattern | State |
| Purpose | Change behavior according to internal state |

## Discovery extension

Add supporting references, context, tradeoffs, limitations, and validated relationships when reviewed; keep original source fields intact.
<!-- SWE-KB:END -->

<!-- SWE-KB:FILE design-patterns/behavioral-gang-of-four/strategy.md -->
---
record_id: design-patterns--behavioral-gang-of-four--strategy
concept_id: strategy
status: seed
source_table: design-patterns/behavioral-gang-of-four
---

# Strategy

> Seed record from `Organize Software Concepts.txt`. Classification and terminology are preserved from the source table; not independently verified.

| Field | Source value |
|---|---|
| Pattern | Strategy |
| Purpose | Swap interchangeable algorithms |

## Discovery extension

Add supporting references, context, tradeoffs, limitations, and validated relationships when reviewed; keep original source fields intact.
<!-- SWE-KB:END -->

<!-- SWE-KB:FILE design-patterns/behavioral-gang-of-four/template-method.md -->
---
record_id: design-patterns--behavioral-gang-of-four--template-method
concept_id: template-method
status: seed
source_table: design-patterns/behavioral-gang-of-four
---

# Template Method

> Seed record from `Organize Software Concepts.txt`. Classification and terminology are preserved from the source table; not independently verified.

| Field | Source value |
|---|---|
| Pattern | Template Method |
| Purpose | Define an algorithm skeleton |

## Discovery extension

Add supporting references, context, tradeoffs, limitations, and validated relationships when reviewed; keep original source fields intact.
<!-- SWE-KB:END -->

<!-- SWE-KB:FILE design-patterns/behavioral-gang-of-four/visitor.md -->
---
record_id: design-patterns--behavioral-gang-of-four--visitor
concept_id: visitor
status: seed
source_table: design-patterns/behavioral-gang-of-four
---

# Visitor

> Seed record from `Organize Software Concepts.txt`. Classification and terminology are preserved from the source table; not independently verified.

| Field | Source value |
|---|---|
| Pattern | Visitor |
| Purpose | Add operations across object structures |

## Discovery extension

Add supporting references, context, tradeoffs, limitations, and validated relationships when reviewed; keep original source fields intact.
<!-- SWE-KB:END -->

<!-- SWE-KB:FILE design-patterns/creational-gang-of-four/INDEX.md -->
# Design Patterns/Creational Gang Of Four — Index

> Generated from source rows. Use the paths below from the repository root.

- **Back:** `cat design-patterns/INDEX.md`
- **Search:** `./scripts/kb search "<term>"`

## Source rows (5)

| Row | Direct command |
|---|---|
| Abstract Factory | `cat design-patterns/creational-gang-of-four/abstract-factory.md` |
| Builder | `cat design-patterns/creational-gang-of-four/builder.md` |
| Factory Method | `cat design-patterns/creational-gang-of-four/factory-method.md` |
| Prototype | `cat design-patterns/creational-gang-of-four/prototype.md` |
| Singleton | `cat design-patterns/creational-gang-of-four/singleton.md` |
<!-- SWE-KB:END -->

<!-- SWE-KB:FILE design-patterns/creational-gang-of-four/abstract-factory.md -->
---
record_id: design-patterns--creational-gang-of-four--abstract-factory
concept_id: abstract-factory
status: seed
source_table: design-patterns/creational-gang-of-four
---

# Abstract Factory

> Seed record from `Organize Software Concepts.txt`. Classification and terminology are preserved from the source table; not independently verified.

| Field | Source value |
|---|---|
| Pattern | Abstract Factory |
| Purpose | Create related families of objects |

## Discovery extension

Add supporting references, context, tradeoffs, limitations, and validated relationships when reviewed; keep original source fields intact.
<!-- SWE-KB:END -->

<!-- SWE-KB:FILE design-patterns/creational-gang-of-four/builder.md -->
---
record_id: design-patterns--creational-gang-of-four--builder
concept_id: builder
status: seed
source_table: design-patterns/creational-gang-of-four
---

# Builder

> Seed record from `Organize Software Concepts.txt`. Classification and terminology are preserved from the source table; not independently verified.

| Field | Source value |
|---|---|
| Pattern | Builder |
| Purpose | Construct complex objects step by step |

## Discovery extension

Add supporting references, context, tradeoffs, limitations, and validated relationships when reviewed; keep original source fields intact.
<!-- SWE-KB:END -->

<!-- SWE-KB:FILE design-patterns/creational-gang-of-four/factory-method.md -->
---
record_id: design-patterns--creational-gang-of-four--factory-method
concept_id: factory-method
status: seed
source_table: design-patterns/creational-gang-of-four
---

# Factory Method

> Seed record from `Organize Software Concepts.txt`. Classification and terminology are preserved from the source table; not independently verified.

| Field | Source value |
|---|---|
| Pattern | Factory Method |
| Purpose | Delegate object creation to subclasses |

## Discovery extension

Add supporting references, context, tradeoffs, limitations, and validated relationships when reviewed; keep original source fields intact.
<!-- SWE-KB:END -->

<!-- SWE-KB:FILE design-patterns/creational-gang-of-four/prototype.md -->
---
record_id: design-patterns--creational-gang-of-four--prototype
concept_id: prototype
status: seed
source_table: design-patterns/creational-gang-of-four
---

# Prototype

> Seed record from `Organize Software Concepts.txt`. Classification and terminology are preserved from the source table; not independently verified.

| Field | Source value |
|---|---|
| Pattern | Prototype |
| Purpose | Create objects by cloning |

## Discovery extension

Add supporting references, context, tradeoffs, limitations, and validated relationships when reviewed; keep original source fields intact.
<!-- SWE-KB:END -->

<!-- SWE-KB:FILE design-patterns/creational-gang-of-four/singleton.md -->
---
record_id: design-patterns--creational-gang-of-four--singleton
concept_id: singleton
status: seed
source_table: design-patterns/creational-gang-of-four
---

# Singleton

> Seed record from `Organize Software Concepts.txt`. Classification and terminology are preserved from the source table; not independently verified.

| Field | Source value |
|---|---|
| Pattern | Singleton |
| Purpose | Ensure one instance within a defined scope |

## Discovery extension

Add supporting references, context, tradeoffs, limitations, and validated relationships when reviewed; keep original source fields intact.
<!-- SWE-KB:END -->

<!-- SWE-KB:FILE design-patterns/structural-gang-of-four/INDEX.md -->
# Design Patterns/Structural Gang Of Four — Index

> Generated from source rows. Use the paths below from the repository root.

- **Back:** `cat design-patterns/INDEX.md`
- **Search:** `./scripts/kb search "<term>"`

## Source rows (7)

| Row | Direct command |
|---|---|
| Adapter | `cat design-patterns/structural-gang-of-four/adapter.md` |
| Bridge | `cat design-patterns/structural-gang-of-four/bridge.md` |
| Composite | `cat design-patterns/structural-gang-of-four/composite.md` |
| Decorator | `cat design-patterns/structural-gang-of-four/decorator.md` |
| Facade | `cat design-patterns/structural-gang-of-four/facade.md` |
| Flyweight | `cat design-patterns/structural-gang-of-four/flyweight.md` |
| Proxy | `cat design-patterns/structural-gang-of-four/proxy.md` |
<!-- SWE-KB:END -->

<!-- SWE-KB:FILE design-patterns/structural-gang-of-four/adapter.md -->
---
record_id: design-patterns--structural-gang-of-four--adapter
concept_id: adapter
status: seed
source_table: design-patterns/structural-gang-of-four
---

# Adapter

> Seed record from `Organize Software Concepts.txt`. Classification and terminology are preserved from the source table; not independently verified.

| Field | Source value |
|---|---|
| Pattern | Adapter |
| Purpose | Convert one interface into another |

## Discovery extension

Add supporting references, context, tradeoffs, limitations, and validated relationships when reviewed; keep original source fields intact.
<!-- SWE-KB:END -->

<!-- SWE-KB:FILE design-patterns/structural-gang-of-four/bridge.md -->
---
record_id: design-patterns--structural-gang-of-four--bridge
concept_id: bridge
status: seed
source_table: design-patterns/structural-gang-of-four
---

# Bridge

> Seed record from `Organize Software Concepts.txt`. Classification and terminology are preserved from the source table; not independently verified.

| Field | Source value |
|---|---|
| Pattern | Bridge |
| Purpose | Separate abstraction from implementation |

## Discovery extension

Add supporting references, context, tradeoffs, limitations, and validated relationships when reviewed; keep original source fields intact.
<!-- SWE-KB:END -->

<!-- SWE-KB:FILE design-patterns/structural-gang-of-four/composite.md -->
---
record_id: design-patterns--structural-gang-of-four--composite
concept_id: composite
status: seed
source_table: design-patterns/structural-gang-of-four
---

# Composite

> Seed record from `Organize Software Concepts.txt`. Classification and terminology are preserved from the source table; not independently verified.

| Field | Source value |
|---|---|
| Pattern | Composite |
| Purpose | Treat individual objects and groups uniformly |

## Discovery extension

Add supporting references, context, tradeoffs, limitations, and validated relationships when reviewed; keep original source fields intact.
<!-- SWE-KB:END -->

<!-- SWE-KB:FILE design-patterns/structural-gang-of-four/decorator.md -->
---
record_id: design-patterns--structural-gang-of-four--decorator
concept_id: decorator
status: seed
source_table: design-patterns/structural-gang-of-four
---

# Decorator

> Seed record from `Organize Software Concepts.txt`. Classification and terminology are preserved from the source table; not independently verified.

| Field | Source value |
|---|---|
| Pattern | Decorator |
| Purpose | Add behavior through composition |

## Discovery extension

Add supporting references, context, tradeoffs, limitations, and validated relationships when reviewed; keep original source fields intact.
<!-- SWE-KB:END -->

<!-- SWE-KB:FILE design-patterns/structural-gang-of-four/facade.md -->
---
record_id: design-patterns--structural-gang-of-four--facade
concept_id: facade
status: seed
source_table: design-patterns/structural-gang-of-four
---

# Facade

> Seed record from `Organize Software Concepts.txt`. Classification and terminology are preserved from the source table; not independently verified.

| Field | Source value |
|---|---|
| Pattern | Facade |
| Purpose | Simplify access to a complex subsystem |

## Discovery extension

Add supporting references, context, tradeoffs, limitations, and validated relationships when reviewed; keep original source fields intact.
<!-- SWE-KB:END -->

<!-- SWE-KB:FILE design-patterns/structural-gang-of-four/flyweight.md -->
---
record_id: design-patterns--structural-gang-of-four--flyweight
concept_id: flyweight
status: seed
source_table: design-patterns/structural-gang-of-four
---

# Flyweight

> Seed record from `Organize Software Concepts.txt`. Classification and terminology are preserved from the source table; not independently verified.

| Field | Source value |
|---|---|
| Pattern | Flyweight |
| Purpose | Share reusable intrinsic state |

## Discovery extension

Add supporting references, context, tradeoffs, limitations, and validated relationships when reviewed; keep original source fields intact.
<!-- SWE-KB:END -->

<!-- SWE-KB:FILE design-patterns/structural-gang-of-four/proxy.md -->
---
record_id: design-patterns--structural-gang-of-four--proxy
concept_id: proxy
status: seed
source_table: design-patterns/structural-gang-of-four
---

# Proxy

> Seed record from `Organize Software Concepts.txt`. Classification and terminology are preserved from the source table; not independently verified.

| Field | Source value |
|---|---|
| Pattern | Proxy |
| Purpose | Control access to another object |

## Discovery extension

Add supporting references, context, tradeoffs, limitations, and validated relationships when reviewed; keep original source fields intact.
<!-- SWE-KB:END -->

<!-- SWE-KB:FILE implementation-techniques/INDEX.md -->
# Implementation Techniques — Index

> Generated from source rows. Use the paths below from the repository root.

- **Back:** `cat AGENTS.md`
- **Search:** `./scripts/kb search "<term>"`

## Source rows (35)

| Row | Direct command |
|---|---|
| Adapter Wrappers | `cat implementation-techniques/adapter-wrappers.md` |
| Algebraic Data Types | `cat implementation-techniques/algebraic-data-types.md` |
| Automated Refactoring | `cat implementation-techniques/automated-refactoring.md` |
| Closures | `cat implementation-techniques/closures.md` |
| Code Generation | `cat implementation-techniques/code-generation.md` |
| Composition Root | `cat implementation-techniques/composition-root.md` |
| Constructor Injection | `cat implementation-techniques/constructor-injection.md` |
| Contract Testing | `cat implementation-techniques/contract-testing.md` |
| Copy-on-Write | `cat implementation-techniques/copy-on-write.md` |
| Database Migrations | `cat implementation-techniques/database-migrations.md` |
| Delegation | `cat implementation-techniques/delegation.md` |
| Dependency Injection Container | `cat implementation-techniques/dependency-injection-container.md` |
| Dependency Mocking | `cat implementation-techniques/dependency-mocking.md` |
| Discriminated Unions | `cat implementation-techniques/discriminated-unions.md` |
| Dynamic Dispatch | `cat implementation-techniques/dynamic-dispatch.md` |
| Feature Flags | `cat implementation-techniques/feature-flags.md` |
| Generics / Parametric Polymorphism | `cat implementation-techniques/generics-parametric-polymorphism.md` |
| Higher-Order Functions | `cat implementation-techniques/higher-order-functions.md` |
| Immutable Data Structures | `cat implementation-techniques/immutable-data-structures.md` |
| Interface Extraction | `cat implementation-techniques/interface-extraction.md` |
| Interface Injection | `cat implementation-techniques/interface-injection.md` |
| Lazy Evaluation | `cat implementation-techniques/lazy-evaluation.md` |
| Linting | `cat implementation-techniques/linting.md` |
| Manual Dependency Wiring | `cat implementation-techniques/manual-dependency-wiring.md` |
| Memoization | `cat implementation-techniques/memoization.md` |
| Method Injection | `cat implementation-techniques/method-injection.md` |
| Property-Based Testing | `cat implementation-techniques/property-based-testing.md` |
| Pure Functions | `cat implementation-techniques/pure-functions.md` |
| Referential Transparency | `cat implementation-techniques/referential-transparency.md` |
| Schema Versioning | `cat implementation-techniques/schema-versioning.md` |
| Setter Injection | `cat implementation-techniques/setter-injection.md` |
| Static Analysis | `cat implementation-techniques/static-analysis.md` |
| Static Dispatch | `cat implementation-techniques/static-dispatch.md` |
| Test Doubles | `cat implementation-techniques/test-doubles.md` |
| Type Guards / Refinement | `cat implementation-techniques/type-guards-refinement.md` |
<!-- SWE-KB:END -->

<!-- SWE-KB:FILE implementation-techniques/adapter-wrappers.md -->
---
record_id: implementation-techniques--main--adapter-wrappers
concept_id: adapter-wrappers
status: seed
source_table: implementation-techniques
---

# Adapter Wrappers

> Seed record from `Organize Software Concepts.txt`. Classification and terminology are preserved from the source table; not independently verified.

| Field | Source value |
|---|---|
| Technique | Adapter Wrappers |
| Purpose | Normalize incompatible interfaces |
| Related concepts | Adapter |

## Discovery extension

Add supporting references, context, tradeoffs, limitations, and validated relationships when reviewed; keep original source fields intact.
<!-- SWE-KB:END -->

<!-- SWE-KB:FILE implementation-techniques/algebraic-data-types.md -->
---
record_id: implementation-techniques--main--algebraic-data-types
concept_id: algebraic-data-types
status: seed
source_table: implementation-techniques
---

# Algebraic Data Types

> Seed record from `Organize Software Concepts.txt`. Classification and terminology are preserved from the source table; not independently verified.

| Field | Source value |
|---|---|
| Technique | Algebraic Data Types |
| Purpose | Represent structured alternatives |
| Related concepts | Type safety |

## Discovery extension

Add supporting references, context, tradeoffs, limitations, and validated relationships when reviewed; keep original source fields intact.
<!-- SWE-KB:END -->

<!-- SWE-KB:FILE implementation-techniques/automated-refactoring.md -->
---
record_id: implementation-techniques--main--automated-refactoring
concept_id: automated-refactoring
status: seed
source_table: implementation-techniques
---

# Automated Refactoring

> Seed record from `Organize Software Concepts.txt`. Classification and terminology are preserved from the source table; not independently verified.

| Field | Source value |
|---|---|
| Technique | Automated Refactoring |
| Purpose | Change code structure while preserving behavior |
| Related concepts | Maintainability |

## Discovery extension

Add supporting references, context, tradeoffs, limitations, and validated relationships when reviewed; keep original source fields intact.
<!-- SWE-KB:END -->

<!-- SWE-KB:FILE implementation-techniques/closures.md -->
---
record_id: implementation-techniques--main--closures
concept_id: closures
status: seed
source_table: implementation-techniques
---

# Closures

> Seed record from `Organize Software Concepts.txt`. Classification and terminology are preserved from the source table; not independently verified.

| Field | Source value |
|---|---|
| Technique | Closures |
| Purpose | Capture state in function environments |
| Related concepts | Encapsulation |

## Discovery extension

Add supporting references, context, tradeoffs, limitations, and validated relationships when reviewed; keep original source fields intact.
<!-- SWE-KB:END -->

<!-- SWE-KB:FILE implementation-techniques/code-generation.md -->
---
record_id: implementation-techniques--main--code-generation
concept_id: code-generation
status: seed
source_table: implementation-techniques
---

# Code Generation

> Seed record from `Organize Software Concepts.txt`. Classification and terminology are preserved from the source table; not independently verified.

| Field | Source value |
|---|---|
| Technique | Code Generation |
| Purpose | Produce repetitive code from definitions |
| Related concepts | DRY |

## Discovery extension

Add supporting references, context, tradeoffs, limitations, and validated relationships when reviewed; keep original source fields intact.
<!-- SWE-KB:END -->

<!-- SWE-KB:FILE implementation-techniques/composition-root.md -->
---
record_id: implementation-techniques--main--composition-root
concept_id: composition-root
status: seed
source_table: implementation-techniques
---

# Composition Root

> Seed record from `Organize Software Concepts.txt`. Classification and terminology are preserved from the source table; not independently verified.

| Field | Source value |
|---|---|
| Technique | Composition Root |
| Purpose | Centralize object graph assembly |
| Related concepts | DI, IoC |

## Discovery extension

Add supporting references, context, tradeoffs, limitations, and validated relationships when reviewed; keep original source fields intact.
<!-- SWE-KB:END -->

<!-- SWE-KB:FILE implementation-techniques/constructor-injection.md -->
---
record_id: implementation-techniques--main--constructor-injection
concept_id: constructor-injection
status: seed
source_table: implementation-techniques
---

# Constructor Injection

> Seed record from `Organize Software Concepts.txt`. Classification and terminology are preserved from the source table; not independently verified.

| Field | Source value |
|---|---|
| Technique | Constructor Injection |
| Purpose | Pass dependencies through constructors |
| Related concepts | DI, DIP |

## Discovery extension

Add supporting references, context, tradeoffs, limitations, and validated relationships when reviewed; keep original source fields intact.
<!-- SWE-KB:END -->

<!-- SWE-KB:FILE implementation-techniques/contract-testing.md -->
---
record_id: implementation-techniques--main--contract-testing
concept_id: contract-testing
status: seed
source_table: implementation-techniques
---

# Contract Testing

> Seed record from `Organize Software Concepts.txt`. Classification and terminology are preserved from the source table; not independently verified.

| Field | Source value |
|---|---|
| Technique | Contract Testing |
| Purpose | Verify compatibility across boundaries |
| Related concepts | Distributed systems |

## Discovery extension

Add supporting references, context, tradeoffs, limitations, and validated relationships when reviewed; keep original source fields intact.
<!-- SWE-KB:END -->

<!-- SWE-KB:FILE implementation-techniques/copy-on-write.md -->
---
record_id: implementation-techniques--main--copy-on-write
concept_id: copy-on-write
status: seed
source_table: implementation-techniques
---

# Copy-on-Write

> Seed record from `Organize Software Concepts.txt`. Classification and terminology are preserved from the source table; not independently verified.

| Field | Source value |
|---|---|
| Technique | Copy-on-Write |
| Purpose | Defer copying until modification |
| Related concepts | Immutability |

## Discovery extension

Add supporting references, context, tradeoffs, limitations, and validated relationships when reviewed; keep original source fields intact.
<!-- SWE-KB:END -->

<!-- SWE-KB:FILE implementation-techniques/database-migrations.md -->
---
record_id: implementation-techniques--main--database-migrations
concept_id: database-migrations
status: seed
source_table: implementation-techniques
---

# Database Migrations

> Seed record from `Organize Software Concepts.txt`. Classification and terminology are preserved from the source table; not independently verified.

| Field | Source value |
|---|---|
| Technique | Database Migrations |
| Purpose | Evolve persisted schemas |
| Related concepts | Expand–Contract |

## Discovery extension

Add supporting references, context, tradeoffs, limitations, and validated relationships when reviewed; keep original source fields intact.
<!-- SWE-KB:END -->

<!-- SWE-KB:FILE implementation-techniques/delegation.md -->
---
record_id: implementation-techniques--main--delegation
concept_id: delegation
status: seed
source_table: implementation-techniques
---

# Delegation

> Seed record from `Organize Software Concepts.txt`. Classification and terminology are preserved from the source table; not independently verified.

| Field | Source value |
|---|---|
| Technique | Delegation |
| Purpose | Forward behavior to collaborators |
| Related concepts | Composition |

## Discovery extension

Add supporting references, context, tradeoffs, limitations, and validated relationships when reviewed; keep original source fields intact.
<!-- SWE-KB:END -->

<!-- SWE-KB:FILE implementation-techniques/dependency-injection-container.md -->
---
record_id: implementation-techniques--main--dependency-injection-container
concept_id: dependency-injection-container
status: seed
source_table: implementation-techniques
---

# Dependency Injection Container

> Seed record from `Organize Software Concepts.txt`. Classification and terminology are preserved from the source table; not independently verified.

| Field | Source value |
|---|---|
| Technique | Dependency Injection Container |
| Purpose | Resolve and manage object graphs |
| Related concepts | DI, IoC |

## Discovery extension

Add supporting references, context, tradeoffs, limitations, and validated relationships when reviewed; keep original source fields intact.
<!-- SWE-KB:END -->

<!-- SWE-KB:FILE implementation-techniques/dependency-mocking.md -->
---
record_id: implementation-techniques--main--dependency-mocking
concept_id: dependency-mocking
status: seed
source_table: implementation-techniques
---

# Dependency Mocking

> Seed record from `Organize Software Concepts.txt`. Classification and terminology are preserved from the source table; not independently verified.

| Field | Source value |
|---|---|
| Technique | Dependency Mocking |
| Purpose | Replace collaborators during tests |
| Related concepts | Testability |

## Discovery extension

Add supporting references, context, tradeoffs, limitations, and validated relationships when reviewed; keep original source fields intact.
<!-- SWE-KB:END -->

<!-- SWE-KB:FILE implementation-techniques/discriminated-unions.md -->
---
record_id: implementation-techniques--main--discriminated-unions
concept_id: discriminated-unions
status: seed
source_table: implementation-techniques
---

# Discriminated Unions

> Seed record from `Organize Software Concepts.txt`. Classification and terminology are preserved from the source table; not independently verified.

| Field | Source value |
|---|---|
| Technique | Discriminated Unions |
| Purpose | Model variants with explicit tags |
| Related concepts | State, Result |

## Discovery extension

Add supporting references, context, tradeoffs, limitations, and validated relationships when reviewed; keep original source fields intact.
<!-- SWE-KB:END -->

<!-- SWE-KB:FILE implementation-techniques/dynamic-dispatch.md -->
---
record_id: implementation-techniques--main--dynamic-dispatch
concept_id: dynamic-dispatch
status: seed
source_table: implementation-techniques
---

# Dynamic Dispatch

> Seed record from `Organize Software Concepts.txt`. Classification and terminology are preserved from the source table; not independently verified.

| Field | Source value |
|---|---|
| Technique | Dynamic Dispatch |
| Purpose | Select implementations at runtime |
| Related concepts | Polymorphism |

## Discovery extension

Add supporting references, context, tradeoffs, limitations, and validated relationships when reviewed; keep original source fields intact.
<!-- SWE-KB:END -->

<!-- SWE-KB:FILE implementation-techniques/feature-flags.md -->
---
record_id: implementation-techniques--main--feature-flags
concept_id: feature-flags
status: seed
source_table: implementation-techniques
---

# Feature Flags

> Seed record from `Organize Software Concepts.txt`. Classification and terminology are preserved from the source table; not independently verified.

| Field | Source value |
|---|---|
| Technique | Feature Flags |
| Purpose | Control behavior without redeployment |
| Related concepts | Migration |

## Discovery extension

Add supporting references, context, tradeoffs, limitations, and validated relationships when reviewed; keep original source fields intact.
<!-- SWE-KB:END -->

<!-- SWE-KB:FILE implementation-techniques/generics-parametric-polymorphism.md -->
---
record_id: implementation-techniques--main--generics-parametric-polymorphism
concept_id: generics-parametric-polymorphism
status: seed
source_table: implementation-techniques
---

# Generics / Parametric Polymorphism

> Seed record from `Organize Software Concepts.txt`. Classification and terminology are preserved from the source table; not independently verified.

| Field | Source value |
|---|---|
| Technique | Generics / Parametric Polymorphism |
| Purpose | Reuse behavior across types |
| Related concepts | Abstraction |

## Discovery extension

Add supporting references, context, tradeoffs, limitations, and validated relationships when reviewed; keep original source fields intact.
<!-- SWE-KB:END -->

<!-- SWE-KB:FILE implementation-techniques/higher-order-functions.md -->
---
record_id: implementation-techniques--main--higher-order-functions
concept_id: higher-order-functions
status: seed
source_table: implementation-techniques
---

# Higher-Order Functions

> Seed record from `Organize Software Concepts.txt`. Classification and terminology are preserved from the source table; not independently verified.

| Field | Source value |
|---|---|
| Technique | Higher-Order Functions |
| Purpose | Pass or return behavior as functions |
| Related concepts | Strategy, composition |

## Discovery extension

Add supporting references, context, tradeoffs, limitations, and validated relationships when reviewed; keep original source fields intact.
<!-- SWE-KB:END -->

<!-- SWE-KB:FILE implementation-techniques/immutable-data-structures.md -->
---
record_id: implementation-techniques--main--immutable-data-structures
concept_id: immutable-data-structures
status: seed
source_table: implementation-techniques
---

# Immutable Data Structures

> Seed record from `Organize Software Concepts.txt`. Classification and terminology are preserved from the source table; not independently verified.

| Field | Source value |
|---|---|
| Technique | Immutable Data Structures |
| Purpose | Prevent in-place mutation |
| Related concepts | Immutability |

## Discovery extension

Add supporting references, context, tradeoffs, limitations, and validated relationships when reviewed; keep original source fields intact.
<!-- SWE-KB:END -->

<!-- SWE-KB:FILE implementation-techniques/interface-extraction.md -->
---
record_id: implementation-techniques--main--interface-extraction
concept_id: interface-extraction
status: seed
source_table: implementation-techniques
---

# Interface Extraction

> Seed record from `Organize Software Concepts.txt`. Classification and terminology are preserved from the source table; not independently verified.

| Field | Source value |
|---|---|
| Technique | Interface Extraction |
| Purpose | Separate contracts from implementations |
| Related concepts | DIP, ISP |

## Discovery extension

Add supporting references, context, tradeoffs, limitations, and validated relationships when reviewed; keep original source fields intact.
<!-- SWE-KB:END -->

<!-- SWE-KB:FILE implementation-techniques/interface-injection.md -->
---
record_id: implementation-techniques--main--interface-injection
concept_id: interface-injection
status: seed
source_table: implementation-techniques
---

# Interface Injection

> Seed record from `Organize Software Concepts.txt`. Classification and terminology are preserved from the source table; not independently verified.

| Field | Source value |
|---|---|
| Technique | Interface Injection |
| Purpose | Define a contract for supplying dependencies |
| Related concepts | DI |

## Discovery extension

Add supporting references, context, tradeoffs, limitations, and validated relationships when reviewed; keep original source fields intact.
<!-- SWE-KB:END -->

<!-- SWE-KB:FILE implementation-techniques/lazy-evaluation.md -->
---
record_id: implementation-techniques--main--lazy-evaluation
concept_id: lazy-evaluation
status: seed
source_table: implementation-techniques
---

# Lazy Evaluation

> Seed record from `Organize Software Concepts.txt`. Classification and terminology are preserved from the source table; not independently verified.

| Field | Source value |
|---|---|
| Technique | Lazy Evaluation |
| Purpose | Delay computation |
| Related concepts | Efficiency |

## Discovery extension

Add supporting references, context, tradeoffs, limitations, and validated relationships when reviewed; keep original source fields intact.
<!-- SWE-KB:END -->

<!-- SWE-KB:FILE implementation-techniques/linting.md -->
---
record_id: implementation-techniques--main--linting
concept_id: linting
status: seed
source_table: implementation-techniques
---

# Linting

> Seed record from `Organize Software Concepts.txt`. Classification and terminology are preserved from the source table; not independently verified.

| Field | Source value |
|---|---|
| Technique | Linting |
| Purpose | Enforce code conventions and detect suspicious patterns |
| Related concepts | Maintainability |

## Discovery extension

Add supporting references, context, tradeoffs, limitations, and validated relationships when reviewed; keep original source fields intact.
<!-- SWE-KB:END -->

<!-- SWE-KB:FILE implementation-techniques/manual-dependency-wiring.md -->
---
record_id: implementation-techniques--main--manual-dependency-wiring
concept_id: manual-dependency-wiring
status: seed
source_table: implementation-techniques
---

# Manual Dependency Wiring

> Seed record from `Organize Software Concepts.txt`. Classification and terminology are preserved from the source table; not independently verified.

| Field | Source value |
|---|---|
| Technique | Manual Dependency Wiring |
| Purpose | Assemble dependencies without a container |
| Related concepts | DI |

## Discovery extension

Add supporting references, context, tradeoffs, limitations, and validated relationships when reviewed; keep original source fields intact.
<!-- SWE-KB:END -->

<!-- SWE-KB:FILE implementation-techniques/memoization.md -->
---
record_id: implementation-techniques--main--memoization
concept_id: memoization
status: seed
source_table: implementation-techniques
---

# Memoization

> Seed record from `Organize Software Concepts.txt`. Classification and terminology are preserved from the source table; not independently verified.

| Field | Source value |
|---|---|
| Technique | Memoization |
| Purpose | Cache function results |
| Related concepts | Performance |

## Discovery extension

Add supporting references, context, tradeoffs, limitations, and validated relationships when reviewed; keep original source fields intact.
<!-- SWE-KB:END -->

<!-- SWE-KB:FILE implementation-techniques/method-injection.md -->
---
record_id: implementation-techniques--main--method-injection
concept_id: method-injection
status: seed
source_table: implementation-techniques
---

# Method Injection

> Seed record from `Organize Software Concepts.txt`. Classification and terminology are preserved from the source table; not independently verified.

| Field | Source value |
|---|---|
| Technique | Method Injection |
| Purpose | Pass dependencies to individual operations |
| Related concepts | DI |

## Discovery extension

Add supporting references, context, tradeoffs, limitations, and validated relationships when reviewed; keep original source fields intact.
<!-- SWE-KB:END -->

<!-- SWE-KB:FILE implementation-techniques/property-based-testing.md -->
---
record_id: implementation-techniques--main--property-based-testing
concept_id: property-based-testing
status: seed
source_table: implementation-techniques
---

# Property-Based Testing

> Seed record from `Organize Software Concepts.txt`. Classification and terminology are preserved from the source table; not independently verified.

| Field | Source value |
|---|---|
| Technique | Property-Based Testing |
| Purpose | Validate properties across generated inputs |
| Related concepts | Correctness |

## Discovery extension

Add supporting references, context, tradeoffs, limitations, and validated relationships when reviewed; keep original source fields intact.
<!-- SWE-KB:END -->

<!-- SWE-KB:FILE implementation-techniques/pure-functions.md -->
---
record_id: implementation-techniques--main--pure-functions
concept_id: pure-functions
status: seed
source_table: implementation-techniques
---

# Pure Functions

> Seed record from `Organize Software Concepts.txt`. Classification and terminology are preserved from the source table; not independently verified.

| Field | Source value |
|---|---|
| Technique | Pure Functions |
| Purpose | Avoid observable side effects |
| Related concepts | Functional programming |

## Discovery extension

Add supporting references, context, tradeoffs, limitations, and validated relationships when reviewed; keep original source fields intact.
<!-- SWE-KB:END -->

<!-- SWE-KB:FILE implementation-techniques/referential-transparency.md -->
---
record_id: implementation-techniques--main--referential-transparency
concept_id: referential-transparency
status: seed
source_table: implementation-techniques
---

# Referential Transparency

> Seed record from `Organize Software Concepts.txt`. Classification and terminology are preserved from the source table; not independently verified.

| Field | Source value |
|---|---|
| Technique | Referential Transparency |
| Purpose | Make expressions replaceable by their values |
| Related concepts | Functional programming |

## Discovery extension

Add supporting references, context, tradeoffs, limitations, and validated relationships when reviewed; keep original source fields intact.
<!-- SWE-KB:END -->

<!-- SWE-KB:FILE implementation-techniques/schema-versioning.md -->
---
record_id: implementation-techniques--main--schema-versioning
concept_id: schema-versioning
status: seed
source_table: implementation-techniques
---

# Schema Versioning

> Seed record from `Organize Software Concepts.txt`. Classification and terminology are preserved from the source table; not independently verified.

| Field | Source value |
|---|---|
| Technique | Schema Versioning |
| Purpose | Manage compatibility across versions |
| Related concepts | API evolution |

## Discovery extension

Add supporting references, context, tradeoffs, limitations, and validated relationships when reviewed; keep original source fields intact.
<!-- SWE-KB:END -->

<!-- SWE-KB:FILE implementation-techniques/setter-injection.md -->
---
record_id: implementation-techniques--main--setter-injection
concept_id: setter-injection
status: seed
source_table: implementation-techniques
---

# Setter Injection

> Seed record from `Organize Software Concepts.txt`. Classification and terminology are preserved from the source table; not independently verified.

| Field | Source value |
|---|---|
| Technique | Setter Injection |
| Purpose | Configure dependencies after construction |
| Related concepts | DI |

## Discovery extension

Add supporting references, context, tradeoffs, limitations, and validated relationships when reviewed; keep original source fields intact.
<!-- SWE-KB:END -->

<!-- SWE-KB:FILE implementation-techniques/static-analysis.md -->
---
record_id: implementation-techniques--main--static-analysis
concept_id: static-analysis
status: seed
source_table: implementation-techniques
---

# Static Analysis

> Seed record from `Organize Software Concepts.txt`. Classification and terminology are preserved from the source table; not independently verified.

| Field | Source value |
|---|---|
| Technique | Static Analysis |
| Purpose | Detect issues without executing code |
| Related concepts | Quality |

## Discovery extension

Add supporting references, context, tradeoffs, limitations, and validated relationships when reviewed; keep original source fields intact.
<!-- SWE-KB:END -->

<!-- SWE-KB:FILE implementation-techniques/static-dispatch.md -->
---
record_id: implementation-techniques--main--static-dispatch
concept_id: static-dispatch
status: seed
source_table: implementation-techniques
---

# Static Dispatch

> Seed record from `Organize Software Concepts.txt`. Classification and terminology are preserved from the source table; not independently verified.

| Field | Source value |
|---|---|
| Technique | Static Dispatch |
| Purpose | Select implementations at compile time |
| Related concepts | Polymorphism |

## Discovery extension

Add supporting references, context, tradeoffs, limitations, and validated relationships when reviewed; keep original source fields intact.
<!-- SWE-KB:END -->

<!-- SWE-KB:FILE implementation-techniques/test-doubles.md -->
---
record_id: implementation-techniques--main--test-doubles
concept_id: test-doubles
status: seed
source_table: implementation-techniques
---

# Test Doubles

> Seed record from `Organize Software Concepts.txt`. Classification and terminology are preserved from the source table; not independently verified.

| Field | Source value |
|---|---|
| Technique | Test Doubles |
| Purpose | Substitute dependencies for test isolation |
| Related concepts | DI |

## Discovery extension

Add supporting references, context, tradeoffs, limitations, and validated relationships when reviewed; keep original source fields intact.
<!-- SWE-KB:END -->

<!-- SWE-KB:FILE implementation-techniques/type-guards-refinement.md -->
---
record_id: implementation-techniques--main--type-guards-refinement
concept_id: type-guards-refinement
status: seed
source_table: implementation-techniques
---

# Type Guards / Refinement

> Seed record from `Organize Software Concepts.txt`. Classification and terminology are preserved from the source table; not independently verified.

| Field | Source value |
|---|---|
| Technique | Type Guards / Refinement |
| Purpose | Narrow types through runtime or static checks |
| Related concepts | Type safety |

## Discovery extension

Add supporting references, context, tradeoffs, limitations, and validated relationships when reviewed; keep original source fields intact.
<!-- SWE-KB:END -->

<!-- SWE-KB:FILE integration-patterns/INDEX.md -->
# Integration Patterns — Index

> Generated from source rows. Use the paths below from the repository root.

- **Back:** `cat AGENTS.md`
- **Search:** `./scripts/kb search "<term>"`

## Child routes

| Folder | Command |
|---|---|
| `distributed-coordination-and-resilience/` | `cat integration-patterns/distributed-coordination-and-resilience/INDEX.md` |
<!-- SWE-KB:END -->

<!-- SWE-KB:FILE integration-patterns/distributed-coordination-and-resilience/INDEX.md -->
# Integration Patterns/Distributed Coordination And Resilience — Index

> Generated from source rows. Use the paths below from the repository root.

- **Back:** `cat integration-patterns/INDEX.md`
- **Search:** `./scripts/kb search "<term>"`

## Source rows (26)

| Row | Direct command |
|---|---|
| API Composition | `cat integration-patterns/distributed-coordination-and-resilience/api-composition.md` |
| Bulkhead | `cat integration-patterns/distributed-coordination-and-resilience/bulkhead.md` |
| Cache-Aside | `cat integration-patterns/distributed-coordination-and-resilience/cache-aside.md` |
| Circuit Breaker | `cat integration-patterns/distributed-coordination-and-resilience/circuit-breaker.md` |
| Claim Check | `cat integration-patterns/distributed-coordination-and-resilience/claim-check.md` |
| Competing Consumers | `cat integration-patterns/distributed-coordination-and-resilience/competing-consumers.md` |
| Dead Letter Queue | `cat integration-patterns/distributed-coordination-and-resilience/dead-letter-queue.md` |
| Distributed Lock | `cat integration-patterns/distributed-coordination-and-resilience/distributed-lock.md` |
| Health Check | `cat integration-patterns/distributed-coordination-and-resilience/health-check.md` |
| Heartbeat | `cat integration-patterns/distributed-coordination-and-resilience/heartbeat.md` |
| Idempotent Consumer | `cat integration-patterns/distributed-coordination-and-resilience/idempotent-consumer.md` |
| Leader Election | `cat integration-patterns/distributed-coordination-and-resilience/leader-election.md` |
| Lease | `cat integration-patterns/distributed-coordination-and-resilience/lease.md` |
| Load Balancer | `cat integration-patterns/distributed-coordination-and-resilience/load-balancer.md` |
| Materialized View | `cat integration-patterns/distributed-coordination-and-resilience/materialized-view.md` |
| Rate Limiter | `cat integration-patterns/distributed-coordination-and-resilience/rate-limiter.md` |
| Read-Through Cache | `cat integration-patterns/distributed-coordination-and-resilience/read-through-cache.md` |
| Request–Reply | `cat integration-patterns/distributed-coordination-and-resilience/requestreply.md` |
| Retry | `cat integration-patterns/distributed-coordination-and-resilience/retry.md` |
| Saga | `cat integration-patterns/distributed-coordination-and-resilience/saga.md` |
| Scatter–Gather | `cat integration-patterns/distributed-coordination-and-resilience/scattergather.md` |
| Timeout | `cat integration-patterns/distributed-coordination-and-resilience/timeout.md` |
| Transactional Inbox | `cat integration-patterns/distributed-coordination-and-resilience/transactional-inbox.md` |
| Transactional Outbox | `cat integration-patterns/distributed-coordination-and-resilience/transactional-outbox.md` |
| Write-Behind Cache | `cat integration-patterns/distributed-coordination-and-resilience/write-behind-cache.md` |
| Write-Through Cache | `cat integration-patterns/distributed-coordination-and-resilience/write-through-cache.md` |
<!-- SWE-KB:END -->

<!-- SWE-KB:FILE integration-patterns/distributed-coordination-and-resilience/api-composition.md -->
---
record_id: architectural-and-application-integration-patterns--distributed-coordination-and-resilience--api-composition
concept_id: api-composition
status: seed
source_table: integration-patterns/distributed-coordination-and-resilience
---

# API Composition

> Seed record from `Organize Software Concepts.txt`. Classification and terminology are preserved from the source table; not independently verified.

| Field | Source value |
|---|---|
| Pattern | API Composition |
| Purpose | Aggregate data from multiple services |

## Discovery extension

Add supporting references, context, tradeoffs, limitations, and validated relationships when reviewed; keep original source fields intact.
<!-- SWE-KB:END -->

<!-- SWE-KB:FILE integration-patterns/distributed-coordination-and-resilience/bulkhead.md -->
---
record_id: architectural-and-application-integration-patterns--distributed-coordination-and-resilience--bulkhead
concept_id: bulkhead
status: seed
source_table: integration-patterns/distributed-coordination-and-resilience
---

# Bulkhead

> Seed record from `Organize Software Concepts.txt`. Classification and terminology are preserved from the source table; not independently verified.

| Field | Source value |
|---|---|
| Pattern | Bulkhead |
| Purpose | Isolate resource pools and failures |

## Discovery extension

Add supporting references, context, tradeoffs, limitations, and validated relationships when reviewed; keep original source fields intact.
<!-- SWE-KB:END -->

<!-- SWE-KB:FILE integration-patterns/distributed-coordination-and-resilience/cache-aside.md -->
---
record_id: architectural-and-application-integration-patterns--distributed-coordination-and-resilience--cache-aside
concept_id: cache-aside
status: seed
source_table: integration-patterns/distributed-coordination-and-resilience
---

# Cache-Aside

> Seed record from `Organize Software Concepts.txt`. Classification and terminology are preserved from the source table; not independently verified.

| Field | Source value |
|---|---|
| Pattern | Cache-Aside |
| Purpose | Load cache entries on demand |

## Discovery extension

Add supporting references, context, tradeoffs, limitations, and validated relationships when reviewed; keep original source fields intact.
<!-- SWE-KB:END -->

<!-- SWE-KB:FILE integration-patterns/distributed-coordination-and-resilience/circuit-breaker.md -->
---
record_id: architectural-and-application-integration-patterns--distributed-coordination-and-resilience--circuit-breaker
concept_id: circuit-breaker
status: seed
source_table: integration-patterns/distributed-coordination-and-resilience
---

# Circuit Breaker

> Seed record from `Organize Software Concepts.txt`. Classification and terminology are preserved from the source table; not independently verified.

| Field | Source value |
|---|---|
| Pattern | Circuit Breaker |
| Purpose | Stop repeated calls to failing dependencies |

## Discovery extension

Add supporting references, context, tradeoffs, limitations, and validated relationships when reviewed; keep original source fields intact.
<!-- SWE-KB:END -->

<!-- SWE-KB:FILE integration-patterns/distributed-coordination-and-resilience/claim-check.md -->
---
record_id: architectural-and-application-integration-patterns--distributed-coordination-and-resilience--claim-check
concept_id: claim-check
status: seed
source_table: integration-patterns/distributed-coordination-and-resilience
---

# Claim Check

> Seed record from `Organize Software Concepts.txt`. Classification and terminology are preserved from the source table; not independently verified.

| Field | Source value |
|---|---|
| Pattern | Claim Check |
| Purpose | Store large payloads separately from messages |

## Discovery extension

Add supporting references, context, tradeoffs, limitations, and validated relationships when reviewed; keep original source fields intact.
<!-- SWE-KB:END -->

<!-- SWE-KB:FILE integration-patterns/distributed-coordination-and-resilience/competing-consumers.md -->
---
record_id: architectural-and-application-integration-patterns--distributed-coordination-and-resilience--competing-consumers
concept_id: competing-consumers
status: seed
source_table: integration-patterns/distributed-coordination-and-resilience
---

# Competing Consumers

> Seed record from `Organize Software Concepts.txt`. Classification and terminology are preserved from the source table; not independently verified.

| Field | Source value |
|---|---|
| Pattern | Competing Consumers |
| Purpose | Scale processing through multiple consumers |

## Discovery extension

Add supporting references, context, tradeoffs, limitations, and validated relationships when reviewed; keep original source fields intact.
<!-- SWE-KB:END -->

<!-- SWE-KB:FILE integration-patterns/distributed-coordination-and-resilience/dead-letter-queue.md -->
---
record_id: architectural-and-application-integration-patterns--distributed-coordination-and-resilience--dead-letter-queue
concept_id: dead-letter-queue
status: seed
source_table: integration-patterns/distributed-coordination-and-resilience
---

# Dead Letter Queue

> Seed record from `Organize Software Concepts.txt`. Classification and terminology are preserved from the source table; not independently verified.

| Field | Source value |
|---|---|
| Pattern | Dead Letter Queue |
| Purpose | Isolate messages that cannot be processed |

## Discovery extension

Add supporting references, context, tradeoffs, limitations, and validated relationships when reviewed; keep original source fields intact.
<!-- SWE-KB:END -->

<!-- SWE-KB:FILE integration-patterns/distributed-coordination-and-resilience/distributed-lock.md -->
---
record_id: architectural-and-application-integration-patterns--distributed-coordination-and-resilience--distributed-lock
concept_id: distributed-lock
status: seed
source_table: integration-patterns/distributed-coordination-and-resilience
---

# Distributed Lock

> Seed record from `Organize Software Concepts.txt`. Classification and terminology are preserved from the source table; not independently verified.

| Field | Source value |
|---|---|
| Pattern | Distributed Lock |
| Purpose | Coordinate mutually exclusive operations |

## Discovery extension

Add supporting references, context, tradeoffs, limitations, and validated relationships when reviewed; keep original source fields intact.
<!-- SWE-KB:END -->

<!-- SWE-KB:FILE integration-patterns/distributed-coordination-and-resilience/health-check.md -->
---
record_id: architectural-and-application-integration-patterns--distributed-coordination-and-resilience--health-check
concept_id: health-check
status: seed
source_table: integration-patterns/distributed-coordination-and-resilience
---

# Health Check

> Seed record from `Organize Software Concepts.txt`. Classification and terminology are preserved from the source table; not independently verified.

| Field | Source value |
|---|---|
| Pattern | Health Check |
| Purpose | Expose service health |

## Discovery extension

Add supporting references, context, tradeoffs, limitations, and validated relationships when reviewed; keep original source fields intact.
<!-- SWE-KB:END -->

<!-- SWE-KB:FILE integration-patterns/distributed-coordination-and-resilience/heartbeat.md -->
---
record_id: architectural-and-application-integration-patterns--distributed-coordination-and-resilience--heartbeat
concept_id: heartbeat
status: seed
source_table: integration-patterns/distributed-coordination-and-resilience
---

# Heartbeat

> Seed record from `Organize Software Concepts.txt`. Classification and terminology are preserved from the source table; not independently verified.

| Field | Source value |
|---|---|
| Pattern | Heartbeat |
| Purpose | Detect unavailable participants |

## Discovery extension

Add supporting references, context, tradeoffs, limitations, and validated relationships when reviewed; keep original source fields intact.
<!-- SWE-KB:END -->

<!-- SWE-KB:FILE integration-patterns/distributed-coordination-and-resilience/idempotent-consumer.md -->
---
record_id: architectural-and-application-integration-patterns--distributed-coordination-and-resilience--idempotent-consumer
concept_id: idempotent-consumer
status: seed
source_table: integration-patterns/distributed-coordination-and-resilience
---

# Idempotent Consumer

> Seed record from `Organize Software Concepts.txt`. Classification and terminology are preserved from the source table; not independently verified.

| Field | Source value |
|---|---|
| Pattern | Idempotent Consumer |
| Purpose | Safely handle duplicate messages |

## Discovery extension

Add supporting references, context, tradeoffs, limitations, and validated relationships when reviewed; keep original source fields intact.
<!-- SWE-KB:END -->

<!-- SWE-KB:FILE integration-patterns/distributed-coordination-and-resilience/leader-election.md -->
---
record_id: architectural-and-application-integration-patterns--distributed-coordination-and-resilience--leader-election
concept_id: leader-election
status: seed
source_table: integration-patterns/distributed-coordination-and-resilience
---

# Leader Election

> Seed record from `Organize Software Concepts.txt`. Classification and terminology are preserved from the source table; not independently verified.

| Field | Source value |
|---|---|
| Pattern | Leader Election |
| Purpose | Select a coordinator among nodes |

## Discovery extension

Add supporting references, context, tradeoffs, limitations, and validated relationships when reviewed; keep original source fields intact.
<!-- SWE-KB:END -->

<!-- SWE-KB:FILE integration-patterns/distributed-coordination-and-resilience/lease.md -->
---
record_id: architectural-and-application-integration-patterns--distributed-coordination-and-resilience--lease
concept_id: lease
status: seed
source_table: integration-patterns/distributed-coordination-and-resilience
---

# Lease

> Seed record from `Organize Software Concepts.txt`. Classification and terminology are preserved from the source table; not independently verified.

| Field | Source value |
|---|---|
| Pattern | Lease |
| Purpose | Grant temporary ownership |

## Discovery extension

Add supporting references, context, tradeoffs, limitations, and validated relationships when reviewed; keep original source fields intact.
<!-- SWE-KB:END -->

<!-- SWE-KB:FILE integration-patterns/distributed-coordination-and-resilience/load-balancer.md -->
---
record_id: architectural-and-application-integration-patterns--distributed-coordination-and-resilience--load-balancer
concept_id: load-balancer
status: seed
source_table: integration-patterns/distributed-coordination-and-resilience
---

# Load Balancer

> Seed record from `Organize Software Concepts.txt`. Classification and terminology are preserved from the source table; not independently verified.

| Field | Source value |
|---|---|
| Pattern | Load Balancer |
| Purpose | Distribute requests across instances |

## Discovery extension

Add supporting references, context, tradeoffs, limitations, and validated relationships when reviewed; keep original source fields intact.
<!-- SWE-KB:END -->

<!-- SWE-KB:FILE integration-patterns/distributed-coordination-and-resilience/materialized-view.md -->
---
record_id: architectural-and-application-integration-patterns--distributed-coordination-and-resilience--materialized-view
concept_id: materialized-view
status: seed
source_table: integration-patterns/distributed-coordination-and-resilience
---

# Materialized View

> Seed record from `Organize Software Concepts.txt`. Classification and terminology are preserved from the source table; not independently verified.

| Field | Source value |
|---|---|
| Pattern | Materialized View |
| Purpose | Precompute read-optimized representations |

## Discovery extension

Add supporting references, context, tradeoffs, limitations, and validated relationships when reviewed; keep original source fields intact.
<!-- SWE-KB:END -->

<!-- SWE-KB:FILE integration-patterns/distributed-coordination-and-resilience/rate-limiter.md -->
---
record_id: architectural-and-application-integration-patterns--distributed-coordination-and-resilience--rate-limiter
concept_id: rate-limiter
status: seed
source_table: integration-patterns/distributed-coordination-and-resilience
---

# Rate Limiter

> Seed record from `Organize Software Concepts.txt`. Classification and terminology are preserved from the source table; not independently verified.

| Field | Source value |
|---|---|
| Pattern | Rate Limiter |
| Purpose | Restrict request frequency |

## Discovery extension

Add supporting references, context, tradeoffs, limitations, and validated relationships when reviewed; keep original source fields intact.
<!-- SWE-KB:END -->

<!-- SWE-KB:FILE integration-patterns/distributed-coordination-and-resilience/read-through-cache.md -->
---
record_id: architectural-and-application-integration-patterns--distributed-coordination-and-resilience--read-through-cache
concept_id: read-through-cache
status: seed
source_table: integration-patterns/distributed-coordination-and-resilience
---

# Read-Through Cache

> Seed record from `Organize Software Concepts.txt`. Classification and terminology are preserved from the source table; not independently verified.

| Field | Source value |
|---|---|
| Pattern | Read-Through Cache |
| Purpose | Load data through a cache abstraction |

## Discovery extension

Add supporting references, context, tradeoffs, limitations, and validated relationships when reviewed; keep original source fields intact.
<!-- SWE-KB:END -->

<!-- SWE-KB:FILE integration-patterns/distributed-coordination-and-resilience/requestreply.md -->
---
record_id: architectural-and-application-integration-patterns--distributed-coordination-and-resilience--requestreply
concept_id: requestreply
status: seed
source_table: integration-patterns/distributed-coordination-and-resilience
---

# Request–Reply

> Seed record from `Organize Software Concepts.txt`. Classification and terminology are preserved from the source table; not independently verified.

| Field | Source value |
|---|---|
| Pattern | Request–Reply |
| Purpose | Correlate requests with responses |

## Discovery extension

Add supporting references, context, tradeoffs, limitations, and validated relationships when reviewed; keep original source fields intact.
<!-- SWE-KB:END -->

<!-- SWE-KB:FILE integration-patterns/distributed-coordination-and-resilience/retry.md -->
---
record_id: architectural-and-application-integration-patterns--distributed-coordination-and-resilience--retry
concept_id: retry
status: seed
source_table: integration-patterns/distributed-coordination-and-resilience
---

# Retry

> Seed record from `Organize Software Concepts.txt`. Classification and terminology are preserved from the source table; not independently verified.

| Field | Source value |
|---|---|
| Pattern | Retry |
| Purpose | Repeat transiently failed operations |

## Discovery extension

Add supporting references, context, tradeoffs, limitations, and validated relationships when reviewed; keep original source fields intact.
<!-- SWE-KB:END -->

<!-- SWE-KB:FILE integration-patterns/distributed-coordination-and-resilience/saga.md -->
---
record_id: architectural-and-application-integration-patterns--distributed-coordination-and-resilience--saga
concept_id: saga
status: seed
source_table: integration-patterns/distributed-coordination-and-resilience
---

# Saga

> Seed record from `Organize Software Concepts.txt`. Classification and terminology are preserved from the source table; not independently verified.

| Field | Source value |
|---|---|
| Pattern | Saga |
| Purpose | Coordinate distributed transactions through local transactions and compensation |

## Discovery extension

Add supporting references, context, tradeoffs, limitations, and validated relationships when reviewed; keep original source fields intact.
<!-- SWE-KB:END -->

<!-- SWE-KB:FILE integration-patterns/distributed-coordination-and-resilience/scattergather.md -->
---
record_id: architectural-and-application-integration-patterns--distributed-coordination-and-resilience--scattergather
concept_id: scattergather
status: seed
source_table: integration-patterns/distributed-coordination-and-resilience
---

# Scatter–Gather

> Seed record from `Organize Software Concepts.txt`. Classification and terminology are preserved from the source table; not independently verified.

| Field | Source value |
|---|---|
| Pattern | Scatter–Gather |
| Purpose | Aggregate responses from parallel recipients |

## Discovery extension

Add supporting references, context, tradeoffs, limitations, and validated relationships when reviewed; keep original source fields intact.
<!-- SWE-KB:END -->

<!-- SWE-KB:FILE integration-patterns/distributed-coordination-and-resilience/timeout.md -->
---
record_id: architectural-and-application-integration-patterns--distributed-coordination-and-resilience--timeout
concept_id: timeout
status: seed
source_table: integration-patterns/distributed-coordination-and-resilience
---

# Timeout

> Seed record from `Organize Software Concepts.txt`. Classification and terminology are preserved from the source table; not independently verified.

| Field | Source value |
|---|---|
| Pattern | Timeout |
| Purpose | Bound operation duration |

## Discovery extension

Add supporting references, context, tradeoffs, limitations, and validated relationships when reviewed; keep original source fields intact.
<!-- SWE-KB:END -->

<!-- SWE-KB:FILE integration-patterns/distributed-coordination-and-resilience/transactional-inbox.md -->
---
record_id: architectural-and-application-integration-patterns--distributed-coordination-and-resilience--transactional-inbox
concept_id: transactional-inbox
status: seed
source_table: integration-patterns/distributed-coordination-and-resilience
---

# Transactional Inbox

> Seed record from `Organize Software Concepts.txt`. Classification and terminology are preserved from the source table; not independently verified.

| Field | Source value |
|---|---|
| Pattern | Transactional Inbox |
| Purpose | Deduplicate and track consumed messages |

## Discovery extension

Add supporting references, context, tradeoffs, limitations, and validated relationships when reviewed; keep original source fields intact.
<!-- SWE-KB:END -->

<!-- SWE-KB:FILE integration-patterns/distributed-coordination-and-resilience/transactional-outbox.md -->
---
record_id: architectural-and-application-integration-patterns--distributed-coordination-and-resilience--transactional-outbox
concept_id: transactional-outbox
status: seed
source_table: integration-patterns/distributed-coordination-and-resilience
---

# Transactional Outbox

> Seed record from `Organize Software Concepts.txt`. Classification and terminology are preserved from the source table; not independently verified.

| Field | Source value |
|---|---|
| Pattern | Transactional Outbox |
| Purpose | Reliably publish events alongside database updates |

## Discovery extension

Add supporting references, context, tradeoffs, limitations, and validated relationships when reviewed; keep original source fields intact.
<!-- SWE-KB:END -->

<!-- SWE-KB:FILE integration-patterns/distributed-coordination-and-resilience/write-behind-cache.md -->
---
record_id: architectural-and-application-integration-patterns--distributed-coordination-and-resilience--write-behind-cache
concept_id: write-behind-cache
status: seed
source_table: integration-patterns/distributed-coordination-and-resilience
---

# Write-Behind Cache

> Seed record from `Organize Software Concepts.txt`. Classification and terminology are preserved from the source table; not independently verified.

| Field | Source value |
|---|---|
| Pattern | Write-Behind Cache |
| Purpose | Persist cached writes asynchronously |

## Discovery extension

Add supporting references, context, tradeoffs, limitations, and validated relationships when reviewed; keep original source fields intact.
<!-- SWE-KB:END -->

<!-- SWE-KB:FILE integration-patterns/distributed-coordination-and-resilience/write-through-cache.md -->
---
record_id: architectural-and-application-integration-patterns--distributed-coordination-and-resilience--write-through-cache
concept_id: write-through-cache
status: seed
source_table: integration-patterns/distributed-coordination-and-resilience
---

# Write-Through Cache

> Seed record from `Organize Software Concepts.txt`. Classification and terminology are preserved from the source table; not independently verified.

| Field | Source value |
|---|---|
| Pattern | Write-Through Cache |
| Purpose | Update cache during writes |

## Discovery extension

Add supporting references, context, tradeoffs, limitations, and validated relationships when reviewed; keep original source fields intact.
<!-- SWE-KB:END -->

<!-- SWE-KB:FILE records.tsv -->
record_id	concept_id	record_kind	source_table	path
architectural-and-application-integration-patterns--distributed-coordination-and-resilience--api-composition	api-composition	concept-source	integration-patterns/distributed-coordination-and-resilience	integration-patterns/distributed-coordination-and-resilience/api-composition.md
architectural-and-application-integration-patterns--distributed-coordination-and-resilience--bulkhead	bulkhead	concept-source	integration-patterns/distributed-coordination-and-resilience	integration-patterns/distributed-coordination-and-resilience/bulkhead.md
architectural-and-application-integration-patterns--distributed-coordination-and-resilience--cache-aside	cache-aside	concept-source	integration-patterns/distributed-coordination-and-resilience	integration-patterns/distributed-coordination-and-resilience/cache-aside.md
architectural-and-application-integration-patterns--distributed-coordination-and-resilience--circuit-breaker	circuit-breaker	concept-source	integration-patterns/distributed-coordination-and-resilience	integration-patterns/distributed-coordination-and-resilience/circuit-breaker.md
architectural-and-application-integration-patterns--distributed-coordination-and-resilience--claim-check	claim-check	concept-source	integration-patterns/distributed-coordination-and-resilience	integration-patterns/distributed-coordination-and-resilience/claim-check.md
architectural-and-application-integration-patterns--distributed-coordination-and-resilience--competing-consumers	competing-consumers	concept-source	integration-patterns/distributed-coordination-and-resilience	integration-patterns/distributed-coordination-and-resilience/competing-consumers.md
architectural-and-application-integration-patterns--distributed-coordination-and-resilience--dead-letter-queue	dead-letter-queue	concept-source	integration-patterns/distributed-coordination-and-resilience	integration-patterns/distributed-coordination-and-resilience/dead-letter-queue.md
architectural-and-application-integration-patterns--distributed-coordination-and-resilience--distributed-lock	distributed-lock	concept-source	integration-patterns/distributed-coordination-and-resilience	integration-patterns/distributed-coordination-and-resilience/distributed-lock.md
architectural-and-application-integration-patterns--distributed-coordination-and-resilience--health-check	health-check	concept-source	integration-patterns/distributed-coordination-and-resilience	integration-patterns/distributed-coordination-and-resilience/health-check.md
architectural-and-application-integration-patterns--distributed-coordination-and-resilience--heartbeat	heartbeat	concept-source	integration-patterns/distributed-coordination-and-resilience	integration-patterns/distributed-coordination-and-resilience/heartbeat.md
architectural-and-application-integration-patterns--distributed-coordination-and-resilience--idempotent-consumer	idempotent-consumer	concept-source	integration-patterns/distributed-coordination-and-resilience	integration-patterns/distributed-coordination-and-resilience/idempotent-consumer.md
architectural-and-application-integration-patterns--distributed-coordination-and-resilience--leader-election	leader-election	concept-source	integration-patterns/distributed-coordination-and-resilience	integration-patterns/distributed-coordination-and-resilience/leader-election.md
architectural-and-application-integration-patterns--distributed-coordination-and-resilience--lease	lease	concept-source	integration-patterns/distributed-coordination-and-resilience	integration-patterns/distributed-coordination-and-resilience/lease.md
architectural-and-application-integration-patterns--distributed-coordination-and-resilience--load-balancer	load-balancer	concept-source	integration-patterns/distributed-coordination-and-resilience	integration-patterns/distributed-coordination-and-resilience/load-balancer.md
architectural-and-application-integration-patterns--distributed-coordination-and-resilience--materialized-view	materialized-view	concept-source	integration-patterns/distributed-coordination-and-resilience	integration-patterns/distributed-coordination-and-resilience/materialized-view.md
architectural-and-application-integration-patterns--distributed-coordination-and-resilience--rate-limiter	rate-limiter	concept-source	integration-patterns/distributed-coordination-and-resilience	integration-patterns/distributed-coordination-and-resilience/rate-limiter.md
architectural-and-application-integration-patterns--distributed-coordination-and-resilience--read-through-cache	read-through-cache	concept-source	integration-patterns/distributed-coordination-and-resilience	integration-patterns/distributed-coordination-and-resilience/read-through-cache.md
architectural-and-application-integration-patterns--distributed-coordination-and-resilience--requestreply	requestreply	concept-source	integration-patterns/distributed-coordination-and-resilience	integration-patterns/distributed-coordination-and-resilience/requestreply.md
architectural-and-application-integration-patterns--distributed-coordination-and-resilience--retry	retry	concept-source	integration-patterns/distributed-coordination-and-resilience	integration-patterns/distributed-coordination-and-resilience/retry.md
architectural-and-application-integration-patterns--distributed-coordination-and-resilience--saga	saga	concept-source	integration-patterns/distributed-coordination-and-resilience	integration-patterns/distributed-coordination-and-resilience/saga.md
architectural-and-application-integration-patterns--distributed-coordination-and-resilience--scattergather	scattergather	concept-source	integration-patterns/distributed-coordination-and-resilience	integration-patterns/distributed-coordination-and-resilience/scattergather.md
architectural-and-application-integration-patterns--distributed-coordination-and-resilience--timeout	timeout	concept-source	integration-patterns/distributed-coordination-and-resilience	integration-patterns/distributed-coordination-and-resilience/timeout.md
architectural-and-application-integration-patterns--distributed-coordination-and-resilience--transactional-inbox	transactional-inbox	concept-source	integration-patterns/distributed-coordination-and-resilience	integration-patterns/distributed-coordination-and-resilience/transactional-inbox.md
architectural-and-application-integration-patterns--distributed-coordination-and-resilience--transactional-outbox	transactional-outbox	concept-source	integration-patterns/distributed-coordination-and-resilience	integration-patterns/distributed-coordination-and-resilience/transactional-outbox.md
architectural-and-application-integration-patterns--distributed-coordination-and-resilience--write-behind-cache	write-behind-cache	concept-source	integration-patterns/distributed-coordination-and-resilience	integration-patterns/distributed-coordination-and-resilience/write-behind-cache.md
architectural-and-application-integration-patterns--distributed-coordination-and-resilience--write-through-cache	write-through-cache	concept-source	integration-patterns/distributed-coordination-and-resilience	integration-patterns/distributed-coordination-and-resilience/write-through-cache.md
architectural-patterns--data-and-communication--api-gateway	api-gateway	concept-source	architectural-patterns/data-and-communication	architectural-patterns/data-and-communication/api-gateway.md
architectural-patterns--data-and-communication--cqrs	cqrs	concept-source	architectural-patterns/data-and-communication	architectural-patterns/data-and-communication/cqrs.md
architectural-patterns--data-and-communication--data-lakehouse	data-lakehouse	concept-source	architectural-patterns/data-and-communication	architectural-patterns/data-and-communication/data-lakehouse.md
architectural-patterns--data-and-communication--data-mesh	data-mesh	concept-source	architectural-patterns/data-and-communication	architectural-patterns/data-and-communication/data-mesh.md
architectural-patterns--data-and-communication--event-driven-architecture-eda	event-driven-architecture-eda	concept-source	architectural-patterns/data-and-communication	architectural-patterns/data-and-communication/event-driven-architecture-eda.md
architectural-patterns--data-and-communication--event-sourcing	event-sourcing	concept-source	architectural-patterns/data-and-communication	architectural-patterns/data-and-communication/event-sourcing.md
architectural-patterns--data-and-communication--kappa-architecture	kappa-architecture	concept-source	architectural-patterns/data-and-communication	architectural-patterns/data-and-communication/kappa-architecture.md
architectural-patterns--data-and-communication--lambda-architecture	lambda-architecture	concept-source	architectural-patterns/data-and-communication	architectural-patterns/data-and-communication/lambda-architecture.md
architectural-patterns--data-and-communication--leaderfollower	leaderfollower	concept-source	architectural-patterns/data-and-communication	architectural-patterns/data-and-communication/leaderfollower.md
architectural-patterns--data-and-communication--message-broker	message-broker	concept-source	architectural-patterns/data-and-communication	architectural-patterns/data-and-communication/message-broker.md
architectural-patterns--data-and-communication--peer-to-peer	peer-to-peer	concept-source	architectural-patterns/data-and-communication	architectural-patterns/data-and-communication/peer-to-peer.md
architectural-patterns--data-and-communication--pipes-and-filters	pipes-and-filters	concept-source	architectural-patterns/data-and-communication	architectural-patterns/data-and-communication/pipes-and-filters.md
architectural-patterns--data-and-communication--primaryreplica	primaryreplica	concept-source	architectural-patterns/data-and-communication	architectural-patterns/data-and-communication/primaryreplica.md
architectural-patterns--data-and-communication--publishsubscribe	publishsubscribe	concept-source	architectural-patterns/data-and-communication	architectural-patterns/data-and-communication/publishsubscribe.md
architectural-patterns--data-and-communication--sharding-partitioning	sharding-partitioning	concept-source	architectural-patterns/data-and-communication	architectural-patterns/data-and-communication/sharding-partitioning.md
architectural-patterns--data-and-communication--shared-nothing-architecture	shared-nothing-architecture	concept-source	architectural-patterns/data-and-communication	architectural-patterns/data-and-communication/shared-nothing-architecture.md
architectural-patterns--data-and-communication--sidecar	sidecar	concept-source	architectural-patterns/data-and-communication	architectural-patterns/data-and-communication/sidecar.md
architectural-patterns--migration-and-modernization--anti-corruption-layer	anti-corruption-layer	concept-source	architectural-patterns/migration-and-modernization	architectural-patterns/migration-and-modernization/anti-corruption-layer.md
architectural-patterns--migration-and-modernization--bluegreen-deployment	bluegreen-deployment	concept-source	architectural-patterns/migration-and-modernization	architectural-patterns/migration-and-modernization/bluegreen-deployment.md
architectural-patterns--migration-and-modernization--branch-by-abstraction	branch-by-abstraction	concept-source	architectural-patterns/migration-and-modernization	architectural-patterns/migration-and-modernization/branch-by-abstraction.md
architectural-patterns--migration-and-modernization--canary-deployment	canary-deployment	concept-source	architectural-patterns/migration-and-modernization	architectural-patterns/migration-and-modernization/canary-deployment.md
architectural-patterns--migration-and-modernization--change-data-capture-cdc	change-data-capture-cdc	concept-source	architectural-patterns/migration-and-modernization	architectural-patterns/migration-and-modernization/change-data-capture-cdc.md
architectural-patterns--migration-and-modernization--dual-write	dual-write	concept-source	architectural-patterns/migration-and-modernization	architectural-patterns/migration-and-modernization/dual-write.md
architectural-patterns--migration-and-modernization--expand-and-contract	expand-and-contract	concept-source	architectural-patterns/migration-and-modernization	architectural-patterns/migration-and-modernization/expand-and-contract.md
architectural-patterns--migration-and-modernization--feature-toggles	feature-toggles	concept-source	architectural-patterns/migration-and-modernization	architectural-patterns/migration-and-modernization/feature-toggles.md
architectural-patterns--migration-and-modernization--parallel-run	parallel-run	concept-source	architectural-patterns/migration-and-modernization	architectural-patterns/migration-and-modernization/parallel-run.md
architectural-patterns--migration-and-modernization--shadow-traffic	shadow-traffic	concept-source	architectural-patterns/migration-and-modernization	architectural-patterns/migration-and-modernization/shadow-traffic.md
architectural-patterns--migration-and-modernization--strangler-fig	strangler-fig	concept-source	architectural-patterns/migration-and-modernization	architectural-patterns/migration-and-modernization/strangler-fig.md
architectural-patterns--system-structure--backend-for-frontend-bff	backend-for-frontend-bff	concept-source	architectural-patterns/system-structure	architectural-patterns/system-structure/backend-for-frontend-bff.md
architectural-patterns--system-structure--cell-based-architecture	cell-based-architecture	concept-source	architectural-patterns/system-structure	architectural-patterns/system-structure/cell-based-architecture.md
architectural-patterns--system-structure--clean-architecture	clean-architecture	concept-source	architectural-patterns/system-structure	architectural-patterns/system-structure/clean-architecture.md
architectural-patterns--system-structure--hexagonal-ports-and-adapters	hexagonal-ports-and-adapters	concept-source	architectural-patterns/system-structure	architectural-patterns/system-structure/hexagonal-ports-and-adapters.md
architectural-patterns--system-structure--layered-n-tier	layered-n-tier	concept-source	architectural-patterns/system-structure	architectural-patterns/system-structure/layered-n-tier.md
architectural-patterns--system-structure--microkernel-plugin	microkernel-plugin	concept-source	architectural-patterns/system-structure	architectural-patterns/system-structure/microkernel-plugin.md
architectural-patterns--system-structure--microservices	microservices	concept-source	architectural-patterns/system-structure	architectural-patterns/system-structure/microservices.md
architectural-patterns--system-structure--modular-monolith	modular-monolith	concept-source	architectural-patterns/system-structure	architectural-patterns/system-structure/modular-monolith.md
architectural-patterns--system-structure--monolithic	monolithic	concept-source	architectural-patterns/system-structure	architectural-patterns/system-structure/monolithic.md
architectural-patterns--system-structure--onion-architecture	onion-architecture	concept-source	architectural-patterns/system-structure	architectural-patterns/system-structure/onion-architecture.md
architectural-patterns--system-structure--self-contained-systems	self-contained-systems	concept-source	architectural-patterns/system-structure	architectural-patterns/system-structure/self-contained-systems.md
architectural-patterns--system-structure--serverless	serverless	concept-source	architectural-patterns/system-structure	architectural-patterns/system-structure/serverless.md
architectural-patterns--system-structure--service-oriented-architecture-soa	service-oriented-architecture-soa	concept-source	architectural-patterns/system-structure	architectural-patterns/system-structure/service-oriented-architecture-soa.md
architectural-patterns--system-structure--space-based-architecture	space-based-architecture	concept-source	architectural-patterns/system-structure	architectural-patterns/system-structure/space-based-architecture.md
cross-category-relationships--main--data-consistency	data-consistency	relationship-source	cross-category-relationships	cross-category-relationships/data-consistency.md
cross-category-relationships--main--dip	dip	relationship-source	cross-category-relationships	cross-category-relationships/dip.md
cross-category-relationships--main--dry	dry	relationship-source	cross-category-relationships	cross-category-relationships/dry.md
cross-category-relationships--main--fault-isolation	fault-isolation	relationship-source	cross-category-relationships	cross-category-relationships/fault-isolation.md
cross-category-relationships--main--high-cohesion	high-cohesion	relationship-source	cross-category-relationships	cross-category-relationships/high-cohesion.md
cross-category-relationships--main--idempotency	idempotency	relationship-source	cross-category-relationships	cross-category-relationships/idempotency.md
cross-category-relationships--main--incremental-migration	incremental-migration	relationship-source	cross-category-relationships	cross-category-relationships/incremental-migration.md
cross-category-relationships--main--ioc	ioc	relationship-source	cross-category-relationships	cross-category-relationships/ioc.md
cross-category-relationships--main--isp	isp	relationship-source	cross-category-relationships	cross-category-relationships/isp.md
cross-category-relationships--main--low-coupling	low-coupling	relationship-source	cross-category-relationships	cross-category-relationships/low-coupling.md
cross-category-relationships--main--lsp	lsp	relationship-source	cross-category-relationships	cross-category-relationships/lsp.md
cross-category-relationships--main--ocp	ocp	relationship-source	cross-category-relationships	cross-category-relationships/ocp.md
cross-category-relationships--main--separation-of-concerns	separation-of-concerns	relationship-source	cross-category-relationships	cross-category-relationships/separation-of-concerns.md
cross-category-relationships--main--srp	srp	relationship-source	cross-category-relationships	cross-category-relationships/srp.md
design-patterns--additional-application-design-patterns--active-record	active-record	concept-source	design-patterns/additional-application-design-patterns	design-patterns/additional-application-design-patterns/active-record.md
design-patterns--additional-application-design-patterns--aggregate	aggregate	concept-source	design-patterns/additional-application-design-patterns	design-patterns/additional-application-design-patterns/aggregate.md
design-patterns--additional-application-design-patterns--callback	callback	concept-source	design-patterns/additional-application-design-patterns	design-patterns/additional-application-design-patterns/callback.md
design-patterns--additional-application-design-patterns--data-mapper	data-mapper	concept-source	design-patterns/additional-application-design-patterns	design-patterns/additional-application-design-patterns/data-mapper.md
design-patterns--additional-application-design-patterns--data-transfer-object-dto	data-transfer-object-dto	concept-source	design-patterns/additional-application-design-patterns	design-patterns/additional-application-design-patterns/data-transfer-object-dto.md
design-patterns--additional-application-design-patterns--dependency-injection-container	dependency-injection-container	concept-source	design-patterns/additional-application-design-patterns	design-patterns/additional-application-design-patterns/dependency-injection-container.md
design-patterns--additional-application-design-patterns--dependency-injection-di	dependency-injection-di	concept-source	design-patterns/additional-application-design-patterns	design-patterns/additional-application-design-patterns/dependency-injection-di.md
design-patterns--additional-application-design-patterns--domain-event	domain-event	concept-source	design-patterns/additional-application-design-patterns	design-patterns/additional-application-design-patterns/domain-event.md
design-patterns--additional-application-design-patterns--domain-service	domain-service	concept-source	design-patterns/additional-application-design-patterns	design-patterns/additional-application-design-patterns/domain-service.md
design-patterns--additional-application-design-patterns--entity	entity	concept-source	design-patterns/additional-application-design-patterns	design-patterns/additional-application-design-patterns/entity.md
design-patterns--additional-application-design-patterns--functional-core-imperative-shell	functional-core-imperative-shell	concept-source	design-patterns/additional-application-design-patterns	design-patterns/additional-application-design-patterns/functional-core-imperative-shell.md
design-patterns--additional-application-design-patterns--identity-map	identity-map	concept-source	design-patterns/additional-application-design-patterns	design-patterns/additional-application-design-patterns/identity-map.md
design-patterns--additional-application-design-patterns--lazy-initialization	lazy-initialization	concept-source	design-patterns/additional-application-design-patterns	design-patterns/additional-application-design-patterns/lazy-initialization.md
design-patterns--additional-application-design-patterns--middleware-interceptor	middleware-interceptor	concept-source	design-patterns/additional-application-design-patterns	design-patterns/additional-application-design-patterns/middleware-interceptor.md
design-patterns--additional-application-design-patterns--null-object	null-object	concept-source	design-patterns/additional-application-design-patterns	design-patterns/additional-application-design-patterns/null-object.md
design-patterns--additional-application-design-patterns--object-pool	object-pool	concept-source	design-patterns/additional-application-design-patterns	design-patterns/additional-application-design-patterns/object-pool.md
design-patterns--additional-application-design-patterns--plugin	plugin	concept-source	design-patterns/additional-application-design-patterns	design-patterns/additional-application-design-patterns/plugin.md
design-patterns--additional-application-design-patterns--policy-object	policy-object	concept-source	design-patterns/additional-application-design-patterns	design-patterns/additional-application-design-patterns/policy-object.md
design-patterns--additional-application-design-patterns--registry	registry	concept-source	design-patterns/additional-application-design-patterns	design-patterns/additional-application-design-patterns/registry.md
design-patterns--additional-application-design-patterns--repository	repository	concept-source	design-patterns/additional-application-design-patterns	design-patterns/additional-application-design-patterns/repository.md
design-patterns--additional-application-design-patterns--result-either	result-either	concept-source	design-patterns/additional-application-design-patterns	design-patterns/additional-application-design-patterns/result-either.md
design-patterns--additional-application-design-patterns--service-layer	service-layer	concept-source	design-patterns/additional-application-design-patterns	design-patterns/additional-application-design-patterns/service-layer.md
design-patterns--additional-application-design-patterns--service-locator	service-locator	concept-source	design-patterns/additional-application-design-patterns	design-patterns/additional-application-design-patterns/service-locator.md
design-patterns--additional-application-design-patterns--specification	specification	concept-source	design-patterns/additional-application-design-patterns	design-patterns/additional-application-design-patterns/specification.md
design-patterns--additional-application-design-patterns--unit-of-work	unit-of-work	concept-source	design-patterns/additional-application-design-patterns	design-patterns/additional-application-design-patterns/unit-of-work.md
design-patterns--additional-application-design-patterns--value-object	value-object	concept-source	design-patterns/additional-application-design-patterns	design-patterns/additional-application-design-patterns/value-object.md
design-patterns--behavioral-gang-of-four--chain-of-responsibility	chain-of-responsibility	concept-source	design-patterns/behavioral-gang-of-four	design-patterns/behavioral-gang-of-four/chain-of-responsibility.md
design-patterns--behavioral-gang-of-four--command	command	concept-source	design-patterns/behavioral-gang-of-four	design-patterns/behavioral-gang-of-four/command.md
design-patterns--behavioral-gang-of-four--interpreter	interpreter	concept-source	design-patterns/behavioral-gang-of-four	design-patterns/behavioral-gang-of-four/interpreter.md
design-patterns--behavioral-gang-of-four--iterator	iterator	concept-source	design-patterns/behavioral-gang-of-four	design-patterns/behavioral-gang-of-four/iterator.md
design-patterns--behavioral-gang-of-four--mediator	mediator	concept-source	design-patterns/behavioral-gang-of-four	design-patterns/behavioral-gang-of-four/mediator.md
design-patterns--behavioral-gang-of-four--memento	memento	concept-source	design-patterns/behavioral-gang-of-four	design-patterns/behavioral-gang-of-four/memento.md
design-patterns--behavioral-gang-of-four--observer	observer	concept-source	design-patterns/behavioral-gang-of-four	design-patterns/behavioral-gang-of-four/observer.md
design-patterns--behavioral-gang-of-four--state	state	concept-source	design-patterns/behavioral-gang-of-four	design-patterns/behavioral-gang-of-four/state.md
design-patterns--behavioral-gang-of-four--strategy	strategy	concept-source	design-patterns/behavioral-gang-of-four	design-patterns/behavioral-gang-of-four/strategy.md
design-patterns--behavioral-gang-of-four--template-method	template-method	concept-source	design-patterns/behavioral-gang-of-four	design-patterns/behavioral-gang-of-four/template-method.md
design-patterns--behavioral-gang-of-four--visitor	visitor	concept-source	design-patterns/behavioral-gang-of-four	design-patterns/behavioral-gang-of-four/visitor.md
design-patterns--creational-gang-of-four--abstract-factory	abstract-factory	concept-source	design-patterns/creational-gang-of-four	design-patterns/creational-gang-of-four/abstract-factory.md
design-patterns--creational-gang-of-four--builder	builder	concept-source	design-patterns/creational-gang-of-four	design-patterns/creational-gang-of-four/builder.md
design-patterns--creational-gang-of-four--factory-method	factory-method	concept-source	design-patterns/creational-gang-of-four	design-patterns/creational-gang-of-four/factory-method.md
design-patterns--creational-gang-of-four--prototype	prototype	concept-source	design-patterns/creational-gang-of-four	design-patterns/creational-gang-of-four/prototype.md
design-patterns--creational-gang-of-four--singleton	singleton	concept-source	design-patterns/creational-gang-of-four	design-patterns/creational-gang-of-four/singleton.md
design-patterns--structural-gang-of-four--adapter	adapter	concept-source	design-patterns/structural-gang-of-four	design-patterns/structural-gang-of-four/adapter.md
design-patterns--structural-gang-of-four--bridge	bridge	concept-source	design-patterns/structural-gang-of-four	design-patterns/structural-gang-of-four/bridge.md
design-patterns--structural-gang-of-four--composite	composite	concept-source	design-patterns/structural-gang-of-four	design-patterns/structural-gang-of-four/composite.md
design-patterns--structural-gang-of-four--decorator	decorator	concept-source	design-patterns/structural-gang-of-four	design-patterns/structural-gang-of-four/decorator.md
design-patterns--structural-gang-of-four--facade	facade	concept-source	design-patterns/structural-gang-of-four	design-patterns/structural-gang-of-four/facade.md
design-patterns--structural-gang-of-four--flyweight	flyweight	concept-source	design-patterns/structural-gang-of-four	design-patterns/structural-gang-of-four/flyweight.md
design-patterns--structural-gang-of-four--proxy	proxy	concept-source	design-patterns/structural-gang-of-four	design-patterns/structural-gang-of-four/proxy.md
implementation-techniques--main--adapter-wrappers	adapter-wrappers	concept-source	implementation-techniques	implementation-techniques/adapter-wrappers.md
implementation-techniques--main--algebraic-data-types	algebraic-data-types	concept-source	implementation-techniques	implementation-techniques/algebraic-data-types.md
implementation-techniques--main--automated-refactoring	automated-refactoring	concept-source	implementation-techniques	implementation-techniques/automated-refactoring.md
implementation-techniques--main--closures	closures	concept-source	implementation-techniques	implementation-techniques/closures.md
implementation-techniques--main--code-generation	code-generation	concept-source	implementation-techniques	implementation-techniques/code-generation.md
implementation-techniques--main--composition-root	composition-root	concept-source	implementation-techniques	implementation-techniques/composition-root.md
implementation-techniques--main--constructor-injection	constructor-injection	concept-source	implementation-techniques	implementation-techniques/constructor-injection.md
implementation-techniques--main--contract-testing	contract-testing	concept-source	implementation-techniques	implementation-techniques/contract-testing.md
implementation-techniques--main--copy-on-write	copy-on-write	concept-source	implementation-techniques	implementation-techniques/copy-on-write.md
implementation-techniques--main--database-migrations	database-migrations	concept-source	implementation-techniques	implementation-techniques/database-migrations.md
implementation-techniques--main--delegation	delegation	concept-source	implementation-techniques	implementation-techniques/delegation.md
implementation-techniques--main--dependency-injection-container	dependency-injection-container	concept-source	implementation-techniques	implementation-techniques/dependency-injection-container.md
implementation-techniques--main--dependency-mocking	dependency-mocking	concept-source	implementation-techniques	implementation-techniques/dependency-mocking.md
implementation-techniques--main--discriminated-unions	discriminated-unions	concept-source	implementation-techniques	implementation-techniques/discriminated-unions.md
implementation-techniques--main--dynamic-dispatch	dynamic-dispatch	concept-source	implementation-techniques	implementation-techniques/dynamic-dispatch.md
implementation-techniques--main--feature-flags	feature-flags	concept-source	implementation-techniques	implementation-techniques/feature-flags.md
implementation-techniques--main--generics-parametric-polymorphism	generics-parametric-polymorphism	concept-source	implementation-techniques	implementation-techniques/generics-parametric-polymorphism.md
implementation-techniques--main--higher-order-functions	higher-order-functions	concept-source	implementation-techniques	implementation-techniques/higher-order-functions.md
implementation-techniques--main--immutable-data-structures	immutable-data-structures	concept-source	implementation-techniques	implementation-techniques/immutable-data-structures.md
implementation-techniques--main--interface-extraction	interface-extraction	concept-source	implementation-techniques	implementation-techniques/interface-extraction.md
implementation-techniques--main--interface-injection	interface-injection	concept-source	implementation-techniques	implementation-techniques/interface-injection.md
implementation-techniques--main--lazy-evaluation	lazy-evaluation	concept-source	implementation-techniques	implementation-techniques/lazy-evaluation.md
implementation-techniques--main--linting	linting	concept-source	implementation-techniques	implementation-techniques/linting.md
implementation-techniques--main--manual-dependency-wiring	manual-dependency-wiring	concept-source	implementation-techniques	implementation-techniques/manual-dependency-wiring.md
implementation-techniques--main--memoization	memoization	concept-source	implementation-techniques	implementation-techniques/memoization.md
implementation-techniques--main--method-injection	method-injection	concept-source	implementation-techniques	implementation-techniques/method-injection.md
implementation-techniques--main--property-based-testing	property-based-testing	concept-source	implementation-techniques	implementation-techniques/property-based-testing.md
implementation-techniques--main--pure-functions	pure-functions	concept-source	implementation-techniques	implementation-techniques/pure-functions.md
implementation-techniques--main--referential-transparency	referential-transparency	concept-source	implementation-techniques	implementation-techniques/referential-transparency.md
implementation-techniques--main--schema-versioning	schema-versioning	concept-source	implementation-techniques	implementation-techniques/schema-versioning.md
implementation-techniques--main--setter-injection	setter-injection	concept-source	implementation-techniques	implementation-techniques/setter-injection.md
implementation-techniques--main--static-analysis	static-analysis	concept-source	implementation-techniques	implementation-techniques/static-analysis.md
implementation-techniques--main--static-dispatch	static-dispatch	concept-source	implementation-techniques	implementation-techniques/static-dispatch.md
implementation-techniques--main--test-doubles	test-doubles	concept-source	implementation-techniques	implementation-techniques/test-doubles.md
implementation-techniques--main--type-guards-refinement	type-guards-refinement	concept-source	implementation-techniques	implementation-techniques/type-guards-refinement.md
software-design-principles--additional-object-oriented-and-modularity-principles--acyclic-dependencies-principle-adp	acyclic-dependencies-principle-adp	concept-source	software-design-principles/additional-object-oriented-and-modularity-principles	software-design-principles/additional-object-oriented-and-modularity-principles/acyclic-dependencies-principle-adp.md
software-design-principles--additional-object-oriented-and-modularity-principles--commandquery-separation-cqs	commandquery-separation-cqs	concept-source	software-design-principles/additional-object-oriented-and-modularity-principles	software-design-principles/additional-object-oriented-and-modularity-principles/commandquery-separation-cqs.md
software-design-principles--additional-object-oriented-and-modularity-principles--common-closure-principle-ccp	common-closure-principle-ccp	concept-source	software-design-principles/additional-object-oriented-and-modularity-principles	software-design-principles/additional-object-oriented-and-modularity-principles/common-closure-principle-ccp.md
software-design-principles--additional-object-oriented-and-modularity-principles--common-reuse-principle-crp	common-reuse-principle-crp	concept-source	software-design-principles/additional-object-oriented-and-modularity-principles	software-design-principles/additional-object-oriented-and-modularity-principles/common-reuse-principle-crp.md
software-design-principles--additional-object-oriented-and-modularity-principles--dependency-abstraction	dependency-abstraction	concept-source	software-design-principles/additional-object-oriented-and-modularity-principles	software-design-principles/additional-object-oriented-and-modularity-principles/dependency-abstraction.md
software-design-principles--additional-object-oriented-and-modularity-principles--design-by-contract-dbc	design-by-contract-dbc	concept-source	software-design-principles/additional-object-oriented-and-modularity-principles	software-design-principles/additional-object-oriented-and-modularity-principles/design-by-contract-dbc.md
software-design-principles--additional-object-oriented-and-modularity-principles--favor-immutability	favor-immutability	concept-source	software-design-principles/additional-object-oriented-and-modularity-principles	software-design-principles/additional-object-oriented-and-modularity-principles/favor-immutability.md
software-design-principles--additional-object-oriented-and-modularity-principles--interface-based-programming	interface-based-programming	concept-source	software-design-principles/additional-object-oriented-and-modularity-principles	software-design-principles/additional-object-oriented-and-modularity-principles/interface-based-programming.md
software-design-principles--additional-object-oriented-and-modularity-principles--inversion-of-control-ioc	inversion-of-control-ioc	concept-source	software-design-principles/additional-object-oriented-and-modularity-principles	software-design-principles/additional-object-oriented-and-modularity-principles/inversion-of-control-ioc.md
software-design-principles--additional-object-oriented-and-modularity-principles--program-to-an-interface	program-to-an-interface	concept-source	software-design-principles/additional-object-oriented-and-modularity-principles	software-design-principles/additional-object-oriented-and-modularity-principles/program-to-an-interface.md
software-design-principles--additional-object-oriented-and-modularity-principles--protected-variations	protected-variations	concept-source	software-design-principles/additional-object-oriented-and-modularity-principles	software-design-principles/additional-object-oriented-and-modularity-principles/protected-variations.md
software-design-principles--additional-object-oriented-and-modularity-principles--reuse-release-equivalence-principle-rep	reuse-release-equivalence-principle-rep	concept-source	software-design-principles/additional-object-oriented-and-modularity-principles	software-design-principles/additional-object-oriented-and-modularity-principles/reuse-release-equivalence-principle-rep.md
software-design-principles--additional-object-oriented-and-modularity-principles--stable-abstractions-principle-sap	stable-abstractions-principle-sap	concept-source	software-design-principles/additional-object-oriented-and-modularity-principles	software-design-principles/additional-object-oriented-and-modularity-principles/stable-abstractions-principle-sap.md
software-design-principles--additional-object-oriented-and-modularity-principles--stable-dependencies-principle-sdp	stable-dependencies-principle-sdp	concept-source	software-design-principles/additional-object-oriented-and-modularity-principles	software-design-principles/additional-object-oriented-and-modularity-principles/stable-dependencies-principle-sdp.md
software-design-principles--additional-object-oriented-and-modularity-principles--tell-don-t-ask	tell-don-t-ask	concept-source	software-design-principles/additional-object-oriented-and-modularity-principles	software-design-principles/additional-object-oriented-and-modularity-principles/tell-don-t-ask.md
software-design-principles--distributed-systems-principles--at-least-once-delivery	at-least-once-delivery	concept-source	software-design-principles/distributed-systems-principles	software-design-principles/distributed-systems-principles/at-least-once-delivery.md
software-design-principles--distributed-systems-principles--at-most-once-delivery	at-most-once-delivery	concept-source	software-design-principles/distributed-systems-principles	software-design-principles/distributed-systems-principles/at-most-once-delivery.md
software-design-principles--distributed-systems-principles--backpressure	backpressure	concept-source	software-design-principles/distributed-systems-principles	software-design-principles/distributed-systems-principles/backpressure.md
software-design-principles--distributed-systems-principles--defense-in-depth	defense-in-depth	concept-source	software-design-principles/distributed-systems-principles	software-design-principles/distributed-systems-principles/defense-in-depth.md
software-design-principles--distributed-systems-principles--end-to-end-principle	end-to-end-principle	concept-source	software-design-principles/distributed-systems-principles	software-design-principles/distributed-systems-principles/end-to-end-principle.md
software-design-principles--distributed-systems-principles--eventual-consistency	eventual-consistency	concept-source	software-design-principles/distributed-systems-principles	software-design-principles/distributed-systems-principles/eventual-consistency.md
software-design-principles--distributed-systems-principles--fault-isolation	fault-isolation	concept-source	software-design-principles/distributed-systems-principles	software-design-principles/distributed-systems-principles/fault-isolation.md
software-design-principles--distributed-systems-principles--graceful-degradation	graceful-degradation	concept-source	software-design-principles/distributed-systems-principles	software-design-principles/distributed-systems-principles/graceful-degradation.md
software-design-principles--distributed-systems-principles--idempotency	idempotency	concept-source	software-design-principles/distributed-systems-principles	software-design-principles/distributed-systems-principles/idempotency.md
software-design-principles--distributed-systems-principles--retry-with-backoff	retry-with-backoff	concept-source	software-design-principles/distributed-systems-principles	software-design-principles/distributed-systems-principles/retry-with-backoff.md
software-design-principles--distributed-systems-principles--strong-consistency	strong-consistency	concept-source	software-design-principles/distributed-systems-principles	software-design-principles/distributed-systems-principles/strong-consistency.md
software-design-principles--distributed-systems-principles--timeout-budgeting	timeout-budgeting	concept-source	software-design-principles/distributed-systems-principles	software-design-principles/distributed-systems-principles/timeout-budgeting.md
software-design-principles--distributed-systems-principles--zero-trust	zero-trust	concept-source	software-design-principles/distributed-systems-principles	software-design-principles/distributed-systems-principles/zero-trust.md
software-design-principles--general-engineering-principles--composition-over-inheritance	composition-over-inheritance	concept-source	software-design-principles/general-engineering-principles	software-design-principles/general-engineering-principles/composition-over-inheritance.md
software-design-principles--general-engineering-principles--convention-over-configuration	convention-over-configuration	concept-source	software-design-principles/general-engineering-principles	software-design-principles/general-engineering-principles/convention-over-configuration.md
software-design-principles--general-engineering-principles--defensive-programming	defensive-programming	concept-source	software-design-principles/general-engineering-principles	software-design-principles/general-engineering-principles/defensive-programming.md
software-design-principles--general-engineering-principles--dry	dry	concept-source	software-design-principles/general-engineering-principles	software-design-principles/general-engineering-principles/dry.md
software-design-principles--general-engineering-principles--encapsulation	encapsulation	concept-source	software-design-principles/general-engineering-principles	software-design-principles/general-engineering-principles/encapsulation.md
software-design-principles--general-engineering-principles--explicit-over-implicit	explicit-over-implicit	concept-source	software-design-principles/general-engineering-principles	software-design-principles/general-engineering-principles/explicit-over-implicit.md
software-design-principles--general-engineering-principles--fail-fast	fail-fast	concept-source	software-design-principles/general-engineering-principles	software-design-principles/general-engineering-principles/fail-fast.md
software-design-principles--general-engineering-principles--high-cohesion	high-cohesion	concept-source	software-design-principles/general-engineering-principles	software-design-principles/general-engineering-principles/high-cohesion.md
software-design-principles--general-engineering-principles--information-hiding	information-hiding	concept-source	software-design-principles/general-engineering-principles	software-design-principles/general-engineering-principles/information-hiding.md
software-design-principles--general-engineering-principles--kiss	kiss	concept-source	software-design-principles/general-engineering-principles	software-design-principles/general-engineering-principles/kiss.md
software-design-principles--general-engineering-principles--least-astonishment	least-astonishment	concept-source	software-design-principles/general-engineering-principles	software-design-principles/general-engineering-principles/least-astonishment.md
software-design-principles--general-engineering-principles--low-coupling	low-coupling	concept-source	software-design-principles/general-engineering-principles	software-design-principles/general-engineering-principles/low-coupling.md
software-design-principles--general-engineering-principles--orthogonality	orthogonality	concept-source	software-design-principles/general-engineering-principles	software-design-principles/general-engineering-principles/orthogonality.md
software-design-principles--general-engineering-principles--principle-of-least-authority	principle-of-least-authority	concept-source	software-design-principles/general-engineering-principles	software-design-principles/general-engineering-principles/principle-of-least-authority.md
software-design-principles--general-engineering-principles--principle-of-least-knowledge-law-of-demeter	principle-of-least-knowledge-law-of-demeter	concept-source	software-design-principles/general-engineering-principles	software-design-principles/general-engineering-principles/principle-of-least-knowledge-law-of-demeter.md
software-design-principles--general-engineering-principles--principle-of-least-privilege	principle-of-least-privilege	concept-source	software-design-principles/general-engineering-principles	software-design-principles/general-engineering-principles/principle-of-least-privilege.md
software-design-principles--general-engineering-principles--principle-of-reversibility	principle-of-reversibility	concept-source	software-design-principles/general-engineering-principles	software-design-principles/general-engineering-principles/principle-of-reversibility.md
software-design-principles--general-engineering-principles--separation-of-concerns-soc	separation-of-concerns-soc	concept-source	software-design-principles/general-engineering-principles	software-design-principles/general-engineering-principles/separation-of-concerns-soc.md
software-design-principles--general-engineering-principles--single-source-of-truth	single-source-of-truth	concept-source	software-design-principles/general-engineering-principles	software-design-principles/general-engineering-principles/single-source-of-truth.md
software-design-principles--general-engineering-principles--yagni	yagni	concept-source	software-design-principles/general-engineering-principles	software-design-principles/general-engineering-principles/yagni.md
software-design-principles--solid-principles--d-dependency-inversion-dip	d-dependency-inversion-dip	concept-source	software-design-principles/solid-principles	software-design-principles/solid-principles/d-dependency-inversion-dip.md
software-design-principles--solid-principles--i-interface-segregation-isp	i-interface-segregation-isp	concept-source	software-design-principles/solid-principles	software-design-principles/solid-principles/i-interface-segregation-isp.md
software-design-principles--solid-principles--l-liskov-substitution-lsp	l-liskov-substitution-lsp	concept-source	software-design-principles/solid-principles	software-design-principles/solid-principles/l-liskov-substitution-lsp.md
software-design-principles--solid-principles--o-open-closed-ocp	o-open-closed-ocp	concept-source	software-design-principles/solid-principles	software-design-principles/solid-principles/o-open-closed-ocp.md
software-design-principles--solid-principles--s-single-responsibility-srp	s-single-responsibility-srp	concept-source	software-design-principles/solid-principles	software-design-principles/solid-principles/s-single-responsibility-srp.md
<!-- SWE-KB:END -->

<!-- SWE-KB:FILE relationships.tsv -->
subject	subject_id	relation	object	object_id	source_record_id	source_path	status
Data Consistency		common-pattern	Outbox		cross-category-relationships--main--data-consistency	cross-category-relationships/data-consistency.md	seed
Data Consistency		common-pattern	Saga	saga	cross-category-relationships--main--data-consistency	cross-category-relationships/data-consistency.md	seed
Data Consistency		implementation-technique	deduplication		cross-category-relationships--main--data-consistency	cross-category-relationships/data-consistency.md	seed
Data Consistency		implementation-technique	Transactions		cross-category-relationships--main--data-consistency	cross-category-relationships/data-consistency.md	seed
Incremental Migration		common-pattern	Branch by Abstraction	branch-by-abstraction	cross-category-relationships--main--incremental-migration	cross-category-relationships/incremental-migration.md	seed
Incremental Migration		common-pattern	Strangler Fig	strangler-fig	cross-category-relationships--main--incremental-migration	cross-category-relationships/incremental-migration.md	seed
Incremental Migration		implementation-technique	feature flags	feature-flags	cross-category-relationships--main--incremental-migration	cross-category-relationships/incremental-migration.md	seed
Incremental Migration		implementation-technique	Routing		cross-category-relationships--main--incremental-migration	cross-category-relationships/incremental-migration.md	seed
Adapter Wrappers	adapter-wrappers	related-concept	Adapter	adapter	implementation-techniques--main--adapter-wrappers	implementation-techniques/adapter-wrappers.md	seed
Algebraic Data Types	algebraic-data-types	related-concept	Type safety		implementation-techniques--main--algebraic-data-types	implementation-techniques/algebraic-data-types.md	seed
Automated Refactoring	automated-refactoring	related-concept	Maintainability		implementation-techniques--main--automated-refactoring	implementation-techniques/automated-refactoring.md	seed
Closures	closures	related-concept	Encapsulation	encapsulation	implementation-techniques--main--closures	implementation-techniques/closures.md	seed
Code Generation	code-generation	related-concept	DRY	dry	implementation-techniques--main--code-generation	implementation-techniques/code-generation.md	seed
Composition Root	composition-root	related-concept	DI	dependency-injection-di	implementation-techniques--main--composition-root	implementation-techniques/composition-root.md	seed
Composition Root	composition-root	related-concept	IoC	inversion-of-control-ioc	implementation-techniques--main--composition-root	implementation-techniques/composition-root.md	seed
Constructor Injection	constructor-injection	related-concept	DI	dependency-injection-di	implementation-techniques--main--constructor-injection	implementation-techniques/constructor-injection.md	seed
Constructor Injection	constructor-injection	related-concept	DIP	d-dependency-inversion-dip	implementation-techniques--main--constructor-injection	implementation-techniques/constructor-injection.md	seed
Contract Testing	contract-testing	related-concept	Distributed systems		implementation-techniques--main--contract-testing	implementation-techniques/contract-testing.md	seed
Copy-on-Write	copy-on-write	related-concept	Immutability		implementation-techniques--main--copy-on-write	implementation-techniques/copy-on-write.md	seed
DIP	d-dependency-inversion-dip	common-pattern	Adapter	adapter	cross-category-relationships--main--dip	cross-category-relationships/dip.md	seed
DIP	d-dependency-inversion-dip	common-pattern	DI	dependency-injection-di	cross-category-relationships--main--dip	cross-category-relationships/dip.md	seed
DIP	d-dependency-inversion-dip	common-pattern	Strategy	strategy	cross-category-relationships--main--dip	cross-category-relationships/dip.md	seed
DIP	d-dependency-inversion-dip	implementation-technique	Constructor injection	constructor-injection	cross-category-relationships--main--dip	cross-category-relationships/dip.md	seed
DIP	d-dependency-inversion-dip	implementation-technique	interfaces		cross-category-relationships--main--dip	cross-category-relationships/dip.md	seed
Database Migrations	database-migrations	related-concept	Expand–Contract		implementation-techniques--main--database-migrations	implementation-techniques/database-migrations.md	seed
Delegation	delegation	related-concept	Composition		implementation-techniques--main--delegation	implementation-techniques/delegation.md	seed
Dependency Injection Container	dependency-injection-container	related-concept	DI	dependency-injection-di	implementation-techniques--main--dependency-injection-container	implementation-techniques/dependency-injection-container.md	seed
Dependency Injection Container	dependency-injection-container	related-concept	IoC	inversion-of-control-ioc	implementation-techniques--main--dependency-injection-container	implementation-techniques/dependency-injection-container.md	seed
Dependency Mocking	dependency-mocking	related-concept	Testability		implementation-techniques--main--dependency-mocking	implementation-techniques/dependency-mocking.md	seed
Discriminated Unions	discriminated-unions	related-concept	Result		implementation-techniques--main--discriminated-unions	implementation-techniques/discriminated-unions.md	seed
Discriminated Unions	discriminated-unions	related-concept	State	state	implementation-techniques--main--discriminated-unions	implementation-techniques/discriminated-unions.md	seed
DRY	dry	common-pattern	Strategy	strategy	cross-category-relationships--main--dry	cross-category-relationships/dry.md	seed
DRY	dry	common-pattern	Template Method	template-method	cross-category-relationships--main--dry	cross-category-relationships/dry.md	seed
DRY	dry	implementation-technique	code generation	code-generation	cross-category-relationships--main--dry	cross-category-relationships/dry.md	seed
DRY	dry	implementation-technique	Shared abstractions		cross-category-relationships--main--dry	cross-category-relationships/dry.md	seed
Dynamic Dispatch	dynamic-dispatch	related-concept	Polymorphism		implementation-techniques--main--dynamic-dispatch	implementation-techniques/dynamic-dispatch.md	seed
Fault Isolation	fault-isolation	common-pattern	Bulkhead	bulkhead	cross-category-relationships--main--fault-isolation	cross-category-relationships/fault-isolation.md	seed
Fault Isolation	fault-isolation	common-pattern	Cell-Based		cross-category-relationships--main--fault-isolation	cross-category-relationships/fault-isolation.md	seed
Fault Isolation	fault-isolation	implementation-technique	Separate resource pools		cross-category-relationships--main--fault-isolation	cross-category-relationships/fault-isolation.md	seed
Feature Flags	feature-flags	related-concept	Migration		implementation-techniques--main--feature-flags	implementation-techniques/feature-flags.md	seed
Generics / Parametric Polymorphism	generics-parametric-polymorphism	related-concept	Abstraction		implementation-techniques--main--generics-parametric-polymorphism	implementation-techniques/generics-parametric-polymorphism.md	seed
High Cohesion	high-cohesion	common-pattern	Aggregate	aggregate	cross-category-relationships--main--high-cohesion	cross-category-relationships/high-cohesion.md	seed
High Cohesion	high-cohesion	common-pattern	Modular Monolith	modular-monolith	cross-category-relationships--main--high-cohesion	cross-category-relationships/high-cohesion.md	seed
High Cohesion	high-cohesion	implementation-technique	Module boundaries		cross-category-relationships--main--high-cohesion	cross-category-relationships/high-cohesion.md	seed
Higher-Order Functions	higher-order-functions	related-concept	composition		implementation-techniques--main--higher-order-functions	implementation-techniques/higher-order-functions.md	seed
Higher-Order Functions	higher-order-functions	related-concept	Strategy	strategy	implementation-techniques--main--higher-order-functions	implementation-techniques/higher-order-functions.md	seed
ISP	i-interface-segregation-isp	common-pattern	Adapter	adapter	cross-category-relationships--main--isp	cross-category-relationships/isp.md	seed
ISP	i-interface-segregation-isp	common-pattern	Facade	facade	cross-category-relationships--main--isp	cross-category-relationships/isp.md	seed
ISP	i-interface-segregation-isp	implementation-technique	Small interfaces		cross-category-relationships--main--isp	cross-category-relationships/isp.md	seed
Idempotency	idempotency	common-pattern	Idempotent Consumer	idempotent-consumer	cross-category-relationships--main--idempotency	cross-category-relationships/idempotency.md	seed
Idempotency	idempotency	common-pattern	Inbox		cross-category-relationships--main--idempotency	cross-category-relationships/idempotency.md	seed
Idempotency	idempotency	implementation-technique	Idempotency keys		cross-category-relationships--main--idempotency	cross-category-relationships/idempotency.md	seed
Immutable Data Structures	immutable-data-structures	related-concept	Immutability		implementation-techniques--main--immutable-data-structures	implementation-techniques/immutable-data-structures.md	seed
Interface Extraction	interface-extraction	related-concept	DIP	d-dependency-inversion-dip	implementation-techniques--main--interface-extraction	implementation-techniques/interface-extraction.md	seed
Interface Extraction	interface-extraction	related-concept	ISP	i-interface-segregation-isp	implementation-techniques--main--interface-extraction	implementation-techniques/interface-extraction.md	seed
Interface Injection	interface-injection	related-concept	DI	dependency-injection-di	implementation-techniques--main--interface-injection	implementation-techniques/interface-injection.md	seed
IoC	inversion-of-control-ioc	common-pattern	DI	dependency-injection-di	cross-category-relationships--main--ioc	cross-category-relationships/ioc.md	seed
IoC	inversion-of-control-ioc	common-pattern	Observer	observer	cross-category-relationships--main--ioc	cross-category-relationships/ioc.md	seed
IoC	inversion-of-control-ioc	common-pattern	Template Method	template-method	cross-category-relationships--main--ioc	cross-category-relationships/ioc.md	seed
IoC	inversion-of-control-ioc	implementation-technique	Callbacks		cross-category-relationships--main--ioc	cross-category-relationships/ioc.md	seed
IoC	inversion-of-control-ioc	implementation-technique	containers		cross-category-relationships--main--ioc	cross-category-relationships/ioc.md	seed
LSP	l-liskov-substitution-lsp	common-pattern	Strategy	strategy	cross-category-relationships--main--lsp	cross-category-relationships/lsp.md	seed
LSP	l-liskov-substitution-lsp	common-pattern	Template Method	template-method	cross-category-relationships--main--lsp	cross-category-relationships/lsp.md	seed
LSP	l-liskov-substitution-lsp	implementation-technique	Contract tests		cross-category-relationships--main--lsp	cross-category-relationships/lsp.md	seed
Lazy Evaluation	lazy-evaluation	related-concept	Efficiency		implementation-techniques--main--lazy-evaluation	implementation-techniques/lazy-evaluation.md	seed
Linting	linting	related-concept	Maintainability		implementation-techniques--main--linting	implementation-techniques/linting.md	seed
Low Coupling	low-coupling	common-pattern	DI	dependency-injection-di	cross-category-relationships--main--low-coupling	cross-category-relationships/low-coupling.md	seed
Low Coupling	low-coupling	common-pattern	Mediator	mediator	cross-category-relationships--main--low-coupling	cross-category-relationships/low-coupling.md	seed
Low Coupling	low-coupling	common-pattern	Observer	observer	cross-category-relationships--main--low-coupling	cross-category-relationships/low-coupling.md	seed
Low Coupling	low-coupling	implementation-technique	Event dispatch		cross-category-relationships--main--low-coupling	cross-category-relationships/low-coupling.md	seed
Low Coupling	low-coupling	implementation-technique	interfaces		cross-category-relationships--main--low-coupling	cross-category-relationships/low-coupling.md	seed
Manual Dependency Wiring	manual-dependency-wiring	related-concept	DI	dependency-injection-di	implementation-techniques--main--manual-dependency-wiring	implementation-techniques/manual-dependency-wiring.md	seed
Memoization	memoization	related-concept	Performance		implementation-techniques--main--memoization	implementation-techniques/memoization.md	seed
Method Injection	method-injection	related-concept	DI	dependency-injection-di	implementation-techniques--main--method-injection	implementation-techniques/method-injection.md	seed
OCP	o-open-closed-ocp	common-pattern	Decorator	decorator	cross-category-relationships--main--ocp	cross-category-relationships/ocp.md	seed
OCP	o-open-closed-ocp	common-pattern	Plugin	plugin	cross-category-relationships--main--ocp	cross-category-relationships/ocp.md	seed
OCP	o-open-closed-ocp	common-pattern	Strategy	strategy	cross-category-relationships--main--ocp	cross-category-relationships/ocp.md	seed
OCP	o-open-closed-ocp	implementation-technique	composition		cross-category-relationships--main--ocp	cross-category-relationships/ocp.md	seed
OCP	o-open-closed-ocp	implementation-technique	Polymorphism		cross-category-relationships--main--ocp	cross-category-relationships/ocp.md	seed
Property-Based Testing	property-based-testing	related-concept	Correctness		implementation-techniques--main--property-based-testing	implementation-techniques/property-based-testing.md	seed
Pure Functions	pure-functions	related-concept	Functional programming		implementation-techniques--main--pure-functions	implementation-techniques/pure-functions.md	seed
Referential Transparency	referential-transparency	related-concept	Functional programming		implementation-techniques--main--referential-transparency	implementation-techniques/referential-transparency.md	seed
SRP	s-single-responsibility-srp	common-pattern	Repository	repository	cross-category-relationships--main--srp	cross-category-relationships/srp.md	seed
SRP	s-single-responsibility-srp	common-pattern	Service Layer	service-layer	cross-category-relationships--main--srp	cross-category-relationships/srp.md	seed
SRP	s-single-responsibility-srp	implementation-technique	Module extraction		cross-category-relationships--main--srp	cross-category-relationships/srp.md	seed
Schema Versioning	schema-versioning	related-concept	API evolution		implementation-techniques--main--schema-versioning	implementation-techniques/schema-versioning.md	seed
Separation of Concerns	separation-of-concerns-soc	common-pattern	CQRS	cqrs	cross-category-relationships--main--separation-of-concerns	cross-category-relationships/separation-of-concerns.md	seed
Separation of Concerns	separation-of-concerns-soc	common-pattern	Hexagonal		cross-category-relationships--main--separation-of-concerns	cross-category-relationships/separation-of-concerns.md	seed
Separation of Concerns	separation-of-concerns-soc	common-pattern	MVC		cross-category-relationships--main--separation-of-concerns	cross-category-relationships/separation-of-concerns.md	seed
Separation of Concerns	separation-of-concerns-soc	implementation-technique	Layering		cross-category-relationships--main--separation-of-concerns	cross-category-relationships/separation-of-concerns.md	seed
Separation of Concerns	separation-of-concerns-soc	implementation-technique	ports		cross-category-relationships--main--separation-of-concerns	cross-category-relationships/separation-of-concerns.md	seed
Setter Injection	setter-injection	related-concept	DI	dependency-injection-di	implementation-techniques--main--setter-injection	implementation-techniques/setter-injection.md	seed
Static Analysis	static-analysis	related-concept	Quality		implementation-techniques--main--static-analysis	implementation-techniques/static-analysis.md	seed
Static Dispatch	static-dispatch	related-concept	Polymorphism		implementation-techniques--main--static-dispatch	implementation-techniques/static-dispatch.md	seed
Test Doubles	test-doubles	related-concept	DI	dependency-injection-di	implementation-techniques--main--test-doubles	implementation-techniques/test-doubles.md	seed
Type Guards / Refinement	type-guards-refinement	related-concept	Type safety		implementation-techniques--main--type-guards-refinement	implementation-techniques/type-guards-refinement.md	seed
<!-- SWE-KB:END -->

<!-- SWE-KB:FILE scripts/build-index.py mode=755 -->
#!/usr/bin/env python3
"""Rebuild CLI lookup indexes and hierarchical INDEX.md from Markdown seed records.

No third-party dependencies. Leaf Markdown is the source of truth. Generated files
must not be manually edited: rerun `python3 scripts/build-index.py`.
"""
from __future__ import annotations

import argparse
import collections
import re
import sys
import unicodedata
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
ROOT_AGENTS = ROOT / 'AGENTS.md'
SEED_TABLE = 'cross-category-relationships'
SUMMARY_KEYS = ('Purpose', 'Meaning', 'Definition', 'Primary benefit')
SKIP = {'AGENTS.md', 'INDEX.md', 'README.md'}


def norm(value: str) -> str:
    value = unicodedata.normalize('NFKD', value).casefold()
    value = ''.join(c for c in value if not unicodedata.combining(c))
    return re.sub(r'[^a-z0-9]+', '-', value).strip('-')


def read_record(path: Path) -> dict[str, str]:
    raw = path.read_text(encoding='utf-8')
    if not raw.startswith('---\n') or '\n---\n' not in raw[4:]:
        raise ValueError(f'No YAML frontmatter: {path}')
    head, body = raw[4:].split('\n---\n', 1)
    meta = dict(line.split(': ', 1) for line in head.splitlines() if ': ' in line)
    for key in ('record_id', 'concept_id', 'status', 'source_table'):
        if not meta.get(key):
            raise ValueError(f'Missing {key}: {path}')
    title_match = re.search(r'^# (.+)$', body, re.M)
    if title_match is None:
        raise ValueError(f'Missing title: {path}')
    fields = {}
    for line in body.splitlines():
        if line.startswith('|'):
            cols = [cell.strip().replace('\\|', '|') for cell in line.split('|')[1:-1]]
            if len(cols) == 2 and cols[0] not in ('Field', '---'):
                fields[cols[0]] = cols[1]
    return dict(meta, title=title_match.group(1).strip(), fields=fields,
                path=path.relative_to(ROOT).as_posix(), content=body)


def candidates_for_alias(record: dict[str, str]) -> list[tuple[str, str]]:
    title = record['title']
    result = [(record['concept_id'], 'id'), (title, 'title')]
    prefix_removed = re.sub(r'^[SOLID] [—–-] ', '', title)
    if prefix_removed != title:
        result.append((prefix_removed, 'title-variant'))
    for s in (title, prefix_removed):
        shortened = re.sub(r'\s*\(([^)]{1,12})\)\s*$', '', s)
        if shortened != s:
            result.extend([(shortened, 'title-variant'), (norm(shortened), 'slug-variant')])
        m = re.search(r'\(([^)]{1,12})\)\s*$', s)
        if m and re.fullmatch(r'[A-Za-z][A-Za-z0-9&-]{1,9}', m.group(1)):
            result.append((m.group(1), 'acronym'))
    for item in record.get('aliases', '').split(','):
        if item.strip():
            result.append((item.strip(), 'curated'))
    return [(label, origin) for label, origin in result if norm(label)]


def tsv(headers: list[str], rows: list[list[str]]) -> str:
    def clean(s: object) -> str:
        return str(s).replace('\t', ' ').replace('\r', ' ').replace('\n', ' ')
    return '\n'.join(['\t'.join(headers)] + ['\t'.join(map(clean, row)) for row in rows]) + '\n'


def build() -> tuple[dict[Path, str], dict[str, object]]:
    paths = sorted(p for p in ROOT.rglob('*.md') if p.name not in SKIP)
    records = [read_record(p) for p in paths]
    ids = [r['record_id'] for r in records]
    if len(set(ids)) != len(ids):
        raise ValueError('Duplicate record_id (source record identifiers must be unique)')
    concepts: dict[str, list[dict[str, str]]] = collections.defaultdict(list)
    for record in records:
        if not record['path'].startswith(SEED_TABLE + '/'):
            concepts[record['concept_id']].append(record)
    # Prefer design-pattern classification over implementation-techniques for one
    # duplicated ID. Source-row classifications remain unchanged/unverified.
    priority = ['architectural-patterns', 'software-design-principles',
                'design-patterns', 'integration-patterns', 'implementation-techniques']
    def weight(r: dict[str, str]) -> tuple[int, str]:
        section = r['path'].split('/', 1)[0]
        return (priority.index(section) if section in priority else 100, r['path'])
    canonical = {cid: min(versions, key=weight) for cid, versions in concepts.items()}

    # Index only unambiguous aliases. Collisions are documented in the report;
    # never silently alias one term to unrelated canonical concepts.
    aliases: dict[str, tuple[str, str, str]] = {}
    conflicts: dict[str, set[str]] = collections.defaultdict(set)
    for cid, record in sorted(canonical.items()):
        for name, origin in candidates_for_alias(record):
            key = norm(name)
            if key in aliases and aliases[key][1] != cid:
                conflicts[key].update((aliases[key][1], cid))
                continue
            if key not in aliases:
                aliases[key] = (name, cid, origin)
    # Exact concept identifiers are stable and take precedence if a conflicting
    # title happens to normalize to the same string.
    for cid in canonical:
        aliases[cid] = (cid, cid, 'id')
    for ambiguous in conflicts:
        if ambiguous not in canonical:
            aliases.pop(ambiguous, None)

    def resolve(label: str) -> str:
        key = norm(label)
        return key if key in canonical else (aliases[key][1] if key in aliases else '')

    record_rows = [[r['record_id'], r['concept_id'],
                    'relationship-source' if r['path'].startswith(SEED_TABLE + '/') else 'concept-source',
                    r['source_table'], r['path']] for r in sorted(records, key=lambda r: r['record_id'])]
    catalog_rows = []
    for cid, r in sorted(canonical.items()):
        category = r['path'].split('/')[0]
        kind = {'architectural-patterns': 'architectural-pattern',
                'software-design-principles': 'principle',
                'design-patterns': 'design-pattern',
                'integration-patterns': 'integration-pattern',
                'implementation-techniques': 'technique'}.get(category, 'unclassified')
        summary = next((r['fields'][k] for k in SUMMARY_KEYS if r['fields'].get(k)), '')
        catalog_rows.append([cid, kind, category, r['title'], r['path'], summary, r['status']])
    alias_rows = [[*aliases[a][:2], a, aliases[a][2]] for a in sorted(aliases)]

    rel_rows: list[list[str]] = []
    for r in records:
        f = r['fields']
        if r['path'].startswith(SEED_TABLE + '/'):
            subject = f.get('Principle / Goal', r['title'])
            for key, pred in (('Common patterns', 'common-pattern'),
                              ('Implementation techniques', 'implementation-technique')):
                for label in (s.strip() for s in f.get(key, '').split(',')):
                    if label:
                        rel_rows.append([subject, resolve(subject), pred, label, resolve(label),
                                         r['record_id'], r['path'], r['status']])
        elif f.get('Related concepts'):
            for label in (s.strip() for s in f['Related concepts'].split(',')):
                if label:
                    rel_rows.append([r['title'], r['concept_id'], 'related-concept',
                                     label, resolve(label), r['record_id'], r['path'], r['status']])
    rel_rows.sort(key=lambda row: (row[1], norm(row[0]), row[2], norm(row[3]), row[5]))

    outputs: dict[Path, str] = {}
    outputs[ROOT / 'catalog.tsv'] = tsv(['id','kind','category','name','path','summary','status'], catalog_rows)
    outputs[ROOT / 'aliases.tsv'] = tsv(['alias','id','normalized','origin'], alias_rows)
    outputs[ROOT / 'records.tsv'] = tsv(['record_id','concept_id','record_kind','source_table','path'], record_rows)
    outputs[ROOT / 'relationships.tsv'] = tsv(['subject','subject_id','relation','object','object_id','source_record_id','source_path','status'], rel_rows)

    # Category indexes are generated from child directories and source row records.
    # Derive route folders from actual source-row paths, never from incidental
    # directories such as scripts/, tests/, caches/, or local tooling.
    route_folders: set[Path] = set()
    for record in records:
        parent = (ROOT / record['path']).parent
        while parent != ROOT:
            route_folders.add(parent)
            parent = parent.parent
    folders = sorted(route_folders, key=lambda p: p.as_posix())
    for folder in folders:
        relative = folder.relative_to(ROOT).as_posix()
        child_dirs = sorted(p for p in folder.iterdir() if p.is_dir())
        children = sorted((r for r in records if Path(r['path']).parent == folder.relative_to(ROOT)),
                          key=lambda r: r['title'].casefold())
        lines = [f'# {relative.replace("-", " ").title()} — Index', '',
                 '> Generated from source rows. Use the paths below from the repository root.', '',
                 f'- **Back:** `cat {folder.parent.relative_to(ROOT).as_posix()}/INDEX.md`' if folder.parent != ROOT else '- **Back:** `cat AGENTS.md`',
                 f'- **Search:** `./scripts/kb search "<term>"`', '']
        # Avoid creating a reference to a nonexisting root INDEX.md.
        if folder.parent == ROOT:
            lines[4] = '- **Back:** `cat AGENTS.md`'
        if child_dirs:
            lines.extend(['## Child routes', '', '| Folder | Command |', '|---|---|'])
            lines.extend(f'| `{p.name}/` | `cat {p.relative_to(ROOT).as_posix()}/INDEX.md` |' for p in child_dirs)
            lines.append('')
        if children:
            lines.extend([f'## Source rows ({len(children)})', '', '| Row | Direct command |', '|---|---|'])
            lines.extend(f'| {r["title"]} | `cat {r["path"]}` |' for r in children)
            lines.append('')
        outputs[folder / 'INDEX.md'] = '\n'.join(lines).rstrip() + '\n'

    sections = sorted(p for p in folders if p.parent == ROOT)
    lines = [
        '# Software Engineering Knowledge Base — Agent Entry Point', '',
        '## Operating rules', '',
        '- Work from the repository root for the commands shown below.',
        '- **Exact lookup first:** `./scripts/kb get dependency-injection` (aliases including `DI` supported).',
        '- **Discovery:** `./scripts/kb search "legacy migration"` or `rg -i "legacy" catalog.tsv aliases.tsv`.',
        '- **Category navigation:** `./scripts/kb category design-patterns`.',
        '- **Relations:** `./scripts/kb related dependency-injection`.',
        '- **Direct path:** `./scripts/kb path strangler-fig`.',
        '- **Metadata-only lookup:** `awk -F "\\t" \'$1=="strangler-fig" {print $5; exit}\' catalog.tsv`.',
        '- Read only the necessary concept files; do not bulk-load the catalog.',
        '- Source files are **seed** data, not verified classifications or an exhaustive ontology.',
        '- Never treat category placement or provisional relationship labels as independently validated facts.',
        '- Preserve source rows, record IDs, and canonical concept IDs when adding knowledge.',
        '- `cross-category-relationships/` contains source relationship records, **not canonical concepts**.',
        '- Keep `AGENTS.md` procedural. Every category and table has a generated `INDEX.md`.',
        '- Regenerate indexes: `python3 scripts/build-index.py`; verify: `python3 scripts/build-index.py --check`.',
        '', '## Category routes', '', '| Section | Command |', '|---|---|',
    ]
    lines.extend(f'| `{p.name}` | `cat {p.name}/INDEX.md` |' for p in sections)
    lines.extend(['', '## Read without a helper CLI', '',
                  '```sh',
                  'awk -F "\\t" \'$1=="strangler-fig" {print $5; exit}\' catalog.tsv',
                  'cat architectural-patterns/migration-and-modernization/strangler-fig.md',
                  'rg -in "dependency injection" catalog.tsv aliases.tsv',
                  '```', '',
                  '## Data contract', '',
                  '- `catalog.tsv`: one canonical entry per concept ID.',
                  '- `aliases.tsv`: exact, case-insensitive alternate-name resolution.',
                  '- `records.tsv`: all original source rows, including duplicates and relationship records.',
                  '- `relationships.tsv`: source-attributed **seed** edges; blank IDs mean unresolved references.',
                  '- `INDEX.md`: generated human-readable parent → child routes.',
                  '- Markdown leaf frontmatter: source of truth for identity, status, and category provenance.',
                  '',
                  '## Pattern Language skill integration', '',
                  '- The skill invokes lookup and reads targeted Markdown; avoid embedding the knowledge base in its entrypoint.',
                  '- Concept selection, comparison, and reasoning remain with the skill, not this CLI.',
                  '- Run the index builder after changing leaf files; never manually edit TSV or INDEX outputs.',
                  '',
                  '**Original source:** `Organize Software Concepts.txt`.', ''])
    outputs[ROOT_AGENTS] = '\n'.join(lines)
    return outputs, {
        'source_rows': len(records), 'canonical_concepts': len(canonical),
        'relationship_source_rows': len([r for r in records if r['path'].startswith(SEED_TABLE + '/')]),
        'aliases': len(alias_rows), 'relationships': len(rel_rows),
        'unresolved_relationships': sum(not row[4] or not row[1] for row in rel_rows),
        'duplicates': {k: [r['path'] for r in rs] for k, rs in concepts.items() if len(rs)>1},
        'alias_conflicts': {k: sorted(v) for k, v in conflicts.items() if k not in canonical},
    }


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--check', action='store_true', help='Verify generated files match source (no writes)')
    args = parser.parse_args()
    outputs, report = build()
    if args.check:
        wrong = [p.relative_to(ROOT) for p, content in outputs.items()
                 if not p.is_file() or p.read_text(encoding='utf-8') != content]
        stale = [p.relative_to(ROOT) for p in ROOT.rglob('INDEX.md') if p not in outputs]
        if wrong or stale:
            for p in wrong: print(f'OUT OF DATE: {p}', file=sys.stderr)
            for p in stale: print(f'STALE: {p}', file=sys.stderr)
            return 1
    else:
        for p, content in outputs.items():
            p.write_text(content, encoding='utf-8')
        for p in ROOT.rglob('INDEX.md'):
            if p not in outputs:
                p.unlink()
    print('Index checks passed.' if args.check else 'Indexes rebuilt.')
    print(f"{report['source_rows']} source rows; {report['canonical_concepts']} canonical concepts; "
          f"{report['aliases']} aliases; {report['relationships']} provisional relationships; "
          f"{report['unresolved_relationships']} unresolved edges.")
    if report['alias_conflicts']:
        print(f"Ambiguous aliases excluded: {report['alias_conflicts']}")
    return 0

if __name__ == '__main__':
    raise SystemExit(main())
<!-- SWE-KB:END -->

<!-- SWE-KB:FILE scripts/kb mode=755 -->
#!/usr/bin/env python3
"""Small, dependency-free command-line reader for the Markdown knowledge base.

Usage:
    ./scripts/kb get <id-or-alias>
    ./scripts/kb path <id-or-alias>
    ./scripts/kb search <terms> [--limit N]
    ./scripts/kb related <id-or-alias>
    ./scripts/kb category <relative-folder-or-unambiguous-name>
    ./scripts/kb sources <id-or-alias>
    ./scripts/kb check
"""
from __future__ import annotations

import argparse
import csv
import re
import subprocess
import sys
import unicodedata
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent


def normalize(text: str) -> str:
    value = unicodedata.normalize('NFKD', text).casefold()
    value = ''.join(c for c in value if not unicodedata.combining(c))
    return re.sub(r'[^a-z0-9]+', '-', value).strip('-')


def load(filename: str) -> list[dict[str, str]]:
    with (ROOT / filename).open(encoding='utf-8', newline='') as file:
        return list(csv.DictReader(file, delimiter='\t'))


def catalog() -> dict[str, dict[str, str]]:
    return {item['id']: item for item in load('catalog.tsv')}


def lookup(query: str, entries: dict[str, dict[str, str]]) -> dict[str, str]:
    key = normalize(query)
    if key in entries:
        return entries[key]
    aliases = {row['normalized']: row['id'] for row in load('aliases.tsv')}
    if key in aliases:
        return entries[aliases[key]]
    raise ValueError(f'Unknown concept: {query!r}. Try: kb search {query!r}')


def file_inside_root(relpath: str) -> Path:
    path = (ROOT / relpath).resolve()
    if not path.is_relative_to(ROOT):
        raise ValueError(f'Unsafe path: {relpath}')
    return path


def show(path: Path) -> None:
    sys.stdout.write(path.read_text(encoding='utf-8'))


def command_get(args: argparse.Namespace) -> None:
    item = lookup(args.query, catalog())
    show(file_inside_root(item['path']))


def command_path(args: argparse.Namespace) -> None:
    item = lookup(args.query, catalog())
    print(item['path'])


def command_search(args: argparse.Namespace) -> None:
    terms = [normalize(t) for t in re.split(r'\s+', args.query.strip()) if normalize(t)]
    if not terms:
        raise ValueError('Search query must have at least one word')
    aliases: dict[str, list[str]] = {}
    for row in load('aliases.tsv'):
        aliases.setdefault(row['id'], []).append(row['alias'])
    matches = []
    for row in catalog().values():
        body = file_inside_root(row['path']).read_text(encoding='utf-8')
        haystack = normalize(' '.join([row['id'], row['name'], row['summary'], row['path'],
                                       ' '.join(aliases.get(row['id'], [])), body]))
        if all(term in haystack for term in terms):
            matches.append(row)
    for row in sorted(matches, key=lambda r: (r['name'].casefold(), r['id']))[:args.limit]:
        print(f"{row['id']}\t{row['name']}\t{row['path']}")
    if not matches:
        print('No matches.', file=sys.stderr)


def command_related(args: argparse.Namespace) -> None:
    item = lookup(args.query, catalog())
    cid = item['id']
    matches = []
    for row in load('relationships.tsv'):
        if row['subject_id'] == cid:
            matches.append(('out', row))
        elif row['object_id'] == cid:
            matches.append(('in', row))
    if not matches:
        print(f'No source-recorded relationships for {cid}.')
        return
    print('direction\trelation\tother_concept\tresolved_id\tsource_path\tstatus')
    for direction, row in matches:
        other = row['object'] if direction == 'out' else row['subject']
        target_id = row['object_id'] if direction == 'out' else row['subject_id']
        print('\t'.join([direction, row['relation'], other, target_id or '(unresolved)',
                         row['source_path'], row['status']]))


def command_category(args: argparse.Namespace) -> None:
    value = args.category.strip().strip('/')
    folders = sorted(p for p in ROOT.rglob('INDEX.md') if 'scripts' not in p.parts)
    matches = [p for p in folders if p.parent.relative_to(ROOT).as_posix() == value]
    if not matches:
        key = normalize(value)
        matches = [p for p in folders if normalize(p.parent.name) == key]
    if not matches:
        raise ValueError(f'Unknown category: {value}. See: cat AGENTS.md')
    if len(matches) > 1:
        paths = ', '.join(p.parent.relative_to(ROOT).as_posix() for p in matches)
        raise ValueError(f'Ambiguous category: {value}. Use a full path from: {paths}')
    show(matches[0])


def command_sources(args: argparse.Namespace) -> None:
    item = lookup(args.query, catalog())
    matches = [row for row in load('records.tsv') if row['concept_id'] == item['id']]
    print('record_id\tsource_table\tpath')
    for row in matches:
        print(f"{row['record_id']}\t{row['source_table']}\t{row['path']}")


def command_check(_: argparse.Namespace) -> None:
    result = subprocess.run([sys.executable, str(ROOT/'scripts'/'build-index.py'), '--check'], check=False)
    if result.returncode:
        raise SystemExit(result.returncode)


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    sub = parser.add_subparsers(dest='command', required=True)
    handlers = {'get': command_get, 'path': command_path,
                'search': command_search, 'related': command_related,
                'category': command_category, 'sources': command_sources,
                'check': command_check}
    for name, handler in handlers.items():
        p = sub.add_parser(name)
        p.set_defaults(handler=handler)
        if name in ('get', 'path', 'related', 'sources'):
            p.add_argument('query', help='Concept ID or alias')
        elif name == 'search':
            p.add_argument('query', help='Case-insensitive AND search over paths, names, and source text')
            p.add_argument('--limit', type=int, default=30, help='Maximum results (default: 30)')
        elif name == 'category':
            p.add_argument('category', help='Relative path or unambiguous folder name')
    args = parser.parse_args()
    try:
        args.handler(args)
    except (ValueError, OSError) as err:
        print(f'kb: {err}', file=sys.stderr)
        return 2
    return 0

if __name__ == '__main__':
    raise SystemExit(main())
<!-- SWE-KB:END -->

<!-- SWE-KB:FILE software-design-principles/INDEX.md -->
# Software Design Principles — Index

> Generated from source rows. Use the paths below from the repository root.

- **Back:** `cat AGENTS.md`
- **Search:** `./scripts/kb search "<term>"`

## Child routes

| Folder | Command |
|---|---|
| `additional-object-oriented-and-modularity-principles/` | `cat software-design-principles/additional-object-oriented-and-modularity-principles/INDEX.md` |
| `distributed-systems-principles/` | `cat software-design-principles/distributed-systems-principles/INDEX.md` |
| `general-engineering-principles/` | `cat software-design-principles/general-engineering-principles/INDEX.md` |
| `solid-principles/` | `cat software-design-principles/solid-principles/INDEX.md` |
<!-- SWE-KB:END -->

<!-- SWE-KB:FILE software-design-principles/additional-object-oriented-and-modularity-principles/INDEX.md -->
# Software Design Principles/Additional Object Oriented And Modularity Principles — Index

> Generated from source rows. Use the paths below from the repository root.

- **Back:** `cat software-design-principles/INDEX.md`
- **Search:** `./scripts/kb search "<term>"`

## Source rows (15)

| Row | Direct command |
|---|---|
| Acyclic Dependencies Principle (ADP) | `cat software-design-principles/additional-object-oriented-and-modularity-principles/acyclic-dependencies-principle-adp.md` |
| Command–Query Separation (CQS) | `cat software-design-principles/additional-object-oriented-and-modularity-principles/commandquery-separation-cqs.md` |
| Common Closure Principle (CCP) | `cat software-design-principles/additional-object-oriented-and-modularity-principles/common-closure-principle-ccp.md` |
| Common Reuse Principle (CRP) | `cat software-design-principles/additional-object-oriented-and-modularity-principles/common-reuse-principle-crp.md` |
| Dependency Abstraction | `cat software-design-principles/additional-object-oriented-and-modularity-principles/dependency-abstraction.md` |
| Design by Contract (DbC) | `cat software-design-principles/additional-object-oriented-and-modularity-principles/design-by-contract-dbc.md` |
| Favor Immutability | `cat software-design-principles/additional-object-oriented-and-modularity-principles/favor-immutability.md` |
| Interface-Based Programming | `cat software-design-principles/additional-object-oriented-and-modularity-principles/interface-based-programming.md` |
| Inversion of Control (IoC) | `cat software-design-principles/additional-object-oriented-and-modularity-principles/inversion-of-control-ioc.md` |
| Program to an Interface | `cat software-design-principles/additional-object-oriented-and-modularity-principles/program-to-an-interface.md` |
| Protected Variations | `cat software-design-principles/additional-object-oriented-and-modularity-principles/protected-variations.md` |
| Reuse/Release Equivalence Principle (REP) | `cat software-design-principles/additional-object-oriented-and-modularity-principles/reuse-release-equivalence-principle-rep.md` |
| Stable Abstractions Principle (SAP) | `cat software-design-principles/additional-object-oriented-and-modularity-principles/stable-abstractions-principle-sap.md` |
| Stable Dependencies Principle (SDP) | `cat software-design-principles/additional-object-oriented-and-modularity-principles/stable-dependencies-principle-sdp.md` |
| Tell, Don't Ask | `cat software-design-principles/additional-object-oriented-and-modularity-principles/tell-don-t-ask.md` |
<!-- SWE-KB:END -->

<!-- SWE-KB:FILE software-design-principles/additional-object-oriented-and-modularity-principles/acyclic-dependencies-principle-adp.md -->
---
record_id: software-design-principles--additional-object-oriented-and-modularity-principles--acyclic-dependencies-principle-adp
concept_id: acyclic-dependencies-principle-adp
status: seed
source_table: software-design-principles/additional-object-oriented-and-modularity-principles
---

# Acyclic Dependencies Principle (ADP)

> Seed record from `Organize Software Concepts.txt`. Classification and terminology are preserved from the source table; not independently verified.

| Field | Source value |
|---|---|
| Principle | Acyclic Dependencies Principle (ADP) |
| Purpose | Prevent dependency cycles |

## Discovery extension

Add supporting references, context, tradeoffs, limitations, and validated relationships when reviewed; keep original source fields intact.
<!-- SWE-KB:END -->

<!-- SWE-KB:FILE software-design-principles/additional-object-oriented-and-modularity-principles/commandquery-separation-cqs.md -->
---
record_id: software-design-principles--additional-object-oriented-and-modularity-principles--commandquery-separation-cqs
concept_id: commandquery-separation-cqs
status: seed
source_table: software-design-principles/additional-object-oriented-and-modularity-principles
---

# Command–Query Separation (CQS)

> Seed record from `Organize Software Concepts.txt`. Classification and terminology are preserved from the source table; not independently verified.

| Field | Source value |
|---|---|
| Principle | Command–Query Separation (CQS) |
| Purpose | Distinguish state-changing commands from queries |

## Discovery extension

Add supporting references, context, tradeoffs, limitations, and validated relationships when reviewed; keep original source fields intact.
<!-- SWE-KB:END -->

<!-- SWE-KB:FILE software-design-principles/additional-object-oriented-and-modularity-principles/common-closure-principle-ccp.md -->
---
record_id: software-design-principles--additional-object-oriented-and-modularity-principles--common-closure-principle-ccp
concept_id: common-closure-principle-ccp
status: seed
source_table: software-design-principles/additional-object-oriented-and-modularity-principles
---

# Common Closure Principle (CCP)

> Seed record from `Organize Software Concepts.txt`. Classification and terminology are preserved from the source table; not independently verified.

| Field | Source value |
|---|---|
| Principle | Common Closure Principle (CCP) |
| Purpose | Group elements that change together |

## Discovery extension

Add supporting references, context, tradeoffs, limitations, and validated relationships when reviewed; keep original source fields intact.
<!-- SWE-KB:END -->

<!-- SWE-KB:FILE software-design-principles/additional-object-oriented-and-modularity-principles/common-reuse-principle-crp.md -->
---
record_id: software-design-principles--additional-object-oriented-and-modularity-principles--common-reuse-principle-crp
concept_id: common-reuse-principle-crp
status: seed
source_table: software-design-principles/additional-object-oriented-and-modularity-principles
---

# Common Reuse Principle (CRP)

> Seed record from `Organize Software Concepts.txt`. Classification and terminology are preserved from the source table; not independently verified.

| Field | Source value |
|---|---|
| Principle | Common Reuse Principle (CRP) |
| Purpose | Group elements reused together |

## Discovery extension

Add supporting references, context, tradeoffs, limitations, and validated relationships when reviewed; keep original source fields intact.
<!-- SWE-KB:END -->

<!-- SWE-KB:FILE software-design-principles/additional-object-oriented-and-modularity-principles/dependency-abstraction.md -->
---
record_id: software-design-principles--additional-object-oriented-and-modularity-principles--dependency-abstraction
concept_id: dependency-abstraction
status: seed
source_table: software-design-principles/additional-object-oriented-and-modularity-principles
---

# Dependency Abstraction

> Seed record from `Organize Software Concepts.txt`. Classification and terminology are preserved from the source table; not independently verified.

| Field | Source value |
|---|---|
| Principle | Dependency Abstraction |
| Purpose | Depend on stable contracts |

## Discovery extension

Add supporting references, context, tradeoffs, limitations, and validated relationships when reviewed; keep original source fields intact.
<!-- SWE-KB:END -->

<!-- SWE-KB:FILE software-design-principles/additional-object-oriented-and-modularity-principles/design-by-contract-dbc.md -->
---
record_id: software-design-principles--additional-object-oriented-and-modularity-principles--design-by-contract-dbc
concept_id: design-by-contract-dbc
status: seed
source_table: software-design-principles/additional-object-oriented-and-modularity-principles
---

# Design by Contract (DbC)

> Seed record from `Organize Software Concepts.txt`. Classification and terminology are preserved from the source table; not independently verified.

| Field | Source value |
|---|---|
| Principle | Design by Contract (DbC) |
| Purpose | Specify preconditions, postconditions, and invariants |

## Discovery extension

Add supporting references, context, tradeoffs, limitations, and validated relationships when reviewed; keep original source fields intact.
<!-- SWE-KB:END -->

<!-- SWE-KB:FILE software-design-principles/additional-object-oriented-and-modularity-principles/favor-immutability.md -->
---
record_id: software-design-principles--additional-object-oriented-and-modularity-principles--favor-immutability
concept_id: favor-immutability
status: seed
source_table: software-design-principles/additional-object-oriented-and-modularity-principles
---

# Favor Immutability

> Seed record from `Organize Software Concepts.txt`. Classification and terminology are preserved from the source table; not independently verified.

| Field | Source value |
|---|---|
| Principle | Favor Immutability |
| Purpose | Reduce mutable shared state |

## Discovery extension

Add supporting references, context, tradeoffs, limitations, and validated relationships when reviewed; keep original source fields intact.
<!-- SWE-KB:END -->

<!-- SWE-KB:FILE software-design-principles/additional-object-oriented-and-modularity-principles/interface-based-programming.md -->
---
record_id: software-design-principles--additional-object-oriented-and-modularity-principles--interface-based-programming
concept_id: interface-based-programming
status: seed
source_table: software-design-principles/additional-object-oriented-and-modularity-principles
---

# Interface-Based Programming

> Seed record from `Organize Software Concepts.txt`. Classification and terminology are preserved from the source table; not independently verified.

| Field | Source value |
|---|---|
| Principle | Interface-Based Programming |
| Purpose | Program against contracts |

## Discovery extension

Add supporting references, context, tradeoffs, limitations, and validated relationships when reviewed; keep original source fields intact.
<!-- SWE-KB:END -->

<!-- SWE-KB:FILE software-design-principles/additional-object-oriented-and-modularity-principles/inversion-of-control-ioc.md -->
---
record_id: software-design-principles--additional-object-oriented-and-modularity-principles--inversion-of-control-ioc
concept_id: inversion-of-control-ioc
status: seed
source_table: software-design-principles/additional-object-oriented-and-modularity-principles
---

# Inversion of Control (IoC)

> Seed record from `Organize Software Concepts.txt`. Classification and terminology are preserved from the source table; not independently verified.

| Field | Source value |
|---|---|
| Principle | Inversion of Control (IoC) |
| Purpose | Delegate control to an external mechanism |

## Discovery extension

Add supporting references, context, tradeoffs, limitations, and validated relationships when reviewed; keep original source fields intact.
<!-- SWE-KB:END -->

<!-- SWE-KB:FILE software-design-principles/additional-object-oriented-and-modularity-principles/program-to-an-interface.md -->
---
record_id: software-design-principles--additional-object-oriented-and-modularity-principles--program-to-an-interface
concept_id: program-to-an-interface
status: seed
source_table: software-design-principles/additional-object-oriented-and-modularity-principles
---

# Program to an Interface

> Seed record from `Organize Software Concepts.txt`. Classification and terminology are preserved from the source table; not independently verified.

| Field | Source value |
|---|---|
| Principle | Program to an Interface |
| Purpose | Avoid unnecessary dependence on concrete types |

## Discovery extension

Add supporting references, context, tradeoffs, limitations, and validated relationships when reviewed; keep original source fields intact.
<!-- SWE-KB:END -->

<!-- SWE-KB:FILE software-design-principles/additional-object-oriented-and-modularity-principles/protected-variations.md -->
---
record_id: software-design-principles--additional-object-oriented-and-modularity-principles--protected-variations
concept_id: protected-variations
status: seed
source_table: software-design-principles/additional-object-oriented-and-modularity-principles
---

# Protected Variations

> Seed record from `Organize Software Concepts.txt`. Classification and terminology are preserved from the source table; not independently verified.

| Field | Source value |
|---|---|
| Principle | Protected Variations |
| Purpose | Isolate elements likely to change |

## Discovery extension

Add supporting references, context, tradeoffs, limitations, and validated relationships when reviewed; keep original source fields intact.
<!-- SWE-KB:END -->

<!-- SWE-KB:FILE software-design-principles/additional-object-oriented-and-modularity-principles/reuse-release-equivalence-principle-rep.md -->
---
record_id: software-design-principles--additional-object-oriented-and-modularity-principles--reuse-release-equivalence-principle-rep
concept_id: reuse-release-equivalence-principle-rep
status: seed
source_table: software-design-principles/additional-object-oriented-and-modularity-principles
---

# Reuse/Release Equivalence Principle (REP)

> Seed record from `Organize Software Concepts.txt`. Classification and terminology are preserved from the source table; not independently verified.

| Field | Source value |
|---|---|
| Principle | Reuse/Release Equivalence Principle (REP) |
| Purpose | Align reusable units with release units |

## Discovery extension

Add supporting references, context, tradeoffs, limitations, and validated relationships when reviewed; keep original source fields intact.
<!-- SWE-KB:END -->

<!-- SWE-KB:FILE software-design-principles/additional-object-oriented-and-modularity-principles/stable-abstractions-principle-sap.md -->
---
record_id: software-design-principles--additional-object-oriented-and-modularity-principles--stable-abstractions-principle-sap
concept_id: stable-abstractions-principle-sap
status: seed
source_table: software-design-principles/additional-object-oriented-and-modularity-principles
---

# Stable Abstractions Principle (SAP)

> Seed record from `Organize Software Concepts.txt`. Classification and terminology are preserved from the source table; not independently verified.

| Field | Source value |
|---|---|
| Principle | Stable Abstractions Principle (SAP) |
| Purpose | Balance stability with abstraction |

## Discovery extension

Add supporting references, context, tradeoffs, limitations, and validated relationships when reviewed; keep original source fields intact.
<!-- SWE-KB:END -->

<!-- SWE-KB:FILE software-design-principles/additional-object-oriented-and-modularity-principles/stable-dependencies-principle-sdp.md -->
---
record_id: software-design-principles--additional-object-oriented-and-modularity-principles--stable-dependencies-principle-sdp
concept_id: stable-dependencies-principle-sdp
status: seed
source_table: software-design-principles/additional-object-oriented-and-modularity-principles
---

# Stable Dependencies Principle (SDP)

> Seed record from `Organize Software Concepts.txt`. Classification and terminology are preserved from the source table; not independently verified.

| Field | Source value |
|---|---|
| Principle | Stable Dependencies Principle (SDP) |
| Purpose | Depend toward more stable components |

## Discovery extension

Add supporting references, context, tradeoffs, limitations, and validated relationships when reviewed; keep original source fields intact.
<!-- SWE-KB:END -->

<!-- SWE-KB:FILE software-design-principles/additional-object-oriented-and-modularity-principles/tell-don-t-ask.md -->
---
record_id: software-design-principles--additional-object-oriented-and-modularity-principles--tell-don-t-ask
concept_id: tell-don-t-ask
status: seed
source_table: software-design-principles/additional-object-oriented-and-modularity-principles
---

# Tell, Don't Ask

> Seed record from `Organize Software Concepts.txt`. Classification and terminology are preserved from the source table; not independently verified.

| Field | Source value |
|---|---|
| Principle | Tell, Don't Ask |
| Purpose | Put behavior near the data it operates on |

## Discovery extension

Add supporting references, context, tradeoffs, limitations, and validated relationships when reviewed; keep original source fields intact.
<!-- SWE-KB:END -->

<!-- SWE-KB:FILE software-design-principles/distributed-systems-principles/INDEX.md -->
# Software Design Principles/Distributed Systems Principles — Index

> Generated from source rows. Use the paths below from the repository root.

- **Back:** `cat software-design-principles/INDEX.md`
- **Search:** `./scripts/kb search "<term>"`

## Source rows (13)

| Row | Direct command |
|---|---|
| At-Least-Once Delivery | `cat software-design-principles/distributed-systems-principles/at-least-once-delivery.md` |
| At-Most-Once Delivery | `cat software-design-principles/distributed-systems-principles/at-most-once-delivery.md` |
| Backpressure | `cat software-design-principles/distributed-systems-principles/backpressure.md` |
| Defense in Depth | `cat software-design-principles/distributed-systems-principles/defense-in-depth.md` |
| End-to-End Principle | `cat software-design-principles/distributed-systems-principles/end-to-end-principle.md` |
| Eventual Consistency | `cat software-design-principles/distributed-systems-principles/eventual-consistency.md` |
| Fault Isolation | `cat software-design-principles/distributed-systems-principles/fault-isolation.md` |
| Graceful Degradation | `cat software-design-principles/distributed-systems-principles/graceful-degradation.md` |
| Idempotency | `cat software-design-principles/distributed-systems-principles/idempotency.md` |
| Retry with Backoff | `cat software-design-principles/distributed-systems-principles/retry-with-backoff.md` |
| Strong Consistency | `cat software-design-principles/distributed-systems-principles/strong-consistency.md` |
| Timeout Budgeting | `cat software-design-principles/distributed-systems-principles/timeout-budgeting.md` |
| Zero Trust | `cat software-design-principles/distributed-systems-principles/zero-trust.md` |
<!-- SWE-KB:END -->

<!-- SWE-KB:FILE software-design-principles/distributed-systems-principles/at-least-once-delivery.md -->
---
record_id: software-design-principles--distributed-systems-principles--at-least-once-delivery
concept_id: at-least-once-delivery
status: seed
source_table: software-design-principles/distributed-systems-principles
---

# At-Least-Once Delivery

> Seed record from `Organize Software Concepts.txt`. Classification and terminology are preserved from the source table; not independently verified.

| Field | Source value |
|---|---|
| Principle | At-Least-Once Delivery |
| Purpose | Ensure delivery with possible duplicates |

## Discovery extension

Add supporting references, context, tradeoffs, limitations, and validated relationships when reviewed; keep original source fields intact.
<!-- SWE-KB:END -->

<!-- SWE-KB:FILE software-design-principles/distributed-systems-principles/at-most-once-delivery.md -->
---
record_id: software-design-principles--distributed-systems-principles--at-most-once-delivery
concept_id: at-most-once-delivery
status: seed
source_table: software-design-principles/distributed-systems-principles
---

# At-Most-Once Delivery

> Seed record from `Organize Software Concepts.txt`. Classification and terminology are preserved from the source table; not independently verified.

| Field | Source value |
|---|---|
| Principle | At-Most-Once Delivery |
| Purpose | Avoid duplicate delivery with possible loss |

## Discovery extension

Add supporting references, context, tradeoffs, limitations, and validated relationships when reviewed; keep original source fields intact.
<!-- SWE-KB:END -->

<!-- SWE-KB:FILE software-design-principles/distributed-systems-principles/backpressure.md -->
---
record_id: software-design-principles--distributed-systems-principles--backpressure
concept_id: backpressure
status: seed
source_table: software-design-principles/distributed-systems-principles
---

# Backpressure

> Seed record from `Organize Software Concepts.txt`. Classification and terminology are preserved from the source table; not independently verified.

| Field | Source value |
|---|---|
| Principle | Backpressure |
| Purpose | Prevent producers from overwhelming consumers |

## Discovery extension

Add supporting references, context, tradeoffs, limitations, and validated relationships when reviewed; keep original source fields intact.
<!-- SWE-KB:END -->

<!-- SWE-KB:FILE software-design-principles/distributed-systems-principles/defense-in-depth.md -->
---
record_id: software-design-principles--distributed-systems-principles--defense-in-depth
concept_id: defense-in-depth
status: seed
source_table: software-design-principles/distributed-systems-principles
---

# Defense in Depth

> Seed record from `Organize Software Concepts.txt`. Classification and terminology are preserved from the source table; not independently verified.

| Field | Source value |
|---|---|
| Principle | Defense in Depth |
| Purpose | Apply multiple independent security controls |

## Discovery extension

Add supporting references, context, tradeoffs, limitations, and validated relationships when reviewed; keep original source fields intact.
<!-- SWE-KB:END -->

<!-- SWE-KB:FILE software-design-principles/distributed-systems-principles/end-to-end-principle.md -->
---
record_id: software-design-principles--distributed-systems-principles--end-to-end-principle
concept_id: end-to-end-principle
status: seed
source_table: software-design-principles/distributed-systems-principles
---

# End-to-End Principle

> Seed record from `Organize Software Concepts.txt`. Classification and terminology are preserved from the source table; not independently verified.

| Field | Source value |
|---|---|
| Principle | End-to-End Principle |
| Purpose | Place certain correctness guarantees at endpoints |

## Discovery extension

Add supporting references, context, tradeoffs, limitations, and validated relationships when reviewed; keep original source fields intact.
<!-- SWE-KB:END -->

<!-- SWE-KB:FILE software-design-principles/distributed-systems-principles/eventual-consistency.md -->
---
record_id: software-design-principles--distributed-systems-principles--eventual-consistency
concept_id: eventual-consistency
status: seed
source_table: software-design-principles/distributed-systems-principles
---

# Eventual Consistency

> Seed record from `Organize Software Concepts.txt`. Classification and terminology are preserved from the source table; not independently verified.

| Field | Source value |
|---|---|
| Principle | Eventual Consistency |
| Purpose | Allow replicas to converge asynchronously |

## Discovery extension

Add supporting references, context, tradeoffs, limitations, and validated relationships when reviewed; keep original source fields intact.
<!-- SWE-KB:END -->

<!-- SWE-KB:FILE software-design-principles/distributed-systems-principles/fault-isolation.md -->
---
record_id: software-design-principles--distributed-systems-principles--fault-isolation
concept_id: fault-isolation
status: seed
source_table: software-design-principles/distributed-systems-principles
---

# Fault Isolation

> Seed record from `Organize Software Concepts.txt`. Classification and terminology are preserved from the source table; not independently verified.

| Field | Source value |
|---|---|
| Principle | Fault Isolation |
| Purpose | Prevent failures from propagating |

## Discovery extension

Add supporting references, context, tradeoffs, limitations, and validated relationships when reviewed; keep original source fields intact.
<!-- SWE-KB:END -->

<!-- SWE-KB:FILE software-design-principles/distributed-systems-principles/graceful-degradation.md -->
---
record_id: software-design-principles--distributed-systems-principles--graceful-degradation
concept_id: graceful-degradation
status: seed
source_table: software-design-principles/distributed-systems-principles
---

# Graceful Degradation

> Seed record from `Organize Software Concepts.txt`. Classification and terminology are preserved from the source table; not independently verified.

| Field | Source value |
|---|---|
| Principle | Graceful Degradation |
| Purpose | Preserve reduced functionality under failure |

## Discovery extension

Add supporting references, context, tradeoffs, limitations, and validated relationships when reviewed; keep original source fields intact.
<!-- SWE-KB:END -->

<!-- SWE-KB:FILE software-design-principles/distributed-systems-principles/idempotency.md -->
---
record_id: software-design-principles--distributed-systems-principles--idempotency
concept_id: idempotency
status: seed
source_table: software-design-principles/distributed-systems-principles
---

# Idempotency

> Seed record from `Organize Software Concepts.txt`. Classification and terminology are preserved from the source table; not independently verified.

| Field | Source value |
|---|---|
| Principle | Idempotency |
| Purpose | Make repeated operations safe |

## Discovery extension

Add supporting references, context, tradeoffs, limitations, and validated relationships when reviewed; keep original source fields intact.
<!-- SWE-KB:END -->

<!-- SWE-KB:FILE software-design-principles/distributed-systems-principles/retry-with-backoff.md -->
---
record_id: software-design-principles--distributed-systems-principles--retry-with-backoff
concept_id: retry-with-backoff
status: seed
source_table: software-design-principles/distributed-systems-principles
---

# Retry with Backoff

> Seed record from `Organize Software Concepts.txt`. Classification and terminology are preserved from the source table; not independently verified.

| Field | Source value |
|---|---|
| Principle | Retry with Backoff |
| Purpose | Recover from transient failures |

## Discovery extension

Add supporting references, context, tradeoffs, limitations, and validated relationships when reviewed; keep original source fields intact.
<!-- SWE-KB:END -->

<!-- SWE-KB:FILE software-design-principles/distributed-systems-principles/strong-consistency.md -->
---
record_id: software-design-principles--distributed-systems-principles--strong-consistency
concept_id: strong-consistency
status: seed
source_table: software-design-principles/distributed-systems-principles
---

# Strong Consistency

> Seed record from `Organize Software Concepts.txt`. Classification and terminology are preserved from the source table; not independently verified.

| Field | Source value |
|---|---|
| Principle | Strong Consistency |
| Purpose | Enforce defined consistency guarantees |

## Discovery extension

Add supporting references, context, tradeoffs, limitations, and validated relationships when reviewed; keep original source fields intact.
<!-- SWE-KB:END -->

<!-- SWE-KB:FILE software-design-principles/distributed-systems-principles/timeout-budgeting.md -->
---
record_id: software-design-principles--distributed-systems-principles--timeout-budgeting
concept_id: timeout-budgeting
status: seed
source_table: software-design-principles/distributed-systems-principles
---

# Timeout Budgeting

> Seed record from `Organize Software Concepts.txt`. Classification and terminology are preserved from the source table; not independently verified.

| Field | Source value |
|---|---|
| Principle | Timeout Budgeting |
| Purpose | Bound waiting and resource consumption |

## Discovery extension

Add supporting references, context, tradeoffs, limitations, and validated relationships when reviewed; keep original source fields intact.
<!-- SWE-KB:END -->

<!-- SWE-KB:FILE software-design-principles/distributed-systems-principles/zero-trust.md -->
---
record_id: software-design-principles--distributed-systems-principles--zero-trust
concept_id: zero-trust
status: seed
source_table: software-design-principles/distributed-systems-principles
---

# Zero Trust

> Seed record from `Organize Software Concepts.txt`. Classification and terminology are preserved from the source table; not independently verified.

| Field | Source value |
|---|---|
| Principle | Zero Trust |
| Purpose | Verify access rather than trusting network location |

## Discovery extension

Add supporting references, context, tradeoffs, limitations, and validated relationships when reviewed; keep original source fields intact.
<!-- SWE-KB:END -->

<!-- SWE-KB:FILE software-design-principles/general-engineering-principles/INDEX.md -->
# Software Design Principles/General Engineering Principles — Index

> Generated from source rows. Use the paths below from the repository root.

- **Back:** `cat software-design-principles/INDEX.md`
- **Search:** `./scripts/kb search "<term>"`

## Source rows (20)

| Row | Direct command |
|---|---|
| Composition over Inheritance | `cat software-design-principles/general-engineering-principles/composition-over-inheritance.md` |
| Convention over Configuration | `cat software-design-principles/general-engineering-principles/convention-over-configuration.md` |
| Defensive Programming | `cat software-design-principles/general-engineering-principles/defensive-programming.md` |
| DRY | `cat software-design-principles/general-engineering-principles/dry.md` |
| Encapsulation | `cat software-design-principles/general-engineering-principles/encapsulation.md` |
| Explicit over Implicit | `cat software-design-principles/general-engineering-principles/explicit-over-implicit.md` |
| Fail Fast | `cat software-design-principles/general-engineering-principles/fail-fast.md` |
| High Cohesion | `cat software-design-principles/general-engineering-principles/high-cohesion.md` |
| Information Hiding | `cat software-design-principles/general-engineering-principles/information-hiding.md` |
| KISS | `cat software-design-principles/general-engineering-principles/kiss.md` |
| Least Astonishment | `cat software-design-principles/general-engineering-principles/least-astonishment.md` |
| Low Coupling | `cat software-design-principles/general-engineering-principles/low-coupling.md` |
| Orthogonality | `cat software-design-principles/general-engineering-principles/orthogonality.md` |
| Principle of Least Authority | `cat software-design-principles/general-engineering-principles/principle-of-least-authority.md` |
| Principle of Least Knowledge / Law of Demeter | `cat software-design-principles/general-engineering-principles/principle-of-least-knowledge-law-of-demeter.md` |
| Principle of Least Privilege | `cat software-design-principles/general-engineering-principles/principle-of-least-privilege.md` |
| Principle of Reversibility | `cat software-design-principles/general-engineering-principles/principle-of-reversibility.md` |
| Separation of Concerns (SoC) | `cat software-design-principles/general-engineering-principles/separation-of-concerns-soc.md` |
| Single Source of Truth | `cat software-design-principles/general-engineering-principles/single-source-of-truth.md` |
| YAGNI | `cat software-design-principles/general-engineering-principles/yagni.md` |
<!-- SWE-KB:END -->

<!-- SWE-KB:FILE software-design-principles/general-engineering-principles/composition-over-inheritance.md -->
---
record_id: software-design-principles--general-engineering-principles--composition-over-inheritance
concept_id: composition-over-inheritance
status: seed
source_table: software-design-principles/general-engineering-principles
---

# Composition over Inheritance

> Seed record from `Organize Software Concepts.txt`. Classification and terminology are preserved from the source table; not independently verified.

| Field | Source value |
|---|---|
| Principle | Composition over Inheritance |
| Meaning | Prefer assembling behavior to inheritance hierarchies |
| Primary concern | Flexibility |

## Discovery extension

Add supporting references, context, tradeoffs, limitations, and validated relationships when reviewed; keep original source fields intact.
<!-- SWE-KB:END -->

<!-- SWE-KB:FILE software-design-principles/general-engineering-principles/convention-over-configuration.md -->
---
record_id: software-design-principles--general-engineering-principles--convention-over-configuration
concept_id: convention-over-configuration
status: seed
source_table: software-design-principles/general-engineering-principles
---

# Convention over Configuration

> Seed record from `Organize Software Concepts.txt`. Classification and terminology are preserved from the source table; not independently verified.

| Field | Source value |
|---|---|
| Principle | Convention over Configuration |
| Meaning | Use defaults to reduce explicit setup |
| Primary concern | Developer experience |

## Discovery extension

Add supporting references, context, tradeoffs, limitations, and validated relationships when reviewed; keep original source fields intact.
<!-- SWE-KB:END -->

<!-- SWE-KB:FILE software-design-principles/general-engineering-principles/defensive-programming.md -->
---
record_id: software-design-principles--general-engineering-principles--defensive-programming
concept_id: defensive-programming
status: seed
source_table: software-design-principles/general-engineering-principles
---

# Defensive Programming

> Seed record from `Organize Software Concepts.txt`. Classification and terminology are preserved from the source table; not independently verified.

| Field | Source value |
|---|---|
| Principle | Defensive Programming |
| Meaning | Guard against invalid inputs and states |
| Primary concern | Robustness |

## Discovery extension

Add supporting references, context, tradeoffs, limitations, and validated relationships when reviewed; keep original source fields intact.
<!-- SWE-KB:END -->

<!-- SWE-KB:FILE software-design-principles/general-engineering-principles/dry.md -->
---
record_id: software-design-principles--general-engineering-principles--dry
concept_id: dry
status: seed
source_table: software-design-principles/general-engineering-principles
---

# DRY

> Seed record from `Organize Software Concepts.txt`. Classification and terminology are preserved from the source table; not independently verified.

| Field | Source value |
|---|---|
| Principle | DRY |
| Meaning | Don't Repeat Yourself |
| Primary concern | Knowledge duplication |

## Discovery extension

Add supporting references, context, tradeoffs, limitations, and validated relationships when reviewed; keep original source fields intact.
<!-- SWE-KB:END -->

<!-- SWE-KB:FILE software-design-principles/general-engineering-principles/encapsulation.md -->
---
record_id: software-design-principles--general-engineering-principles--encapsulation
concept_id: encapsulation
status: seed
source_table: software-design-principles/general-engineering-principles
---

# Encapsulation

> Seed record from `Organize Software Concepts.txt`. Classification and terminology are preserved from the source table; not independently verified.

| Field | Source value |
|---|---|
| Principle | Encapsulation |
| Meaning | Protect state and behavior behind boundaries |
| Primary concern | Maintainability |

## Discovery extension

Add supporting references, context, tradeoffs, limitations, and validated relationships when reviewed; keep original source fields intact.
<!-- SWE-KB:END -->

<!-- SWE-KB:FILE software-design-principles/general-engineering-principles/explicit-over-implicit.md -->
---
record_id: software-design-principles--general-engineering-principles--explicit-over-implicit
concept_id: explicit-over-implicit
status: seed
source_table: software-design-principles/general-engineering-principles
---

# Explicit over Implicit

> Seed record from `Organize Software Concepts.txt`. Classification and terminology are preserved from the source table; not independently verified.

| Field | Source value |
|---|---|
| Principle | Explicit over Implicit |
| Meaning | Make behavior and dependencies visible |
| Primary concern | Understandability |

## Discovery extension

Add supporting references, context, tradeoffs, limitations, and validated relationships when reviewed; keep original source fields intact.
<!-- SWE-KB:END -->

<!-- SWE-KB:FILE software-design-principles/general-engineering-principles/fail-fast.md -->
---
record_id: software-design-principles--general-engineering-principles--fail-fast
concept_id: fail-fast
status: seed
source_table: software-design-principles/general-engineering-principles
---

# Fail Fast

> Seed record from `Organize Software Concepts.txt`. Classification and terminology are preserved from the source table; not independently verified.

| Field | Source value |
|---|---|
| Principle | Fail Fast |
| Meaning | Detect invalid states early |
| Primary concern | Reliability |

## Discovery extension

Add supporting references, context, tradeoffs, limitations, and validated relationships when reviewed; keep original source fields intact.
<!-- SWE-KB:END -->

<!-- SWE-KB:FILE software-design-principles/general-engineering-principles/high-cohesion.md -->
---
record_id: software-design-principles--general-engineering-principles--high-cohesion
concept_id: high-cohesion
status: seed
source_table: software-design-principles/general-engineering-principles
---

# High Cohesion

> Seed record from `Organize Software Concepts.txt`. Classification and terminology are preserved from the source table; not independently verified.

| Field | Source value |
|---|---|
| Principle | High Cohesion |
| Meaning | Keep closely related responsibilities together |
| Primary concern | Module quality |

## Discovery extension

Add supporting references, context, tradeoffs, limitations, and validated relationships when reviewed; keep original source fields intact.
<!-- SWE-KB:END -->

<!-- SWE-KB:FILE software-design-principles/general-engineering-principles/information-hiding.md -->
---
record_id: software-design-principles--general-engineering-principles--information-hiding
concept_id: information-hiding
status: seed
source_table: software-design-principles/general-engineering-principles
---

# Information Hiding

> Seed record from `Organize Software Concepts.txt`. Classification and terminology are preserved from the source table; not independently verified.

| Field | Source value |
|---|---|
| Principle | Information Hiding |
| Meaning | Hide implementation decisions behind interfaces |
| Primary concern | Encapsulation |

## Discovery extension

Add supporting references, context, tradeoffs, limitations, and validated relationships when reviewed; keep original source fields intact.
<!-- SWE-KB:END -->

<!-- SWE-KB:FILE software-design-principles/general-engineering-principles/kiss.md -->
---
record_id: software-design-principles--general-engineering-principles--kiss
concept_id: kiss
status: seed
source_table: software-design-principles/general-engineering-principles
---

# KISS

> Seed record from `Organize Software Concepts.txt`. Classification and terminology are preserved from the source table; not independently verified.

| Field | Source value |
|---|---|
| Principle | KISS |
| Meaning | Keep It Simple |
| Primary concern | Complexity |

## Discovery extension

Add supporting references, context, tradeoffs, limitations, and validated relationships when reviewed; keep original source fields intact.
<!-- SWE-KB:END -->

<!-- SWE-KB:FILE software-design-principles/general-engineering-principles/least-astonishment.md -->
---
record_id: software-design-principles--general-engineering-principles--least-astonishment
concept_id: least-astonishment
status: seed
source_table: software-design-principles/general-engineering-principles
---

# Least Astonishment

> Seed record from `Organize Software Concepts.txt`. Classification and terminology are preserved from the source table; not independently verified.

| Field | Source value |
|---|---|
| Principle | Least Astonishment |
| Meaning | Behavior should match reasonable expectations |
| Primary concern | Predictability |

## Discovery extension

Add supporting references, context, tradeoffs, limitations, and validated relationships when reviewed; keep original source fields intact.
<!-- SWE-KB:END -->

<!-- SWE-KB:FILE software-design-principles/general-engineering-principles/low-coupling.md -->
---
record_id: software-design-principles--general-engineering-principles--low-coupling
concept_id: low-coupling
status: seed
source_table: software-design-principles/general-engineering-principles
---

# Low Coupling

> Seed record from `Organize Software Concepts.txt`. Classification and terminology are preserved from the source table; not independently verified.

| Field | Source value |
|---|---|
| Principle | Low Coupling |
| Meaning | Minimize dependencies between components |
| Primary concern | Change isolation |

## Discovery extension

Add supporting references, context, tradeoffs, limitations, and validated relationships when reviewed; keep original source fields intact.
<!-- SWE-KB:END -->

<!-- SWE-KB:FILE software-design-principles/general-engineering-principles/orthogonality.md -->
---
record_id: software-design-principles--general-engineering-principles--orthogonality
concept_id: orthogonality
status: seed
source_table: software-design-principles/general-engineering-principles
---

# Orthogonality

> Seed record from `Organize Software Concepts.txt`. Classification and terminology are preserved from the source table; not independently verified.

| Field | Source value |
|---|---|
| Principle | Orthogonality |
| Meaning | Keep independent concerns independently changeable |
| Primary concern | Maintainability |

## Discovery extension

Add supporting references, context, tradeoffs, limitations, and validated relationships when reviewed; keep original source fields intact.
<!-- SWE-KB:END -->

<!-- SWE-KB:FILE software-design-principles/general-engineering-principles/principle-of-least-authority.md -->
---
record_id: software-design-principles--general-engineering-principles--principle-of-least-authority
concept_id: principle-of-least-authority
status: seed
source_table: software-design-principles/general-engineering-principles
---

# Principle of Least Authority

> Seed record from `Organize Software Concepts.txt`. Classification and terminology are preserved from the source table; not independently verified.

| Field | Source value |
|---|---|
| Principle | Principle of Least Authority |
| Meaning | Minimize accessible capabilities |
| Primary concern | Security |

## Discovery extension

Add supporting references, context, tradeoffs, limitations, and validated relationships when reviewed; keep original source fields intact.
<!-- SWE-KB:END -->

<!-- SWE-KB:FILE software-design-principles/general-engineering-principles/principle-of-least-knowledge-law-of-demeter.md -->
---
record_id: software-design-principles--general-engineering-principles--principle-of-least-knowledge-law-of-demeter
concept_id: principle-of-least-knowledge-law-of-demeter
status: seed
source_table: software-design-principles/general-engineering-principles
---

# Principle of Least Knowledge / Law of Demeter

> Seed record from `Organize Software Concepts.txt`. Classification and terminology are preserved from the source table; not independently verified.

| Field | Source value |
|---|---|
| Principle | Principle of Least Knowledge / Law of Demeter |
| Meaning | Minimize knowledge of other objects' internals |
| Primary concern | Coupling |

## Discovery extension

Add supporting references, context, tradeoffs, limitations, and validated relationships when reviewed; keep original source fields intact.
<!-- SWE-KB:END -->

<!-- SWE-KB:FILE software-design-principles/general-engineering-principles/principle-of-least-privilege.md -->
---
record_id: software-design-principles--general-engineering-principles--principle-of-least-privilege
concept_id: principle-of-least-privilege
status: seed
source_table: software-design-principles/general-engineering-principles
---

# Principle of Least Privilege

> Seed record from `Organize Software Concepts.txt`. Classification and terminology are preserved from the source table; not independently verified.

| Field | Source value |
|---|---|
| Principle | Principle of Least Privilege |
| Meaning | Grant only necessary permissions |
| Primary concern | Security |

## Discovery extension

Add supporting references, context, tradeoffs, limitations, and validated relationships when reviewed; keep original source fields intact.
<!-- SWE-KB:END -->

<!-- SWE-KB:FILE software-design-principles/general-engineering-principles/principle-of-reversibility.md -->
---
record_id: software-design-principles--general-engineering-principles--principle-of-reversibility
concept_id: principle-of-reversibility
status: seed
source_table: software-design-principles/general-engineering-principles
---

# Principle of Reversibility

> Seed record from `Organize Software Concepts.txt`. Classification and terminology are preserved from the source table; not independently verified.

| Field | Source value |
|---|---|
| Principle | Principle of Reversibility |
| Meaning | Favor decisions that are inexpensive to undo |
| Primary concern | Evolution |

## Discovery extension

Add supporting references, context, tradeoffs, limitations, and validated relationships when reviewed; keep original source fields intact.
<!-- SWE-KB:END -->

<!-- SWE-KB:FILE software-design-principles/general-engineering-principles/separation-of-concerns-soc.md -->
---
record_id: software-design-principles--general-engineering-principles--separation-of-concerns-soc
concept_id: separation-of-concerns-soc
status: seed
source_table: software-design-principles/general-engineering-principles
---

# Separation of Concerns (SoC)

> Seed record from `Organize Software Concepts.txt`. Classification and terminology are preserved from the source table; not independently verified.

| Field | Source value |
|---|---|
| Principle | Separation of Concerns (SoC) |
| Meaning | Isolate distinct responsibilities |
| Primary concern | Modularity |

## Discovery extension

Add supporting references, context, tradeoffs, limitations, and validated relationships when reviewed; keep original source fields intact.
<!-- SWE-KB:END -->

<!-- SWE-KB:FILE software-design-principles/general-engineering-principles/single-source-of-truth.md -->
---
record_id: software-design-principles--general-engineering-principles--single-source-of-truth
concept_id: single-source-of-truth
status: seed
source_table: software-design-principles/general-engineering-principles
---

# Single Source of Truth

> Seed record from `Organize Software Concepts.txt`. Classification and terminology are preserved from the source table; not independently verified.

| Field | Source value |
|---|---|
| Principle | Single Source of Truth |
| Meaning | Establish one authoritative source for each fact |
| Primary concern | Consistency |

## Discovery extension

Add supporting references, context, tradeoffs, limitations, and validated relationships when reviewed; keep original source fields intact.
<!-- SWE-KB:END -->

<!-- SWE-KB:FILE software-design-principles/general-engineering-principles/yagni.md -->
---
record_id: software-design-principles--general-engineering-principles--yagni
concept_id: yagni
status: seed
source_table: software-design-principles/general-engineering-principles
---

# YAGNI

> Seed record from `Organize Software Concepts.txt`. Classification and terminology are preserved from the source table; not independently verified.

| Field | Source value |
|---|---|
| Principle | YAGNI |
| Meaning | You Aren't Gonna Need It |
| Primary concern | Premature functionality |

## Discovery extension

Add supporting references, context, tradeoffs, limitations, and validated relationships when reviewed; keep original source fields intact.
<!-- SWE-KB:END -->

<!-- SWE-KB:FILE software-design-principles/solid-principles/INDEX.md -->
# Software Design Principles/Solid Principles — Index

> Generated from source rows. Use the paths below from the repository root.

- **Back:** `cat software-design-principles/INDEX.md`
- **Search:** `./scripts/kb search "<term>"`

## Source rows (5)

| Row | Direct command |
|---|---|
| D — Dependency Inversion (DIP) | `cat software-design-principles/solid-principles/d-dependency-inversion-dip.md` |
| I — Interface Segregation (ISP) | `cat software-design-principles/solid-principles/i-interface-segregation-isp.md` |
| L — Liskov Substitution (LSP) | `cat software-design-principles/solid-principles/l-liskov-substitution-lsp.md` |
| O — Open/Closed (OCP) | `cat software-design-principles/solid-principles/o-open-closed-ocp.md` |
| S — Single Responsibility (SRP) | `cat software-design-principles/solid-principles/s-single-responsibility-srp.md` |
<!-- SWE-KB:END -->

<!-- SWE-KB:FILE software-design-principles/solid-principles/d-dependency-inversion-dip.md -->
---
record_id: software-design-principles--solid-principles--d-dependency-inversion-dip
concept_id: d-dependency-inversion-dip
status: seed
source_table: software-design-principles/solid-principles
---

# D — Dependency Inversion (DIP)

> Seed record from `Organize Software Concepts.txt`. Classification and terminology are preserved from the source table; not independently verified.

| Field | Source value |
|---|---|
| Principle | D — Dependency Inversion (DIP) |
| Definition | High-level policy should not depend directly on low-level implementation details |
| Primary benefit | Decoupling |

## Discovery extension

Add supporting references, context, tradeoffs, limitations, and validated relationships when reviewed; keep original source fields intact.
<!-- SWE-KB:END -->

<!-- SWE-KB:FILE software-design-principles/solid-principles/i-interface-segregation-isp.md -->
---
record_id: software-design-principles--solid-principles--i-interface-segregation-isp
concept_id: i-interface-segregation-isp
status: seed
source_table: software-design-principles/solid-principles
---

# I — Interface Segregation (ISP)

> Seed record from `Organize Software Concepts.txt`. Classification and terminology are preserved from the source table; not independently verified.

| Field | Source value |
|---|---|
| Principle | I — Interface Segregation (ISP) |
| Definition | Avoid forcing consumers to depend on unused operations |
| Primary benefit | Interface quality |

## Discovery extension

Add supporting references, context, tradeoffs, limitations, and validated relationships when reviewed; keep original source fields intact.
<!-- SWE-KB:END -->

<!-- SWE-KB:FILE software-design-principles/solid-principles/l-liskov-substitution-lsp.md -->
---
record_id: software-design-principles--solid-principles--l-liskov-substitution-lsp
concept_id: l-liskov-substitution-lsp
status: seed
source_table: software-design-principles/solid-principles
---

# L — Liskov Substitution (LSP)

> Seed record from `Organize Software Concepts.txt`. Classification and terminology are preserved from the source table; not independently verified.

| Field | Source value |
|---|---|
| Principle | L — Liskov Substitution (LSP) |
| Definition | Subtypes must preserve their base type's behavioral contracts |
| Primary benefit | Substitutability |

## Discovery extension

Add supporting references, context, tradeoffs, limitations, and validated relationships when reviewed; keep original source fields intact.
<!-- SWE-KB:END -->

<!-- SWE-KB:FILE software-design-principles/solid-principles/o-open-closed-ocp.md -->
---
record_id: software-design-principles--solid-principles--o-open-closed-ocp
concept_id: o-open-closed-ocp
status: seed
source_table: software-design-principles/solid-principles
---

# O — Open/Closed (OCP)

> Seed record from `Organize Software Concepts.txt`. Classification and terminology are preserved from the source table; not independently verified.

| Field | Source value |
|---|---|
| Principle | O — Open/Closed (OCP) |
| Definition | Extend behavior without modifying stable existing code |
| Primary benefit | Extensibility |

## Discovery extension

Add supporting references, context, tradeoffs, limitations, and validated relationships when reviewed; keep original source fields intact.
<!-- SWE-KB:END -->

<!-- SWE-KB:FILE software-design-principles/solid-principles/s-single-responsibility-srp.md -->
---
record_id: software-design-principles--solid-principles--s-single-responsibility-srp
concept_id: s-single-responsibility-srp
status: seed
source_table: software-design-principles/solid-principles
---

# S — Single Responsibility (SRP)

> Seed record from `Organize Software Concepts.txt`. Classification and terminology are preserved from the source table; not independently verified.

| Field | Source value |
|---|---|
| Principle | S — Single Responsibility (SRP) |
| Definition | A module should have one reason to change |
| Primary benefit | Cohesion |

## Discovery extension

Add supporting references, context, tradeoffs, limitations, and validated relationships when reviewed; keep original source fields intact.
<!-- SWE-KB:END -->

<!-- SWE-KB:FILE tests/test_kb.py -->
"""Smoke and consistency tests; only Python standard library required."""
import csv
import subprocess
import sys
import unittest
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
CLI = ROOT/'scripts'/'kb'
GEN = ROOT/'scripts'/'build-index.py'


def rows(name):
    with (ROOT/name).open(encoding='utf-8', newline='') as f:
        return list(csv.DictReader(f, delimiter='\t'))


def run(*args, cwd=None):
    return subprocess.run([sys.executable, str(CLI), *args], cwd=cwd or ROOT,
                          capture_output=True, text=True)


class KnowledgeBaseTests(unittest.TestCase):
    def test_seed_counts_and_preservation(self):
        records = rows('records.tsv')
        catalog = rows('catalog.tsv')
        self.assertEqual(len(records), 219)
        self.assertEqual(len(catalog), 204)
        self.assertEqual(sum(r['record_kind'] == 'relationship-source' for r in records), 14)
        self.assertEqual(len({r['record_id'] for r in records}), len(records))
        self.assertEqual(len({r['id'] for r in catalog}), len(catalog))
        for r in records:
            self.assertTrue((ROOT/r['path']).is_file(), r['path'])
        for r in catalog:
            self.assertTrue((ROOT/r['path']).is_file(), r['path'])

    def test_generated_files_reproducible(self):
        p = subprocess.run([sys.executable, str(GEN), '--check'], cwd=ROOT,
                           capture_output=True, text=True)
        self.assertEqual(p.returncode, 0, p.stdout+p.stderr)

    def test_all_parents_have_index_without_nested_agents(self):
        parents = {Path(r['path']).parent for r in rows('records.tsv')}
        for child in list(parents):
            parent = child.parent
            while parent != Path('.'):
                parents.add(parent)
                parent = parent.parent
        for folder in parents:
            self.assertTrue((ROOT/folder/'INDEX.md').is_file(), str(folder))
        self.assertEqual(sorted(ROOT.rglob('AGENTS.md')), [ROOT/'AGENTS.md'])

    def test_exact_lookup_aliases_and_paths(self):
        aliases = {
            'DI': 'design-patterns/additional-application-design-patterns/dependency-injection-di.md',
            'dependency-injection': 'design-patterns/additional-application-design-patterns/dependency-injection-di.md',
            'DIP': 'software-design-principles/solid-principles/d-dependency-inversion-dip.md',
            'IoC': 'software-design-principles/additional-object-oriented-and-modularity-principles/inversion-of-control-ioc.md',
            'strangler fig': 'architectural-patterns/migration-and-modernization/strangler-fig.md',
        }
        for alias, path in aliases.items():
            with self.subTest(alias=alias):
                out = run('path', alias)
                self.assertEqual(out.returncode, 0, out.stderr)
                self.assertEqual(out.stdout.strip(), path)
        self.assertIn('# Dependency Injection (DI)', run('get', 'DI').stdout)

    def test_search_and_category(self):
        result = run('search', 'legacy migration')
        self.assertEqual(result.returncode, 0, result.stderr)
        self.assertIn('strangler-fig', result.stdout)
        result = run('category', 'design-patterns')
        self.assertEqual(result.returncode, 0, result.stderr)
        self.assertIn('creational-gang-of-four/INDEX.md', result.stdout)
        result = run('category', 'additional-application-design-patterns')
        self.assertEqual(result.returncode, 0, result.stderr)
        self.assertIn('dependency-injection-di.md', result.stdout)

    def test_relationships_and_provenance(self):
        valid_ids = {r['id'] for r in rows('catalog.tsv')}
        for rel in rows('relationships.tsv'):
            self.assertEqual(rel['status'], 'seed')
            self.assertTrue((ROOT/rel['source_path']).is_file())
            for key in ('subject_id','object_id'):
                if rel[key]:
                    self.assertIn(rel[key], valid_ids)
        result = run('related', 'DI')
        self.assertEqual(result.returncode, 0, result.stderr)
        self.assertIn('cross-category-relationships/dip.md', result.stdout)

    def test_duplicates_and_unknowns(self):
        result = run('sources', 'dependency-injection-container')
        self.assertEqual(result.returncode, 0, result.stderr)
        self.assertEqual(result.stdout.count('dependency-injection-container.md'), 2)
        result = run('get', 'no-such-pattern')
        self.assertEqual(result.returncode, 2)
        self.assertIn('Unknown concept', result.stderr)

    def test_can_execute_from_external_working_directory(self):
        out = run('path', 'strangler-fig', cwd='/tmp')
        self.assertEqual(out.returncode, 0, out.stderr)
        self.assertIn('strangler-fig.md', out.stdout)

    def test_unambiguous_alias_index(self):
        aliases = rows('aliases.tsv')
        self.assertEqual(len({r['normalized'] for r in aliases}), len(aliases))
        ids = {r['id'] for r in rows('catalog.tsv')}
        self.assertTrue(all(r['id'] in ids for r in aliases))


if __name__ == '__main__':
    unittest.main()
<!-- SWE-KB:END -->

