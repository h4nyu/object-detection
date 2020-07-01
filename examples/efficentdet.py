import torch
from torch.utils.data import DataLoader
from object_detection.models.backbones import EfficientNetBackbone
from object_detection.models.efficientdet import (
    collate_fn,
    EfficientDet,
    Trainer,
    Criterion,
    Visualize,
)
from object_detection.model_loader import ModelLoader
from object_detection.data.object import ObjectDataset
from logging import getLogger, StreamHandler, Formatter, INFO, FileHandler

logger = getLogger()
logger.setLevel(INFO)
stream_handler = StreamHandler()
stream_handler.setLevel(INFO)
handler_format = Formatter("%(asctime)s|%(name)s|%(message)s")
stream_handler.setFormatter(handler_format)
logger.addHandler(stream_handler)

train_dataset = ObjectDataset(
    (256, 256), object_count_range=(1, 20), object_size_range=(32, 64), num_samples=256
)
test_dataset = ObjectDataset(
    (256, 256), object_count_range=(1, 20), object_size_range=(32, 64), num_samples=8
)
channels = 64
backbone = EfficientNetBackbone(1, out_channels=channels, pretrained=True)
model = EfficientDet(num_classes=1, channels=channels, backbone=backbone)
model_loader = ModelLoader("/store/efficientdet")
criterion = Criterion()
optimizer = torch.optim.Adam(model.parameters(), lr=1e-3)
visualize = Visualize("/store/efficientdet", "test", limit=2)
trainer = Trainer(
    model,
    DataLoader(
        train_dataset, collate_fn=collate_fn, batch_size=4, num_workers=8, shuffle=True,
    ),
    DataLoader(
        test_dataset, collate_fn=collate_fn, batch_size=2, num_workers=8, shuffle=True
    ),
    model_loader=model_loader,
    optimizer=optimizer,
    visualize=visualize,
    criterion=criterion,
    device="cuda",
)
trainer.train(1000)
