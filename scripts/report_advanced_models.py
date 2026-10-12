"""Executed HGB/comparison notebooks and offline figures from saved validation runs."""

import argparse
import contextlib
import csv
import io
import json
from pathlib import Path
import sys

OUT = Path('reports/model')


def notebook(stage: str) -> None:
    import pandas as pd
    cells = []
    def md(source): cells.append({'cell_type':'markdown','metadata':{},'source':source.splitlines(keepends=True)})
    def code(source): cells.append({'cell_type':'code','metadata':{},'source':source.splitlines(keepends=True),'execution_count':None,'outputs':[]})
    setup = 'from pathlib import Path\nimport sys\nimport json\nimport pandas as pd\nroot = Path.cwd() if Path("src/airalerts").exists() else Path.cwd().parent\nsys.path.insert(0, str(root / "src"))\nfrom airalerts.evaluate import latest_results\nout = root / "reports/model"\nlatest = latest_results(out / "results.csv")\n'
    if stage == 'hgb':
        md('# HGB walk-forward validation\n\nOfficial B; one pooled model per lead, independent folds and 25-hour embargo. All 8 grid candidates × 4 folds × 9 leads ran. Ordered TRAIN: core, 14-day stopping tail, 14-day calibration tail, with 25-hour inner gaps. Stop by Brier every 10 trees, patience 30 and tolerance 1e-5; refit pre-calibration TRAIN at chosen iterations. Base rates fit only each actual fitting subset. Selected recency uses TRAIN-only weights. No random split, calendar/STL predictor, class resampling, xgboost or TEST evaluation.\n\nPooled raw VALID ECE >0.03 is the predeclared calibration trigger; coefficients would fit the untouched chronological TRAIN calibration tail. Candidate selection and conditional CIs use VALID, so they are not unbiased final scores.\n')
        code(setup)
        code('hgb = latest.loc[latest.model.isin(["hgb", "hgb_platt"]) & latest.fold_id.eq("pooled") & latest.scope.eq("ALL")]\nprint(hgb[["model", "lead", "n", "brier", "bss_vs_clim", "bss_vs_persistence", "bss_vs_ses", "bss_ci_low", "bss_ci_high", "ece"]].to_string(index=False))\nprint(pd.read_csv(out / "hgb_selected.csv").to_string(index=False))\n')
        code('grid = pd.read_csv(out / "hgb_candidate_scores.csv")\ngrid["error_sum"] = grid.n * grid.brier\nsummary = grid.groupby(["lead", "learning_rate", "max_depth", "max_iter"])[["error_sum", "n"]].sum()\nsummary["pooled_brier"] = summary.error_sum / summary.n\nprint(summary[["pooled_brier"]].to_string())\nprint("Candidate-fold evaluations:", len(grid))\nprint(pd.read_csv(out / "hgb_train_tails.csv").to_string(index=False))\n')
        frame=pd.read_csv(OUT / 'hgb_validation.csv',dtype={'fold_id':str})
        frame=frame.loc[frame.fold_id.eq('pooled') & frame.scope.eq('ALL') & frame.model.eq('hgb')].set_index('lead')
        md(f'![HGB calibration](../reports/model/hgb_calibration.png)\n\nHGB BSS versus climatology at lead 1 is {frame.loc[1,"bss_vs_clim"]:.5f} and at lead 6 is {frame.loc[6,"bss_vs_clim"]:.5f}. Maximum pooled raw ECE is {frame.ece.max():.5f}, below 0.03, so real-data Platt was not triggered. At leads 12/24, BSS versus SES is {frame.loc[12,"bss_vs_ses"]:.5f}/{frame.loc[24,"bss_vs_ses"]:.5f}; this protocol provides no point-score superiority to SES there, and no FINAL inference is made.\n')
        filename='04_hgb.ipynb'
    else:
        md('# Validation comparison and frozen configuration\n\nLead 0 is separate; leads 1–6 are primary, 12/24 are secondary. Tables use latest run_id per (model,fold,lead); stale records remain in the append-only log. Models fit TRAIN only; feature gates and candidate/ensemble selection use walk-forward VALID. Seven-day paired UTC blocks cover all regions together. CIs do not adjust for hyperparameter selection/multiple comparisons. No TEST or remaining optional experiment is run.\n')
        code(setup)
        code('comparison = pd.read_csv(out / "comparison_table.csv")\nfor reference in ["clim", "persistence", "ses"]:\n    table = comparison.loc[comparison.reference.eq(reference)]\n    print("BSS versus", reference)\n    print(table.pivot(index="model", columns="lead", values="bss").to_string())\n    print(table[["model", "lead", "bss", "ci_low", "ci_high", "ece"]].to_string(index=False))\n')
        md('![BSS versus forecast lead](../reports/model/bss_vs_lead.png)\n\nAll recorded models are shown; lead 0 is a separate panel and is never averaged with primary leads.\n')
        code('frozen = json.loads((root / "config/final_config.json").read_text())\nprint(pd.read_csv(out / "frozen_validation.csv").to_string(index=False))\nprint(pd.read_csv(out / "ensemble_selection.csv").to_string(index=False))\nprint("Frozen status:", frozen["status"], "TEST evaluated:", frozen["test_evaluated"])\n')
        md('## Per-oblast metrics and TRAIN flags\n\nFlags are fold/lead-specific TRAIN target rates below 3% or above 95%; base_rate in the result schema is the evaluation positive rate. This table keeps folds explicit rather than assigning one retrospective flag to all periods.\n')
        code('regions = pd.read_csv(out / "best_per_oblast.csv")\nprint(regions.to_string(index=False))\n')
        md('![Frozen-model validation calibration](../reports/model/best_calibration.png)\n\nThe frozen settings contain per-lead model, ordered features, hyperparameters, half-life and learned-model ensemble weight. Future FINAL fitting must estimate coefficients/SES alpha/HGB stopping iterations using only FINAL TRAIN and the frozen rules.\n\nSee [validation_summary.md](../reports/model/validation_summary.md) for the ordered experiments and HYPOTHESES NOT CONFIRMED. TEST remains unevaluated.\n')
        filename='05_comparison.ipynb'
    namespace={}; count=0
    for cell in cells:
        if cell['cell_type']!='code':continue
        count+=1;captured=io.StringIO()
        with contextlib.redirect_stdout(captured):exec(''.join(cell['source']),namespace)
        cell['execution_count']=count
        if captured.getvalue():cell['outputs']=[{'output_type':'stream','name':'stdout','text':captured.getvalue().splitlines(keepends=True)}]
    for i,cell in enumerate(cells):cell['id']=f'{stage}-{i:03d}'
    nb={'cells':cells,'metadata':{'kernelspec':{'display_name':'Python 3','language':'python','name':'python3'},'language_info':{'name':'python','version':sys.version.split()[0]}},'nbformat':4,'nbformat_minor':5}
    Path('notebooks',filename).write_text(json.dumps(nb,ensure_ascii=False,indent=1)+'\n')
    print('Executed',filename,':',count,'code cells')


def plot(stage: str) -> None:
    import matplotlib
    matplotlib.use('Agg')
    import matplotlib.pyplot as plt
    if stage=='hgb':
        with (OUT/'hgb_reliability.csv').open() as handle:rows=list(csv.DictReader(handle))
        rows=[r for r in rows if r['fold_id']=='pooled' and r['scope']=='ALL' and int(r['n'])>0]
        path=OUT/'hgb_calibration.png'
    else:
        with (OUT/'best_reliability.csv').open() as handle:rows=list(csv.DictReader(handle))
        rows=[r for r in rows if int(r['n'])>0]
        path=OUT/'best_calibration.png'
    leads=sorted({int(r['lead']) for r in rows})
    fig,axes=plt.subplots(3,3,figsize=(13,11))
    for ax,k in zip(axes.flat,leads):
        ax.plot([0,1],[0,1],'k--',linewidth=.7)
        selected=[r for r in rows if int(r['lead'])==k]
        for model in sorted({r['model'] for r in selected}):
            data=[r for r in selected if r['model']==model]
            ax.plot([float(r['mean_probability']) for r in data],[float(r['observed_rate']) for r in data],marker='o',markersize=3,label=model)
        ax.set(xlim=(0,1),ylim=(0,1),title=f'lead {k}'+(' (separate)' if k==0 else ''),xlabel='Predicted probability',ylabel='Observed rate')
        ax.legend(fontsize=7)
    for ax in list(axes.flat)[len(leads):]:ax.axis('off')
    fig.suptitle(f'{stage}: pooled walk-forward VALID calibration; selection on VALID')
    fig.tight_layout();fig.savefig(path,dpi=150);plt.close(fig)
    if stage!='comparison':return
    with (OUT/'comparison_table.csv').open() as handle:data=list(csv.DictReader(handle))
    data=[r for r in data if r['reference']=='clim']
    names=sorted({r['model'] for r in data})
    fig,axes=plt.subplots(1,2,figsize=(17,7),gridspec_kw={'width_ratios':[1,5]})
    colors=plt.cm.turbo([i/max(1,len(names)-1) for i in range(len(names))])
    for color,name in zip(colors,names):
        model=sorted([r for r in data if r['model']==name],key=lambda r:int(r['lead']))
        zero=[r for r in model if int(r['lead'])==0]
        rest=[r for r in model if int(r['lead'])!=0]
        if zero:axes[0].scatter([0],[float(zero[0]['bss'])],color=color,s=25)
        if rest:axes[1].plot([int(r['lead']) for r in rest],[float(r['bss']) for r in rest],marker='o',markersize=3,color=color,linewidth=1,label=name)
    for ax in axes:ax.axhline(0,color='black',linewidth=.7);ax.set_ylabel('BSS versus climatology')
    axes[0].set(title='Lead 0 (separate)',xticks=[0])
    axes[1].set(title='Primary 1–6; secondary 12/24',xlabel='Forecast lead k (hours)',xticks=[1,2,3,4,5,6,12,24])
    axes[1].legend(loc='center left',bbox_to_anchor=(1.01,.5),fontsize=7)
    fig.suptitle('All recorded validation models; no pooling across leads')
    fig.tight_layout();fig.savefig(OUT/'bss_vs_lead.png',dpi=150);plt.close(fig)


def main() -> None:
    p=argparse.ArgumentParser(description=__doc__)
    p.add_argument('--stage',choices=['hgb','comparison'],required=True)
    p.add_argument('--notebooks-only',action='store_true')
    p.add_argument('--plots-only',action='store_true')
    args=p.parse_args()
    if not args.plots_only:notebook(args.stage)
    if not args.notebooks_only:plot(args.stage)


if __name__=='__main__':main()
