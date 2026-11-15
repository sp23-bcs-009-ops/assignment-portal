# Workflow Demonstration (Task 5)

Repository: https://github.com/sp23-bcs-009-ops/assignment-portal

Each run was triggered by a `git push`. The pipeline ran the tests, and the
report was sent through the Cloudflare tunnel to `receiver.py`, which updated
`test-report.json` on the local computer automatically. A copy of each received
report is in the [`evidence/`](evidence) folder.

| # | Step | Commit | Pipeline run | Tests | Result | Received report |
|---|------|--------|--------------|-------|--------|-----------------|
| 1 | Working version | `b0ec081` | [43739314572](https://github.com/sp23-bcs-009-ops/assignment-portal/actions/runs/43739314572) | 3/3 passed | ✅ Passed | [run1-passed.json](evidence/run1-passed.json) |
| 2 | Defect introduced | `a703e76` | [43739806907](https://github.com/sp23-bcs-009-ops/assignment-portal/actions/runs/43739806907) | 2/3 passed, 1 failed | ❌ Failed | [run2-failed.json](evidence/run2-failed.json) |
| 3 | Defect fixed | `f97d622` | [43739860368](https://github.com/sp23-bcs-009-ops/assignment-portal/actions/runs/43739860368) | 3/3 passed | ✅ Passed | [run3-fixed-passed.json](evidence/run3-fixed-passed.json) |

## The defect
In commit `a703e76`, `is_valid_url()` in `app.py` was changed to always
return `True`, so invalid links were accepted and saved.

The test `test_invalid_url_is_rejected_and_not_saved` caught it. The app
redirected (302, saved) instead of rejecting (400). The "Run tests" step
failed, so the pipeline failed. The report steps still ran (`if: always()`)
and the receiver saved a report with `"status": "failed"` and the failure
message:

```
assert 302 == 400
```

Commit `f97d622` restored the URL check, and all tests passed again.

## Bonus evidence (conditional deploy + email)

Pages URL: https://sp23-bcs-009-ops.github.io/assignment-portal/
(the page footer shows the commit it was deployed from)

| # | Step | Commit | Pipeline run | test job | deploy job | Pages shows | Email |
|---|------|--------|--------------|----------|------------|-------------|-------|
| 4 | Pages added (passing) | `3048e2f` | [43740049655](https://github.com/sp23-bcs-009-ops/assignment-portal/actions/runs/43740049655) | ✅ | ✅ deployed | `3048e2f` | (not configured yet) |
| 5 | Defect introduced | `7830d37` | [43743482829](https://github.com/sp23-bcs-009-ops/assignment-portal/actions/runs/43743482829) | ❌ | ⏭️ skipped | `3048e2f` (unchanged) | `[CI FAILED] ... @ 7830d37 - 2/3 passed` |
| 6 | Defect fixed | `68edd99` | [43743556312](https://github.com/sp23-bcs-009-ops/assignment-portal/actions/runs/43743556312) | ✅ | ✅ deployed | `68edd99` | `[CI PASSED] ... @ 68edd99 - 3/3 passed` |

Received reports for these runs: [run5-failed.json](evidence/run5-failed.json),
[run6-fixed-passed.json](evidence/run6-fixed-passed.json).

## Receiver console output
```
[22:04:37] Report saved: PASSED | commit b0ec081 | run 43739314572 | 3/3 passed, 0 failed
[22:09:44] Report saved: FAILED | commit a703e76 | run 43739806907 | 2/3 passed, 1 failed
[22:10:18] Report saved: PASSED | commit f97d622 | run 43739860368 | 3/3 passed, 0 failed
[22:12:24] Report saved: PASSED | commit 3048e2f | run 43740049655 | 3/3 passed, 0 failed
[22:49:01] Report saved: FAILED | commit 7830d37 | run 43743482829 | 2/3 passed, 1 failed
[22:49:50] Report saved: PASSED | commit 68edd99 | run 43743556312 | 3/3 passed, 0 failed
```
