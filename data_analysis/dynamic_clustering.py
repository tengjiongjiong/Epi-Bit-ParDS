import logging
import os
import time
import warnings
import argparse
import multiprocessing as mp
import pandas as pd
import numpy as np
import matplotlib.pyplot as plt

from sklearn.cluster import KMeans
from sklearn.manifold import TSNE
from sklearn.mixture import GaussianMixture
from sklearn.preprocessing import MinMaxScaler
from sklearn import metrics

warnings.filterwarnings("ignore")

plt.rcParams['figure.dpi'] = 300
names = ['chrom', 'start', 'end', 'name', '?', 'strand', 'thickStart', 'thickEnd',
         'itemRgb', 'coverage', 'score']
chroms = ['L1', 'L2', 'L3', 'L4', 'L5']
pos = [305, 315, 325, 335, 345, 355, 365, 375, 385, 395, 405, 415, 425, 435,
       445, 455, 465, 475, 485, 495, 505, 515, 525, 535, 545, 555, 565, 575,
       585, 595, 605, 615, 625, 635, 645, 655, 665, 675, 685, 695, 705, 715,
       725, 735, 745, 755, 765, 775, 785, 795, 805, 815, 825, 835, 845, 855,
       865, 875, 885, 895, 905, 915, 925, 935, 945, 955, 965, 975, 985, 995]
pos = [p - 1 for p in pos]
seed = 42
logger = logging.getLogger(__name__)
logger.setLevel(logging.INFO)
handler = logging.StreamHandler()
handler.setFormatter(logging.Formatter(fmt='[%(asctime)s][%(levelname)s] %(message)s', datefmt='%Y-%m-%d %H:%M:%S'))
logger.addHandler(handler)


def get_min_barcodes(_b, _barcodes, n=10):
    _top_barcodes = []
    for bar in _barcodes:
        dis = np.sqrt(sum([(float(c1) - float(c2)) ** 2 for c1, c2 in zip(_b, bar)]))
        _top_barcodes.append((dis, bar))
    _top_barcodes.sort(key=lambda _: _[0])
    return _top_barcodes[:n]


def show_TSNE(df_tsne, title=None, path=None):
    fig, ax = plt.subplots()
    unique = np.unique(df_tsne['label'])
    for i in range(len(unique)):
        tmp = df_tsne[df_tsne.label == i]
        ax.scatter(tmp.x, tmp.y, s=2.5, label=i)
    plt.title(title)
    plt.axis('off')
    plt.legend(ncol=5, fontsize='xx-small', bbox_to_anchor=(1, 0))
    if path is not None:
        plt.savefig(path, bbox_inches='tight')
        plt.close()


def distributor(_dataframe, _barcodes, _path, n_iter=1, _tsne_path=None, _seed=42):
    scaler = MinMaxScaler()
    barcodes_set = set(_barcodes.barcode)
    dic = {barcode: pd.DataFrame() for barcode in barcodes_set}
    for barcode, df in _dataframe.groupby('current_min_barcode', sort=False):
        dic[barcode] = df
    dic = dict(sorted(dic.items(), key=lambda _: len(_[1]), reverse=True))

    for i in range(n_iter):
        assert len(dic) == len(barcodes_set)
        iter_path = os.path.join(_path, 'iter_%d' % i)
        if not os.path.exists(iter_path):
            os.makedirs(iter_path)
        for barcode in dic.keys():
            index = _barcodes[_barcodes.barcode == barcode].index[0]
            current_df = dic[barcode]
            x = scaler.fit_transform(current_df[pos])
            best_kmeans, best_score, best_n = None, -1, -1
            for n in range(2, len(_barcodes) // 4):
                if len(x) < n:
                    break
                kmeans = KMeans(n_clusters=n, random_state=_seed)
                kmeans.fit(x)
                score = metrics.silhouette_score(x, kmeans.labels_)
                if score > best_score:
                    best_kmeans, best_score, best_n = kmeans, score, n
            current_df['label'] = best_kmeans.labels_
            min_label = current_df.groupby('label').current_min_dis.mean().idxmin()
            dropped_data = current_df[current_df.label != min_label]
            chosen_data = current_df[current_df.label == min_label]

            # update current barcode and distribute dropped data to other barcodes
            dic[barcode] = chosen_data
            dropped_data['min_barcodes'] = dropped_data['min_barcodes'].apply(lambda x: x[1:])
            dropped_data[['current_min_dis', 'current_min_barcode']] = dropped_data['min_barcodes'].apply(
                lambda x: pd.Series(x[0]))
            for b, d in dropped_data.groupby('current_min_barcode', sort=False):
                dic.update({b: pd.concat([dic[b], d])})
            chosen_data['read_id'].to_csv(os.path.join(iter_path, '%d.txt' % index), index=False, header=['read_id'])

            # show TSNE
            if _tsne_path is not None and len(x) > 100:
                tsne = TSNE(random_state=_seed)
                tsne.fit_transform(x)
                df_tsne = pd.DataFrame(tsne.embedding_, columns=['x', 'y'])
                df_tsne['label'] = best_kmeans.labels_
                if not os.path.exists(os.path.join(_tsne_path, str(i))):
                    os.makedirs(os.path.join(_tsne_path, str(i)))
                show_TSNE(
                    df_tsne,
                    title='%d, reads: %d, n_cluster: %d, score: %.4f' % (index, len(x), best_n, best_score),
                    path=os.path.join(_tsne_path, str(i), "%d.png" % index)
                )

            logger.info("iter: %d, index: %d, reads: %d, n_cluster: %d, score: %.4f, dropped: %d, chosen: %d"
                        % (i, index, len(x), best_n, best_score, len(dropped_data), len(chosen_data)))


def load_data(_path, _code, _barcode_pos):
    per_read = pd.read_csv(_path, sep='\t')
    per_read = per_read[per_read.pos.isin(pos)]
    per_read['mod_prob'] = per_read['mod_log_prob'].apply(np.exp)
    barcode_pos = pd.read_csv(_barcode_pos)

    dataframes = []
    for ch in chroms:
        per_read_ch = per_read[per_read.chrm == ch]
        methyl = {index: {k: v for k, v in zip(df.pos, df.mod_prob)}
                  for index, df in per_read_ch.groupby('read_id')}
        df = pd.DataFrame(methyl).T.dropna()
        df['chrom'] = ch
        dataframes.append(df)

    for i in range(len(dataframes)):
        dataframes[i]['min_barcodes'] = dataframes[i].apply(
            lambda x: get_min_barcodes(x[barcode_pos[barcode_pos.chrom == chroms[i]].pos], _code[_code.chrom == chroms[i]].barcode), axis=1)
        dataframes[i][['current_min_dis', 'current_min_barcode']] = dataframes[i].min_barcodes.apply(
            lambda x: pd.Series(x[0]))
        dataframes[i]['read_id'] = dataframes[i].index
    logger.info("%d reads loaded" % sum([len(df) for df in dataframes]))

    return dataframes


def main():
    args = argparse.ArgumentParser()
    args.add_argument('-p', '--per_read_path', type=str, default=None)
    args.add_argument('-t', '--tsne_path', type=str, default=None)
    args.add_argument('-s', '--seed', type=int, default=42)
    args.add_argument('-i', '--iter', type=int, default=1)
    args.add_argument('-bp', '--barcode_pos', type=str, default=None)
    args.add_argument('-op', '--output_path', type=str, default=None)
    args.add_argument('-cp', '--code_path', type=str, default=None)
    args = args.parse_args()
    logger.info("Arguments: %s" % args)

    code = pd.read_csv(args.code_path, converters={'barcode': str, 'info': str})
    dataframes = load_data(args.per_read_path, code, args.barcode_pos)

    if args.output_path is not None and not os.path.exists(args.output_path):
        os.makedirs(args.output_path)
    if args.tsne_path is not None and not os.path.exists(args.tsne_path):
        os.makedirs(args.tsne_path)

    start = time.time()
    process_list = []
    for i in range(len(dataframes)):
        p = mp.Process(
            target=distributor,
            args=(dataframes[i], code[code.chrom == chroms[i]].barcode.to_frame(),
                  args.output_path, args.iter, args.tsne_path, args.seed)
        )
        process_list.append(p)
        logger.info("Chrom: %s, reads: %d, process: %d" % (chroms[i], len(dataframes[i]), i))
        p.start()
    for p in process_list:
        p.join()
    logger.info("Time cost: %.2f" % (time.time() - start))


if __name__ == '__main__':
    main()
