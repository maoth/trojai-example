# NIST-developed software is provided by NIST as a public service. You may use, copy and distribute copies of the software in any medium, provided that you keep intact this entire notice. You may improve, modify and create derivative works of the software or any portion of the software, and you may copy and distribute such modifications or works. Modified works should carry a notice stating that you changed the software and should note the date and nature of any such change. Please explicitly acknowledge the National Institute of Standards and Technology as the source of the software.

# NIST-developed software is expressly provided "AS IS." NIST MAKES NO WARRANTY OF ANY KIND, EXPRESS, IMPLIED, IN FACT OR ARISING BY OPERATION OF LAW, INCLUDING, WITHOUT LIMITATION, THE IMPLIED WARRANTY OF MERCHANTABILITY, FITNESS FOR A PARTICULAR PURPOSE, NON-INFRINGEMENT AND DATA ACCURACY. NIST NEITHER REPRESENTS NOR WARRANTS THAT THE OPERATION OF THE SOFTWARE WILL BE UNINTERRUPTED OR ERROR-FREE, OR THAT ANY DEFECTS WILL BE CORRECTED. NIST DOES NOT WARRANT OR MAKE ANY REPRESENTATIONS REGARDING THE USE OF THE SOFTWARE OR THE RESULTS THEREOF, INCLUDING BUT NOT LIMITED TO THE CORRECTNESS, ACCURACY, RELIABILITY, OR USEFULNESS OF THE SOFTWARE.

# You are solely responsible for determining the appropriateness of using and distributing the software and you assume all risks associated with its use, including but not limited to the risks and costs of program errors, compliance with applicable laws, damage to or loss of data, programs or equipment, and the unavailability or interruption of operation. This software is not intended to be used in any situation where a failure could cause risk of injury or damage to property. The software developed by NIST employees is not subject to copyright protection within the United States.

import time
import os
import numpy as np
import random
import torch
import torchvision.models
import warnings
warnings.filterwarnings("ignore")

from torch.utils.data import TensorDataset, DataLoader

import utils
from NC_pytorch import Visualizer
from neuron import NeuronAnalyzer

ava_model_type = ['ResNet', 'DenseNet','Inception3']

def build_data_loader(X,Y, batch_size=2):
    tensor_X = torch.Tensor(X)
    tensor_Y = torch.Tensor(Y)
    dataset = TensorDataset(tensor_X, tensor_Y)
    loader = DataLoader(dataset,batch_size=batch_size,drop_last=False, shuffle=False)
    return loader


def fake_trojan_detector(model_filepath, result_filepath, scratch_dirpath, examples_dirpath, example_img_format='png'):

    print('model_filepath = {}'.format(model_filepath))
    print('result_filepath = {}'.format(result_filepath))
    print('scratch_dirpath = {}'.format(scratch_dirpath))
    print('examples_dirpath = {}'.format(examples_dirpath))

    cat_batch = utils.read_example_images(examples_dirpath, example_img_format)


    num_classes=len(cat_batch)
    model = torch.load(model_filepath)
    analyzer = NeuronAnalyzer(model, num_classes)
    all_x = np.concatenate([cat_batch[i]['images'] for i in range(num_classes)])
    all_y = np.concatenate([cat_batch[i]['labels'] for i in range(num_classes)])
    dataloader = build_data_loader(all_x, all_y)

    sc = analyzer.analyse(dataloader)

    trojan_probability = np.min(sc)
    print('Trojan Probability: {}'.format(trojan_probability))
    with open(result_filepath, 'w') as fh:
        fh.write("{}".format(trojan_probability))

    model_name = model_filepath.split('/')[-2]
    np.save(os.path.join('output/', model_name), np.asarray(sc))

    exit(0)


    #visualizer = Visualizer(model, init_cost=1e-3, lr=0.1, \
    #                        num_classes=num_classes, tmp_dir=scratch_dirpath)

    rst_l1_norm = np.zeros((num_classes,num_classes))

    all_x = [cat_batch[i] for i in range(num_classes)]
    big_batch = np.concatenate(all_x, axis=0)

    #for source_lb in range(num_classes):
    source_lb = 0
    for target_lb in range(num_classes):
        #if target_lb==source_lb:
        #  continue
        pattern = np.random.random([3,224,224])*255.0
        mask = np.random.random([224,224])
        #dataloader = build_data_loader(cat_batch[source_lb])
        dataloader = build_data_loader(big_batch)

        visualize_start_time = time.time()

        #pattern, mask, mask_upsample, logs = visualizer.visualize(dataloader, y_target=target_lb, pattern_init=pattern, mask_init=mask, max_steps=1000, num_batches_per_step=9)
        #pattern, mask, mask_upsample, logs = visualizer.visualize(dataloader, y_target=target_lb, pattern_init=pattern, mask_init=mask, max_steps=1000, num_batches_per_step=16)

        visualize_end_time = time.time()

        # meta data about the generated mask
        print('pattern, shape: %s, min: %f, max: %f' %
              (str(pattern.shape), np.min(pattern), np.max(pattern)))
        print('mask, shape: %s, min: %f, max: %f' %
              (str(mask.shape), np.min(mask), np.max(mask)))
        print('mask norm of %d to %d: %f' %
              (source_lb, target_lb, np.sum(np.abs(mask_upsample))))

        print('visualization cost %f seconds' %
              (visualize_end_time - visualize_start_time))

        #utils.save_pattern(pattern, mask_upsample, source_lb, target_lb, scratch_dirpath)

        l1_norm = np.sum(np.abs(mask))
        print('src: %d, tgt: %d, l1-norm: %f'%(source_lb,target_lb,l1_norm))
        rst_l1_norm[source_lb][target_lb] = l1_norm

    print(rst_l1_norm)
    #model_name = model_filepath.split('/')[-2]
    #np.save(os.path.join('output/', model_name), rst_l1_norm)


    #trojan_probability = np.random.rand()
    trojan_probability = 1-np.min(rst_l1_norm[0])/np.max(rst_l1_norm[0])
    print('Trojan Probability: {}'.format(trojan_probability))

    with open(result_filepath, 'w') as fh:
        fh.write("{}".format(trojan_probability))


if __name__ == "__main__":
    import argparse

    parser = argparse.ArgumentParser(description='Fake Trojan Detector to Demonstrate Test and Evaluation Infrastructure.')
    parser.add_argument('--model_filepath', type=str, help='File path to the pytorch model file to be evaluated.', default='./model.pt')
    parser.add_argument('--result_filepath', type=str, help='File path to the file where output result should be written. After execution this file should contain a single line with a single floating point trojan probability.', default='./output.txt')
    parser.add_argument('--scratch_dirpath', type=str, help='File path to the folder where scratch disk space exists. This folder will be empty at execution start and will be deleted at completion of execution.', default='./scratch/')
    parser.add_argument('--examples_dirpath', type=str, help='File path to the folder of examples which might be useful for determining whether a model is poisoned.', default='./example/')


    args = parser.parse_args()
    fake_trojan_detector(args.model_filepath, args.result_filepath, args.scratch_dirpath, args.examples_dirpath)


