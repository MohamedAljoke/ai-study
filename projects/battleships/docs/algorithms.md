# Targeting algorithms — roadmap

Everything here implements `targeting.Strategy` (`Next() game.Position` +
`Observe(p, r)`) and registers in `targeting.All`, so each one drops into
`internal/bench` and is comparable against the others with no engine changes.

**Metric:** mean shots to sink the full 17-cell fleet on a 10×10 board.
Floor is 17, random is ~95.

## Status

| # | Strategy | State | Expected mean shots |
|---|----------|-------|---------------------|
| 0 | `random` | done | ~95 |
| 0 | `hunt` | done | ~65 |
| 0 | `parity` | done | ~60 |
| 0 | `density` | done | ~45 |
| 1 | Monte Carlo | next | ~42 |
| 2 | Entropy / information gain | planned | ~41 |
| 3 | Parity-masked density | planned | ~44 |
| 4 | Learned agent (self-play) | planned | see below |
| 5 | Genetic algorithm (placement side) | planned | n/a — defense |

The "expected" column is literature-typical for a uniform-random placement
prior. Replace with measured numbers from `internal/bench` as each lands —
do not trust the table until it is measured.

---

## 1. Monte Carlo — constraint sampling

**The point:** `density.go` counts placements for each ship *independently* and
multiplies by `hitWeight = 16` per overlapping hit. Both are approximations.
It will happily count a Carrier position without checking that the other four
ships can still fit around it, which gets increasingly wrong as the board fills.

Instead, sample **complete fleet layouts** consistent with every observation:

- every miss cell is empty
- every unsunk hit cell is covered by some ship
- every sunk ship sits exactly where it sank
- no two ships overlap

Count occupancy per unshot cell across N accepted samples → a calibrated
P(hit). Shoot the argmax. `hitWeight` disappears; it emerges from the sampling.

**The hard part is rejection rate.** Naive "place all 5 uniformly at random,
reject if inconsistent" collapses to near-zero acceptance mid-game with 4+ open
hits. Sample constraint-first:

1. Group open hits into clusters (adjacent runs).
2. Assign a ship to each cluster and place it so it covers the cluster.
3. Fill remaining ships uniformly into legal space.
4. Reject on overlap/miss violation; retry with a budget.
5. If the budget is exhausted, fall back to `density` scoring for that shot.

Target ~5–20k accepted samples per shot. Well under a millisecond of real work
in Go per sample, so this stays fast enough for interactive play.

**Watch for:** the sampler must be reproducible from the injected `*rand.Rand`
so `bench` stays deterministic under `seed = 42`.

## 2. Entropy / information gain

Monte Carlo shoots argmax P(hit). But the objective is *fewest shots to sink
the fleet*, and the highest-probability cell is not always the most informative
— a 55% cell that splits the surviving layout set in half can beat a 60% cell
that barely narrows anything.

Reuse the sample pool from step 1: for each candidate cell, compute how much
the hit/miss outcome shrinks the set of surviving layouts, and shoot the cell
that maximizes expected information. Usually a small but real win over pure MC.

Cheap to build once MC exists — it is a different scoring function over the
same samples, not a new algorithm.

## 3. Parity-masked density

Cheap baseline, ~20 lines. `parity.go` hardcodes even parity (stride 2). The
correct mask is the parity of the **smallest afloat ship**: once the 2-cell
Destroyer sinks, no ship is smaller than 3, so a stride-3 lattice still cannot
miss anything. Track the smallest afloat size and tighten the hunt mask as ships
go down, then apply that mask to `density`'s hunt phase.

Worth doing mostly as a clean baseline to prove MC is earning its complexity.

---

## 4. Learned agent — self-play

This is the "learns by playing to get to its best form" one. Some honesty up
front, because it changes what to build:

**scikit-learn is the wrong tool.** It does supervised learning on fixed
feature tables — no self-play loop, no sequential credit assignment, and it is
Python while the engine is Go. The right family is deep RL (DQN or PPO) over a
board-shaped observation.

**And RL probably will not beat a good Monte Carlo agent** at this game. MC is
close to optimal *when the placement prior is uniform*, which it is against
`internal/placement`. This is worth building anyway, for two reasons that are
genuinely real:

- **Non-uniform priors.** Humans do not place ships uniformly — they avoid
  edges, avoid adjacency, cluster in habits. An agent that learns the opponent
  distribution beats MC-under-uniform-assumption against real players. This is
  the honest headline: *RL wins where the prior is unknown.*
- **It is the episode.** Portfolio, video, and course value is in the
  self-play loop working at all, not in shaving a shot off the mean.

### Shape

State is a POMDP with ~3^100 belief states, so tabular Q-learning is out.

- **Observation:** 10×10×N planes — miss, hit-unsunk, sunk, unshot, plus a
  scalar channel per afloat ship size.
- **Action:** 100 logits, one per cell, with already-shot cells masked to -inf.
- **Reward:** −1 per shot (minimize shots), or +1 hit / 0 miss with a terminal
  bonus. Start with −1 per shot; it matches the benchmark metric directly.
- **Algorithm:** PPO or DQN with a small conv net. 3–4 conv layers is plenty;
  this is not a big model.

### Where the code lives

The engine stays in Go. Three options, in order of preference:

1. **Python trains, Go infers.** Export episodes from Go, train in
   Python (PyTorch), export weights as a flat file, load into a Go strategy
   that does forward-pass-only inference. Keeps `targeting.All` pure Go, keeps
   `bench` deterministic. Most work, best result.
2. **Go engine as a gym environment over a socket.** Python drives the loop,
   Go answers `step()`. Simplest to get training running; means the trained
   agent cannot run in `bench` without Python alive.
3. **Pure Go linear/tabular RL over hand-crafted features.** Weakest agent, but
   zero Python and it runs in `bench` natively. Reasonable warm-up episode.

Recommend starting at (2) to get a learning curve on screen fast, then porting
inference to (1) so the agent joins the benchmark table for real.

### Benchmark honestly

Train against one placement strategy, evaluate against a *held-out* one. An
agent that memorizes `internal/placement`'s quirks and reports 38 shots has
learned the RNG, not the game. Also report it against a deliberately
non-uniform "human-like" placer — that is where it should beat MC, and that
comparison is the actual story.

## 5. Genetic algorithm

GA cannot pick **shots** — the state changes every turn, so evolving a shot
sequence is meaningless, and anything it converged to would be a worse
approximation of the MC posterior from step 1.

But GA picking the **policy that picks the shots** is a different problem, and
a standard one. Evaluating a single individual means "play N games, return mean
shots" — a static search over policy space with an expensive, noisy fitness
function. That is exactly GA's shape, and it belongs in `internal/targeting/`.

No separate project needed. Three tiers below, plus the defense side.

### 5a. Evolved scoring policy — offense

Genome is a weight vector over per-cell features: density score, parity bonus,
edge/corner affinity, adjacency-to-hit bonus, distance to nearest miss, one
term per afloat ship size. `Next()` shoots the argmax of the weighted sum.
Fitness is mean shots over a fixed seed set via `bench.Play`.

Slots into `targeting.All` as a normal strategy and lands in the benchmark
table next to `density` and Monte Carlo.

**Be honest in the writeup:** ~10 continuous dimensions is CMA-ES territory and
CMA-ES will probably beat GA here. Run both. That comparison is more
interesting than GA winning.

### 5b. Neuroevolution vs PPO — the one worth building

Step 4 already produces a small conv net: 10×10×N in, 100 masked logits out.
Train that *identical* network two ways — PPO with gradients, and a GA over the
flattened weight vector — then benchmark head to head on the same seeds.

Same architecture, same fitness, same evaluation; two entirely different search
methods. Battleship is small enough that neuroevolution is genuinely
competitive here, which stops being true at larger network sizes.

Either result is publishable. If GA loses, *why* gradients win on this
landscape is the substance of the episode. This also stops the GA and RL work
from being two disconnected folders.

### 5c. Placement — defense

Evolve the defense side in `internal/placement/`, fitness = shots survived
against current targeting strategies.

Two versions, in order:

1. **Evolve one layout.** Genome is 5 genes, `(row, col, orientation)` per
   ship. Best vehicle for learning the mechanics — see the constraint-handling
   notes below. Limitation: a single fixed layout is exploitable once known.
2. **Evolve a placer policy.** `place()` already takes a `weigh` function —
   `Edges`, `Center`, and `Spread` are hand-written ones. Evolve its parameters
   instead of coordinates. Output is a `placement.Factory` that drops into
   `placement.All` and gets benchmarked against every targeting strategy
   automatically. This is the real deliverable: it generalizes, and it produces
   a distribution rather than one exploitable board.

### Cross-cutting concerns

These apply to every tier and are the parts worth getting right:

- **Constraint handling (5c especially).** Ship-wise crossover constantly
  produces overlapping layouts. Reject, penalize, or *repair* by re-placing the
  conflicting ships legally — comparing all three is the most instructive
  experiment in the exercise, and the part toy GA tutorials skip.
- **Noisy fitness.** One game says nothing; variance across games swamps the
  difference between individuals. Evaluate every individual in a generation
  against the **same** seed set — common random numbers. The existing
  `rand.NewPCG(seed, gameIdx)` design gives this for free. Without it, GA
  selects for lucky seeds instead of good policies.
- **Overfitting to the opponent.** Evolve against `density` and you get
  something that beats `density` and may lose to Monte Carlo. Hold out
  strategies for evaluation, same discipline as step 4.
- **Co-evolution.** Alternate generations between 5a/5b and 5c. Red Queen
  dynamics, cycling, and the difficulty of even *measuring* progress when the
  fitness landscape moves underneath you.

Minor secondary use: tuning constants (`hitWeight`, MC sample budgets) against
`bench`. Grid search would do it better; not worth an episode.

---

## Episode mapping

Focus is the AI player for now; the rest is listed so the code shape does not
paint us into a corner later.

| Episode | Depends on |
|---------|-----------|
| Game engine | done — `internal/game` |
| AI opponent | done — `internal/targeting` steps 0 |
| Monte Carlo Search | step 1, 2 |
| Reinforcement Learning | step 4 |
| Genetic algorithm | step 5 — 5b needs step 4's network |
| WebSocket multiplayer | engine + a session layer |
| Kubernetes deployment | multiplayer |
| AWS deployment | Kubernetes |
| Ads / Analytics / Scaling | deployed multiplayer |

The AI episodes need nothing beyond the current `Strategy` interface and
`internal/bench`, so they can all ship before any networking work starts.
