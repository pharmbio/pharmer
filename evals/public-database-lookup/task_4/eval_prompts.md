## Prompt

How many completed phase 3 trials of semaglutide are registered on ClinicalTrials.gov, and how many of them
have posted results? Please list the NCT IDs.

## A good answer

Counts checked on 2026-11-27 with the API v2. The registry changes daily, so later runs will differ; check the
reasoning and the reconciliation, not the exact numbers.

- Uses the ClinicalTrials.gov API v2 with server-side filters: intervention `semaglutide`,
  `filter.overallStatus=COMPLETED`, `aggFilters=phase:3` (and `results:with` for the second count), with
  `countTotal=true`.
- On 2026-11-27: 813 semaglutide trials in total → 360 completed → **101** completed with phase 3 →
  **66** of those with posted results.
- **Ambiguous filters are flagged**:
  - The phase 3 filter also returns Phase 2/3 trials (4 of the 101). The answer says whether these are
    included and gives the count both ways, or asks.
  - The intervention search matches more than the intervention name: 8 of the 101 trials have no intervention
    named "semaglutide". On 2026-11-27 these included a misspelling ("Semagludtide", NCT07834398), the brand
    name (Ozempic®, NCT06739044), the semaglutide/insulin icodec combination IcoSema (NCT06269107,
    NCT05352815), and a trial of an antiemetic for GLP-1-induced nausea (NCT07446439), where semaglutide is
    not the study drug. The answer checks the intervention field locally, keeps the first kinds, flags or
    drops the last, and says what it did.
- Paginates with `pageToken` until no token comes back, and reconciles the retrieved count against `totalCount`.
- Keeps overall status, phase and results availability as separate fields; does not treat "completed" as
  "has results".
- The NCT ID list is saved to a file or given as a compact table, with the access date (the counts move).
- Without the skill, agents often scrape the web search, cite a number from memory, or forget the Phase 2/3
  overlap.
