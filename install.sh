#!/usr/bin/env bash
# 把仓库里的 skill 一键装到 ~/.claude/skills/
# 用法：./install.sh
#
# 行为：把 skills/<name>/ 链接到 ~/.claude/skills/<name>/
# 用 symlink 不复制 — 后续 git pull 自动更新

set -e
DEST=~/.claude/skills
HERE="$(cd "$(dirname "$0")" && pwd)"
SRC="$HERE/skills"

mkdir -p "$DEST"

for skill_dir in "$SRC"/*/; do
  name="$(basename "$skill_dir")"
  target="$DEST/$name"

  if [ -L "$target" ]; then
    echo "  ↻ relinking $name"
    rm "$target"
  elif [ -e "$target" ]; then
    backup="$target.backup-$(date +%s)"
    echo "  ! $name 已存在（非符号链接）→ 备份到 $backup"
    mv "$target" "$backup"
  fi

  ln -s "$skill_dir" "$target"
  echo "  ✓ $name → $skill_dir"
done

echo
echo "装好了。重启 Claude Code（或新开一个会话）即可使用。"
echo "验证：ls -la ~/.claude/skills/"
