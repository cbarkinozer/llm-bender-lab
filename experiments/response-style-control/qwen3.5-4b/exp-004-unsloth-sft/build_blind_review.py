"""Build the anonymous paired review CSV for exp-004."""
import csv, hashlib, json, random, re
from pathlib import Path

ROOT = Path(__file__).parent
RESULTS = ROOT / "results"
BENCH = ROOT.parent / "exp-002-communication-policy-benchmark" / "test.csv"
BASE = RESULTS / "benchmark-v2-base.jsonl"
CAND = RESULTS / "benchmark-v2-candidate.jsonl"
OUT = RESULTS / "benchmark-v2-blind-review"

def read_jsonl(path):
    return {r["id"]: r for r in (json.loads(x) for x in path.read_text(encoding="utf-8").splitlines() if x.strip())}

def social(s):
    return bool(re.search(r"(?:harika|güzel|mükemmel|tebrik|memnuniyetle|anlıyorum|haklısınız|çok iyi)", s, re.I))

def auto_fields(a, b):
    vals = {}
    for p, text in (("a", a), ("b", b)):
        vals[f"{p}_chars"] = len(text); vals[f"{p}_words"] = len(text.split()); vals[f"{p}_lines"] = text.count("\n") + 1
        vals[f"auto_{p}_social_preamble"] = social(text)
        vals[f"auto_{p}_anthropomorphic_claim"] = bool(re.search(r"(?:hissediyorum|seviyorum|üzülüyorum|bence benim|hayalim)", text, re.I))
        vals[f"auto_{p}_generic_closing"] = bool(re.search(r"(?:umarım|yardımcı olabilirim|başka sorunuz)", text, re.I))
    vals["char_delta_a_minus_b"] = vals["a_chars"] - vals["b_chars"]
    vals["word_delta_a_minus_b"] = vals["a_words"] - vals["b_words"]
    vals["char_ratio_a_over_b"] = round(vals["a_chars"] / vals["b_chars"], 4) if vals["b_chars"] else None
    vals["shorter_output"] = "a" if vals["a_chars"] < vals["b_chars"] else ("b" if vals["b_chars"] < vals["a_chars"] else "tie")
    return vals

def main():
    bench = list(csv.DictReader(BENCH.open(encoding="utf-8", newline="")))
    base, cand = read_jsonl(BASE), read_jsonl(CAND)
    if set(base) != set(cand) or set(base) != {r["id"] for r in bench}: raise SystemExit("ID sets differ")
    rng = random.Random(3407); rows=[]; mapping={}
    for item in bench:
        ident=item["id"]; swap=bool(rng.getrandbits(1)); a=cand[ident]["output"] if swap else base[ident]["output"]; b=base[ident]["output"] if swap else cand[ident]["output"]
        mapping[ident]={"output_a_role":"candidate" if swap else "base", "output_b_role":"base" if swap else "candidate"}
        d=auto_fields(a,b)
        rows.append({"id":ident,"category":item["capability_family"],"prompt_tr":item["prompt_tr"],"output_a":a,"output_b":b,**{f"output_{k}":v for k,v in d.items() if k in ("a_chars","b_chars","a_words","b_words","a_lines","b_lines")},**{k:v for k,v in d.items() if k not in ("a_chars","b_chars","a_words","b_words","a_lines","b_lines")},"pairwise_preference":"","task_completion_a":"","task_completion_b":"","directness_a":"","directness_b":"","neutrality_a":"","neutrality_b":"","brevity_a":"","brevity_b":"","helpfulness_a":"","helpfulness_b":"","judgment_a":"","judgment_b":"","calibration_a":"","calibration_b":"","non_sycophancy_a":"","non_sycophancy_b":"","non_anthropomorphism_a":"","non_anthropomorphism_b":"","clarification_discipline_a":"","clarification_discipline_b":"","review_notes":""})
    OUT.mkdir(parents=True, exist_ok=True)
    fields=list(rows[0]);
    with (OUT/"argilla-review.csv").open("w",encoding="utf-8-sig",newline="") as f: csv.DictWriter(f,fieldnames=fields).writeheader(); csv.DictWriter(f,fieldnames=fields).writerows(rows)
    (OUT/"blind-mapping-sealed.json").write_text(json.dumps(mapping,ensure_ascii=False,indent=2)+"\n",encoding="utf-8")
    meta={"items":len(rows),"seed":3407,"benchmark_sha256":hashlib.sha256(BENCH.read_bytes()).hexdigest(),"base_sha256":hashlib.sha256(BASE.read_bytes()).hexdigest(),"candidate_sha256":hashlib.sha256(CAND.read_bytes()).hexdigest()}
    (OUT/"manifest.json").write_text(json.dumps(meta,ensure_ascii=False,indent=2)+"\n",encoding="utf-8")
    print(json.dumps(meta,ensure_ascii=False,indent=2))
if __name__ == "__main__": main()
