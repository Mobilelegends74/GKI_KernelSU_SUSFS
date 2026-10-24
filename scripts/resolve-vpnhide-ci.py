#!/usr/bin/env python3
"""Resolve the latest successful upstream main CI to an immutable source SHA."""
import json
import re
import subprocess


def resolve(run=subprocess.check_output):
    data = json.loads(run(['gh', 'api',
        'repos/okhsunrog/vpnhide/actions/workflows/ci.yml/runs?branch=main&status=success&per_page=100'], text=True))
    runs = [r for r in data['workflow_runs']
            if r.get('status') == 'completed' and r.get('conclusion') == 'success'
            and r.get('head_branch') == 'main' and r.get('event') in ('push', 'workflow_dispatch')
            and r.get('head_repository', {}).get('full_name') == 'okhsunrog/vpnhide']
    if not runs:
        raise ValueError('No successful upstream main CI; refusing untested branch fallback')
    selected = max(runs, key=lambda r: r['run_number'])
    sha = selected['head_sha']
    assert re.fullmatch('[0-9a-f]{40}', sha), 'Invalid upstream source SHA'
    run_id = str(selected['id'])
    assert run_id.isdigit()
    return {'vpnhide_sha': sha, 'vpnhide_run_id': run_id,
            'vpnhide_run_url': 'https://github.com/okhsunrog/vpnhide/actions/runs/' + run_id}


if __name__ == '__main__':
    print(json.dumps(resolve()))
