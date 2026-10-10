import sys, random
from pathlib import Path
from PIL import Image
sys.path.insert(0, 'deepfake_model')
from detector import DeepfakeDetector

root = Path('scamai-deepfake-detector-dataset-main')
random.seed(1)
det = DeepfakeDetector()
for label in ('fake', 'real'):
    folders = [p for p in root.rglob('*') if p.is_dir() and p.name.lower() == label]
    if not folders:
        print('no', label, 'folder found')
        continue
    files = [f for f in folders[0].iterdir() if f.suffix.lower() in ('.jpg', '.jpeg', '.png', '.webp')]
    sample = random.sample(files, min(15, len(files)))
    counts = {'REAL': 0, 'FAKE': 0, 'UNCERTAIN': 0}
    for f in sample:
        counts[det.predict(Image.open(f))['verdict']] += 1
    print(label, 'folder:', folders[0].name, '| tested:', len(sample), '|', counts)
