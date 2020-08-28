import os

home = os.environ['HOME']
#folder_root = os.path.join(home,'data/trojai-round0-dataset')
#folder_root = os.path.join(home,'data/round1-dataset-train/models/')
folder_root = os.path.join(home,'/home/huthvincent/Desktop/newDisk/trojanAI/version/v02/0-199')
dirs = os.listdir(folder_root)

k = 0
for d in dirs:
    model_filepath=os.path.join(folder_root, d, 'model.pt')
    print(model_filepath)
    examples_dirpath=os.path.join(folder_root, d, 'example_data')


    cmmd = 'timeout 600 python3 trojan_detector.py --model_filepath='+model_filepath+' --examples_dirpath='+examples_dirpath

    print(cmmd)
    os.system(cmmd)
  
