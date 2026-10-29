---
title: HTML inline style formatting is not idempotent
status: todo
created: 2026-10-29
---

## Description

Prettier formats a long `grid-template-columns` value inside an HTML `style` attribute differently on the first and second run; the third run matches the second. This is upstream non-idempotency, but projects that commit formatter output (circuitry) get a spurious diff on the next run. Found in circuitry `design/reference/month-page.dc.html`.

Repro, in an empty git repo:

    <!DOCTYPE html>
    <html><body><div style="display:grid;grid-template-columns:minmax(0,1.5fr) minmax(0,1.2fr) minmax(0,0.9fr) 60px;gap:12px;padding:0 0 6px;font-size:13px"><span>Performer</span></div></body></html>

Pass 1 splits `minmax(0, 0.9fr)` across lines; pass 2 rewraps the whole value.

Decision (2026-10-29): Taidy reruns formatters, bounded, until output stops changing, so that `format(format(x)) == format(x)`.

## Acceptance Criteria

- [ ] A regression test using the repro above fails before the fix and passes after it.
- [ ] The format phase reruns formatters on changed files until no file changes, up to a module-level maximum pass count.
- [ ] Hitting the maximum is reported as an infrastructure failure naming the files that never stabilised, with a non-zero exit.
- [ ] An idempotency test formats the sample-file fixtures twice and fails if the second pass changes anything.

## Notes

Suggestion origin: circuitry

## History

- 2026-10-29 → backlog
- 2026-10-29 backlog → todo
