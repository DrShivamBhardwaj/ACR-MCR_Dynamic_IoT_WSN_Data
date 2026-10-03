"""Editable vector schematics for Figures 1 and 2.

Run this module to regenerate only the two schematics. The statistical figures
and all archived simulation results are left untouched.
"""
from pathlib import Path
import json
import matplotlib
matplotlib.use('Agg')
import matplotlib.pyplot as plt
from matplotlib.patches import FancyBboxPatch, FancyArrowPatch, Polygon
from matplotlib.path import Path as MplPath

ROOT = Path(__file__).resolve().parent
BLUE = '#174A70'
TEAL = '#007A72'
INK = '#182B39'
GRAY = '#52616C'
STYLE = {'font.family': 'sans-serif', 'font.sans-serif': ['Nimbus Sans', 'DejaVu Sans'],
         'font.size': 10, 'svg.fonttype': 'none', 'pdf.fonttype': 42, 'ps.fonttype': 42}

from figure_text import CAPTIONS, EXPLANATIONS


def canvas(height):
    fig = plt.figure(figsize=(6.8, height))
    ax = fig.add_axes([0, 0, 1, 1])
    ax.set(xlim=(0, 6.8), ylim=(0, height))
    ax.axis('off')
    return fig, ax


def box(ax, x, y, w, h, title, detail, color=BLUE, fill='#EFF4F7', title_size=10):
    ax.add_patch(FancyBboxPatch((x, y), w, h,
                 boxstyle='round,pad=0,rounding_size=0.055',
                 facecolor=fill, edgecolor=color, linewidth=1.05, zorder=3))
    ax.text(x+w/2, y+h-.19, title, ha='center', va='center',
            fontsize=title_size, fontweight='bold', color=INK, zorder=4)
    ax.text(x+w/2, y+(h-.26)/2-.015, detail, ha='center', va='center',
            fontsize=9.6, color=INK, linespacing=1.25, zorder=4)


def arrow(ax, points, color=GRAY, style='-'):
    path = MplPath(points, [MplPath.MOVETO]+[MplPath.LINETO]*(len(points)-1))
    ax.add_patch(FancyArrowPatch(path=path, arrowstyle='-|>', mutation_scale=10,
                 linewidth=1.1, color=color, linestyle=style, zorder=2))


def diagram1():
    with plt.rc_context(STYLE):
        fig, ax = canvas(4.0)
        xs = [.12, 2.42, 4.72]
        w = 1.96
        box(ax, xs[0], 3.06, w, .78, 'Observable state',
            'Geometry, energy and\nnode availability')
        box(ax, xs[1], 3.06, w, .78, 'ACR-MCR planner',
            'Heads, assignments and\nbackbone routes')
        box(ax, xs[2], 3.06, w, .78, 'Network execution',
            'Data, control and probe\nradio transactions')
        box(ax, xs[0], 1.63, w, .84, 'Link predictions',
            'Point forecasts and scales\nAdaptive upper bounds', TEAL, '#EEF7F4')
        box(ax, xs[1], 1.63, w, .84, 'Learner + calibrator',
            'Past probes only\nACKs, timings and residuals', TEAL, '#EEF7F4')
        box(ax, xs[2], 1.63, w, .84, 'Observable outcomes',
            'ACKs, attempts and\nsample arrival times')
        box(ax, .12, .20, 6.56, .80, 'Performance and coverage evaluation',
            'Separate probe / data coverage; delivered and timely samples\n'
            'Radio ledger: data, probes, control and aggregation', '#52616C', '#F5F7F8', 10.5)
        arrow(ax, [(2.08, 3.45), (2.42, 3.45)])
        arrow(ax, [(4.38, 3.45), (4.72, 3.45)])
        arrow(ax, [(5.70, 3.06), (5.70, 2.47)])
        arrow(ax, [(4.72, 2.05), (4.38, 2.05)], TEAL)
        arrow(ax, [(2.42, 2.05), (2.08, 2.05)], TEAL)
        arrow(ax, [(1.10, 2.47), (1.10, 2.72), (3.40, 2.72), (3.40, 3.06)], TEAL)
        ax.text(2.25, 2.82, 'Issued before execution', ha='center', va='bottom',
                fontsize=9.3, color=TEAL)
        arrow(ax, [(1.10, 1.63), (1.10, 1.00)])
        ax.text(1.24, 1.32, 'Issued bounds', ha='left', va='center', fontsize=9.3, color=GRAY)
        arrow(ax, [(5.70, 1.63), (5.70, 1.00)])
        ax.text(5.54, 1.32, 'Probe + data records', ha='right', va='center', fontsize=9.3, color=GRAY)
        return fig


def diagram2():
    with plt.rc_context(STYLE):
        fig, ax = canvas(4.9)
        box(ax, 1.95, 4.22, 3.40, .54, 'Start round',
            'Apply failures and freeze current predictions', title_size=10.3)
        cx, cy = 3.65, 3.62
        ax.add_patch(Polygon([(cx, cy+.40), (cx+1.08, cy),
                              (cx, cy-.40), (cx-1.08, cy)],
                             closed=True, facecolor='#EEF7F4', edgecolor=TEAL,
                             linewidth=1.1, zorder=3))
        ax.text(cx, cy, 'Refresh heads?', ha='center', va='center',
                fontsize=10.2, fontweight='bold', color=INK, zorder=4)
        box(ax, .72, 2.39, 2.72, .71, 'Search candidate head sets',
            'Initialize, improve by ≥0.5%, or recover\nDebit local control broadcasts', title_size=10)
        box(ax, 4.02, 2.39, 2.40, .71, 'Keep current head set',
            'No head search', title_size=10)
        box(ax, 1.35, 1.36, 4.60, .66, 'Recompute assignments and routes',
            'Collect, aggregate and forward data; record arrival times', title_size=10.3)
        box(ax, 1.35, .16, 4.60, .82, 'Probe, score, then update',
            'Execute fixed-budget probes; score both observation streams\n'
            'Update from probes and check the radio ledger', TEAL, '#EEF7F4', 10.3)
        arrow(ax, [(cx, 4.22), (cx, 4.02)])
        arrow(ax, [(cx-1.08, cy), (2.08, cy), (2.08, 3.10)])
        arrow(ax, [(cx+1.08, cy), (5.22, cy), (5.22, 3.10)])
        ax.text(2.08, 3.74, 'Yes', fontsize=9.8, ha='center', color=INK)
        ax.text(5.22, 3.74, 'No', fontsize=9.8, ha='center', color=INK)
        ax.plot([2.08, 2.08, 5.22, 5.22], [2.39, 2.20, 2.20, 2.39],
                color=GRAY, lw=1.1, zorder=2)
        arrow(ax, [(cx, 2.20), (cx, 2.02)])
        arrow(ax, [(cx, 1.36), (cx, .98)])
        arrow(ax, [(1.35, .57), (.30, .57), (.30, 4.49), (1.95, 4.49)])
        ax.text(.16, 2.45, 'Next round (if any)', rotation=90,
                ha='center', va='center', fontsize=9.5, color=GRAY)
        return fig


def save_diagrams():
    out = ROOT/'figures'
    out.mkdir(exist_ok=True)
    manifest_path = out/'figure_manifest.json'
    manifest = json.loads(manifest_path.read_text()) if manifest_path.exists() else []
    entries = {item['number']: item for item in manifest}
    for n, fn in [(1, diagram1), (2, diagram2)]:
        fig = fn()
        with plt.rc_context(STYLE):
            for ext in ['png', 'svg', 'eps']:
                fig.savefig(out/f'Fig{n}.{ext}', dpi=600, facecolor='white',
                            bbox_inches='tight', pad_inches=.06)
        plt.close(fig)
        entries[n] = dict(number=n, file=f'Fig{n}.png', caption=CAPTIONS[n], explanation=EXPLANATIONS[n], dpi=600,
                          source='diagram_figures.py; controller information and round sequence')
    manifest_path.write_text(json.dumps([entries[k] for k in sorted(entries)], indent=2))


if __name__ == '__main__':
    save_diagrams()
