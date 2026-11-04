# PWA

한국어 · [English](#english)

각 `index.html`에 설치용 매니페스트, 아이콘, 설치 안내, 범위가 분리된 서비스 워커를 연결했습니다. HTTPS 또는 localhost에서 설치할 수 있습니다.

인터넷 연결 없이 PWA를 새로 실행하거나 기본 화면의 네트워크 요청이 실패하면 앱 대신 다음 문구를 표시합니다.

> 인터넷 연결 상태가 불안정하여 어플리케이션을 실행할 수 없습니다.
>
> 네트워크 환경을 확인해 주세요.

연결을 다시 시도하려면 화면을 아무 곳이나 누르세요. 화면 전체가 재시도 영역이며 키보드 Enter·Space도 지원합니다. 캐시된 앱 화면으로 우회하여 실행하지 않습니다. 새 버전은 작업을 저장한 뒤 업데이트 버튼을 누르거나 기존 창을 닫을 때 적용됩니다.

저장소 이름, 기본 브랜치, 기존 원본과 빌드 경로는 유지됩니다. 캐시는 해당 앱과 서비스 워커 범위로 분리하며 다른 앱의 캐시, localStorage, IndexedDB를 삭제하지 않습니다. 업로드, POST, 외부 도메인, API, Range 요청을 캐시하지 않습니다. 탐색 URL의 쿼리는 HTML 캐시 키에서 제외합니다.

## 적용된 진입 페이지

- `index.html`

## English

Every first-party index listed above has installation metadata, icons, and an isolated service worker. HTTPS or localhost is required for installation. Launching without connectivity, or a failed navigation network request, displays the exact Korean connection notice above instead of running a cached application. Retry checks the connection again.

Repository names, default branches, original application paths, and build paths remain intact. Updates wait for user action or closure of existing clients. Existing work is never automatically reloaded. Other applications' caches and browser storage are preserved. Build outputs must retain the PWA bundle next to the index.

연결 안내 화면의 배경은 해당 앱의 서버 원본에서 기능 스크립트·이벤트를 제거한 정적 UI입니다. 샌드박스와 별도의 보안 정책으로 실행·입력을 막습니다. 실제 작업 화면이나 업로드 이미지는 수집하지 않습니다.
