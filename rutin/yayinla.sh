#!/bin/bash
# Farsçadan yayın betiği — hem yerelde hem bulut rutininde aynı çalışır.
# Kaynak dalı (kaynak) → derle → kontrol et → public/ çıktısını main dalına commit'le ve gönder.
# Kimlik doğrulama: bulutta oturumun git yetkisi, yerelde credential helper (Anahtar Zinciri).
set -euo pipefail
ROOT="$(git rev-parse --show-toplevel)"
cd "$ROOT"
MSG="${1:-Yayın $(date -u '+%Y-%m-%d %H:%M') UTC}"

# 1) Kaynak değişikliklerini kaydet ve gönder
git add -A content static site.json build.py check_links.py rutin ICERIK_SOZLESMESI.md README.md 2>/dev/null || true
if ! git diff --cached --quiet; then
  git -c user.name="Farsçadan Yayın" -c user.email="yayin@farscadan.com" commit -q -m "İçerik: $MSG"
fi
git pull -q --rebase origin kaynak || true
git push -q origin HEAD:kaynak

# 2) Derle ve kontrol et
python3 build.py
python3 check_links.py

# 3) public/ → main
WT="$(mktemp -d)"
git fetch -q origin main
git worktree add -q --detach "$WT" origin/main
( cd "$WT" && git rm -rq --ignore-unmatch . && cp -R "$ROOT/public/." . && git add -A
  if git diff --cached --quiet; then echo "main: değişiklik yok"; else
    git -c user.name="Farsçadan Yayın" -c user.email="yayin@farscadan.com" commit -q -m "$MSG"
    git push -q origin HEAD:main && echo "main: yayınlandı"; fi )
git worktree remove --force "$WT"
