"""AI-generated image detector: ensemble of two Xception checkpoints.

Label convention used in training: fake = 0, real = 1.
"""
from pathlib import Path

import numpy as np
import timm
import torch
from PIL import Image, ImageOps
from torchvision import transforms

CROP = 299
HERE = Path(__file__).parent

# mode "crops"  = grid of native-resolution 299x299 crops (how v2 was trained/tested)
# mode "resize" = whole image resized to 299x299 (use if v3 was trained on resized faces)
DEFAULT_MODELS = [
    {"name": "v2", "path": HERE / "deepfake_xception_v2.pth", "mode": "crops",  "weight": 1.0},
    {"name": "v3", "path": HERE / "deepfake_xception_v3.pth", "mode": "crops",  "weight": 1.0},
]


class DeepfakeDetector:
    def __init__(self, models=None, grid=3,
                 uncertain_low=0.35, uncertain_high=0.65,
                 max_spread=0.20, max_model_gap=0.40):
        self.device = "cuda" if torch.cuda.is_available() else "cpu"
        self.grid = grid
        self.low, self.high = uncertain_low, uncertain_high
        self.max_spread, self.max_gap = max_spread, max_model_gap

        self.cfgs = models or DEFAULT_MODELS
        self.nets = []
        for cfg in self.cfgs:
            net = timm.create_model("legacy_xception", pretrained=False, num_classes=2)
            state = torch.load(str(cfg["path"]), map_location=self.device, weights_only=True)
            net.load_state_dict(state)
            self.nets.append(net.eval().to(self.device))

        self.tf = transforms.Compose([
            transforms.ToTensor(),
            transforms.Normalize([0.5] * 3, [0.5] * 3),
        ])

    def _crops(self, img: Image.Image):
        """Deterministic grid of native-resolution 299x299 crops."""
        w, h = img.size
        if w < CROP or h < CROP:  # pad small images with black, like training did
            canvas = Image.new("RGB", (max(w, CROP), max(h, CROP)), (0, 0, 0))
            canvas.paste(img, (0, 0))
            img, (w, h) = canvas, canvas.size
        xs = np.linspace(0, w - CROP, self.grid).round().astype(int)
        ys = np.linspace(0, h - CROP, self.grid).round().astype(int)
        return [img.crop((x, y, x + CROP, y + CROP)) for y in ys for x in xs]

    def _views(self, img: Image.Image, mode: str):
        if mode == "resize":
            return [img.resize((CROP, CROP), Image.BICUBIC)]
        return self._crops(img)

    @torch.no_grad()
    def _score(self, net, views):
        batch = torch.stack([self.tf(v) for v in views]).to(self.device)
        return torch.softmax(net(batch).float(), dim=1)[:, 1].cpu().numpy()

    @torch.no_grad()
    def predict(self, img: Image.Image) -> dict:
        img = ImageOps.exif_transpose(img).convert("RGB")

        per_model, means, weights, spreads, n_views = {}, [], [], [], 0
        for cfg, net in zip(self.cfgs, self.nets):
            views = self._views(img, cfg["mode"])
            p_each = self._score(net, views)
            m, s = float(p_each.mean()), float(p_each.std())
            per_model[cfg["name"]] = {"p_real": round(m, 3), "spread": round(s, 3)}
            means.append(m); weights.append(cfg.get("weight", 1.0)); spreads.append(s)
            n_views += len(views)

        p_real = float(np.average(means, weights=weights))
        spread = float(max(spreads))
        gap = float(max(means) - min(means))   # how much the models disagree

        if (self.low < p_real < self.high) or spread > self.max_spread or gap > self.max_gap:
            verdict = "UNCERTAIN"
        else:
            verdict = "REAL" if p_real >= 0.5 else "FAKE"

        return {
            "verdict": verdict,
            "p_real": round(p_real, 3),
            "p_fake": round(1 - p_real, 3),
            "spread": round(spread, 3),
            "model_gap": round(gap, 3),
            "per_model": per_model,
            "crops": n_views,
        }


if __name__ == "__main__":
    # Quick command-line test:  python detector.py path\to\image.jpg
    import sys
    if len(sys.argv) < 2:
        sys.exit("usage: python detector.py <image path>")
    print(DeepfakeDetector().predict(Image.open(sys.argv[1])))