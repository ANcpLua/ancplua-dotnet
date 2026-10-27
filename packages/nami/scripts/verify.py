"""Run packaged examples in disposable workspaces; keep no test-report history."""
import argparse
import json
from pathlib import Path
import shutil
import subprocess
import tempfile
import xml.etree.ElementTree as ET

ROOT = Path(__file__).resolve().parents[1]


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('scope', choices=['fixtures', 'union'])
    args = parser.parse_args()
    with tempfile.TemporaryDirectory(prefix='nami-plugin-check-') as temporary:
        directory = Path(temporary)
        if args.scope == 'union':
            code = subprocess.run(['python3', '-B', str(ROOT / 'plugins/nami/skills/csharp-union-types/scripts/verify.py'),
                                   '--report', str(directory / 'report.json')], cwd=ROOT).returncode
            report = json.loads((directory / 'report.json').read_text())
            return code if code else 0 if report.get('passed') and report.get('checks') else 1
        source = ROOT / 'plugins/nami/skills/fixture-scope/examples'
        shutil.copytree(source, directory / 'example')
        shutil.copyfile(ROOT / 'global.json', directory / 'global.json')
        code = subprocess.run(['dotnet', 'test', '--project', str(directory / 'example/FixtureExamples.csproj'),
                               '--report-trx', '--results-directory', str(directory / 'results')], cwd=directory).returncode
        reports = list((directory / 'results').glob('*.trx'))
        if code or not reports:
            return code or 1
        namespace = {'t': 'http://microsoft.com/schemas/VisualStudio/TeamTest/2010'}
        results = [r for report in reports for r in ET.parse(report).findall('.//t:UnitTestResult', namespace)]
        if len(results) != 21 or any(r.get('outcome') != 'Passed' for r in results):
            print('Fixture verification did not execute all 21 expected passing tests')
            return 1
        print('Fixture verification: 21 passed; temporary workspace removed on return')
        return 0


if __name__ == '__main__':
    raise SystemExit(main())
