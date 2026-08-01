"""
Resolve plant taxonomic names using the TNRS API.

This is a Python port of the R TNRS package. API endpoint: https://tnrsapi.xyz/tnrs_api.php

Exported functions:
    TNRS()          - Main entry: resolve/parse names, auto-batch if >5000
    TNRS_base()     - Single API call with input preprocessing
    TNRS_core()     - Low-level HTTP POST to the TNRS API
    TNRS_robust()   - TNRS + automatic retry of suspicious results
    TNRS_synonyms() - Query synonyms for a single species
"""

import hashlib
import json
import socket
import sys
import time
import urllib.error
import urllib.request
from pathlib import Path
from typing import Optional, Union

import pandas as pd


def _check_internet(timeout: float = 5.0) -> bool:
    # save the previous global default timeout to avoid a process-wide side effect
    old_timeout = socket.getdefaulttimeout()
    try:
        socket.setdefaulttimeout(timeout)
        urllib.request.urlopen("https://tnrsapi.xyz", timeout=timeout)
        return True
    except Exception:
        return False
    finally:
        socket.setdefaulttimeout(old_timeout)


def TNRS_core(
    data_json: Optional[str] = None,
    sources: Union[str, list] = "wcvp,wfo",
    classification: str = "wfo",
    mode: str = "resolve",
    matches: str = "best",
    accuracy: Optional[float] = None,
    url: str = "https://tnrsapi.xyz/tnrs_api.php",
) -> Optional[pd.DataFrame]:
    if isinstance(sources, (list, tuple)):
        sources = ",".join(sources)

    headers = {
        "Accept": "application/json",
        "Content-Type": "application/json",
        "charset": "UTF-8",
    }

    opts = {
        "sources": sources,
        "class": classification,
        "mode": mode,
        "matches": matches,
    }
    if accuracy is not None:
        opts["acc"] = accuracy

    if data_json is None:
        input_json = json.dumps({"opts": opts})
    else:
        input_json = json.dumps({"opts": opts, "data": json.loads(data_json)})

    try:
        req = urllib.request.Request(
            url,
            data=input_json.encode("utf-8"),
            headers=headers,
            method="POST",
        )
        with urllib.request.urlopen(req, timeout=120) as response:
            status_code = response.status
            raw_content = response.read().decode("utf-8")

        if status_code != 200:
            print(f"Problem with the API: HTTP Status {status_code}")
            print(raw_content)
            return None

        results_raw = json.loads(raw_content)
        results = pd.DataFrame(results_raw)
        return results

    except urllib.error.URLError as e:
        print(f"There appears to be a problem reaching the API: {e}")
        return None
    except (socket.timeout, TimeoutError) as e:
        print(f"Timeout while contacting the API: {e}")
        return None
    except json.JSONDecodeError as e:
        print(f"There seems to be a problem with the query, which returned: {e}")
        return None


def TNRS_base(
    taxonomic_names: Union[list, pd.DataFrame],
    sources: Union[str, list] = "wcvp,wfo",
    classification: str = "wfo",
    mode: str = "resolve",
    matches: str = "best",
    accuracy: Optional[float] = None,
    skip_internet_check: bool = False,
) -> Optional[pd.DataFrame]:
    if not skip_internet_check:
        if not _check_internet():
            print(
                "This function requires internet access, please check your connection."
            )
            return None

    if isinstance(taxonomic_names, list):
        taxonomic_names = pd.DataFrame(
            {
                "ID": range(1, len(taxonomic_names) + 1),
                "Name": taxonomic_names,
            }
        )

    name_col = taxonomic_names.columns[1]

    if taxonomic_names[name_col].str.contains("|", regex=False).any():
        print("[WARNING] A pipe was found in the supplied names. Removing it.")
        taxonomic_names[name_col] = taxonomic_names[name_col].str.replace(
            "|", "", regex=False
        )

    if accuracy is not None:
        if not isinstance(accuracy, (int, float)) or not (0 <= accuracy <= 1):
            raise ValueError(
                "accuracy should be either numeric between 0 and 1, or None"
            )

    data_json = json.dumps(taxonomic_names.values.tolist())

    results = TNRS_core(
        data_json=data_json,
        sources=sources,
        classification=classification,
        mode=mode,
        matches=matches,
        accuracy=accuracy,
    )

    if results is None:
        return None

    score_cols = [col for col in results.columns if col.endswith("_score")]
    for col in score_cols:
        results[col] = pd.to_numeric(results[col], errors="coerce")

    return results


_VALID_SOURCES = {"wfo", "wcvp", "cact"}
_VALID_CLASSIFICATIONS = {"wfo"}
_VALID_MODES = {"resolve", "parse"}
_VALID_MATCHES = {"best", "all"}

_MAX_ATTEMPTS = 3
_TIMEOUT_SECS = 20 * 60


def _call_with_retry(
    taxonomic_names,
    sources,
    classification,
    mode,
    matches,
    accuracy,
    max_attempts=_MAX_ATTEMPTS,
    timeout=_TIMEOUT_SECS,
    retry_delay: float = 5,
):
    """Call TNRS_base with retry logic. Returns DataFrame or None.

    Each retry waits ``retry_delay * (attempt - 1)`` seconds before the
    next attempt (5s, 10s, ...), matching the backoff used by
    ``blast_put_get._urlopen_with_retry``.
    """
    for attempt in range(1, max_attempts + 1):
        if attempt > 1:
            print(f"  Retry attempt {attempt} of {max_attempts}")
            time.sleep(retry_delay * (attempt - 1))
        try:
            result = TNRS_base(
                taxonomic_names=taxonomic_names,
                sources=sources,
                classification=classification,
                mode=mode,
                matches=matches,
                accuracy=accuracy,
                skip_internet_check=True,
            )
            if result is not None and len(result) > 0:
                return result
            print("  Query succeeded but returned empty result. Retrying...")
        except Exception as e:
            print(f"  TNRS query failed: {e}")
    return None


def _compute_cache_key(names: list, sources: str, accuracy) -> str:
    """Compute a hash key from input names + params for cache validation."""
    payload = json.dumps({"names": names, "sources": sources, "accuracy": accuracy})
    return hashlib.sha256(payload.encode("utf-8")).hexdigest()[:16]


def TNRS_cached(
    taxonomic_names: list,
    sources: str = "wcvp,wfo",
    accuracy: Optional[float] = None,
    cache_dir: Optional[Union[str, Path]] = None,
    name_limit: int = 5000,
    emit_log=None,
) -> Optional[pd.DataFrame]:
    """Batch TNRS with per-batch caching and two-pass retry.

    - Pass 1: process all batches; cache successes; collect failures.
    - Pass 2: retry failed batches once more (3 attempts each).
    - If any batch still fails after pass 2 → return None (abort).
    - On next run, cached batches are loaded directly (validated by hash).
    """
    if emit_log is None:
        def emit_log(msg, level=None):
            print(msg)

    if not _check_internet():
        emit_log("No internet connection. Cannot reach TNRS API.", "WARNING")
        return None

    names = [n.strip() for n in taxonomic_names]
    n_total = len(names)
    n_chunks = (n_total + name_limit - 1) // name_limit
    cache_key = _compute_cache_key(names, sources, accuracy)

    cache_path = Path(cache_dir) if cache_dir else None
    if cache_path:
        cache_path.mkdir(parents=True, exist_ok=True)
        meta_file = cache_path / "meta.json"
        if meta_file.exists():
            saved_meta = json.loads(meta_file.read_text(encoding="utf-8"))
            if saved_meta.get("cache_key") != cache_key:
                emit_log("Input changed since last run. Clearing TNRS cache.", "INFO")
                for f in cache_path.glob("batch_*.csv"):
                    f.unlink()
                meta_file.unlink()
        meta_file.write_text(
            json.dumps({"cache_key": cache_key, "n_chunks": n_chunks, "sources": sources, "accuracy": accuracy}),
            encoding="utf-8",
        )

    emit_log(f"TNRS: {n_total} names, {n_chunks} batch(es), sources={sources}, accuracy={accuracy}", "INFO")

    all_results = [None] * n_chunks
    failed_indices = []

    # Pass 1
    for i in range(n_chunks):
        batch_file = cache_path / f"batch_{i}.csv" if cache_path else None

        if batch_file and batch_file.exists():
            all_results[i] = pd.read_csv(batch_file)
            emit_log(f"  Batch {i+1}/{n_chunks}: loaded from cache", "INFO")
            continue

        start = i * name_limit
        end = min(start + name_limit, n_total)
        chunk_df = pd.DataFrame({"ID": range(start + 1, end + 1), "Name": names[start:end]})

        emit_log(f"  Batch {i+1}/{n_chunks}: querying ({end - start} names)...", "INFO")
        result = _call_with_retry(
            taxonomic_names=chunk_df,
            sources=sources,
            classification="wfo",
            mode="resolve",
            matches="best",
            accuracy=accuracy,
        )

        if result is not None and len(result) > 0:
            all_results[i] = result
            if batch_file:
                result.to_csv(batch_file, index=False)
            emit_log(f"  Batch {i+1}/{n_chunks}: success", "INFO")
        else:
            failed_indices.append(i)
            emit_log(f"  Batch {i+1}/{n_chunks}: failed after {_MAX_ATTEMPTS} attempts", "WARNING")

    # Pass 2: retry failed batches
    if failed_indices:
        emit_log(f"Retrying {len(failed_indices)} failed batch(es)...", "INFO")
        still_failed = []
        for i in failed_indices:
            start = i * name_limit
            end = min(start + name_limit, n_total)
            chunk_df = pd.DataFrame({"ID": range(start + 1, end + 1), "Name": names[start:end]})
            batch_file = cache_path / f"batch_{i}.csv" if cache_path else None

            emit_log(f"  Retry batch {i+1}/{n_chunks}...", "INFO")
            result = _call_with_retry(
                taxonomic_names=chunk_df,
                sources=sources,
                classification="wfo",
                mode="resolve",
                matches="best",
                accuracy=accuracy,
            )

            if result is not None and len(result) > 0:
                all_results[i] = result
                if batch_file:
                    result.to_csv(batch_file, index=False)
                emit_log(f"  Batch {i+1}/{n_chunks}: recovered", "INFO")
            else:
                still_failed.append(i)

        if still_failed:
            failed_names_range = f"batch(es) {[i+1 for i in still_failed]}"
            emit_log(
                f"TNRS aborted: {failed_names_range} still failed. "
                f"Cached results preserved. Re-run to retry remaining batches.",
                "WARNING",
            )
            return None

    return pd.concat(all_results, ignore_index=True)


def TNRS(
    taxonomic_names: Union[list, pd.DataFrame],
    sources: Union[str, list] = "wcvp,wfo",
    classification: str = "wfo",
    mode: str = "resolve",
    matches: str = "best",
    accuracy: Optional[float] = None,
    skip_internet_check: bool = False,
    name_limit: int = 5000,
) -> Optional[pd.DataFrame]:
    if not skip_internet_check:
        if not _check_internet():
            print(
                "This function requires internet access, please check your connection."
            )
            return None

    if isinstance(taxonomic_names, list):
        taxonomic_names = pd.DataFrame(
            {
                "ID": range(1, len(taxonomic_names) + 1),
                "Name": taxonomic_names,
            }
        )

    if name_limit > 5000:
        print("name_limit cannot exceed 5000, fixing")
        name_limit = 5000

    if accuracy is not None:
        if not isinstance(accuracy, (int, float)) or not (0 <= accuracy <= 1):
            raise ValueError(
                "accuracy should be either numeric between 0 and 1, or None"
            )

    if isinstance(sources, str):
        sources_list = [s.strip() for s in sources.split(",")]
    else:
        sources_list = list(sources)
    if not set(sources_list).issubset(_VALID_SOURCES):
        print(f"Invalid source(s) specified. Current options are: {_VALID_SOURCES}")
        return None

    if classification not in _VALID_CLASSIFICATIONS:
        print(
            f"Invalid classification specified. Current options are: {_VALID_CLASSIFICATIONS}"
        )
        return None

    if mode not in _VALID_MODES:
        print(f"Invalid mode specified. Current options are: {_VALID_MODES}")
        return None

    if matches not in _VALID_MATCHES:
        print(f"Invalid matches specified. Current options are: {_VALID_MATCHES}")
        return None

    sources_str = ",".join(sources_list)

    n_total = len(taxonomic_names)

    if n_total <= name_limit:
        return _call_with_retry(
            taxonomic_names=taxonomic_names,
            sources=sources_str,
            classification=classification,
            mode=mode,
            matches=matches,
            accuracy=accuracy,
        )

    n_chunks = (n_total + name_limit - 1) // name_limit
    print(
        f"Splitting {n_total} names into {n_chunks} batches of up to {name_limit} each..."
    )

    results = None
    failed_batches = []
    for i in range(n_chunks):
        start = i * name_limit
        end = min((i + 1) * name_limit, n_total)
        chunk = taxonomic_names.iloc[start:end]

        chunk_result = _call_with_retry(
            taxonomic_names=chunk,
            sources=sources_str,
            classification=classification,
            mode=mode,
            matches=matches,
            accuracy=accuracy,
        )

        if chunk_result is None or len(chunk_result) == 0:
            print(f"Batch {i + 1}/{n_chunks} failed after retries, excluding {end - start} names.")
            failed_batches.append(i + 1)
            continue

        if results is None:
            results = chunk_result
        else:
            results = pd.concat([results, chunk_result], ignore_index=True)

        sys.stdout.write(f"\r  Batch {i + 1}/{n_chunks} completed")
        sys.stdout.flush()

    sys.stdout.write("\n")
    sys.stdout.flush()

    if failed_batches:
        print(f"Failed batches: {failed_batches}")

    return results


def TNRS_robust(
    taxonomic_names: Union[list, pd.DataFrame],
    sources: Union[str, list] = "wcvp,wfo",
    classification: str = "wfo",
    mode: str = "resolve",
    matches: str = "best",
    accuracy: Optional[float] = None,
    skip_internet_check: bool = False,
    name_limit: int = 5000,
    attempts: int = 10,
) -> Optional[pd.DataFrame]:
    if not skip_internet_check:
        if not _check_internet():
            print(
                "This function requires internet access, please check your connection."
            )
            return None

    if isinstance(taxonomic_names, list):
        taxonomic_names = pd.DataFrame(
            {
                "ID": range(1, len(taxonomic_names) + 1),
                "Name": taxonomic_names,
            }
        )

    if name_limit > 5000:
        print("name_limit cannot exceed 5000, fixing")
        name_limit = 5000

    if accuracy is not None:
        if not isinstance(accuracy, (int, float)) or not (0 <= accuracy <= 1):
            raise ValueError(
                "accuracy should be either numeric between 0 and 1, or None"
            )

    if isinstance(sources, str):
        sources_list = [s.strip() for s in sources.split(",")]
    else:
        sources_list = list(sources)
    if not set(sources_list).issubset(_VALID_SOURCES):
        print(f"Invalid source(s) specified. Current options are: {_VALID_SOURCES}")
        return None

    if classification not in _VALID_CLASSIFICATIONS:
        print(
            f"Invalid classification specified. Current options are: {_VALID_CLASSIFICATIONS}"
        )
        return None

    if mode not in _VALID_MODES:
        print(f"Invalid mode specified. Current options are: {_VALID_MODES}")
        return None

    if matches not in _VALID_MATCHES:
        print(f"Invalid matches specified. Current options are: {_VALID_MATCHES}")
        return None

    first_stab = TNRS(
        taxonomic_names=taxonomic_names,
        sources=sources,
        classification=classification,
        mode=mode,
        matches=matches,
        accuracy=accuracy,
        skip_internet_check=True,
        name_limit=name_limit,
    )

    if first_stab is None:
        return None

    name_col = first_stab.columns[1]

    bad_mask = (first_stab[name_col] == first_stab["Unmatched_terms"]) & first_stab[
        "Overall_score"
    ].notna()

    good_mask = (first_stab[name_col] != first_stab["Unmatched_terms"]) | (
        (first_stab[name_col] == first_stab["Unmatched_terms"])
        & first_stab["Overall_score"].isna()
    )

    bad_output = first_stab[bad_mask].copy()
    good_output = first_stab[good_mask].copy()

    if len(bad_output) == 0:
        return first_stab

    print(f"Detected {len(bad_output)} suspicious results. Re-doing.")

    for attempt in range(attempts):
        if len(bad_output) == 0:
            break

        name_subset = bad_output.iloc[:, :2]

        revised_output = TNRS(
            taxonomic_names=name_subset,
            sources=sources,
            classification=classification,
            mode=mode,
            matches=matches,
            accuracy=accuracy,
            skip_internet_check=True,
            name_limit=name_limit,
        )

        if revised_output is None:
            print(f"  Retry attempt {attempt + 1} failed, continuing with remaining...")
            continue

        bad_mask2 = (
            revised_output[name_col] == revised_output["Unmatched_terms"]
        ) & revised_output["Overall_score"].notna()

        good_mask2 = (revised_output[name_col] != revised_output["Unmatched_terms"]) | (
            (revised_output[name_col] == revised_output["Unmatched_terms"])
            & revised_output["Overall_score"].isna()
        )

        ok_revised = revised_output[good_mask2]
        bad_output = revised_output[bad_mask2]

        good_output = pd.concat([good_output, ok_revised], ignore_index=True)

        if len(bad_output) == 0:
            print(f"  All suspicious results resolved after {attempt + 1} attempt(s).")
        elif attempt == attempts - 1:
            print(
                f"  {len(bad_output)} results still suspicious after {attempts} attempts, discarding."
            )

    return good_output


def TNRS_synonyms(
    taxonomic_name: Union[str, list, pd.DataFrame],
    source: str = "wcvp",
    skip_internet_check: bool = False,
) -> Optional[pd.DataFrame]:
    if not skip_internet_check:
        if not _check_internet():
            print(
                "This function requires internet access, please check your connection."
            )
            return None

    if isinstance(taxonomic_name, str):
        taxonomic_name = pd.DataFrame({"ID": [1], "Name": [taxonomic_name]})
    elif isinstance(taxonomic_name, list):
        if len(taxonomic_name) != 1:
            print("This function can only take one taxonomic name at a time.")
            return None
        taxonomic_name = pd.DataFrame({"ID": [1], "Name": taxonomic_name})
    elif isinstance(taxonomic_name, pd.DataFrame):
        if len(taxonomic_name) != 1:
            print("This function can only take one taxonomic name at a time.")
            return None

    if source not in _VALID_SOURCES:
        print(
            f"Source '{source}' is not a valid option. Please choose from {_VALID_SOURCES}"
        )
        return None

    data_json = json.dumps(taxonomic_name.values.tolist())

    results = TNRS_core(
        data_json=data_json,
        sources=source,
        classification=None,
        mode="syn",
        matches=None,
        accuracy=None,
    )

    return results
