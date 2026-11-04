#!/usr/bin/env python3
"""Build a single resource-vs-load report for one test execution."""

import csv
import json
import sys
from pathlib import Path


def values(rows, field):
    return [float(row[field]) for row in rows if row.get(field)]


def average(items):
    return sum(items) / len(items) if items else 0.0


def metric(summary, name, value='value'):
    return (
        summary.get('k6', {})
        .get('metrics', {})
        .get(name, {})
        .get('values', {})
        .get(value, 0)
    )


def main():
    if len(sys.argv) != 2:
        raise SystemExit('Uso: report.py DIRETORIO_DA_EXECUCAO')

    directory = Path(sys.argv[1])
    monitor_file = directory / 'monitoramento.csv'
    summary_file = directory / 'k6-summary.json'

    with monitor_file.open(newline='') as file:
        rows = list(csv.DictReader(file))

    app_rows = [row for row in rows if row.get('name') == 'painel-focos-app']
    if not app_rows:
        raise SystemExit('Container painel-focos-app não encontrado no monitoramento.')

    with summary_file.open() as file:
        summary = json.load(file)

    memory = values(app_rows, 'mem_used_bytes')
    cpu = values(app_rows, 'cpu_percent')
    pids = values(app_rows, 'pids')
    resets = sum(
        1 for previous, current in zip(memory, memory[1:])
        if previous > 512 * 1024 * 1024 and current < previous * 0.5
    )

    report = {
        'users_configured': summary['test']['configured_vus'],
        'page': summary['test']['page'],
        'interactions': summary['test']['interactions'],
        'ramp_up': summary['test']['ramp_up'],
        'hold': summary['test']['hold'],
        'ramp_down': summary['test']['ramp_down'],
        'app_cpu_avg_pct': round(average(cpu), 2),
        'app_cpu_max_pct': round(max(cpu), 2),
        'app_memory_avg_bytes': round(average(memory)),
        'app_memory_max_bytes': round(max(memory)),
        'app_memory_max_pct': round(max(values(app_rows, 'mem_percent')), 2),
        'app_pids_max': int(max(pids)),
        'app_memory_reset_events': resets,
        'k6_vus_max': metric(summary, 'vus_max', 'max'),
        'k6_iterations': metric(summary, 'iterations', 'count'),
        'k6_checks_rate': metric(summary, 'checks', 'rate'),
        'k6_http_failed_rate': metric(summary, 'browser_http_req_failed', 'rate'),
        'k6_fcp_p95_ms': metric(summary, 'browser_web_vital_fcp', 'p(95)'),
    }

    with (directory / 'resource-report.json').open('w') as file:
        json.dump(report, file, indent=2)

    with (directory / 'resource-report.csv').open('w', newline='') as file:
        writer = csv.DictWriter(file, fieldnames=report.keys())
        writer.writeheader()
        writer.writerow(report)

    print(json.dumps(report, indent=2))


if __name__ == '__main__':
    main()
