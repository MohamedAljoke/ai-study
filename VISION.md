# Vision

## What this is right now

A website you open and play **Battleships** in. That is the whole scope for now.

No game picker, no catalog, no accounts. You land on the site, the game is there, you
play. The engine already exists in Go (`battleships/`); what is missing is the web part.

More games come later, and the site should be able to grow into a multi-game site — but
nothing gets built for that until the second game actually exists.

## Why I am doing it

Three reasons, in order:

1. **Ship something real.** A working site with a working game, publicly reachable.
2. **Turn the build into content.** I will record how I built the website and the game —
   long-form videos plus shorts — and publish them. The building and the content are the
   same work; the project is the material.
3. **Monetize it.** Advertisements on the site, once there is something worth putting them
   on.

## The reuse principle

Game logic is written to be reused, not tied to one site. The Battleships engine should be
usable from a different frontend without changing it. Later I want to build other websites
(for example an event or wedding site with small games in it, points, that kind of thing)
that pull in the same game logic.

Practically that means: keep game rules in their own package, keep them free of HTTP/UI
concerns, and let each site be a thin layer on top.

## How I work

- **Simple first, SaaS later.** Build the simplest thing that works and is live. Only turn
  something into a product/service once the simple version is running and there is a reason
  to.
- **Document as I go.** Write things down while building, because the documentation feeds
  the video scripts.
- **Use AI for the content pipeline.** Generating video scripts, drafting docs, and
  producing the YouTube/shorts material.
- **Multiple income streams.** Ads on the site now; other streams later. This project is
  one of them, not the only one.

## Tooling I still need to find

Software for recording, editing, and producing the videos and shorts. Not chosen yet.

## Phase 1 — playable site

Done when:

- Battleships is playable in a browser.
- It is deployed and publicly reachable.
- The build is documented well enough to write video scripts from.

Nothing else is in phase 1. No picker page, no second game, no ads.

## Phase 2 — ads

Once the site is live and playable, the next thing to work on is ads: learning how ad
networks actually work, what is required to get approved, and how to place them on the page
without ruining the game. This is a learning step as much as a build step.

## Not decided yet

These are directions, not commitments — they get written up properly once they are thought
through:

- The other games beyond Battleships.
- The wedding/event site and its points mechanic.
- What the SaaS version would actually be.
- Which income streams beyond ads.
