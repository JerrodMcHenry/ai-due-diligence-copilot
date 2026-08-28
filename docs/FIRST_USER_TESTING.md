# First-User Testing Protocol

Phase 10.11 — Product Polish + First-User Readiness.

This is a **manual usability-testing protocol**, not an analytics build. No
tracking, telemetry, or new instrumentation is required to run it — an
observer sits with each participant (in person or on a screen share),
gives them the URL and a single starting prompt, and records what happens
using the metrics below.

## Ground rules for the observer

- **Give the URL and the starting prompt. Say nothing else.** Do not
  explain what SIE stands for, what VPS/SPS mean, what a "mission" or
  "playbook" is, or which button to click next. The whole point of this
  phase was to make that explanation unnecessary — if the observer has to
  supply it, that's a finding, not a workaround.
- If a participant is stuck for more than ~30 seconds with no idea what
  to try, let them stay stuck and write it down (see "Failure signals"
  in each test) rather than rescuing them mid-task — a rescue erases the
  exact data point this protocol exists to capture.
- Ask the "questions to ask AFTER completion" only after the task
  portion ends, never mid-task.
- Never ask a leading question ("Was the Mission feature useful?").
  Prefer open ones ("What would you do next?" / "What did you expect to
  happen here?").
- Run each test with at least 3-5 participants who actually match the
  persona (a real aspiring founder, a real small-business owner, etc.) —
  a single session is an anecdote, not a signal.

---

## TEST A — Aspiring Founder

**Persona:** someone who has an idea for a company but has never started
one.

**Starting prompt (say exactly this, then stop talking):**

> "Here's a link. Imagine you've always wanted to try building this idea
> you have. Just do what feels natural — I'm going to watch quietly and
> take notes."

**Tasks (do not read this list to the participant — it's the observer's
checklist):**

1. Land on Home and decide what to do.
2. Enter a real idea they'd actually want to explore.
3. Get through sign-in/sign-up if prompted.
4. Reach a modeled venture (Venture Workspace).
5. Form some opinion about what the score on the page means.
6. Identify what the product thinks their biggest unknown is.
7. Start a mission from that unknown.
8. Notice and open a contextual Playbook link.
9. Return to the venture from the Playbook.
10. Record a reflection ("what did you learn") on the mission.
11. Try a "What If?" scenario.
12. Notice the option to turn the idea into a real startup analysis (they
    do not need to actually click through — noticing it is enough).

**What NOT to explain:** Idea Lab, VPS, "modeled venture," Founder
Missions, Playbooks, the founder journey stages, the difference between
VPS and SPS.

**What to observe:**

- Where their cursor/attention goes first on each new screen.
- Whether they read the score explanation or skip straight past it.
- Whether they can articulate, in their own words, what the score means
  and what it doesn't mean (a prediction vs. a model).
- Whether "next move" language reads as an instruction or as trivia.
- Any moment of visible confusion, hesitation, or backtracking.
- Any moment of visible delight or surprise (note the exact trigger).

**Failure signals:**

- They ask "wait, what is this site for?" more than once.
- They can't find how to create their first venture within ~60 seconds
  of landing on Home.
- They describe the VPS as predicting whether they'll succeed.
- They never notice a mission, a Playbook link, or What If exists without
  being told.
- They abandon before reaching a modeled venture.
- They say "I don't know what to do now" at any point after the model is
  built.

**Questions to ask AFTER completion:**

- "Walk me back through what just happened, in your own words."
- "What did that score mean to you?"
- "What would you do next if I asked you to keep going?"
- "Was there anything you expected to find but couldn't?"
- "Would you come back to this on your own?"

**Metrics to record manually:**

- Time to first meaningful action (typing an idea and submitting it).
- Time to a modeled venture existing.
- Whether they identified the biggest unknown unprompted (Y/N).
- Whether they started a mission unprompted (Y/N).
- Whether they opened a Playbook unprompted (Y/N).
- Whether they could explain VPS without it sounding like a prediction
  (Y/N).
- Whether they understood that recording a reflection is different from
  the model actually changing (Y/N).
- Whether, at the end, they could say what they'd do next (Y/N).
- Whether they said they'd return.
- Anything they expected but couldn't find (free text).

---

## TEST B — Existing Founder

**Persona:** someone who already runs a real company and is raising or
preparing to raise.

**Starting prompt:**

> "Here's a link. Imagine you already run a real company and you're
> starting to think about fundraising. Do what feels natural."

**Tasks (observer checklist, not read aloud):**

1. Land on Home and find the path for someone who already has a startup.
2. Run an analysis of their (real or hypothetical) company.
3. Reach the resulting Startup Profile and form an opinion about the
   score.
4. Discover "My Startup" / Founder Workspace on their own.
5. Notice Actions, Milestones, and Updates without needing all three
   explained.
6. Discover Pitch Deck Coach.
7. Discover Fundraising Readiness.
8. Understand, without being told, that Fundraising Readiness is not the
   same thing as their Startup Power Score.
9. Understand what re-analysis is for.

**What NOT to explain:** Founder Workspace, Founder Actions vs. Founder
Updates vs. Milestones, Fundraising Readiness, SPS, canonical vs. modeled
anything.

**What to observe:**

- Whether they hesitate between "Analyze My Startup" and other entry
  points on Home.
- Whether they read the SPS explanation or skip it.
- Whether they can find Founder Workspace from the analysis result
  without searching the nav.
- Whether Pitch Deck Coach and Fundraising Readiness feel like one
  connected idea or two unrelated features.
- Whether they try to re-analyze without being told that's an option.

**Failure signals:**

- They can't find their own company's private workspace after analyzing
  it.
- They think Fundraising Readiness IS their Startup Power Score.
- They never notice Pitch Deck Coach exists.
- They ask what the difference between an "Action" and an "Update" is.
- They give up before finding anything actionable to work on.

**Questions to ask AFTER completion:**

- "What does this score tell an investor, in your own words?"
- "If you wanted to improve your standing, what would you do first?"
- "What's the difference between what you just saw on the Startup
  Profile and what you saw in Fundraising Readiness?"
- "Was there a point where you weren't sure what to click?"

**Metrics to record manually:**

- Time to first meaningful action (starting an analysis).
- Time to a completed Startup Profile.
- Whether they found Founder Workspace unprompted (Y/N).
- Whether they found Pitch Deck Coach unprompted (Y/N).
- Whether they found Fundraising Readiness unprompted (Y/N).
- Whether they correctly distinguished SPS from Fundraising Readiness
  (Y/N).
- Whether they knew what to do next at the end (Y/N).
- What they expected but couldn't find (free text).

---

## TEST C — MBA / Student

**Persona:** a student exploring startup ideas out of curiosity, with no
real company and no intention of forming one (yet).

**Starting prompt:**

> "Here's a link. Imagine you're curious about a startup idea and want to
> play around with it — nothing serious. Do what feels natural."

**Tasks (observer checklist):**

1. Build an idea from Home.
2. Experiment with assumptions (edit the model or use What If).
3. Learn at least one startup concept via a Playbook, without being told
   Playbooks exist.
4. Create a mission (system-suggested or their own).
5. Confirm they never get funneled into a canonical-startup / "claim your
   company" workflow they didn't ask for.

**What NOT to explain:** the founder journey stages, Playbooks, What If,
missions, VPS.

**What to observe:**

- Whether they treat this as "a fun thing to try" or "a form to fill
  out."
- Whether they notice What If on their own.
- Whether Explore/Rankings feels inviting to browse or feels like an
  investor tool that isn't for them.
- Whether anything nudges them toward claiming a real company or an
  identity they don't have.

**Failure signals:**

- They think they're required to have a real company to use the product.
- They never try What If without prompting.
- They hit a screen that assumes they're a verified founder.
- They find Explore intimidating rather than interesting.

**Questions to ask AFTER completion:**

- "Did this feel like something built for people like you, or for
  professional investors?"
- "What was the most interesting thing you saw?"
- "Did anything make you feel like you were doing this wrong?"

**Metrics to record manually:**

- Time to modeled venture.
- Whether they used What If unprompted (Y/N).
- Whether they opened a Playbook unprompted (Y/N).
- Whether they created a mission unprompted (Y/N).
- Whether they ever felt required to "become a real founder" to keep
  going (Y/N).
- Whether they said they'd show this to a friend.

---

## TEST D — Pitch Deck User

**Persona:** someone with an existing pitch deck (their own, or a
class/competition deck) who wants feedback on it.

**Starting prompt:**

> "Here's a link, and here's a pitch deck PDF. Imagine you want feedback
> on this deck before showing it to someone else. Do what feels
> natural."

**Tasks (observer checklist):**

1. Find the pitch-deck path from Home.
2. Upload the deck.
3. Understand the resulting story reconstruction.
4. Identify the single most important thing to fix.
5. Follow a contextual Playbook link tied to a specific weak section.
6. Understand what to do next after reading the review.

**What NOT to explain:** Pitch Deck Coach, deck readiness labels, SIE
generally.

**What to observe:**

- Whether they understand the review is coaching, not a grade — watch
  for them asking "so what's my score?"
- Whether the top-priority fix is obvious without reading the whole
  page.
- Whether "possible investor question" phrasing reads as speculative
  coaching or as something that sounds like real investor feedback.
- Whether they open a Playbook link tied to their weakest section.

**Failure signals:**

- They ask what their deck "scored."
- They can't identify the single most important fix within a few
  seconds of reaching that section.
- They think a specific "possible investor question" is something a
  real investor actually said.
- They have no idea what to do after finishing the review.

**Questions to ask AFTER completion:**

- "What's the one thing you'd change about your deck after this?"
- "Did this feel like a score, or like advice?"
- "What would you do right after this if you were actually about to
  pitch?"

**Metrics to record manually:**

- Time from Home to a completed deck review.
- Whether they identified the top-priority fix unprompted (Y/N).
- Whether they opened a Playbook link unprompted (Y/N).
- Whether they mistakenly treated the review as a numeric score (Y/N).
- Whether they knew what to do next at the end (Y/N).

---

## After running all four

Look across sessions, not within one, for patterns:

- The same "I don't know what to click" moment showing up for multiple
  participants in the same test is a real finding; one participant
  hesitating once is noise.
- Compare "time to first meaningful action" across tests — a large gap
  between Test A and Test C (both start from Home with no real company)
  points at Home itself, not at Idea Lab.
- Track "would you return" and "would you show a friend" over time as
  the plainest signal of whether polish is working.

This document describes the protocol only. Running it, and any resulting
product changes, are future work — this phase does not include running
these sessions.
