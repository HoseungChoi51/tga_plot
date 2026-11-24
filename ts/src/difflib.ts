// Python's difflib.SequenceMatcher ratio and get_close_matches, so "did you mean" hints match the Python plotkit.
// Sequences are compared by code point, as Python compares str.

class SequenceMatcher {
  private a: string[] = [];
  private b: string[] = [];
  private b2j = new Map<string, number[]>();
  private fullbcount: Map<string, number> | null = null;
  private matching: [number, number, number][] | null = null;

  setSeq1(a: string): void {
    this.a = Array.from(a);
    this.matching = null;
  }

  setSeq2(b: string): void {
    this.b = Array.from(b);
    this.matching = null;
    this.fullbcount = null;
    const b2j = new Map<string, number[]>();
    this.b.forEach((elt, i) => {
      const idx = b2j.get(elt);
      if (idx) idx.push(i);
      else b2j.set(elt, [i]);
    });
    const n = this.b.length;
    if (n >= 200) {                                  // autojunk: popular elements
      const ntest = Math.floor(n / 100) + 1;
      for (const [elt, idxs] of [...b2j]) if (idxs.length > ntest) b2j.delete(elt);
    }
    this.b2j = b2j;
  }

  private findLongestMatch(alo: number, ahi: number, blo: number, bhi: number): [number, number, number] {
    const { a, b, b2j } = this;
    let besti = alo, bestj = blo, bestsize = 0;
    let j2len = new Map<number, number>();
    for (let i = alo; i < ahi; i++) {
      const newj2len = new Map<number, number>();
      for (const j of b2j.get(a[i]) ?? []) {
        if (j < blo) continue;
        if (j >= bhi) break;
        const k = (j2len.get(j - 1) ?? 0) + 1;
        newj2len.set(j, k);
        if (k > bestsize) { besti = i - k + 1; bestj = j - k + 1; bestsize = k; }
      }
      j2len = newj2len;
    }
    // isjunk is None, so nothing is junk: extend the match over equal neighbours (popular elements included)
    while (besti > alo && bestj > blo && a[besti - 1] === b[bestj - 1]) {
      besti--; bestj--; bestsize++;
    }
    while (besti + bestsize < ahi && bestj + bestsize < bhi && a[besti + bestsize] === b[bestj + bestsize]) bestsize++;
    return [besti, bestj, bestsize];
  }

  private matchingBlocks(): [number, number, number][] {
    if (this.matching) return this.matching;
    const la = this.a.length, lb = this.b.length;
    const queue: [number, number, number, number][] = [[0, la, 0, lb]];
    const blocks: [number, number, number][] = [];
    while (queue.length) {
      const [alo, ahi, blo, bhi] = queue.pop()!;
      const x = this.findLongestMatch(alo, ahi, blo, bhi);
      const [i, j, k] = x;
      if (k) {
        blocks.push(x);
        if (alo < i && blo < j) queue.push([alo, i, blo, j]);
        if (i + k < ahi && j + k < bhi) queue.push([i + k, ahi, j + k, bhi]);
      }
    }
    blocks.sort((p, q) => p[0] - q[0] || p[1] - q[1] || p[2] - q[2]);
    let i1 = 0, j1 = 0, k1 = 0;
    const out: [number, number, number][] = [];
    for (const [i2, j2, k2] of blocks) {
      if (i1 + k1 === i2 && j1 + k1 === j2) k1 += k2;
      else {
        if (k1) out.push([i1, j1, k1]);
        i1 = i2; j1 = j2; k1 = k2;
      }
    }
    if (k1) out.push([i1, j1, k1]);
    out.push([la, lb, 0]);
    this.matching = out;
    return out;
  }

  ratio(): number {
    const m = this.matchingBlocks().reduce((s, t) => s + t[2], 0);
    return calc(m, this.a.length + this.b.length);
  }

  quickRatio(): number {
    if (!this.fullbcount) {
      this.fullbcount = new Map();
      for (const elt of this.b) this.fullbcount.set(elt, (this.fullbcount.get(elt) ?? 0) + 1);
    }
    const avail = new Map<string, number>();
    let matches = 0;
    for (const elt of this.a) {
      const numb = avail.has(elt) ? avail.get(elt)! : (this.fullbcount.get(elt) ?? 0);
      avail.set(elt, numb - 1);
      if (numb > 0) matches++;
    }
    return calc(matches, this.a.length + this.b.length);
  }

  realQuickRatio(): number {
    const la = this.a.length, lb = this.b.length;
    return calc(Math.min(la, lb), la + lb);
  }
}

function calc(matches: number, length: number): number {
  return length ? (2.0 * matches) / length : 1.0;
}

/** difflib.SequenceMatcher(None, a, b).ratio() */
export function ratio(a: string, b: string): number {
  const s = new SequenceMatcher();
  s.setSeq2(b);
  s.setSeq1(a);
  return s.ratio();
}

/** difflib.get_close_matches(word, possibilities, n, cutoff): best first; ties by the larger string, as heapq does. */
export function getCloseMatches(word: string, possibilities: Iterable<string>, n = 3, cutoff = 0.6): string[] {
  const s = new SequenceMatcher();
  s.setSeq2(word);
  const result: [number, string][] = [];
  for (const x of possibilities) {
    s.setSeq1(x);
    if (s.realQuickRatio() >= cutoff && s.quickRatio() >= cutoff && s.ratio() >= cutoff) result.push([s.ratio(), x]);
  }
  result.sort((p, q) => (q[0] - p[0]) || (q[1] < p[1] ? -1 : q[1] > p[1] ? 1 : 0));
  return result.slice(0, n).map(r => r[1]);
}
