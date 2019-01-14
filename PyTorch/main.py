import argparse
import os

import torch
from ignite.engine import Engine, Events
from ignite.handlers import EarlyStopping, ModelCheckpoint
from torch import nn, optim
from torch.utils.data import DataLoader, Dataset

import loader
import models

parser = argparse.ArgumentParser()
parser.add_argument('epochs', type=int, default=300,
                    help='number of epochs, default=300')
parser.add_argument('--points', type=int, default=1024,
                    help='number of points per sample, default=1024')
parser.add_argument('--lr', type=float, default=1e-3,
                    help='learning rate, default=1e-3')
parser.add_argument('--batch_size', type=int, default=64,
                    help='number of sets per batch, default=64')
parser.add_argument('--train_files',
                    default='./data/modelnet40_ply_hdf5_2048/train_files.txt')
parser.add_argument('--test_files',
                    default='./data/modelnet40_ply_hdf5_2048/test_files.txt')
rotation = parser.add_argument_group('rotation')
rotation.add_argument('--rotate', action='store_true',
                      help='apply rotation to data')
rotation.add_argument('--rotate_val', action='store_true',
                      help='apply rotation to validation data')
rotation.add_argument('--per_rotation', type=int, default=5,
                      help='how many epochs per rotation')
parser.add_argument('--cuda', type=str, default='0',
                    help='configure which cuda device to use')
args = parser.parse_args()


class PointCloud(Dataset):
    def __init__(self, train, label):
        super().__init__()
        self._train = torch.tensor(train, device=device)
        self._label = torch.tensor(label, device=device)
        assert len(self._train) == len(self._label)

    def __len__(self):
        return len(self._train)

    def __getitem__(self, index):
        return (self._train[index], self._label[index])


device = 'cuda:{}'.format(args.cuda) if torch.cuda.is_available() else 'cpu'

weight_dir = 'weights'

if not os.path.exists(weight_dir):
    os.makedirs(weight_dir)

(data, label), (test_data, test_label) = loader.load_data(
    args.train_files, args.test_files,
    num_points=args.points,
    shuffle=False,
    rotate=args.rotate,
    rotate_val=args.rotate_val
)

classifier = models.Classifier.to(device)

loss_fn = nn.CrossEntropyLoss()

optimizer = optim.Adam(classifier.parameters())

train_dataset = PointCloud(data, label)
test_dataset = PointCloud(test_data, test_label)
train_loader = DataLoader(train_dataset,
                          batch_size=args.batch_size,
                          shuffle=True)
test_loader = DataLoader(test_dataset,
                         batch_size=args.batch_size,
                         shuffle=False)


def step(engine, batch):
    pass


engine = Engine(step)

modelcheckpoint = ModelCheckpoint(dirname=weight_dir,
                                  filename_prefix='pointnet-classifier')
engine.add_event_handler(Events.EPOCH_COMPLETED, modelcheckpoint)


def acc(engine):
    pass


earlystopping = EarlyStopping(patience=10,
                              score_function=acc,
                              trainer=engine)
engine.add_event_handler(Events.EPOCH_COMPLETED, earlystopping)
