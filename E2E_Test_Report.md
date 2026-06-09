# E2E Test Report — Wonderful Mysterious App

**Branch:** WMWA-Dev
**Test Suite:** `tests/e2e/`
**Files:** `test_e2e_health.py`, `test_e2e_core_flow.py`, `test_e2e_extended.py`
**Server:** Uvicorn subprocess on `0.0.0.0:8000` (shared session, managed by `tests/e2e/conftest.py`)
**Isolated server:** Uvicorn subprocess on `0.0.0.0:8001` (rate limit test only, managed by `test_e2e_extended.py`)
**CI Platform:** GitHub Actions — `e2e-tests` job in `python_tests.yml`
**Runner:** `ubuntu-latest`
**Python:** 3.11.15
**pytest:** 9.0.3
**Plugins:** anyio-4.13.0, asyncio-1.3.0

---

## CI Execution Output

```
Run export PYTHONPATH=$PYTHONPATH:$(pwd)
============================= test session starts ==============================
platform linux -- Python 3.11.15, pytest-9.0.3, pluggy-1.6.0 -- /opt/hostedtoolcache/Python/3.11.15/x64/bin/python
cachedir: .pytest_cache
rootdir: /home/runner/work/WonderfulMysteriousApp/WonderfulMysteriousApp
plugins: anyio-4.13.0, asyncio-1.3.0
asyncio: mode=Mode.STRICT, debug=False, asyncio_default_fixture_loop_scope=None, asyncio_default_test_loop_scope=function
collecting ... collected 25 items

tests/e2e/test_e2e_core_flow.py::test_full_user_flow_saves_and_reads_favorites PASSED [  4%]
tests/e2e/test_e2e_extended.py::test_all_get_endpoints_return_200_and_json[/api/weather] PASSED [  8%]
tests/e2e/test_e2e_extended.py::test_all_get_endpoints_return_200_and_json[/api/insight] PASSED [ 12%]
tests/e2e/test_e2e_extended.py::test_all_get_endpoints_return_200_and_json[/api/fortune] PASSED [ 16%]
tests/e2e/test_e2e_extended.py::test_all_get_endpoints_return_200_and_json[/api/favorites] PASSED [ 20%]
tests/e2e/test_e2e_extended.py::test_landing_page_returns_200_html PASSED [ 24%]
tests/e2e/test_e2e_extended.py::test_weather_response_schema PASSED [ 28%]
tests/e2e/test_e2e_extended.py::test_insight_response_schema PASSED [ 32%]
tests/e2e/test_e2e_extended.py::test_fortune_response_schema PASSED [ 36%]
tests/e2e/test_e2e_extended.py::test_favorites_get_response_schema PASSED [ 40%]
tests/e2e/test_e2e_extended.py::test_favorites_post_returns_201_and_saved_message PASSED [ 44%]
tests/e2e/test_e2e_extended.py::test_favorites_post_id_appears_in_get PASSED [ 48%]
tests/e2e/test_e2e_extended.py::test_favorites_multiple_posts_all_appear_in_get PASSED [ 52%]
tests/e2e/test_e2e_extended.py::test_favorites_post_missing_id_returns_422 PASSED [ 56%]
tests/e2e/test_e2e_extended.py::test_favorites_post_non_integer_id_returns_422 PASSED [ 60%]
tests/e2e/test_e2e_extended.py::test_submit_valid_payload_returns_201_with_echo PASSED [ 64%]
tests/e2e/test_e2e_extended.py::test_submit_missing_user_returns_422 PASSED [ 68%]
tests/e2e/test_e2e_extended.py::test_submit_missing_data_returns_422 PASSED [ 72%]
tests/e2e/test_e2e_extended.py::test_submit_does_not_affect_favorites PASSED [ 76%]
tests/e2e/test_e2e_extended.py::test_rate_limiter_unit_allows_100_then_blocks PASSED [ 80%]
tests/e2e/test_e2e_extended.py::test_rate_limiter_is_per_ip PASSED [ 84%]
tests/e2e/test_e2e_extended.py::test_live_server_rate_limit_returns_429 PASSED [ 88%]
tests/e2e/test_e2e_health.py::test_core_api_endpoints_are_healthy[/api/weather] PASSED [ 92%]
tests/e2e/test_e2e_health.py::test_core_api_endpoints_are_healthy[/api/insight] PASSED [ 96%]
tests/e2e/test_e2e_health.py::test_core_api_endpoints_are_healthy[/api/fortune] PASSED [100%]

============================== 25 passed in 1.27s ==============================
```

---

## Results Summary

| Metric | Value |
|---|---|
| Total tests collected | 25 |
| Passed | 25 |
| Failed | 0 |
| Duration | 1.27s |
| Platform | linux |

---

## Test-by-Test Results

### test_e2e_core_flow.py — Daily Mystery Experience

| # | Test | Result |
|---|---|---|
| 1 | `test_full_user_flow_saves_and_reads_favorites` | ✅ PASSED |

### test_e2e_extended.py — Extended Coverage

| # | Test | Result |
|---|---|---|
| 2 | `test_all_get_endpoints_return_200_and_json[/api/weather]` | ✅ PASSED |
| 3 | `test_all_get_endpoints_return_200_and_json[/api/insight]` | ✅ PASSED |
| 4 | `test_all_get_endpoints_return_200_and_json[/api/fortune]` | ✅ PASSED |
| 5 | `test_all_get_endpoints_return_200_and_json[/api/favorites]` | ✅ PASSED |
| 6 | `test_landing_page_returns_200_html` | ✅ PASSED |
| 7 | `test_weather_response_schema` | ✅ PASSED |
| 8 | `test_insight_response_schema` | ✅ PASSED |
| 9 | `test_fortune_response_schema` | ✅ PASSED |
| 10 | `test_favorites_get_response_schema` | ✅ PASSED |
| 11 | `test_favorites_post_returns_201_and_saved_message` | ✅ PASSED |
| 12 | `test_favorites_post_id_appears_in_get` | ✅ PASSED |
| 13 | `test_favorites_multiple_posts_all_appear_in_get` | ✅ PASSED |
| 14 | `test_favorites_post_missing_id_returns_422` | ✅ PASSED |
| 15 | `test_favorites_post_non_integer_id_returns_422` | ✅ PASSED |
| 16 | `test_submit_valid_payload_returns_201_with_echo` | ✅ PASSED |
| 17 | `test_submit_missing_user_returns_422` | ✅ PASSED |
| 18 | `test_submit_missing_data_returns_422` | ✅ PASSED |
| 19 | `test_submit_does_not_affect_favorites` | ✅ PASSED |
| 20 | `test_rate_limiter_unit_allows_100_then_blocks` | ✅ PASSED |
| 21 | `test_rate_limiter_is_per_ip` | ✅ PASSED |
| 22 | `test_live_server_rate_limit_returns_429` | ✅ PASSED |

### test_e2e_health.py — Core API Health

| # | Test | Result |
|---|---|---|
| 23 | `test_core_api_endpoints_are_healthy[/api/weather]` | ✅ PASSED |
| 24 | `test_core_api_endpoints_are_healthy[/api/insight]` | ✅ PASSED |
| 25 | `test_core_api_endpoints_are_healthy[/api/fortune]` | ✅ PASSED |

---

## Validation Notes

**Test ordering confirmed safe.** The CI runner executed `test_e2e_health.py`
last (tests 23–25), after the rate limit test at position 22. All three health
checks passed with 200 responses, confirming that the isolated server design
(port 8001) fully prevented the rate limit test from consuming budget on the
shared server (port 8000).

**Rate limit test passed cleanly.** `test_live_server_rate_limit_returns_429`
ran at position 22 against its own isolated Uvicorn instance on port 8001 with
a fresh budget of 100. All 100 requests returned 200; the 101st returned 429
with `{"detail": "Too Many Requests"}` as expected.

**25 collected vs 24 expected.** The previous report projected 24 tests. The
actual count is 25 because `test_e2e_core_flow.py` contributes 1 test and
`test_e2e_health.py` contributes 3, for a combined 4 from existing files plus
21 from `test_e2e_extended.py`. The count discrepancy in the previous report was
due to miscounting the extended file as 20 tests when it contains 21.

---

## Remaining Limitations

| Limitation | Status | Notes |
|---|---|---|
| Browser UI interaction | Not automated | Covered in `E2E_Manual_Testing.md` |
| Rate limit window expiry timing | Not automated | Requires real wall-clock wait; covered in manual testing |
| Container restart / favorites reset | Not automated | Requires Docker stop/start; covered in manual testing |
| CI double-Uvicorn on port 8000 | Known, low risk | `nohup` in CI + `app_server` fixture both bind 8000; functional in all runs |
