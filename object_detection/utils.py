import torch
from typing import *
from torch import Tensor
from PIL import Image, ImageDraw
import json
import random
import numpy as np
import torch.nn.functional as F
from typing import Dict, Optional
from torch import nn
from pathlib import Path
from torch import Tensor
from logging import getLogger
from .entities.box import (
    CoCoBoxes,
    YoloBoxes,
    PascalBoxes,
    Labels,
    yolo_to_coco,
    pascal_to_coco,
)
from torchvision.utils import save_image
from torch.nn.functional import interpolate

logger = getLogger(__name__)


def init_seed(seed: int = 777) -> None:
    random.seed(seed)
    np.random.seed(seed)
    torch.manual_seed(seed)  # type: ignore
    torch.cuda.manual_seed(seed)  # type: ignore


colors = [
    "green",
    "red",
    "blue",
]


class DetectionPlot:
    def __init__(
        self,
        img: torch.Tensor,
        box_limit: int = 500,
    ) -> None:
        self.img = self.to_image(img * 255)
        self.draw = ImageDraw.Draw(self.img)
        self.box_limit = box_limit

    def to_image(self, img: torch.Tensor) -> Image:
        if img.ndim == 2:
            ndarr = img.to("cpu", torch.uint8).numpy()
        elif img.ndim == 3:
            ndarr = img.to("cpu", torch.uint8).permute(1, 2, 0).numpy()
        else:
            raise ValueError("invalid shape")
        return Image.fromarray(ndarr)

    def save(self, path: Union[str, Path]) -> None:
        self.img.save(path)

    @torch.no_grad()
    def draw_boxes(
        self,
        boxes: PascalBoxes,
        confidences: Optional[Tensor] = None,
        labels: Optional[Tensor] = None,
        color: str = "white",
        line_width: int = 1,
    ) -> None:
        _labels = labels.tolist() if labels is not None else []
        for i, box in enumerate(boxes[: self.box_limit].tolist()):
            self.draw.rectangle(box, width=line_width, outline=color)
            label = "{}".format(labels[i]) if labels is not None else ""
            confidence = (
                "{:.3f}".format(float(confidences[i]))
                if confidences is not None
                else ""
            )
            self.draw.text((box[0], box[1]), f"{label} {confidence}", fill=color)
