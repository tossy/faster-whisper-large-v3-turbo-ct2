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

## [2026-09-24] Brave の Cookie が読めずダウンロードが 0 件になる問題
**症状**: `uv run pipeline.py` のダウンロードが 0 件で終わる。exit code は 0 のため、失敗に気付きにくい。
```
ERROR: could not find brave cookies database in "/Users/toshihidesato/Library/Application Support/BraveSoftware/Brave-Browser"
Error downloading https://www.youtube.com/playlist?list=...: failed to load cookies
```

**環境**: macOS 27 (Darwin 27.0.0), yt-dlp, `COOKIES_FROM_BROWSER = "brave"`

**再現手順**:
1. VS Code の統合ターミナル、または VS Code 上の Claude Code から `uv run pipeline.py` を実行する
2. 上記のエラーでダウンロードが 0 件になる

**試行錯誤**:
1. Brave で YouTube にアクセスし直した → 変化なし
2. Cookie なしで実行した (`--cookies-from-browser ""`) → プレイリストの一覧は取得できる。新しい動画はすべて `HTTP Error 403: Forbidden` で失敗する
3. `tccutil reset SystemPolicyAppData com.microsoft.VSCode` で VS Code の権限をリセットし、VS Code を再起動した → 変化なし (許可ダイアログも出なかった)
4. Terminal.app から実行した → 同じエラー
5. Terminal.app で `ls ~/Library/Application\ Support/BraveSoftware/Brave-Browser/` を実行した → `Operation not permitted`。親の `BraveSoftware/` は一覧できる

**最終解決方法**:
システム設定 > プライバシーとセキュリティ > フルディスクアクセス で Terminal.app をオンにし、Terminal.app を再起動した。ダウンロードは Terminal.app から `uv run pipeline.py` で実行する。

VS Code は引き続き `Operation not permitted` になる。VS Code からは `--transcribe-only` (Cookie 不要) だけを実行する。

**根本原因**:
macOS が `Brave-Browser/` フォルダへのアクセスを、フルディスクアクセスのないアプリに対して拒否している。yt-dlp は `os.walk` で Cookie のファイルを探す。`os.walk` は権限エラーを黙って無視するため、権限拒否が「ファイルが見つからない」エラーとして表示される。

macOS 27 へのアップデート後に発生したため、アプリデータ保護の範囲が広がったことが原因と推測している (未確認)。

**予防策**:
- `could not find brave cookies database` が出たら、まず Terminal で `ls` を実行し、`Operation not permitted` かどうか確認する
- ダウンロードは Terminal.app から実行する
- YouTube は Cookie なしのダウンロードを 403 で拒否するため、Cookie なしでの実行は代わりにならない

---

## [YYYY-MM-DD] 問題の概要
**症状**:
**環境**:
**再現手順**:
**試行錯誤**:
**最終解決方法**:
**根本原因**:
**予防策**: 
