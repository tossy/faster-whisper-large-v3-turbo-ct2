# デバッグ記録

## [2026-01-03] YouTube プレイリストの最初の動画が .m4a になる問題
**症状**: プレイリストをダウンロードすると、最初の動画だけが .m4a (音声のみ) になり、2番目以降は正常に .mp4 になる

**環境**: macOS, yt-dlp, deno (JavaScript runtime)

**再現手順**:
1. `pipeline.py` または `downloader.py` でYouTubeプレイリストをダウンロード
2. 最初の動画が `.m4a` 拡張子でダウンロードされる
3. 2番目以降の動画は正常に `.mp4` でダウンロードされる

**試行錯誤**:
1. 最初は `progress_hooks` が中間ファイル名をキャプチャしているのが原因と推測 → `postprocessor_hooks` に変更
2. しかし問題は継続。ログを詳細に確認すると、最初の動画で JS チャレンジ解決に失敗していることが判明
   - `WARNING: [youtube] _NLHFoVNlbg: n challenge solving failed`
   - `[info] _NLHFoVNlbg: Downloading 1 format(s): 139` (139 = audio-only)
3. 2番目以降は `[info] DNCn1BpCAUY: Downloading 1 format(s): 399+140` (video+audio) で正常

**最終解決方法**:
yt-dlp オプションに `"remote_components": {"ejs:github"}` を追加。これにより GitHub から JS チャレンジ解決スクリプトが事前にダウンロードされる。

**根本原因**:
yt-dlp の JavaScript チャレンジ解決器が初回リクエスト時に失敗。deno runtime は存在するが、チャレンジ解決用スクリプトがキャッシュされていないため、最初の動画でビデオフォーマットが取得できず、audio-only (format 139) にフォールバック。2番目以降はスクリプトがキャッシュされ正常動作。

**予防策**:
- `remote_components` オプションを常に設定し、JS チャレンジ解決スクリプトを事前取得
- yt-dlp のログで `n challenge solving failed` 警告を監視

---

## [YYYY-MM-DD] 問題の概要
**症状**:
**環境**:
**再現手順**:
**試行錯誤**:
**最終解決方法**:
**根本原因**:
**予防策**: 
