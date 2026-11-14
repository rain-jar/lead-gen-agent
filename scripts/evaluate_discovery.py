"""Case-level offline diagnostics for a saved discovery run."""
from __future__ import annotations
import collections
import json
import sys
from pathlib import Path
from score_search_provider_benchmark import normalize_url

ROOT=Path(__file__).resolve().parents[1]

def rows(path):
    return [json.loads(s) for s in path.read_text(encoding='utf-8').split('\n') if s]

def evaluate(run: Path):
    benchmark=json.loads((ROOT/'docs/benchmark/v2/benchmark.json').read_text())
    candidates=rows(run/'candidates.jsonl')
    excluded=rows(run/'excluded.jsonl')
    watch=rows(run/'watchlist.jsonl')
    by_url=collections.defaultdict(list)
    for bucket, data in (('candidate',candidates),('excluded',excluded)):
        for row in data:
            for source in row['sources']:
                by_url[normalize_url(source['url'])].append((bucket,row))
    case_rows=[]
    for opp in benchmark['opportunities']:
        urls={normalize_url(s['url']) for s in opp['sources']}
        urls.update(normalize_url(s['url']) for case in benchmark['cases'] if case['opportunity_id']==opp['opportunity_id'] for s in case['sources'])
        matched={(bucket, id(row)): (bucket,row) for url in urls for bucket,row in by_url.get(url,[])}
        case_rows.append({'opportunity_id':opp['opportunity_id'],'edition_key':opp['edition_key'],'split':opp['split'],'expected_discovery':opp['expected_discovery'],'candidate_count':sum(bucket=='candidate' for bucket,_ in matched.values()),'candidate_windows':sorted({row['window_status'] for bucket,row in matched.values() if bucket=='candidate'}),'excluded_count':sum(bucket=='excluded' for bucket,_ in matched.values()),'excluded_reasons':sorted({row.get('exclude_reason') for bucket,row in matched.values() if bucket=='excluded'}),'candidate_keys':sorted({row['dedupe_key'] for bucket,row in matched.values() if bucket=='candidate'})})
    live=[r for r in case_rows if r['split']=='live' and r['expected_discovery']=='eligible' and r['candidate_count']]
    traps=[r for r in case_rows if r['split']=='live' and r['expected_discovery']=='ineligible']
    social=[r for r in candidates if r['page_kind']=='social']
    programs=[r for r in candidates if r['page_kind']=='program' and r['window_status']=='in_window']
    return {'case_rows':case_rows,'a3_live_surfaced':len(live),'a3_bad_window':[r['opportunity_id'] for r in live if any(x not in ('in_window','pending_date') for x in r['candidate_windows']) or r['excluded_count']],'a4_ineligible_traps':traps,'a6_multi_record_eligible':[{'edition_key':r['edition_key'],'candidate_count':r['candidate_count']} for r in case_rows if r['expected_discovery']=='eligible' and r['candidate_count']>1],'a7_program_in_window':len(programs),'a7_social_count':len(social),'a7_social_missing_alternate':sum(not r['needs_alternate_source'] for r in social),'a7_social_missing_watch':sum(not any(w['dedupe_key']==r['dedupe_key'] and 'alternate_source_needed' in w['reasons'] for w in watch) for r in social),'query_family_unique_editions':dict(collections.Counter(f for r in candidates for f in r['query_families'])),'conflict_flags':dict(collections.Counter(reason for r in candidates for reason in r['conflict_reasons']))}

if __name__=='__main__':
    print(json.dumps(evaluate(Path(sys.argv[1])),indent=2,ensure_ascii=False))
