import typing as t
import torch
import torch.nn.functional as F
from torch import nn, Tensor

from .matcher import HungarianMatcher, Outputs, Targets, MatchIndecies
from .utils import box_cxcywh_to_xyxy, generalized_box_iou
from typing_extensions import TypedDict


Losses = TypedDict("Losses", {"box": Tensor, "label": Tensor,})


class SetCriterion(nn.Module):
    def __init__(
        self,
        num_classes: int,
        eos_coef: float = 1.0,
        matcher: HungarianMatcher = HungarianMatcher(),
    ) -> None:
        super().__init__()
        self.matcher = matcher
        self.num_classes = num_classes
        self.eos_coef = eos_coef
        weight = torch.ones(self.num_classes + 1)
        weight[-1] = self.eos_coef
        self.weight = weight

    def forward(self, outputs: Outputs, targets: Targets) -> Tensor:
        indices = self.matcher(outputs, targets)
        num_boxes = sum(len(t["labels"]) for t in targets)
        src_logits = outputs["pred_logits"]
        tgt_lables = [t["labels"] for t in targets]

        loss_label = self.loss_labels(src_logits, tgt_lables, indices)
        loss_box = self.loss_boxes(outputs, targets, indices, num_boxes)
        #  print(f"{loss_giou=}")
        return (
            loss_label
            + loss_box
            #  + loss_cardinality
            #  + config.loss_giou * loss_giou
        )

    def loss_cardinality(
        self, outputs: Outputs, targets: Targets, indices: MatchIndecies, num_boxes: int
    ) -> Tensor:
        """ Compute the cardinality error, ie the absolute error in the number of predicted non-empty boxes
        This is not really a loss, it is intended for logging purposes only. It doesn't propagate gradients
        """
        pred_logits = outputs["pred_logits"]
        device = pred_logits.device
        tgt_lengths = torch.as_tensor(
            [len(v["labels"]) for v in targets], device=device
        )

        # Count the number of predictions that are NOT "no-object" (which is the last class)
        card_pred = (pred_logits.argmax(-1) != pred_logits.shape[-1] - 1).sum(1)

        card_err = F.l1_loss(card_pred.float(), tgt_lengths.float())
        return card_err

    def loss_boxes(
        self, outputs: Outputs, targets: Targets, indices: MatchIndecies, num_boxes: int
    ) -> Tensor:
        idx = self._get_src_permutation_idx(indices)
        pred_boxes = outputs["pred_boxes"][idx]
        target_boxes = torch.cat(
            [t["boxes"][i] for t, (_, i) in zip(targets, indices)], dim=0
        )
        loss_box = (
            F.smooth_l1_loss(pred_boxes, target_boxes, reduction="none").sum()
            / num_boxes
        )
        return loss_box

    def loss_labels(
        self, src_logits: Tensor, tgt_lables: t.List[Tensor], indices: MatchIndecies
    ) -> Tensor:
        device = src_logits.device
        idx = self._get_src_permutation_idx(indices)
        tgt_classes_o = torch.cat([t[i] for t, (_, i) in zip(tgt_lables, indices)])

        # fill no-object class
        # the no-object class is the last class equal to self.num_classes
        tgt_classes = torch.full(
            src_logits.shape[:2],
            self.num_classes,
            dtype=torch.int64,
            device=src_logits.device,  # type: ignore
        )

        # tgt_classes contains object class and no-object class
        tgt_classes[idx] = tgt_classes_o
        loss_ce = F.cross_entropy(
            src_logits.transpose(1, 2), tgt_classes, weight=self.weight.to(device)  # type: ignore
        )
        return loss_ce

    def _get_src_permutation_idx(
        self, indices: MatchIndecies
    ) -> t.Tuple[Tensor, Tensor]:
        # permute predictions following indices
        batch_idx = torch.cat(
            [torch.full_like(src, i) for i, (src, _) in enumerate(indices)]
        )
        src_idx = torch.cat([src for (src, _) in indices])
        return batch_idx, src_idx
