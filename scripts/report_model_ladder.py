"""Generate executed validation notebooks and calibration figures from run tables."""

import argparse
import contextlib
import csv
import io
import json
from pathlib import Path
import sys


FILES = {'A': '01_logreg.ipynb', 'AB': '02_logreg_context.ipynb', 'recency': '03_recency.ipynb'}


def notebook(stage: str) -> None:
    import pandas as pd
    out = Path('reports/model')
    results = pd.read_csv(out / f'{stage}_validation.csv', dtype={'fold_id': str})
    pooled = results.loc[results.fold_id.eq('pooled') & results.scope.eq('ALL')]
    cells = []
    def md(source): cells.append({'cell_type':'markdown','metadata':{},'source':source.splitlines(keepends=True)})
    def code(source): cells.append({'cell_type':'code','metadata':{},'source':source.splitlines(keepends=True),'execution_count':None,'outputs':[]})
    md(f'# {stage}: pooled direct logistic validation\n\nOne model per lead; all oblasts pooled, no identity encoding, calendar or STL predictors. Leads 1–6 are primary; lead 0 is separate; 12/24 are secondary. Each fold starts from scratch on TRAIN ending 25 hours before VALID. Scaling, rates and coefficients fit TRAIN only. C is selected by pooled VALID Brier over four independent folds; these are selection scores, not unbiased final performance. No resampling or TEST evaluation.\n')
    code('from pathlib import Path\nimport sys\nimport pandas as pd\nroot = Path.cwd() if Path("src/airalerts").exists() else Path.cwd().parent\nsys.path.insert(0, str(root / "src"))\nfrom airalerts.evaluate import latest_results\nout = root / "reports/model"\nlatest = latest_results(out / "results.csv")\n')
    code(f'results = pd.read_csv(out / "{stage}_validation.csv", dtype={{"fold_id": str}})\nsummary = results.loc[results.fold_id.eq("pooled") & results.scope.eq("ALL")]\nprint(summary[["model", "lead", "n", "brier", "bss_vs_clim", "bss_vs_persistence", "bss_vs_ses", "bss_ci_low", "bss_ci_high", "ece"]].to_string(index=False))\nprint(pd.read_csv(out / "{stage}_selected.csv").to_string(index=False))\n')
    if stage == 'A':
        code('reference = pd.read_csv(out / "reference_validation.csv")\nprint(reference.loc[reference.scope.eq("ALL") & reference.model.isin(["climatology", "persistence_prob", "ses"]), ["model", "lead", "brier", "bss_vs_clim", "ece"]].to_string(index=False))\n')
        lead1 = pooled.loc[pooled.lead.eq(1)].iloc[0]; lead6 = pooled.loc[pooled.lead.eq(6)].iloc[0]
        conclusion = f'Pooled validation BSS versus climatology is {lead1.bss_vs_clim:.5f} at lead 1 and {lead6.bss_vs_clim:.5f} at lead 6. At lead 1 BSS versus persistence is {lead1.bss_vs_persistence:.5f} and versus SES is {lead1.bss_vs_ses:.5f}. Longer-lead estimates and confidence intervals are in the table; selection used VALID and no final-test conclusion is drawn.'
    elif stage == 'AB':
        code('print(summary.pivot(index="lead", columns="model", values="bss_vs_clim").to_string())\nprint(pd.read_csv(out / "ab_selection.csv").to_string(index=False))\n')
        choices = pd.read_csv(out / 'ab_selection.csv')
        kept = choices.loc[choices.keep_context,'lead'].tolist(); dropped = choices.loc[~choices.keep_context,'lead'].tolist()
        conclusion = f'The paired seven-day gain interval excludes zero in favor of full context for leads {kept}. For leads {dropped}, there is no evidence of improvement and Group B is not carried into recency. Neighbor-only, national-only and base-rate-only additions are descriptive ablations in the table; no geographic identity predictor is added.'
    else:
        md('## Recency setup\n\nUse A or AB per lead according to the context gain rule, fixing its previously selected C. Fit scaler and logistic loss with w=0.5**(age_days/half_life), age from exclusive TRAIN end. Select half-life 14/30/60/inf on pooled VALID; inf is the unweighted sensitivity.\n')
        code('print(pd.read_csv(out / "recency_selection.csv").to_string(index=False))\n')
        choices = pd.read_csv(out / 'recency_selection.csv')
        conclusion = f'Selected half-lives by lead are {dict(zip(choices.lead, choices.half_life))}. The paired gain intervals versus each unweighted base are reported, including intervals crossing zero. These are validation selections only; no HGB, frozen final configuration or TEST evaluation is run.'
    md('## Calibration\n\nECE uses ten bins. CIs pair all regions within circular seven-day UTC blocks; one-day blocks are sensitivity only. Flags are computed separately from each fold TRAIN target rate, below 3% or above 95%; per-oblast and pooled excluded-flagged metrics are in results.csv.\n')
    md(f'![Calibration: {stage}](../reports/model/{stage}_calibration.png)\n\n{conclusion}\n')
    namespace = {}; count = 0
    for cell in cells:
        if cell['cell_type'] != 'code': continue
        count += 1; captured = io.StringIO()
        with contextlib.redirect_stdout(captured): exec(''.join(cell['source']), namespace)
        cell['execution_count'] = count
        if captured.getvalue(): cell['outputs'] = [{'output_type':'stream','name':'stdout','text':captured.getvalue().splitlines(keepends=True)}]
    for i,cell in enumerate(cells): cell['id'] = f'{stage}-validation-{i}'
    result = {'cells':cells,'metadata':{'kernelspec':{'display_name':'Python 3','language':'python','name':'python3'},'language_info':{'name':'python','version':sys.version.split()[0]}},'nbformat':4,'nbformat_minor':5}
    Path('notebooks').mkdir(exist_ok=True)
    Path('notebooks',FILES[stage]).write_text(json.dumps(result,ensure_ascii=False,indent=1)+'\n')
    print('Executed notebook:',FILES[stage],';',count,'code cells')


def plot(stage: str) -> None:
    import matplotlib
    matplotlib.use('Agg')
    import matplotlib.pyplot as plt
    out = Path('reports/model')
    with (out / f'{stage}_reliability.csv').open() as handle: rows = list(csv.DictReader(handle))
    rows = [row for row in rows if row['fold_id']=='pooled' and row['scope']=='ALL' and int(row['n'])>0]
    if stage == 'recency':
        with (out / 'recency_selection.csv').open() as handle:
            chosen = {int(row['lead']):row['model'] for row in csv.DictReader(handle)}
        rows = [row for row in rows if row['model']==chosen[int(row['lead'])]]
    leads = sorted({int(row['lead']) for row in rows})
    fig,axes = plt.subplots(3,3,figsize=(13,11))
    for ax,k in zip(axes.flat,leads):
        ax.plot([0,1],[0,1],color='black',linestyle='--',linewidth=.7)
        selected = [row for row in rows if int(row['lead'])==k]
        for name in sorted({row['model'] for row in selected}):
            group = [row for row in selected if row['model']==name]
            ax.plot([float(row['mean_probability']) for row in group],[float(row['observed_rate']) for row in group],marker='o',markersize=3,label=name)
        ax.set(xlim=(0,1),ylim=(0,1),title=f'lead {k}'+(' (separate)' if k==0 else ''),xlabel='Predicted probability',ylabel='Observed rate')
        ax.legend(fontsize=7)
    for ax in list(axes.flat)[len(leads):]: ax.axis('off')
    fig.suptitle(f'{stage}: pooled walk-forward VALID calibration; selection on VALID')
    fig.tight_layout()
    fig.savefig(out / f'{stage}_calibration.png',dpi=150)
    plt.close(fig)


def main() -> None:
    p=argparse.ArgumentParser(description=__doc__)
    p.add_argument('--stage',choices=list(FILES),required=True)
    p.add_argument('--notebooks-only',action='store_true')
    p.add_argument('--plots-only',action='store_true')
    args=p.parse_args()
    if not args.plots_only: notebook(args.stage)
    if not args.notebooks_only: plot(args.stage)


if __name__=='__main__': main()
