import torch
from typing import NewType, Tuple, Callable, Union
from torch import Tensor
from torchvision.ops.boxes import box_iou, box_area
from .image import ImageSize

CoCoBoxes = NewType(
    "CoCoBoxes", Tensor
)  # [B, Pos] Pos:[x0, y0, width, height] original torch.int32
YoloBoxes = NewType(
    "YoloBoxes", Tensor
)  # [B, Pos] Pos:[cx, cy, width, height] normalized
PascalBoxes = NewType(
    "PascalBoxes", Tensor
)  # [B, Pos] Pos:[x0, y0, x1, y1] original torch.int32

FcosBoxes = NewType(
    "FcosBoxes", Tensor
)  # [B, Pos] Pos:[l, t, r, b] original torch.int32
BoxMaps = NewType("BoxMaps", Tensor)  # [B, 4, H, W]
BoxMap = NewType("BoxMap", Tensor)  # [4, H, W]
Nummber = Union[float, int]


AnchorMap = NewType("AnchorMap", Tensor)  # [N, [H, W]], H, W]

Labels = NewType("Labels", Tensor)
Confidences = NewType("Confidences", Tensor)

PredBoxes = Tuple[CoCoBoxes, Confidences]
LabelBoxes = Tuple[CoCoBoxes, Labels]

YoloBoxBatch = NewType("YoloBoxBatch", Tensor)  # [B, N, 4]
ConfidenceBatch = NewType("ConfidenceBatch", Tensor)  # [B, N] 0.0 ~ 1.0


def boxmap_to_boxes(x: BoxMap) -> YoloBoxes:
    return YoloBoxes(x.permute(2, 1, 0).reshape(-1, 4))


def boxmaps_to_boxes(x: BoxMaps) -> YoloBoxes:
    return YoloBoxes(x.permute(3, 2, 0, 1).reshape(-1, 4))


def resize(boxes: PascalBoxes, scale: Tuple[float, float]) -> PascalBoxes:
    if len(boxes) == 0:
        return boxes
    wr, hr = scale
    x0, y0, x1, y1 = boxes.unbind(-1)
    b = [
        x0 * wr,
        y0 * hr,
        x1 * wr,
        y1 * hr,
    ]
    return PascalBoxes(torch.stack(b, dim=-1))


def coco_to_yolo(coco: CoCoBoxes, size: ImageSize) -> YoloBoxes:
    if len(coco) == 0:
        return YoloBoxes(coco)
    size_w, size_h = size
    x0, y0, x1, y1 = coco_to_pascal(coco).float().unbind(-1)
    b = [
        (x0 + x1) / 2 / size_w,
        (y0 + y1) / 2 / size_h,
        (x1 - x0) / size_w,
        (y1 - y0) / size_h,
    ]
    return YoloBoxes(torch.stack(b, dim=-1))


def coco_to_pascal(coco: CoCoBoxes) -> PascalBoxes:
    if len(coco) == 0:
        return PascalBoxes(coco)
    x0, y0, w, h = coco.unbind(-1)
    b = [x0, y0, x0 + w, y0 + h]
    return PascalBoxes(torch.stack(b, dim=-1))


def yolo_to_pascal(yolo: YoloBoxes, wh: ImageSize) -> PascalBoxes:
    if len(yolo) == 0:
        return PascalBoxes(yolo)
    image_w, image_h = wh
    cx, cy, w, h = yolo.unbind(-1)
    size_w, size_h = wh
    b = [
        ((cx - 0.5 * w) * size_w),
        ((cy - 0.5 * h) * size_h),
        ((cx + 0.5 * w) * size_w),
        ((cy + 0.5 * h) * size_h),
    ]
    return PascalBoxes(torch.stack(b, dim=-1))


def yolo_to_coco(yolo: YoloBoxes, size: ImageSize) -> CoCoBoxes:
    if len(yolo) == 0:
        return CoCoBoxes(yolo)
    x0, y0, x1, y1 = yolo_to_pascal(yolo, size).unbind(-1)
    b = torch.stack([x0, y0, x1 - x0, y1 - y0], dim=-1)
    return CoCoBoxes(b)


def pascal_to_yolo(pascal: PascalBoxes, size: ImageSize) -> YoloBoxes:
    if len(pascal) == 0:
        return YoloBoxes(pascal)
    x0, y0, x1, y1 = pascal.float().unbind(-1)
    size_w, size_h = size
    b = [
        (x0 + x1) / 2 / size_w,
        (y0 + y1) / 2 / size_h,
        (x1 - x0) / size_w,
        (y1 - y0) / size_h,
    ]
    return YoloBoxes(torch.stack(b, dim=-1))


def pascal_to_coco(pascal: PascalBoxes) -> CoCoBoxes:
    if len(pascal) == 0:
        return CoCoBoxes(pascal)
    x0, y0, x1, y1 = pascal.unbind(-1)
    b = [
        x0,
        y0,
        (x1 - x0),
        (y1 - y0),
    ]
    return CoCoBoxes(torch.stack(b, dim=-1))


def yolo_hflip(yolo: YoloBoxes) -> YoloBoxes:
    if len(yolo) == 0:
        return yolo
    cx, cy, w, h = yolo.unbind(-1)
    b = [
        1.0 - cx,
        cy,
        w,
        h,
    ]
    return YoloBoxes(torch.stack(b, dim=-1))


def yolo_vflip(yolo: YoloBoxes) -> YoloBoxes:
    cx, cy, w, h = yolo.unbind(-1)
    b = [
        cx,
        1.0 - cy,
        w,
        h,
    ]
    return YoloBoxes(torch.stack(b, dim=-1))


def yolo_clamp(yolo: YoloBoxes) -> YoloBoxes:
    return pascal_to_yolo(
        PascalBoxes(yolo_to_pascal(yolo, (1, 1)).clamp(min=0.0, max=1.0)),
        (1, 1),
    )


def box_clamp(boxes: PascalBoxes, width: int, height: int) -> PascalBoxes:
    if len(boxes) == 0:
        return boxes
    x0, y0, x1, y1 = boxes.clamp(min=0).unbind(-1)
    x0 = x0.clamp(max=width)
    x1 = x1.clamp(max=width)
    y0 = y0.clamp(max=height)
    y1 = y1.clamp(max=height)
    return PascalBoxes(torch.stack([x0, y0, x1, y1], dim=-1))


def shift(boxes: PascalBoxes, diff: Tuple[Nummber, Nummber]) -> PascalBoxes:
    if len(boxes) == 0:
        return boxes
    diff_x, diff_y = diff
    boxes[:, [0, 2]] = boxes[:, [0, 2]] + diff_x
    boxes[:, [1, 3]] = boxes[:, [1, 3]] + diff_y
    return PascalBoxes(boxes)


def filter_size(
    boxes: PascalBoxes, cond: Callable[[Tensor], Tensor]
) -> Tuple[PascalBoxes, Tensor]:
    if len(boxes) == 0:
        return boxes, torch.tensor([], dtype=torch.bool)
    x0, y0, x1, y1 = boxes.unbind(-1)
    area = (x1 - x0) * (y1 - y0)
    indices = cond(area)
    return PascalBoxes(boxes[indices]), indices


def box_in_area(
    boxes: PascalBoxes,
    area: Tensor,
    min_fill: float = 0.7,
) -> Tensor:
    if len(boxes) == 0:
        return torch.zeros(0, dtype=torch.long, device=boxes.device)
    lt = torch.max(boxes[:, :2], area[:2])
    rb = torch.min(boxes[:, 2:], area[2:])
    wh = (rb - lt).clamp(min=0)
    overlaped_area = wh[:, 0] * wh[:, 1]
    areas = box_area(boxes)
    fill_ratio = overlaped_area / areas
    indices = fill_ratio > min_fill
    return indices


def box_hflip(boxes: PascalBoxes, image_size: Tuple[Nummber, Nummber]) -> PascalBoxes:
    if len(boxes) == 0:
        return boxes
    w, h = image_size
    box_w = boxes[:, 2] - boxes[:, 0]
    boxes[:, 0] = w - boxes[:, 0] - box_w
    boxes[:, 2] = w - boxes[:, 2] + box_w
    return PascalBoxes(boxes)


def box_vflip(boxes: PascalBoxes, image_size: Tuple[Nummber, Nummber]) -> PascalBoxes:
    if len(boxes) == 0:
        return boxes
    w, h = image_size
    box_h = boxes[:, 3] - boxes[:, 1]
    boxes[:, 1] = h - boxes[:, 1] - box_h
    boxes[:, 3] = h - boxes[:, 3] + box_h
    return PascalBoxes(boxes)
