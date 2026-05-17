---
name: lint-fix-standard
description: >
  린트 에러 수정을 위한 표준 워크플로우를 정의합니다.
  @ts-check 활성화, 전역 타입(globals.d.ts) 참조 규칙, IIFE 모듈 노출 표준을 준수합니다.
  트리거: 린트 에러 수정, 타입 오류 해결, 대규모 리팩터링, 고품질 코드 정제 요청 시.
---

# Lint Fix Standard Skill

**구체적인 에러별 해결 패턴, JSDoc 예시, 검증 체크리스트:**  
→ `.agent/skills/lint-fix-standard/reference.md`

## 🎯 Purpose

1. **한 번에 완벽한 수정**: 수정 후 새로운 타입 에러가 발생하지 않도록 전역 프로젝트 설정을 고려한 해결책 제시.
2. **타입 안정성 강화**: `// @ts-check`를 도입하고 `@ts-ignore`를 제거하여 코드의 신뢰도 향상.
3. **구조적 표준화**: 전역 노출 방식을 통합하고(`module-registration` 연계) 일관된 코딩 스타일 유지.

## 🛠️ When To Use

- 사용자로부터 "린트 에러 수정해줘", "코드 정제해줘", "타입 에러 잡아줘" 등의 요청을 받았을 때.
- 기존 파일에 `// @ts-check`를 도입하여 현대화할 때.
- 외부 라이브러리(`Swal`, `bootstrap` 등)의 전역 참조 에러를 해결할 때.

## 📜 Core Rules

### 1. 전역 타입 참조 (SSOT)
- **Global Script vs Module**: `globals.d.ts`가 전역 스케일(`interface Window`, `declare var`)로 작성된 경우, JS 파일에서 `import()`를 사용하지 않는다.
- **jsconfig.json 활용**: 전역 타입 파일이 `jsconfig.json`의 `include`에 포함되어 있다면, 추가 선언 없이 해당 타입을 JSDoc(`@type`, `@param`)에서 직접 사용한다.
- **중복 선언 금지**: 이미 `globals.d.ts` 등에 선언된 변수(`Swal` 등)는 파일 내에서 다시 `var`나 `const`로 선언하지 않는다.

### 2. 파일 현대화 (Modernization)
- **최상단 @ts-check**: 수정하는 모든 JS 파일 최상단에 `// @ts-check`를 명시한다.
- **IIFE 통합 노출**: `module-registration` 규격에 따라 모든 전역 노출은 파일 하단의 단일 IIFE 블록에서 관리한다.

### 3. JSDoc 표준 준수
- 모든 공개 함수는 `jsdoc-standards`에 따라 매개변수와 반환값의 타입을 명시한다.
- 라이브러리 객체는 가능하면 실제 타입을 참조하거나, `globals.d.ts`에 정의된 타입을 사용한다.

## 🔄 Workflow

1. **상태 진단**: `jsconfig.json`과 `static/js/types/` 내의 타입 정의를 먼저 읽어 프로젝트의 전역 타입 스코프를 파악한다.
2. **전략 수립**: 대상 파일에 `// @ts-check`를 추가했을 때 발생하는 에러의 성격(전역 참조 누락, 타입 불일치 등)을 분류한다.
3. **점진적 수정**:
    - 외부 라이브러리 참조를 전역 타입에 맞게 교정한다.
    - `module-registration` 패턴으로 구조를 개편한다.
    - 누락된 JSDoc을 보강한다.
4. **최종 검증**: `npx eslint <file>` 및 `node --check <file>`을 실행하여 무결성을 확인한다.

## 🔗 Related Skills

- **`/jsdoc-standards`**: 구체적인 JSDoc 작성 문법.
- **`/module-registration`**: IIFE 기반 전역 등록 표준.
- **`/verify-implementation`**: 수정 후 최종 코드 품질 검토.
