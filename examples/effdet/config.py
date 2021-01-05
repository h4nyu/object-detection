from typing import *
from object_detection.model_loader import WatchMode

confidence_threshold = 0.5
iou_threshold = 0.60
batch_size = 6

# model
backbone_id = 1
channels = 64
box_depth = 2
lr = 1e-4
out_ids: List[int] = [4, 5, 6]


input_size = (512, 512)
object_count_range = (5, 20)
object_size_range = (32, 64)
out_dir = "/store/efficientdet"
metric: Tuple[str, WatchMode] = ("score", "max")
pretrained = True

# criterion
topk = 39
box_weight = 20
cls_weight = 1

anchor_ratios = [1.0]
anchor_scales = [1.0, 1.25, 1.5, 1.75]
anchor_size = 2
