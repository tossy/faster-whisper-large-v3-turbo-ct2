# 改善履歴

## 2025-12-26: mlx-whisper への移行
**問題**: faster-whisper (CTranslate2) は CPU のみ使用で、Apple Silicon M3 の性能を活かせない
**解決策**: mlx-whisper を導入。MLX フレームワークにより Apple Silicon の GPU/Neural Engine を活用
**成果**:
- M3 チップに最適化された高速推論
- 複数出力フォーマット対応 (txt, json, srt, vtt, tsv)
- 単語レベルタイムスタンプ機能
**教訓**: ハードウェアに最適化されたライブラリ選択が重要

## 2025-06-17: 進捗バーの導入
**問題**: 長時間処理時の進捗が分かりづらい
**試行錯誤**: tqdm 導入で解決
**教訓**: ユーザー体験向上には進捗可視化が有効
