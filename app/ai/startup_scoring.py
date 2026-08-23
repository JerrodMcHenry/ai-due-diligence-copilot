# This module previously defined its own PILLAR_WEIGHTS, independently of
# app/ai/investment_score.py's copy. The two had drifted apart with no
# record of an intentional change (see the SIE pillar-weight authority
# audit). Canonical pillar weights now live in app/ai/scoring_methodology.py
# — import PILLAR_WEIGHTS from there instead of redefining it here.
#
# This file is kept (not deleted) in case other startup-scoring-specific
# logic belongs here in the future.

