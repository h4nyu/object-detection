import torch
from app.models.efficent_det import (
    ClipBoxes,
    BBoxTransform,
    RegressionModel,
    ClassificationModel,
)


def test_clip_boxes() -> None:
    images = torch.ones((1, 1, 10, 10))
    boxes = torch.Tensor([[[14, 0, 20, 0]]])
    fn = ClipBoxes()
    res = fn(boxes, images)

    assert (
        res - torch.Tensor([[[14, 0, 10, 0]]])
    ).sum() == 0  # TODO ??? [10, 0, 10, 0]


def test_bbox_transform() -> None:
    boxes = torch.Tensor([[[2, 2, 20, 6], [4, 2, 8, 6],]])

    deltas = torch.Tensor([[[0.1, 0.1, 0.1, 0.1], [0.1, 0.1, 0.1, 0.1],]])
    fn = BBoxTransform()
    res = fn(boxes, deltas)


def test_regression_model() -> None:
    images = torch.ones((1, 1, 10, 10))
    fn = RegressionModel(1, num_anchors=9)
    res = fn(images)
    assert res.shape == (1, 900, 4)


def test_classification_model() -> None:
    images = torch.ones((1, 100, 10, 10))
    fn = ClassificationModel(num_features_in=100, num_classes=2)
    res = fn(images)
    assert res.shape == (1, 900, 2)
    print(res.shape)
