"""Validate provenance and inspect every turn for train/validation overlap."""
import csv
import io
import json
from collections import Counter
from difflib import SequenceMatcher

from build_v2 import DATA, HERE, ROOT, CHARACTER_ROWS, EXTRA_PROMPT, MULTI_ROWS, TRANSFORMS, transcript, save
from build_selection import digest, normalize, content_only, encode_json


def texts(row):
    return [row["prompt_tr"]] + [m["content"] for m in row["messages"]]


def main():
    manifest = json.loads((DATA / "selection-manifest.json").read_text(encoding="utf-8"))
    for filename, info in manifest["artifacts"].items():
        assert digest((DATA / filename).read_bytes()) == info["sha256"], filename
    rows = [json.loads(line) for line in (DATA / "prompts-100.jsonl").read_text(encoding="utf-8").splitlines()]
    assert len(rows) == len({r["id"] for r in rows}) == 100
    assert Counter(r["split"] for r in rows) == {"train": 80, "validation": 20}
    source_pools = {}
    for path, info in manifest["inputs"].items():
        raw = (ROOT / path).read_bytes()
        assert digest(raw) == info["sha256_bytes"]
        source_pools[path] = {r["id"]: r for r in csv.DictReader(io.StringIO(raw.decode("utf-8-sig")))}
    groups = {}
    for row in rows:
        assert row["messages"][-1]["role"] == "user"
        assert [m["role"] for m in row["messages"]] in [["user"], ["user", "assistant", "user"]]
        assert all(m["content"].strip() and "\ufffd" not in m["content"] for m in row["messages"])
        canonical = json.dumps(row["messages"], ensure_ascii=False, separators=(",", ":")).encode("utf-8")
        assert digest(canonical) == row["input_messages_sha256"]
        assert row["answer_status"] == "not-generated"
        if row["origin"] != "new-agent-authored":
            historical = json.loads(source_pools[row["source_path"]][row["source_id"]]["messages"])
            prompt = historical[0]["content"]
            assert digest(prompt.encode("utf-8")) == row["source_prompt_sha256"]
            if row["is_multi_turn"]:
                assert row["messages"][0]["content"] == prompt
                assert row["messages"][1:] == MULTI_ROWS[row["id"]][3]
                assert row["prompt_tr"] == transcript(row["messages"])
            elif row["id"] in TRANSFORMS:
                assert row["prompt_tr"] == prompt + "\n" + TRANSFORMS[row["id"]]
            else:
                assert row["prompt_tr"] == prompt
        else:
            expected = EXTRA_PROMPT if row["id"] == "me-081" else CHARACTER_ROWS[row["id"]][3]
            assert row["prompt_tr"] == expected
        groups.setdefault(row["scenario_group_id"], set()).add(row["split"])
        assert len(groups[row["scenario_group_id"]]) == 1
    for category in manifest["category_counts"]:
        assert Counter(r["split"] for r in rows if r["category"] == category) == {"train": 8, "validation": 2}
    for split, count in [("train", 80), ("validation", 20)]:
        subset = [json.loads(line) for line in (DATA / f"{split}-prompts-{count}.jsonl").read_text(encoding="utf-8").splitlines()]
        assert subset == [r for r in rows if r["split"] == split]
    train, validation = ([r for r in rows if r["split"] == s] for s in ("train", "validation"))
    exact = []
    closest = []
    for val in validation:
        scores = []
        for tr in train:
            best = 0.0
            for a in texts(val):
                for b in texts(tr):
                    if normalize(a) == normalize(b):
                        exact.append({"validation": val["id"], "train": tr["id"]})
                    best = max(best, SequenceMatcher(None, content_only(a), content_only(b), autojunk=False).ratio())
            scores.append({"validation_id": val["id"], "train_id": tr["id"], "max_turn_similarity": round(best, 4)})
        closest.extend(sorted(scores, key=lambda r: r["max_turn_similarity"], reverse=True)[:3])
    assert not exact, exact
    assert not ({(r["source_path"], r["source_id"]) for r in train} & {(r["source_path"], r["source_id"]) for r in validation})
    overlap = json.loads((DATA / "overlap-report.json").read_text(encoding="utf-8"))
    cross_flags = [p for p in overlap["turn_aware_flags"] if p["cross_split"]]
    # Freeze only after manual resolution. Currently require no cross-split flags.
    assert not cross_flags, cross_flags
    old_audit = json.loads((HERE / "data/audit-report.json").read_text(encoding="utf-8"))
    benchmark_rows = []
    for path, info in old_audit["benchmark_inputs"].items():
        raw = (ROOT / path).read_bytes()
        assert digest(raw) == info["sha256_bytes"]
        for b in csv.DictReader(io.StringIO(raw.decode("utf-8-sig"))):
            if b.get("prompt_tr"):
                benchmark_rows.append((path, b["id"], b["prompt_tr"]))
    b_exact, b_near = [], []
    for row in rows:
        for path, bid, prompt in benchmark_rows:
            for value in texts(row):
                a, b = normalize(value), normalize(prompt)
                if a == b:
                    b_exact.append({"id": row["id"], "benchmark": path, "benchmark_id": bid})
                else:
                    matcher = SequenceMatcher(None, a, b, autojunk=False)
                    if matcher.quick_ratio() >= .78:
                        score = matcher.ratio()
                        if score >= .78:
                            b_near.append({"id": row["id"], "benchmark": path, "benchmark_id": bid, "similarity": round(score, 4)})
    assert not b_exact, b_exact
    assert not b_near, b_near
    coverage = json.loads((DATA / "coverage-map.json").read_text(encoding="utf-8"))
    for spec in coverage.values():
        assert spec["train_ids"] and spec["validation_ids"]
        assert not set(spec["train_ids"]) & set(spec["validation_ids"])
    report = {"status": "passed", "version": "prompt-selection-v2", "rows": 100,
              "split_counts": manifest["split_counts"], "cross_split_pairs": 1600,
              "full_conversations_and_turns_checked": True, "cross_split_exact_turn_or_prompt_matches": exact,
              "cross_split_near_flags": cross_flags, "cross_split_group_overlap": 0,
              "cross_split_source_identity_overlap": 0, "historical_target_answers_copied": 0,
              "historical_provenance_and_authored_text_binding": "passed",
              "benchmark_rows_checked": len(benchmark_rows), "benchmark_exact_matches": b_exact, "benchmark_near_matches": b_near,
              "closest_train_neighbors": closest, "requirements_mapped": list(coverage),
              "within_split_review_flags": overlap["turn_aware_flags"],
              "limitation": "Detected overlap only; manual scenario review is separate, no mathematical proof of universal semantic independence."}
    save(DATA / "audit-report.json", encode_json(report))
    print(json.dumps({k: report[k] for k in ["status", "split_counts", "cross_split_exact_turn_or_prompt_matches", "cross_split_near_flags", "benchmark_exact_matches", "benchmark_near_matches"]}, indent=2))


if __name__ == "__main__":
    main()
