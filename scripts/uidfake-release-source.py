#!/usr/bin/env python3
"""Validate the successful kernel job before publishing an existing artifact."""
import json
import os
import subprocess

run_id = os.environ['SOURCE_RUN_INPUT']
assert run_id.isdigit(), 'Invalid source run ID'
repo = os.environ['GITHUB_REPOSITORY']


def api(path):
    return json.loads(subprocess.check_output(['gh', 'api', f'repos/{repo}/{path}']))


source = api(f'actions/runs/{run_id}')
assert source['head_branch'] == os.environ['GITHUB_REF_NAME']
assert source['path'] == '.github/workflows/main.yml'
jobs = api(f'actions/runs/{run_id}/jobs?per_page=100')['jobs']
builds = [j for j in jobs if j['name'].startswith('build-android14-6-1 / build ')]
assert len(builds) == 1 and builds[0]['conclusion'] == 'success', 'Kernel build did not succeed'
values = dict(BUILD_RUN_ID=run_id, BUILD_SOURCE_SHA=source['head_sha'],
              BUILD_RUN_NUMBER=str(source['run_number']),
              BUILD_RUN_ATTEMPT=str(source['run_attempt']), BUILD_JOB_URL=builds[0]['html_url'])
with open(os.environ['GITHUB_ENV'], 'a') as env:
    for key, value in values.items():
        env.write(f'{key}={value}\n')
print(json.dumps(values, indent=2))
