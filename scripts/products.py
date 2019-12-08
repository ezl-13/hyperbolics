import os
import argh
import subprocess
import itertools
import random

datasets = [
    "wordnet"
    # "synthetic/CS229_datasets/balanced_tree_r3_h5_d0.00549",
    # "synthetic/CS229_datasets/balanced_tree_r5_h3_d0.01282",
    # # "synthetic/CS229_datasets/balanced_tree_r5_h5_d0.00051",
    # "synthetic/CS229_datasets/cycle_tree_c10_r2_h2"
]

models = [
    {'dim': 2, 'hyp': 1, 'edim': 0, 'euc': 0, 'sdim': 0, 'sph': 0},
    {'dim': 10, 'hyp': 1, 'edim': 0, 'euc': 0, 'sdim': 0, 'sph': 0},
]

# LR 0.1

#python /content/hyperbolics/pytorch/pytorch_hyperbolic.py learn /content/hyperbolics/data/edges/synthetic/CS229_datasets/balanced_tree_r3_h5_d0.00549.edges --dim 2 --log-name /content/hyperbolics/out/balanced_tree_r3_h5_d0.00549.H2-1.lr0.1 --batch-size 64 --epochs 1000 --checkpoint-freq 100 -l 0.1 --subsample 16
#python /content/hyperbolics/pytorch/pytorch_hyperbolic.py learn /content/hyperbolics/data/edges/synthetic/CS229_datasets/balanced_tree_r3_h5_d0.00549.edges --dim 10 --log-name /content/hyperbolics/out/balanced_tree_r3_h5_d0.00549.H10-1.lr0.1 --batch-size 64 --epochs 1000 --checkpoint-freq 100 -l 0.1 --subsample 16
#python /content/hyperbolics/pytorch/pytorch_hyperbolic.py learn /content/hyperbolics/data/edges/synthetic/CS229_datasets/balanced_tree_r5_h3_d0.01282.edges --dim 2 --log-name /content/hyperbolics/out/balanced_tree_r5_h3_d0.01282.H2-1.lr0.1 --batch-size 64 --epochs 1000 --checkpoint-freq 100 -l 0.1 --subsample 16
#python /content/hyperbolics/pytorch/pytorch_hyperbolic.py learn /content/hyperbolics/data/edges/synthetic/CS229_datasets/balanced_tree_r5_h3_d0.01282.edges --dim 10 --log-name /content/hyperbolics/out/balanced_tree_r5_h3_d0.01282.H10-1.lr0.1 --batch-size 64 --epochs 1000 --checkpoint-freq 100 -l 0.1 --subsample 16
#python /content/hyperbolics/pytorch/pytorch_hyperbolic.py learn /content/hyperbolics/data/edges/synthetic/CS229_datasets/cycle_tree_c10_r2_h2.edges --dim 2 --log-name /content/hyperbolics/out/cycle_tree_c10_r2_h2.H2-1.lr0.1 --batch-size 64 --epochs 1000 --checkpoint-freq 100 -l 0.1 --subsample 16
#python /content/hyperbolics/pytorch/pytorch_hyperbolic.py learn /content/hyperbolics/data/edges/synthetic/CS229_datasets/cycle_tree_c10_r2_h2.edges --dim 10 --log-name /content/hyperbolics/out/cycle_tree_c10_r2_h2.H10-1.lr0.1 --batch-size 64 --epochs 1000 --checkpoint-freq 100 -l 0.1 --subsample 16

# LR 5

#python /content/hyperbolics/pytorch/pytorch_hyperbolic.py learn /content/hyperbolics/data/edges/synthetic/CS229_datasets/balanced_tree_r3_h5_d0.00549.edges --dim 2 --log-name /content/hyperbolics/out/balanced_tree_r3_h5_d0.00549.H2-1.lr5 --batch-size 64 --epochs 1000 --checkpoint-freq 100 -l 5 --subsample 16
#python /content/hyperbolics/pytorch/pytorch_hyperbolic.py learn /content/hyperbolics/data/edges/synthetic/CS229_datasets/balanced_tree_r3_h5_d0.00549.edges --dim 10 --log-name /content/hyperbolics/out/balanced_tree_r3_h5_d0.00549.H10-1.lr5 --batch-size 64 --epochs 1000 --checkpoint-freq 100 -l 5 --subsample 16
#python /content/hyperbolics/pytorch/pytorch_hyperbolic.py learn /content/hyperbolics/data/edges/synthetic/CS229_datasets/balanced_tree_r5_h3_d0.01282.edges --dim 2 --log-name /content/hyperbolics/out/balanced_tree_r5_h3_d0.01282.H2-1.lr5 --batch-size 64 --epochs 1000 --checkpoint-freq 100 -l 5 --subsample 16
#python /content/hyperbolics/pytorch/pytorch_hyperbolic.py learn /content/hyperbolics/data/edges/synthetic/CS229_datasets/balanced_tree_r5_h3_d0.01282.edges --dim 10 --log-name /content/hyperbolics/out/balanced_tree_r5_h3_d0.01282.H10-1.lr5 --batch-size 64 --epochs 1000 --checkpoint-freq 100 -l 5 --subsample 16
#python /content/hyperbolics/pytorch/pytorch_hyperbolic.py learn /content/hyperbolics/data/edges/synthetic/CS229_datasets/cycle_tree_c10_r2_h2.edges --dim 2 --log-name /content/hyperbolics/out/cycle_tree_c10_r2_h2.H2-1.lr5 --batch-size 64 --epochs 1000 --checkpoint-freq 100 -l 5 --subsample 16
#python /content/hyperbolics/pytorch/pytorch_hyperbolic.py learn /content/hyperbolics/data/edges/synthetic/CS229_datasets/cycle_tree_c10_r2_h2.edges --dim 10 --log-name /content/hyperbolics/out/cycle_tree_c10_r2_h2.H10-1.lr5 --batch-size 64 --epochs 1000 --checkpoint-freq 100 -l 5 --subsample 16


lrs = [.1, 5]

def run_pytorch(run_name, epochs, batch_size):
    params = []
    hparams = list(itertools.product(datasets, models, lrs))
    random.shuffle(hparams)

    for dataset, model, lr in hparams:
        H_name = "" if model['hyp']== 0 else f"H{model['dim']}-{model['hyp']}."
        E_name = "" if model['euc' ]== 0 else f"E{model['edim']}-{model['euc']}."
        S_name = "" if model['sph' ]== 0 else f"S{model['sdim']}-{model['sph']}."
        log_name = f"{run_name}/{os.path.basename(dataset)}.{H_name}{E_name}{S_name}lr{lr}"

        param = [
            "python",
            'pytorch/pytorch_hyperbolic.py', 
            'learn',
            f"data/edges/{dataset}.edges",
            '--dim', str(model['dim']),
            '--log-name', log_name,
            '--batch-size', str(batch_size),
            '--epochs', str(epochs),
            '--checkpoint-freq', '100',
            '-l', str(lr),
            '--subsample', str(16)]
        params.append(" ".join(param))

    for cmd in params:
        subprocess.run(cmd, shell=True)

@argh.arg("run_name", help="Directory to store the run; will be created if necessary")
@argh.arg("--epochs", help="Number of epochs to run Pytorch optimizer")
@argh.arg("--batch-size", help="Batch size")
def run(run_name, epochs=1000, batch_size=64):
    os.makedirs(run_name, exist_ok=True)
    run_pytorch(run_name, epochs=epochs, batch_size=batch_size)


if __name__ == '__main__':
    _parser = argh.ArghParser()
    _parser.set_default_command(run)
    _parser.dispatch()
