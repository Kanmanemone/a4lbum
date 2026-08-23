# CLAUDE.md

Project-specific instructions for Claude Code in this repository.

(Korean: 이 저장소에서 Claude Code를 위한 프로젝트별 지침.)

## Commit Conventions

- Write every commit message as an English conventional-commit subject,
  followed by a blank line, an optional English body, another blank line, and
  its Korean translation in a `(Korean: ...)` block. Apply this format to
  ordinary, squash, and history-rewrite commits.

  (Korean: 모든 커밋 메시지는 conventional-commit 타입을 붙인 영어 제목 한 줄로
  쓰고, 빈 줄 다음에 (필요하면) 영어 본문을, 다시 빈 줄 다음에 그 한국어 번역을
  `(Korean: ...)` 형태로 덧붙인다. 일반 커밋, squash 커밋, 히스토리 재작성 커밋
  모두 이 형식을 따른다.)

- The subject line alone must convey which capability the commit adds or what
  it improves. Describe the change in terms of the resulting user-facing
  capability, not the files touched or the process followed.

  (Korean: 제목 한 줄만 읽어도 그 커밋이 **어떤 기능을 추가했는지 또는 무엇을
  보완했는지** 알 수 있게 쓴다. 건드린 파일이나 밟은 절차가 아니라, 사용자가
  얻게 되는 능력의 변화를 기준으로 기술한다.)

- When picking a conventional-commit type for changes under `.claude/` (skills,
  commands, agent configs, etc.), remember these `.md`/config files are this
  repository's actual product, not incidental documentation about code.
  Classify by the effect on skill behavior — `feat` for new capability, `fix`
  for correcting broken or incomplete behavior, `refactor` for
  no-behavior-change restructuring — not by file extension. Reserve `docs` for
  changes that don't affect what a skill actually does, such as editing this
  file or a README.

  (Korean: `.claude/` 아래(스킬, 커맨드, 에이전트 설정 등)의 변경에
  conventional-commit 타입을 고를 때는, 이 `.md`/설정 파일들이 이 저장소의
  실제 산출물이지 코드에 대한 부수적인 문서가 아님을 기억한다. 파일 확장자가
  아니라 스킬 동작에 미치는 효과로 분류한다 — 새 기능이면 `feat`, 깨지거나
  불완전한 동작을 고친 것이면 `fix`, 동작 변화 없는 재구성이면 `refactor`.
  `docs`는 스킬의 실제 동작에 영향을 주지 않는 변경(이 파일 자체 편집, README
  등)에만 쓴다.)

### Example

```text
feat(analysis): add resumable article labeling

(Korean: 중단 후에도 이어서 실행할 수 있는 글 단위 라벨링 추가)
```
