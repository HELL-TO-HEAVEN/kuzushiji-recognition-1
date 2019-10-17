"""
Unittest for classification model.
"""


import numpy as np
from PIL import Image

from kr.classifier.softmax.resnet import Resnet18


class TestResnet18:

    def test_forward(self):

        model = Resnet18(20)
        x = np.random.uniform(-1, 1, (2, 3, 64, 64)).astype(np.float32)
        h = model(x)
        assert h.shape == (2, 20)

    def test_classify(self):
        model = Resnet18(20)
        img = Image.new('RGB', (500, 300))
        bboxes = np.array([[10, 10, 20, 20],
                           [30, 30, 50, 50]])

        labels, scores = model.classify(img, bboxes)

        assert labels.shape == (2,)
        assert scores.shape == (2,)