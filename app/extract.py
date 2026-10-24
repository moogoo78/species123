"""Pull scientific names out of free text (papers, survey notes, web pages) for checklist matching."""
import re

MAX_CHARS = 200_000

# lowercase words that follow a capitalised word in ordinary prose and are never epithets
STOPWORDS = {
    'and', 'the', 'for', 'was', 'were', 'are', 'from', 'with', 'that', 'this', 'which', 'has', 'have', 'had',
    'not', 'but', 'its', 'also', 'can', 'may', 'been', 'being', 'into', 'than', 'then', 'only', 'other',
    'such', 'these', 'those', 'there', 'their', 'all', 'some', 'most', 'more', 'both', 'each', 'where',
    'when', 'who', 'whose', 'will', 'would', 'should', 'could', 'did', 'does', 'any', 'one', 'two',
    'per', 'via', 'cf', 'aff', 'spp', 'sp', 'nov', 'gen', 'comb', 'sensu', 'lato', 'stricto', 'et', 'al',
}
MARKERS = {'subsp': 'subsp.', 'ssp': 'subsp.', 'var': 'var.', 'fo': 'fo.', 'f': 'fo.', 'forma': 'fo.'}

_WORD = r'[a-zë][a-zë-]{2,}'
BINOMIAL = re.compile(
    r'(?<![A-Za-z])(?P<genus>[A-Z][a-zë]+|[A-Z][a-z]?\.)'
    r'(?:\s+\([A-Z][a-zë]+\))?'                       # zoological subgenus, dropped
    r'\s+(?:(?P<hybrid>×\s*|x\s+))?(?P<sp>' + _WORD + r')(?![A-Za-z])'
    r'(?:\s+(?P<marker>(?:subsp|ssp|var|fo|f)\.|(?:subsp|ssp|var|fo|forma)(?=\s))?\s*(?P<infra>' + _WORD + r')(?![A-Za-z]))?'
)
UNINOMIAL = re.compile(r'(?<![A-Za-z])[A-Z][a-zë]{2,}(?![A-Za-z.])')


class Hit:
    """One distinct name found in the text: candidate spellings to try in order, and how often it occurred."""

    def __init__(self, candidates, genus=None):
        self.candidates = candidates  # [(name, verbatim)], most specific first
        self.genus = genus  # first word of a binomial, else None
        self.count = 1


def names(text):
    """Distinct names in order of first appearance. Binomials and trinomials first; then lone capitalised
    words (possible genera, families…) that are not part of one."""
    text = (text or '')[:MAX_CHARS]
    found, order = {}, []

    def add(key, candidates, genus=None):
        if key in found:
            found[key].count += 1
        else:
            found[key] = Hit(candidates, genus)
            order.append(key)

    last_genus = {}  # initial → full genus, for "B. formosana" after "Begonia ..."
    spans = []
    for m in BINOMIAL.finditer(text):
        genus, sp, marker, infra = m['genus'], m['sp'], m['marker'], m['infra']
        if sp in STOPWORDS:
            continue
        if genus.endswith('.'):
            genus = last_genus.get(genus[:-1])
            if not genus:
                continue
        else:
            last_genus[genus[0]] = genus
        spans.append(m.span())
        species = f"{genus} {'× ' if m['hybrid'] else ''}{sp}"
        cands = []
        if infra and infra not in STOPWORDS:
            rank = MARKERS[marker.rstrip('.')] + ' ' if marker else ''
            cands.append((f'{species} {rank}{infra}', m[0]))
        # without a rank marker a third word may just be the next word of prose, so fall back to the binomial
        cands.append((species, m[0][:m.end('sp') - m.start()]))
        add(cands[0][0], cands, genus)

    masked = list(text)
    for a, b in spans:
        masked[a:b] = ' ' * (b - a)
    for m in UNINOMIAL.finditer(''.join(masked)):
        add(m[0], [(m[0], m[0])])
    return [found[k] for k in order]
