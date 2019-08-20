"""
Kuzushiji dataset
"""


from collections import Counter
import json
from pathlib import Path
from typing import Optional

from chainer.dataset import DatasetMixin
import numpy as np
import pandas as pd
from PIL import Image


_prj_root = Path(__file__).resolve().parent.parent.parent
_dataset_dir = _prj_root / 'data' / 'kuzushiji-recognition'
_converted_dir = _prj_root / 'data' / 'kuzushiji-recognition-converted'


class KuzushijiRecognitionDataset(DatasetMixin):
    """Kaggle Kuzushiji Recognition training dataset."""

    def __init__(self, split: Optional[str] = None) -> None:
        assert _dataset_dir.exists(), \
                ('Download Kaggle Kuzushiji Recognition dataset '
                 'and move files to <prj>/data/kuzushiji-recognition/')

        if split is None or split == 'trainval':
            csv_path = _dataset_dir / 'train.csv'
        elif split in ('train', 'val'):
            csv_path = _converted_dir / f'{split}.csv'

        self.table = pd.read_csv(csv_path)
        self.image_dir = _dataset_dir / 'train_images'

    def __len__(self) -> int:
        return len(self.table)

    def get_example(self, i: int) -> dict:
        row = self.table.iloc[i]

        image = Image.open(self.image_dir / (row.image_id + '.jpg'))

        try:
            labels = row.labels.split()
            unicodes = labels[0::5]
            x = [int(v) for v in labels[1::5]]
            y = [int(v) for v in labels[2::5]]
            w = [int(v) for v in labels[3::5]]
            h = [int(v) for v in labels[4::5]]
            bboxes = np.transpose(np.array([x, y, w, h]))
            bboxes[:, 2:4] += bboxes[:, 0:2]  # (x1, y1, x2, y2)
        except AttributeError:
            unicodes = []
            bboxes = np.empty((0, 4), dtype=np.int)

        return {'image': image, 'bboxes': bboxes, 'unicodes': unicodes}


class KuzushijiUnicodeMapping:
    """Unicode translation data."""

    def __init__(self) -> None:
        csv_path = _dataset_dir / 'unicode_translation.csv'

        self._unicode_to_char = {}
        self._index_to_unicode = {}
        self._unicode_to_index = {}

        with csv_path.open() as f:
            lines = f.readlines()

        for i, line in enumerate(lines[1:]):
            uni, char = line.strip().split(',')
            self._unicode_to_char[uni] = char
            self._index_to_unicode[i] = uni
            self._unicode_to_index[uni] = i

    def __len__(self) -> int:
        return len(self._unicode_to_char)

    def unicode_to_char(self, unicode: str) -> str:
        return self._unicode_to_char[unicode]

    def index_to_unicode(self, index: int) -> str:
        return self._index_to_unicode[index]

    def unicode_to_index(self, unicode: str) -> int:
        return self._unicode_to_index[unicode]


class KuzushijiCharCropDataset(DatasetMixin):
    """Kuzushiji cropped character image dataset."""

    def __init__(self, split: Optional[str] = None) -> None:
        split = split or 'trainval'
        assert split in ('train', 'val', 'trainval')

        self.dir_path = _converted_dir
        annt = json.load((_converted_dir / f'char_images_{split}.json').open())
        self.data = annt['annotations']
        self.mapping = KuzushijiUnicodeMapping()

        self.num_samples = np.ones(len(self.mapping), dtype=np.int32)
        count = Counter([d['unicode'] for d in self.data])
        for unicode, num_samples in count.most_common():
            idx = self.mapping.unicode_to_index(unicode)
            self.num_samples[idx] = num_samples

    def __len__(self) -> int:
        return len(self.data)

    def get_example(self, i) -> dict:
        data = self.data[i]
        data = data.copy()
        data['image'] = Image.open(self.dir_path / data['image_path'])
        data['label'] = self.mapping.unicode_to_index(data['unicode'])
        return data


class KuzushijiTestImages(DatasetMixin):
    """Test image set of Kaggle Kuzushiji Recognition."""

    def __init__(self) -> None:
        image_dir = _dataset_dir / 'test_images'
        self.image_paths = sorted(image_dir.iterdir())

    def __len__(self) -> int:
        return len(self.image_paths)

    def get_example(self, i) -> dict:
        image_path = self.image_paths[i]

        data = {
            'image': Image.open(image_path),
            'image_id': image_path.stem
        }
        return data
