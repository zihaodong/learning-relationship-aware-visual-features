import matplotlib
matplotlib.use('Agg')    
import matplotlib.pyplot as plt
import matplotlib.gridspec as gridspec
from matplotlib.backends.backend_pdf import PdfPages
import cv2
import os
import argparse
import numpy as np
from order import rn_order, rmac_order, graphs_order, states_order, graphs_approx_order
from tqdm import tqdm, trange
import math

class ClevrImageLoader():
    def __init__(self, images_dir):
        self.images_dir = images_dir

    def get(self,index):
        padded_index = str(index).rjust(6,'0')
        img_filename = os.path.join(self.images_dir, 'val', 'CLEVR_val_{}.png'.format(padded_index))
        image = cv2.imread(img_filename)
        return image / 255.

def build_figure(orders, image_loader, query_idx, n=10, scale=1):
    size = (math.ceil(4*n*scale), math.ceil(3*(len(orders)+1)*scale))

    fig = plt.figure('Query idx {}'.format(query_idx), figsize=size)
    gs = gridspec.GridSpec(len(orders)+1, 1)

    #query_img
    query_axs = plt.subplot(gs[0, 0])
    #query_swim = np.swapaxes(query_img,0,2)
    query_axs.set_title('Query Image')
    query_axs.imshow(image_loader.get(query_idx))
    query_axs.set_xticks([])
    query_axs.set_xticklabels([])
    query_axs.set_yticklabels([])
    separator = np.zeros(shape=(320,5,3))

    tmp_dic = {'graph GT\n(proportional)\napprox':'Approx\nGED', 'conv\norig\navg fp':'RN', 'RMAC':'RMAC'}

    for o_idx,o in enumerate(orders):
        _,ordered_dist,permut = o.get(query_idx, False, min_length=15000, keep_orig_consistency=True)
        n_permut = permut[:n]
        row = []
        #n_permut_v = [v + 1 for v in n_permut]
        for idx,p in enumerate(n_permut):
            image = image_loader.get(p)
            if idx == 0:
                row = image
                row = np.concatenate((row, separator), axis=1)
            else:
                row = np.concatenate((row, image, separator), axis=1)
        axs = plt.subplot(gs[o_idx+1, 0])
        #axs.set_title(tmp_dic[o.get_name()], loc='left')
        axs.set_ylabel(tmp_dic[o.get_name()], labelpad=17, rotation='horizontal')
        axs.set_yticklabels([])
        x = np.arange(240,480*n-230,480)
        labels = ['{:.5e}'.format(d) for d in ordered_dist[:n]]
        #axs.set_xticks(x)
        #axs.set_xticklabels(labels)
        axs.set_xticks([])
        axs.set_xticklabels([])
        axs.imshow(row)
    
    return fig

if __name__ == '__main__':
    parser = argparse.ArgumentParser(description='Rankings visualization')
    parser.add_argument('--from-idx', type=int, default=0,
                        help='index of the image to use as query')
    parser.add_argument('--to-idx', type=int, default=5,
                        help='index of the last query image to include in results')
    parser.add_argument('--normalize', action='store_true', default=False,
                        help='enables features normalization')
    parser.add_argument('--clevr-dir', type=str, default='.',
                        help='CLEVR dataset base dir')
    parser.add_argument('--n', type=int, default=10,
                        help='number of images for every row')
    parser.add_argument('--scale', type=float, default=0.5,
                        help='final image scale factor')
    args = parser.parse_args()

    feats_dir = './features'  

    #initialize orders objects
    print('Initializing all orderings...')
    orders = []
    #scene_json_filename = os.path.join(args.clevr_dir, 'scenes', 'CLEVR_val_scenes.json')
    orders.append(graphs_approx_order.GraphsApproxOrder(args.clevr_dir, 'proportional'))
    #orders.append(rn_order.RNOrder(os.path.join(feats_dir,'gfc2_avg_features_fp.pickle'), 'g_fc2\navg fp', args.normalize))
    orders.append(rn_order.RNOrder(os.path.join(feats_dir,'gfc0_avg_features_orig_noprenorm.pickle'), 'conv\norig\navg fp', args.normalize))
    orders.append(rmac_order.RMACOrder(os.path.join(feats_dir,'clevr_rmac_features.h5'),
        os.path.join(feats_dir,'clevr_rmac_features_order.txt'), args.normalize))
    
    #orders.append(graphs_order.GraphsOrder(scene_json_filename, 'proportional', 2))
    
    #orders.append(states_order.StatesOrder(scene_json_filename, mode='fuzzy', ncpu=2))

    #orders.append(rn_order.RNOrder(os.path.join(feats_dir,'avg_features_sd.pickle'), 'g_fc2_avg state description', args.normalize))
    

    #build images
    img_dir = os.path.join(args.clevr_dir,'images')
    img_loader = ClevrImageLoader(img_dir)
    with PdfPages('images_out.pdf') as pdf:
        progress = trange(args.from_idx, args.to_idx+1)
        for idx in progress:
            fig = build_figure(orders, img_loader, idx, args.n, args.scale)
            plt.savefig('img_out.png')
            pdf.savefig(fig)    
    
            
        

    