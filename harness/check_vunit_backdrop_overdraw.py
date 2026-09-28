"""Screen source-attributed V-Unit margin changes against repeated backdrop strips.

This joins already-qualified overdraw reports with saved original DMA. It is a
negative diagnostic gate, not permission to promote or render a candidate.
"""
import argparse
import json
from pathlib import Path

from screen_vunit_panorama_strips import sha, strips
from vunit_display_scene import load


def check_attribution(report, groups):
    if not report.get('passed'):
        raise ValueError('source overdraw report did not pass')
    rows = report.get('changed_prior_game_dma_attribution',
                      report.get('changed_prior_game_current_dma_attribution'))
    guest = report.get('changed_prior_game_pixels',
                       report.get('changed_prior_game_owned_pixels'))
    if rows is None or guest is None or sum(r['changed_pixels'] for r in rows) != guest:
        raise ValueError('incomplete original DMA attribution')
    by_ordinal = {ordinal: group for group in groups for ordinal in group['ordinals']}
    admitted, rejected = [], []
    for row in rows:
        item = dict(row)
        item['strip_ordinals'] = by_ordinal.get(row['original_dma_ordinal'], {}).get('ordinals')
        (admitted if item['strip_ordinals'] else rejected).append(item)
    return dict(prior_game_pixels=guest,
                structurally_backdrop_pixels=sum(r['changed_pixels'] for r in admitted),
                unclassified_game_pixels=sum(r['changed_pixels'] for r in rejected),
                backdrop_dma=admitted, unclassified_dma=rejected)


def screen(pairs):
    results = []
    for report_path, run in pairs:
        report_path, run = Path(report_path), Path(run)
        report = json.loads(report_path.read_text(encoding='utf-8'))
        scene = load(run)
        source = run.parent / 'report.json'
        source_report = json.loads(source.read_text(encoding='utf-8'))
        if not source_report.get('passed'):
            raise ValueError(f'source replay did not pass: {source}')
        # The overlap report's `source_report` is its separate source-time RAM
        # tap. Its original DMA came from the matched `control_report`.
        expected_source = report['sha256'].get(
            'original_source_report', report['sha256'].get('control_report'))
        if expected_source is None or sha(source) != expected_source:
            raise ValueError(f'source replay hash differs: {source}')
        dma = run / 'capture/quads.bin'
        expected = report['sha256']['original_dma']
        if sha(dma) != expected:
            raise ValueError(f'original DMA hash differs: {dma}')
        completed = report.get('completed_frame', report.get('frame'))
        if int(scene.report['completed_frame']) != int(completed):
            raise ValueError(f'completed frame differs: {report_path}')
        groups = strips(scene.current)
        attribution = check_attribution(report, groups)
        results.append(dict(source_report=str(report_path.resolve()),
                            original_run=str(run.resolve()), completed_frame=completed,
                            prior_host_pixels=report.get('changed_prior_host_pixels',
                                                     report.get('changed_prior_host_owned_pixels')),
                            attribution=attribution, backdrop_strips=groups,
                            sha256={'overdraw_report': sha(report_path),
                                    'source_replay_report': sha(source),
                                    'original_dma': sha(dma)}))
    return dict(schema=1, analysis_completed=True,
                all_prior_game_overdraw_structural_backdrop=all(
                    item['attribution']['unclassified_game_pixels'] == 0 for item in results),
                scope='Selected source-qualified frames only. A structural strip is '
                      'not proof of visual safety; prior host pixels, depth, completed '
                      'appearance, transitions and other courses remain independent.',
                samples=results)


def main():
    ap = argparse.ArgumentParser(description=__doc__)
    ap.add_argument('--sample', nargs=2, metavar=('OVERDRAW_JSON', 'ORIGINAL_RUN'),
                    action='append', required=True)
    ap.add_argument('--report', type=Path, required=True)
    args = ap.parse_args()
    if args.report.exists():
        raise ValueError('refusing to overwrite backdrop-overdraw screen')
    result = screen(args.sample)
    args.report.parent.mkdir(parents=True, exist_ok=True)
    args.report.write_text(json.dumps(result, indent=2) + '\n', encoding='utf-8')
    print('SCREEN', len(result['samples']), 'samples',
          'unclassified', sum(x['attribution']['unclassified_game_pixels']
                              for x in result['samples']))


if __name__ == '__main__':
    main()
