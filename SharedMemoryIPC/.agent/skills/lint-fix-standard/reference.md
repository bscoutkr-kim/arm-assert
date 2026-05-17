# Lint Fix Standard Reference

이 문서는 `lint-fix-standard` 스킬을 사용하여 린트 및 타입 에러를 해결할 때 참고할 수 있는 구체적인 가이드와 예시를 제공합니다.

## 1. 전역 타입 참조 (Global Type Resolution)

프로젝트 수준에서 이미 정의된 브라우저 전역 변수나 라이브러리(`Swal`, `bootstrap` 등)를 참조할 때의 표준 방법입니다.

### ✅ DO: 전역 타입 직접 사용
`jsconfig.json`에 `globals.d.ts`가 포함되어 있다면, 추가적인 선언 없이 JSDoc에서 해당 타입을 직접 사용할 수 있습니다.

```javascript
/**
 * @param {Swal} swalInstance - 전역 Swal 인스턴스 (자동 인식됨)
 */
function useSwal(swalInstance) {
    // ...
}
```

### ❌ DON'T: 잘못된 import() 사용
전역 스크립트(Global Script, `export`가 없는 `.d.ts`)에 대해 `import()`를 사용하면 **"Cannot find module"** 에러가 발생합니다.

```javascript
/**
 * ❌ 잘못된 사례 (에러 발생)
 * @typedef {import('./types/globals.d.ts').Swal} Swal
 */
```

### ❌ DON'T: 중복 전역 선언
이미 `declare var`로 선언된 항목을 파일 내에서 다시 선언하지 마십시오. 타입 충돌의 원인이 됩니다.

```javascript
/** ❌ 중복 선언 금지 */
var Swal; 
```

---

## 2. 표준 해결 패턴 (Standard Patterns)

### 2.1 외부 라이브러리 연동
`Swal`, `Chart`, `bootstrap` 등 외부 라이브러리를 사용할 때, 전역 네임스페이스와 충돌하지 않도록 보장합니다.

| 상황 | 해결 방법 |
| :--- | :--- |
| **Swal 사용 시** | 전역 `Swal` 객체를 직접 사용하되, 필요 시 JSDoc 타입 단언을 활용함. |
| **bootstrap 모달** | `bootstrap.Modal.getInstance(el)` 또는 `new bootstrap.Modal(el)` 패턴 사용. |
| **Chart.js 인스턴스** | `Chart.instances` 등을 통해 전역 인스턴스에 접근 시 `// @ts-ignore` 최소화. |

### 2.2 하단 IIFE 노출 (Global Exports)
전역으로 노출해야 하는 함수가 많을 경우, 하단 IIFE에서 `Object.assign`을 사용하여 깔끔하게 통합합니다.

```javascript
(function () {
    const globalObj = (typeof window !== 'undefined') ? window : global;
    if (!globalObj) return;

    Object.assign(globalObj, {
        publicFn1,
        publicFn2
    });

    globalObj['Module'] = {
        fn: publicFn1,
        __registeredAt: new Date().toISOString()
    };
})();
```

---

## 3. 검증 체크리스트 (Verification Checklist)

린트 수정 작업을 완료하기 전, 다음 항목을 반드시 체크하십시오.

1. [ ] **파일 최상단**: `// @ts-check`가 포함되어 있으며, 그 위에 주석 이외의 코드가 없는가?
2. [ ] **전역 타입**: `static/js/types/globals.d.ts`에 정의된 타입을 중복 선언 없이 활용했는가?
3. [ ] **IIFE 위치**: 전역 노출(window.*)은 모두 파일 최하단 IIFE 블록으로 통합되었는가?
4. [ ] **린트 실행**: `npx eslint <filename>`이 에러 없이(혹은 의도한 결과로) 통과하는가?
5. [ ] **구문 에러**: `node --check <filename>`을 통해 최소한의 문법 오류가 없는지 확인했는가?

---

## 4. 관련 파일 위치 (Related Files)

- **전역 타입 정의**: `static/js/types/globals.d.ts`
- **프로젝트 설정**: `jsconfig.json`, `tsconfig.json`
- **린트 설정**: `.eslintrc.json`, `.eslintignore`
