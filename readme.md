# 🏥 의료 프라이버시 보존 AI 시스템 실행 가이드

## 🚀 실행 방법

### 방법 1: 전체 시스템 실행 (권장)

**2개의 터미널/명령 프롬프트 창을 열어주세요:**

#### 1단계: 서버 실행 (첫 번째 터미널)
```bash
# 프로젝트 루트 디렉토리에서
x64\Release\Server_AI.exe
```
또는
```bash
cd x64\Release
Server_AI.exe
cd ..\..
```

**서버가 정상 실행되면:**
```
==================================================
Current Working Directory: ...
Please place 'weights.txt' and 'bias.txt' here
==================================================

[Server] Cleaning up Shared_Channel...
[Server] AI Server is running... Waiting for KEY....
```
이 메시지가 보이면 서버가 대기 중입니다. 🚨**이 창은 닫지 마세요!**

#### 2단계: 웹 앱 실행 (두 번째 터미널)
```bash
# 프로젝트 루트 디렉토리에서
streamlit run result_app.py
```

**웹 브라우저가 자동으로 열립니다.**
- 주소: `http://localhost:8501`
- 웹 앱에서 이미지를 업로드하고 "🔒 암호화 진단 요청" 버튼을 클릭하면 자동으로 클라이언트가 실행됩니다.

**💡 테스트 이미지 사용:**
- 🚨`test_images` 폴더에 있는 테스트 이미지를 사용할 수 있습니다:
  - 정상 이미지: `test_images/test_00001_normal.png`
  - 폐렴 이미지: `test_images/test_00000_pneumonia.png`
- 웹 앱의 "이미지 업로드" 섹션에서 이 파일들을 선택하여 테스트할 수 있습니다.

## ✅ 실행 확인 체크리스트

- [ ] `weights.txt`와 `bias.txt`가 루트 디렉토리에 있음
- [ ] `Server_AI.exe`가 실행 중임 (서버 창이 열려있음)
- [ ] `Shared_Channel` 폴더가 존재함
- [ ] 웹 앱이 브라우저에서 열림

## 🔧 문제 해결

### 서버가 실행되지 않을 때
- `weights.txt`와 `bias.txt`가 루트 디렉토리에 있는지 확인
- `train_model.py`를 실행하여 모델 파일 생성

### 클라이언트가 실행되지 않을 때
- `raw_data.txt` 파일이 루트 디렉토리에 있는지 확인
- 웹 앱에서 먼저 데이터를 입력했는지 확인

### 웹 앱이 열리지 않을 때
```bash
pip install streamlit
streamlit run result_app.py
```

## 📝 실행 순서 요약

1. **서버 실행** (항상 먼저 실행)
   ```bash
   x64\Release\Server_AI.exe
   ```

2. **웹 앱 실행**
   ```bash
   streamlit run result_app.py
   ```

3. **웹 앱에서 이미지 업로드 후 "🔒 암호화 진단 요청" 클릭**
   - `test_images` 폴더에 있는 테스트 이미지 사용 가능:
     - 정상: `test_images/test_00001_normal.png`
     - 폐렴: `test_images/test_00000_pneumonia.png`
   - 클라이언트가 자동으로 실행됩니다.

## 🎯 빠른 실행 (한 줄씩)

```bash
# 터미널 1: 서버
x64\Release\Server_AI.exe

# 터미널 2: 웹 앱
streamlit run result_app.py
```

그 다음 웹 브라우저에서 이미지 upload!
