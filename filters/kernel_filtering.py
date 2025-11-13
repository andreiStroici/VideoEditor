from typing import List
from filters.filters_interface import Filters
from PySide6.QtCore import QTimeLine

class KernelFiltering(Filters):
    def __init__(self, kernel: List[List[float]], normalize: bool = True):
        if not kernel or not all(isinstance(row, list) for row in kernel):
            raise ValueError("Kernel trebuie sa fie o lista de liste.")

        rows = len(kernel)
        cols = len(kernel[0])

        self.kernel = kernel
        self.normalize = normalize
        self.size = rows

    def applyFilter(self, qTimeLine: QTimeLine) -> QTimeLine:
        kernel_flat = []
        for row in self.kernel:
            kernel_flat.extend(row)

        kernel_str = " ".join(map(str, kernel_flat))
        normalize_val = "1" if self.normalize else "0"

        filter_str = f"convolution='{kernel_str}:{kernel_str}:{kernel_str}:{kernel_str}':0m:{normalize_val}:{normalize_val}:{normalize_val}:{normalize_val}:0:128:128:128"

        return self._apply_ffmpeg(qTimeLine, filter_str, "video")
