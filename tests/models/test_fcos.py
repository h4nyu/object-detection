import torch
from object_detection.models.fcos import (
    centerness,
    FocsBoxes,
    Head,
    FCOS,
    FPN,
    Anchor,
)
from object_detection.entities import ImageBatch
from object_detection.models.backbones.resnet import (
    ResNetBackbone,
)


def test_centerness() -> None:
    arg = FocsBoxes(torch.tensor([[10, 20, 5, 15]]))
    res = centerness(arg)
    assert (res - torch.tensor([0.6123])).abs()[0] < 1e-4


def test_head() -> None:
    channels = 32
    n_classes = 2
    fn = Head(depth=2, in_channels=channels, n_classes=n_classes)
    size = 128
    p3 = torch.rand(1, 32, size, size)
    p4 = torch.rand(1, 32, size * 2, size * 2)
    logit_maps, center_maps, box_maps = fn([p3, p4])
    assert logit_maps[0].shape == (1, n_classes, size, size)
    assert logit_maps[1].shape == (
        1,
        n_classes,
        size * 2,
        size * 2,
    )

    assert center_maps[0].shape == (1, 1, size, size)
    assert center_maps[1].shape == (
        1,
        1,
        size * 2,
        size * 2,
    )

    assert box_maps[0].shape == (1, 4, size, size)
    assert box_maps[1].shape == (1, 4, size * 2, size * 2)


def test_fcos() -> None:
    channels = 32
    size = 512
    backbone = ResNetBackbone("resnet34", out_channels=channels)
    fpn = FPN(channels=channels, depth=1)
    head = Head(in_channels=channels, n_classes=1, depth=1)
    fn = FCOS(backbone=backbone, fpn=fpn, head=head)
    image_batch = ImageBatch(torch.rand(1, 3, size, size))

    logits, centers, boxes = fn(image_batch)
    assert len(logits) == 5
    assert len(centers) == 5
    assert len(boxes) == 5


def test_anchor() -> None:
    batch_size = 2
    channels = 3
    width = 1
    height = 1
    features = [
        torch.rand(batch_size, channels, height, width),
    ]

    fn = Anchor(strides=[1])
    res = fn(features)
    assert len(res) == len(features)
    assert res[0].shape == (1, 2)


def test_criterion() -> None:
    batch_size = 2
    channels = 3
    width = 128
    height = 128
    strides = [1, 2]
    features = [
        torch.rand(batch_size, channels, height, width),
        torch.rand(batch_size, channels, height // 2, width // 2),
    ]

    locations = Anchor(strides=strides)(features)
