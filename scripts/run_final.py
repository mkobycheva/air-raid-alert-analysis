"""Explicit one-shot FINAL; frozen config only, no tuning arguments."""
import argparse
from airalerts.final import run, finish_saved

if __name__=='__main__':
    parser=argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--evaluate-saved',action='store_true',help='Evaluate saved FINAL predictions without refitting or predicting')
    args=parser.parse_args()
    finish_saved() if args.evaluate_saved else run()
