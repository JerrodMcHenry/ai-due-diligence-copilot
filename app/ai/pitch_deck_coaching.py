"""
Phase 10.8 -- Pitch Deck Coach V1.

INVESTIGATION FINDING (load-bearing design record, same convention as
app/ai/fundraising_readiness.py's own docstring): the only existing PDF/
pitch-deck code path in this repo is POST /analyze -> run_due_diligence(),
which treats an uploaded PDF purely as one more EVIDENCE SOURCE feeding
Methodology v2's six canonical pillar scores (SPS). That pipeline answers
"what does the evidence say about this company" -- it has no concept of
deck communication quality, slide structure, or investor-narrative
coaching, and reusing it here would silently conflate two genuinely
different questions Part 2 requires kept structurally distinct:

    PITCH DECK QUALITY  !=  STARTUP QUALITY

("A brilliant startup can have a terrible deck. A terrible startup can
have a polished deck.") This module NEVER calls run_due_diligence(),
analyze_pillar(), compute_vps(), or anything in scoring.py/
scoring_methodology.py/vps_scoring.py, and produces no score that could
be mistaken for SPS or VPS.

WHAT THIS MODULE DOES: one LLM call over the deck's own extracted,
page-tagged text, producing a structured coaching review -- a
reconstructed story, per-investor-question section coaching, prioritized
fixes, strengths, open questions, and pitch-prep questions. Follows the
exact same architecture as app/ai/idea_structuring.py: simple JSON-mode
call (not analyze_pillar.py's heavier evidence-validation machinery),
plus a POST-HOC PYTHON SANITIZATION PASS that is the actual anti-
fabrication enforcement -- not merely a prompt instruction. Concretely:

- Every factual claim about the deck (a DeckStory field, a section's
  "what_its_saying") must carry a source_quote + quote_page. The quote is
  verified to be a REAL SUBSTRING of that exact page's extracted text
  (see _verify_quote()) before it is trusted -- an unverifiable claim is
  downgraded to an honest "not found"/"missing", never shown as fact.
  This mirrors idea_structuring.py's _quote_is_verifiable(), scoped one
  level tighter (a specific page, not just "somewhere in the document"),
  which is what makes real page-level provenance possible (Part 16).
- top_fixes/strengths/open_questions/prep_questions are not free text --
  each references a related_category, and Python (not the model's own
  self-report) enforces that a "fix"/"open question" only ever points at
  a section THIS CODE independently classified missing/unclear, and a
  "strength" only ever points at a section classified effective. See
  _sanitize_review()'s cross-checks below.

DECK READINESS LABEL (Part 14): the user's explicit default is NO numeric
Deck Score. `readiness_label` is a small fixed vocabulary (Early Draft /
Developing / Getting Clear / Pitch Ready), computed by PURE ARITHMETIC
over the already-sanitized `sections` list (see readiness_label_for()) --
counting how many of the seven core investor questions (Part 8's own
list: Problem, Solution, Market, Business Model, Traction, Team, Ask)
this deck answers effectively. No LLM call determines this label; it is
a deterministic function over data the founder can already see for
themselves in the section list above it.

INVESTOR LENS (Part 8): `why_investors_care` on every section is FIXED,
hand-written educational copy per category (INVESTOR_LENS below), never
LLM-generated -- it explains what investors generally look for in that
kind of slide, not a claim about this specific deck, so it carries no
grounding requirement and cannot drift between reviews.

PERSISTENCE: none of this module's business -- app/api.py's endpoint
calls generate_pitch_deck_review() and persists the resulting dict into
the new, dedicated pitch_deck_reviews table (app/database/db.py). This
module reads nothing from and writes nothing to any database table.
"""

import json
import os

from dotenv import load_dotenv
from openai import OpenAI

load_dotenv()

client = OpenAI(api_key=os.getenv("OPENAI_API_KEY"))


class PitchDeckCoachingError(Exception):
    """Raised for any LLM/parsing failure -- app/api.py catches this and
    returns a generic, safe error, never the raw underlying exception."""


# Part 6's fixed vocabulary. The model is asked to classify the deck
# against every one of these every time (never a subset it invents) so
# the section list -- and therefore readiness_label_for() below, which
# counts over CORE_CATEGORIES -- stays consistent across every review.
SECTION_LABELS: dict[str, str] = {
    "cover": "Cover",
    "problem": "Problem",
    "solution": "Solution",
    "product": "Product",
    "market": "Market",
    "business_model": "Business Model",
    "traction": "Traction",
    "gtm": "Go-To-Market",
    "competition": "Competition",
    "team": "Team",
    "financials": "Financials",
    "ask": "Fundraising Ask / Use of Funds",
}

CATEGORY_KEYS = list(SECTION_LABELS.keys())

# Part 8's own educational-prompt layer, verbatim where the phase gave an
# example, extended with the same voice for every other category. Fixed
# copy, not model output -- see this module's own docstring.
INVESTOR_LENS: dict[str, str] = {
    "cover": "Investors will often want to understand, within seconds, what this company actually does.",
    "problem": "Investors will often want to understand whether this is painful enough that customers will change behavior or spend money to solve it.",
    "solution": "Investors will often want to understand whether the product actually solves the stated problem, and what makes it different from existing ways of solving it.",
    "product": "Investors will often want to understand whether there is a real, demonstrable product behind the pitch, not only an idea.",
    "market": "Investors will often want to understand whether this can become a large enough business.",
    "business_model": "Investors will often want to understand how this eventually becomes an economically attractive company.",
    "traction": "Investors will often want to understand whether there is evidence that people actually want this.",
    "gtm": "Investors will often want to understand how real customers will actually be acquired, and whether that path is credible at scale.",
    "competition": "Investors will often want to understand why this company can win against real alternatives, including a customer doing nothing at all.",
    "team": "Investors will often want to understand why this team is unusually capable of solving this specific problem.",
    "financials": "Investors will often want to understand whether the numbers hold together, and whether the founder understands their own economics.",
    "ask": "Investors will often want to understand what you're raising, and what that capital will allow you to prove next.",
}

# Part 14's seven core investor questions, exactly Part 8's own list plus
# Solution -- the set readiness_label_for() counts over. cover/product/
# gtm/competition/financials still get full section coaching above; they
# are simply not part of the fixed readiness-band arithmetic, the same
# "not every dimension has to carry the aggregate" posture
# fundraising_readiness.py already takes with its stage weight profiles.
CORE_READINESS_CATEGORIES = (
    "problem", "solution", "market", "business_model", "traction", "team", "ask",
)

READINESS_BANDS = (
    (0, 2, "Early Draft"),
    (2, 4, "Developing"),
    (4, 6, "Getting Clear"),
    (6, 8, "Pitch Ready"),
)


def readiness_label_for(sections: list[dict]) -> str:
    """
    Part 14's deterministic aggregation. Pure arithmetic over the
    ALREADY-SANITIZED sections list this same response shows the founder
    -- counts how many of CORE_READINESS_CATEGORIES were classified
    "effective", then maps the count through READINESS_BANDS. Identical
    input always produces identical output; no LLM call happens here.
    """
    effective_count = sum(
        1 for section in sections
        if section.get("category") in CORE_READINESS_CATEGORIES and section.get("status") == "effective"
    )

    for low, high, label in READINESS_BANDS:
        if low <= effective_count < high:
            return label

    return READINESS_BANDS[-1][2]


# Honest "not found" copy per story field, used whenever the model
# reports found=False OR its found=True claim fails grounding
# verification (_verify_quote() below) -- Part 5's own worked example
# ("We couldn't find a clear fundraising ask in this deck.") extended to
# every field in the same voice.
_STORY_NOT_FOUND: dict[str, str] = {
    "company": "We couldn't find a clear description of what the company does in this deck.",
    "customer": "We couldn't find a clear description of who this is for in this deck.",
    "problem": "We couldn't find a clearly stated problem in this deck.",
    "solution": "We couldn't find a clearly described solution in this deck.",
    "business": "We couldn't find a clear explanation of how this company makes money in this deck.",
    "proof": "We couldn't find traction or evidence in this deck.",
    "ask": "We couldn't find a clear fundraising ask in this deck.",
}

STORY_FIELDS = list(_STORY_NOT_FOUND.keys())

_MAX_PAGES_IN_PROMPT_CHARS = 60_000  # generous; guards a pathological page count/density from blowing the prompt budget


def _build_deck_text(pages: list[str]) -> str:
    labeled = []
    for index, page_text in enumerate(pages, start=1):
        body = page_text.strip() if page_text.strip() else "(no extractable text on this page)"
        labeled.append(f"[PAGE {index}]\n{body}")
    combined = "\n\n".join(labeled)
    return combined[:_MAX_PAGES_IN_PROMPT_CHARS]


_RESPONSE_SHAPE = """
{
  "story": {
    "company": {"found": bool, "summary": string, "source_quote": string|null, "quote_page": int|null},
    "customer": {same shape},
    "problem": {same shape},
    "solution": {same shape},
    "business": {same shape},
    "proof": {same shape},
    "ask": {same shape}
  },
  "sections": [
    {
      "category": one of "cover","problem","solution","product","market","business_model","traction","gtm","competition","team","financials","ask",
      "status": "missing"|"unclear"|"effective",
      "page_refs": [int, ...],
      "what_its_saying": string|null,
      "source_quote": string|null,
      "quote_page": int|null,
      "whats_working": string|null,
      "may_confuse": string|null,
      "try_this": string|null
    }
    // exactly one entry per category listed above, every time, even if status is "missing"
  ],
  "top_fixes": [
    {"title": string, "issue": string, "why_it_matters": string, "try_this": string, "related_category": string}
  ],
  "strengths": [
    {"title": string, "why_it_works": string, "related_category": string}
  ],
  "open_questions": [
    {"question": string, "related_category": string}
  ],
  "prep_questions": [
    {"question": string, "related_category": string}
  ]
}
"""

SYSTEM_PROMPT = f"""You are an experienced startup pitch coach reviewing a founder's pitch deck.
You are coaching the founder, not grading them, and you are not a real
investor -- never claim to represent actual investor opinion. This is an
educational tool, not an investment decision.

You will be given the deck's text, extracted page by page and marked
with [PAGE N]. Some pages may have little or no extractable text (they
may be image-only slides) -- do not guess their content.

YOUR JOB:
1. Reconstruct the story the deck actually tells (the "story" object) --
   company, customer, problem, solution, business model, proof/traction,
   and the fundraising ask. If the deck does not clearly address one of
   these, set found=false and write an honest one-sentence summary saying
   so -- never invent an answer.
2. Classify the deck against EVERY ONE of the twelve fixed categories
   listed in the schema below (the "sections" array must have exactly
   twelve entries, one per category, always, even when a category is
   entirely absent from the deck). For each: is the investor question
   this category represents MISSING (not addressed anywhere), UNCLEAR
   (addressed, but confusingly, incompletely, or hard to follow), or
   EFFECTIVE (clearly and convincingly addressed)? A category doesn't
   need its own dedicated slide -- if it's answered well inside another
   slide, it's effective. Give "try_this" a concrete, actionable
   suggestion regardless of status.
3. Pick the (at most) 3 most important things to fix first (top_fixes),
   each tied to a related_category that you classified missing or
   unclear above. Prioritize -- do not list every weakness.
4. Identify genuine strengths (strengths) the founder should keep, each
   tied to a related_category you classified effective above.
5. List open questions the deck leaves for a reader (open_questions),
   each tied to a related_category you classified missing or unclear.
6. List likely questions the founder should prepare to answer in an
   actual investor conversation (prep_questions), grounded in the deck's
   real gaps or its real claims -- each tied to a related_category.

GROUNDING RULES -- CRITICAL:
- Every factual claim about what the deck says (a "found":true story
  field, or a section's "what_its_saying") MUST include a source_quote:
  a short, near-verbatim phrase COPIED EXACTLY from the text of the page
  named in quote_page. Do not paraphrase into the quote field -- copy it.
- NEVER invent specific numbers, customer counts, revenue figures,
  market sizes, competitor names, or funding amounts that are not
  actually present in the deck text you were given.
- If you are not confident a category is missing/unclear/effective based
  on real page content, prefer "missing" or "unclear" over "effective".
- Coaching language must stay in the register of a coach, not a verdict:
  prefer "may confuse an investor", "consider testing", "try this" --
  never "investors hate this" or "you must".

Return ONLY valid JSON matching this exact shape (no prose, no markdown
fences):
{_RESPONSE_SHAPE}
"""


def _call_llm(deck_text: str) -> dict:
    try:
        response = client.chat.completions.create(
            model="gpt-4.1-mini",
            temperature=0.0,
            max_tokens=4000,
            messages=[
                {"role": "system", "content": SYSTEM_PROMPT},
                {"role": "user", "content": f"Pitch deck text (by page):\n\n{deck_text}"},
            ],
        )
        content = response.choices[0].message.content
    except Exception as error:
        raise PitchDeckCoachingError("LLM request failed") from error

    if not content:
        raise PitchDeckCoachingError("Empty LLM response")

    content = content.replace("```json", "").replace("```", "").strip()

    try:
        return json.loads(content)
    except json.JSONDecodeError as error:
        raise PitchDeckCoachingError("LLM response was not valid JSON") from error


def _normalize(text: str) -> str:
    return " ".join(text.lower().split())


def _verify_quote(quote: str | None, page: int | None, pages: list[str]) -> bool:
    """
    The real enforcement mechanism (see this module's own docstring):
    a claim is only trusted if its source_quote is an actual substring of
    the SPECIFIC page it claims to come from -- catches the model citing
    a real-sounding quote from the wrong page, or from no page at all.
    """
    if not quote or not quote.strip() or page is None:
        return False

    if not isinstance(page, int) or page < 1 or page > len(pages):
        return False

    return _normalize(quote) in _normalize(pages[page - 1])


def _sanitize_story(raw: dict, pages: list[str]) -> dict:
    story_raw = raw.get("story") if isinstance(raw.get("story"), dict) else {}
    story: dict = {}

    for field_name in STORY_FIELDS:
        field = story_raw.get(field_name)
        field = field if isinstance(field, dict) else {}

        found = bool(field.get("found"))
        summary = field.get("summary")
        quote = field.get("source_quote")
        page = field.get("quote_page")

        if found and isinstance(summary, str) and summary.strip() and _verify_quote(quote, page, pages):
            story[field_name] = {
                "found": True,
                "summary": summary.strip(),
                "page_refs": [page],
            }
        else:
            story[field_name] = {
                "found": False,
                "summary": _STORY_NOT_FOUND[field_name],
                "page_refs": [],
            }

    return story


def _sanitize_sections(raw: dict, pages: list[str]) -> list[dict]:
    raw_sections = raw.get("sections") if isinstance(raw.get("sections"), list) else []
    by_category = {
        entry.get("category"): entry
        for entry in raw_sections
        if isinstance(entry, dict) and entry.get("category") in CATEGORY_KEYS
    }

    sections: list[dict] = []

    for category in CATEGORY_KEYS:
        entry = by_category.get(category) or {}
        status = entry.get("status")
        status = status if status in ("missing", "unclear", "effective") else "missing"

        quote = entry.get("source_quote")
        page = entry.get("quote_page")
        raw_page_refs = entry.get("page_refs") if isinstance(entry.get("page_refs"), list) else []
        page_refs = [p for p in raw_page_refs if isinstance(p, int) and 1 <= p <= len(pages)]

        what_its_saying = entry.get("what_its_saying")
        grounded = status != "missing" and isinstance(what_its_saying, str) and what_its_saying.strip() and _verify_quote(quote, page, pages)

        if not grounded:
            # Fail closed: an ungrounded claim of unclear/effective
            # collapses to missing, exactly like an unverifiable
            # DeckStory field collapses to found=False above.
            status = "missing"
            what_its_saying = None
            whats_working = None
            may_confuse = None
            page_refs = []
        else:
            page_refs = sorted(set(page_refs + [page]))
            whats_working = entry.get("whats_working") if status == "effective" else None
            may_confuse = entry.get("may_confuse") if status == "unclear" else None
            whats_working = whats_working.strip() if isinstance(whats_working, str) and whats_working.strip() else None
            may_confuse = may_confuse.strip() if isinstance(may_confuse, str) and may_confuse.strip() else None

        try_this = entry.get("try_this")
        try_this = try_this.strip() if isinstance(try_this, str) and try_this.strip() else None

        sections.append({
            "category": category,
            "label": SECTION_LABELS[category],
            "status": status,
            "page_refs": page_refs,
            "what_its_saying": what_its_saying if grounded else None,
            "whats_working": whats_working if grounded else None,
            "may_confuse": may_confuse if grounded else None,
            "why_investors_care": INVESTOR_LENS[category],
            "try_this": try_this,
        })

    return sections


def _status_by_category(sections: list[dict]) -> dict[str, str]:
    return {section["category"]: section["status"] for section in sections}


def _sanitize_fixes(raw: dict, statuses: dict[str, str]) -> list[dict]:
    raw_fixes = raw.get("top_fixes") if isinstance(raw.get("top_fixes"), list) else []
    fixes: list[dict] = []

    for entry in raw_fixes:
        if not isinstance(entry, dict):
            continue

        category = entry.get("related_category")
        title = entry.get("title")
        issue = entry.get("issue")
        why_it_matters = entry.get("why_it_matters")
        try_this = entry.get("try_this")

        # Enforcement, not a request: a "fix" only survives if it points
        # at a section THIS CODE independently classified missing/unclear.
        if statuses.get(category) not in ("missing", "unclear"):
            continue

        if not all(isinstance(v, str) and v.strip() for v in (title, issue, why_it_matters, try_this)):
            continue

        fixes.append({
            "title": title.strip(),
            "issue": issue.strip(),
            "why_it_matters": why_it_matters.strip(),
            "try_this": try_this.strip(),
            "related_category": category,
        })

        if len(fixes) >= 3:  # Part 9: prioritize, never overwhelm with 27 equal-weight items
            break

    return fixes


def _sanitize_strengths(raw: dict, statuses: dict[str, str]) -> list[dict]:
    raw_strengths = raw.get("strengths") if isinstance(raw.get("strengths"), list) else []
    strengths: list[dict] = []

    for entry in raw_strengths:
        if not isinstance(entry, dict):
            continue

        category = entry.get("related_category")
        title = entry.get("title")
        why_it_works = entry.get("why_it_works")

        if statuses.get(category) != "effective":
            continue

        if not all(isinstance(v, str) and v.strip() for v in (title, why_it_works)):
            continue

        strengths.append({
            "title": title.strip(),
            "why_it_works": why_it_works.strip(),
            "related_category": category,
        })

    return strengths[:5]


def _sanitize_open_questions(raw: dict, statuses: dict[str, str]) -> list[dict]:
    raw_questions = raw.get("open_questions") if isinstance(raw.get("open_questions"), list) else []
    questions: list[dict] = []

    for entry in raw_questions:
        if not isinstance(entry, dict):
            continue

        category = entry.get("related_category")
        question = entry.get("question")

        # Part 11: "Do not manufacture weaknesses merely to populate the
        # section" -- enforced here: an open question only survives if it
        # points at a section actually classified missing/unclear.
        if statuses.get(category) not in ("missing", "unclear"):
            continue

        if not isinstance(question, str) or not question.strip():
            continue

        questions.append({"question": question.strip(), "related_category": category})

    return questions[:8]


def _sanitize_prep_questions(raw: dict, statuses: dict[str, str]) -> list[dict]:
    raw_questions = raw.get("prep_questions") if isinstance(raw.get("prep_questions"), list) else []
    questions: list[dict] = []

    for entry in raw_questions:
        if not isinstance(entry, dict):
            continue

        category = entry.get("related_category")
        question = entry.get("question")

        # Grounded in a category this code actually classified one way or
        # another (gap or claim) -- never an unrelated invented category.
        if category not in statuses:
            continue

        if not isinstance(question, str) or not question.strip():
            continue

        questions.append({"question": question.strip(), "related_category": category})

    return questions[:8]


def generate_pitch_deck_review(pages: list[str], deck_filename: str) -> dict:
    """
    The one entry point app/api.py calls. `pages` is the exact list
    extract_pages_from_pdf() returns (one entry per physical PDF page).
    Returns a dict matching PitchDeckReviewResponse's shape minus
    id/created_at (the caller/database own those). Raises
    PitchDeckCoachingError on any LLM/parsing failure.
    """
    deck_text = _build_deck_text(pages)
    raw = _call_llm(deck_text)

    if not isinstance(raw, dict):
        raise PitchDeckCoachingError("LLM response was not a JSON object")

    story = _sanitize_story(raw, pages)
    sections = _sanitize_sections(raw, pages)
    statuses = _status_by_category(sections)

    return {
        "deck_filename": deck_filename,
        "page_count": len(pages),
        "readiness_label": readiness_label_for(sections),
        "story": story,
        "sections": sections,
        "top_fixes": _sanitize_fixes(raw, statuses),
        "strengths": _sanitize_strengths(raw, statuses),
        "open_questions": _sanitize_open_questions(raw, statuses),
        "prep_questions": _sanitize_prep_questions(raw, statuses),
    }
