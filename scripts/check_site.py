#!/usr/bin/env python3
"""Check generated content and built HTML against the supplied scientific data.

Run after generation and Hugo: ``python3 scripts/check_site.py public``.
Only the Python standard library is required.
"""

import gzip
import json
import sys
from collections import Counter, defaultdict
from fractions import Fraction
from html.parser import HTMLParser
from pathlib import Path
from urllib.parse import unquote, urlsplit

from generate_hall_pages import HUGO_ROOT


class Page(HTMLParser):
    """Collect table cells by section and local links from rendered HTML."""

    def __init__(self, path):
        super().__init__()
        self.section = None
        self.tables = defaultdict(list)
        self.links = set()
        self.row = None
        self.cell = None
        self.feed(path.read_text())

    def handle_starttag(self, tag, attrs):
        attrs = dict(attrs)
        if 'data-section-body' in attrs:
            self.section = attrs['data-section-body']
        for key in ('href', 'src'):
            if attrs.get(key):
                self.links.add(attrs[key])
        if tag == 'tr':
            self.row = []
        elif tag == 'td':
            self.cell = []

    def handle_data(self, data):
        if self.cell is not None:
            self.cell.append(data)

    def handle_endtag(self, tag):
        if tag == 'td' and self.cell is not None:
            self.row.append(' '.join(''.join(self.cell).split()))
            self.cell = None
        elif tag == 'tr' and self.row:
            self.tables[self.section].append(self.row)
            self.row = None


def read_data(name):
    """Read a copied gzipped dataset."""
    with gzip.open(HUGO_ROOT / 'static/data' / name) as stream:
        return json.load(stream)


def embedding_key(g, h, index, matrix, shift):
    """Identify an embedding without discarding its index or origin."""
    return (g, h, index, tuple(tuple(row) for row in matrix), tuple(shift))


def apply(matrix, shift, point):
    """Evaluate an exact affine map on a fractional-coordinate column."""
    return [sum(Fraction(x) * y for x, y in zip(row, point)) + Fraction(p)
            for row, p in zip(matrix, shift)]


def main():
    """Verify all page records, embedding multiplicities, and rendered links."""
    site = Path(sys.argv[1] if len(sys.argv) > 1 else 'public').resolve()
    base_path = urlsplit(sys.argv[2]).path.rstrip('/') if len(sys.argv) > 2 else ''
    basics = read_data('symmetry_basics.json.gz')
    transforms = read_data('transformations_hm_entry.json.gz')['data']['transformations_per_hm_entry']
    entries = {row['hall_entry']: row for row in basics['data']['spacegroups']}
    std_maps = {row['hall_entry']: row['hall_to_it_std_transform']['affine_transformation'] for row in transforms}
    transform_rows = {row['hall_entry']: row for row in reversed(transforms)}
    expected = Counter()
    seen = set()
    for row in transforms:
        g = row['hall_entry']
        for group in row['baernighausen']:
            h = group['target_hall_entry']
            if entries[g]['it_number'] == entries[h]['it_number']:
                continue
            for transform in group['transforms']:
                # Repeated HM aliases can repeat the exact same record.
                signature = (g, h, json.dumps(transform, sort_keys=True))
                if signature in seen:
                    continue
                seen.add(signature)
                affine = transform['affine_transformation']
                expected[embedding_key(g, h, transform['index'], affine['matrix'], affine['vector'])] += 1

    outgoing, incoming = Counter(), Counter()
    links = set()
    hall_paths = {f'{hall}.md' for hall in entries}
    assert {p.name for p in (HUGO_ROOT / 'content/hall').glob('*.md')} == hall_paths, 'Stale or missing Hall pages'
    for hall, source in entries.items():
        page = json.loads((HUGO_ROOT / 'content/hall' / f'{hall}.md').read_text())
        assert page['n_symops'] == len(source['symops'])
        assert len(page['symops_mod_centering']) * source['n_centering_translations'] == source['n_symops']
        assert page['hm_universal'] == page['hm_universal_unicode'] == source['hm_cctbx_universal']
        for actual, raw in zip(page['symops_mod_centering'], source['symops_mod_centering']):
            assert actual['xyz'] == raw['affine_transformation']['xyz']
        assert page['field_doc_urls']['symops'].endswith('/spacegroups/symops')
        for field, counter, forward in (('maximal_subgroup_mappings', outgoing, True), ('minimal_supergroup_mappings', incoming, False)):
            for mapping in page[field]:
                g, h = (hall, mapping['hall_key']) if forward else (mapping['hall_key'], hall)
                counter[embedding_key(g, h, mapping['index'], mapping['transformation_matrix'], mapping['origin_shift'])] += 1
                parent_branches = {wp['letter']: wp['first_orbit'] for wp in entries[g]['wyckoff']}
                for split in mapping['wyckoff_rows']:
                    assert split['g_first_orbit_xyz'] == parent_branches[split['g_wp']]
        # The same physical point must agree via STD and via the composed setting map.
        for mapping in page['setting_transforms']:
            a, b = std_maps[hall], std_maps[mapping['hall_key']]
            for q in ([Fraction(0)] * 3, [Fraction(1, 7), Fraction(2, 11), Fraction(3, 13)]):
                current = apply(a['matrix'], a['vector'], q)
                target = apply(b['matrix'], b['vector'], q)
                assert apply(mapping['transformation_matrix'], mapping['origin_shift'], current) == target
        rendered = Page(site / 'hall' / hall / 'index.html')
        links.update(rendered.links)
        assert len(rendered.tables['symops']) == source['n_pointgroup_symops']
        assert [row[1] for row in rendered.tables['symops']] == [op['affine_transformation']['xyz'] for op in source['symops_mod_centering']]
        assert len(rendered.tables['wyckoff']) == len(source['wyckoff'])
        for actual, wp in zip(rendered.tables['wyckoff'], sorted(source['wyckoff'], key=lambda wp: (not wp['letter'].islower(), wp['letter'].lower(), wp['letter']))):
            assert actual[:3] == [wp['letter'], str(wp['multiplicity']), wp['sitesym']]
            assert actual[3] == ' '.join(f"({op['xyz']})" for op in wp['orbit_mod_centering'])
        for actual, plane in zip(rendered.tables['harker'], source['harker_planes']):
            assert actual[1:] == [plane['algebraic'], ', '.join(map(str, plane['normal'])), ', '.join(plane['point'])]
        assert len(rendered.tables['harker']) == len(source['harker_planes'])
        normalizers = transform_rows[hall]
        euclidean = normalizers['euclidean_normalizer']['symops_mod_centering']
        affine = normalizers['affine_normalizer']['symops']
        normalizer_rows = rendered.tables['normalizer']
        for actual, op in zip(normalizer_rows, euclidean):
            assert actual[1] == op['affine_transformation']['xyz']
            assert actual[3] == str(op['sense'])
            assert actual[6] == ', '.join(op['origin_shift'])
            assert actual[9] == ', '.join(op['affine_transformation']['vector'])
        for actual, op in zip(normalizer_rows[len(euclidean):], affine):
            assert actual[1] == op['affine_transformation']['xyz']
            assert actual[4] == ('Yes' if op['affine_transformation']['is_orthogonal'] else 'No')
        assert len(normalizer_rows) == len(euclidean) + len(affine) + len(normalizers['continuous_normalizer']['basis_vectors'])

    assert outgoing == expected, f'Outgoing embeddings differ: missing {expected - outgoing}, extra {outgoing - expected}'
    assert incoming == expected, f'Incoming embeddings differ: missing {expected - incoming}, extra {incoming - expected}'

    pg_index = json.loads((HUGO_ROOT / 'static/data/pointgroup_index.json').read_text())
    slugs = {row['hm_symbol']: row['slug'] for row in pg_index}
    assert {p.stem for p in (HUGO_ROOT / 'content/pointgroup').glob('*.md')} == {'_index', *slugs.values()}
    for source in basics['data']['pointgroups']:
        rendered = Page(site / 'pointgroup' / slugs[source['hm_symbol']] / 'index.html')
        links.update(rendered.links)
        assert len(rendered.tables['symops']) == source['order']
        for actual, raw in zip(rendered.tables['conjugacy'], source['conjugacy_classes']):
            assert actual[2] == str(raw['representative'] + 1)
            assert actual[5] == ', '.join(str(i + 1) for i in raw['members'])
        for section, field in (('char_real', 'character_table_real'), ('char_complex', 'character_table_complex')):
            rows = rendered.tables[section]
            assert len(rows) == len(source[field])
            assert len({row[0] for row in rows}) == len(rows), (source['hm_symbol'], 'Ambiguous irrep labels')
            assert all('map[' not in cell for row in rows for cell in row)
        assert rendered.tables['symops'][0][5] == '0', 'Zero rotation sense must not be missing'

    for path in (site / 'index.html', site / 'pointgroup/index.html'):
        links.update(Page(path).links)
    for link in links:
        url = urlsplit(link)
        if url.scheme or url.netloc or not url.path:
            continue
        path = unquote(url.path)
        assert path.startswith(base_path + '/'), f'Link escaped site base: {link}'
        target = site / path[len(base_path):].lstrip('/')
        if url.path.endswith('/'):
            target /= 'index.html'
        assert target.is_file(), f'Broken local link: {link}'
    for index in ('index_it_number_to_std_spacegroups', 'index_setting_it_nc_to_spacegroups', 'index_hm_entry_to_spacegroups'):
        prefix = {'index_it_number_to_std_spacegroups': 'itn', 'index_setting_it_nc_to_spacegroups': 'nc', 'index_hm_entry_to_spacegroups': 'hm'}[index]
        for key, pos in basics['indicies'][index].items():
            slug = key.replace(' ', '').replace('/', ':') if prefix == 'hm' else key
            redirect = Page(site / prefix / slug / 'index.html')
            hall = basics['data']['spacegroups'][pos]['hall_entry']
            assert f'{base_path}/hall/{hall}/' in {unquote(urlsplit(link).path) for link in redirect.links}, (index, key, hall)
    print(f'Checked {len(entries)} Hall pages, {len(slugs)} point-group pages, {sum(expected.values())} embeddings in both directions, and all 1290 aliases.')


if __name__ == '__main__':
    main()
