# よく使用するパターン

## 進捗バー付き処理
```python
from tqdm import tqdm
for item in tqdm(items):
    process(item)
```

## 設定ファイルの読み込み
```python
import yaml
with open('config.yaml') as f:
    config = yaml.safe_load(f)
```
