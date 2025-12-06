import streamlit as st
import subprocess
import os
import time
import numpy as np
from PIL import Image
import math

CLIENT_EXE_PATH = r"x64\Release\Client_Hospital.exe" 

RAW_DATA_PATH = "raw_data.txt"
RESULT_PATH = r"Client_Hospital\result.txt"
SHARED_PATH = "Shared_Channel"

def preprocess_image(image):
    """
    이미지를 32x32 Grayscale로 변환하고 0~1로 정규화
    """
    # Grayscale로 변환
    if image.mode != 'L':
        image = image.convert('L')
    
    # 32x32로 리사이즈
    image = image.resize((32, 32), Image.Resampling.LANCZOS)
    
    # numpy 배열로 변환
    img_array = np.array(image, dtype=np.float32)
    
    # 0~1로 정규화 (이미 0~255 범위이므로 255로 나눔)
    img_array = img_array / 255.0
    
    # Flatten: 32x32 -> 1024
    img_flat = img_array.flatten()
    
    return img_flat


def visualize_ciphertext_binary(binary_path, width=256, height=256):
    """
    암호문 바이너리 파일을 이미지로 변환
    바이너리 데이터를 픽셀 값으로 매핑하여 시각화
    """
    try:
        with open(binary_path, 'rb') as f:
            binary_data = f.read()
        
        if len(binary_data) == 0:
            return None
        
        # 바이너리 데이터를 numpy 배열로 변환
        data_array = np.frombuffer(binary_data, dtype=np.uint8)
        
        # 이미지 크기에 맞게 조정
        total_pixels = width * height
        if len(data_array) < total_pixels:
            # 데이터가 부족하면 반복
            repeat_count = (total_pixels // len(data_array)) + 1
            data_array = np.tile(data_array, repeat_count)
        
        # 크기 조정
        data_array = data_array[:total_pixels]
        
        # 2D 배열로 변환
        image_data = data_array.reshape((height, width))
        
        # 이미지 생성
        img = Image.fromarray(image_data, mode='L')
        
        # 컬러맵 적용 (더 시각적으로 보기 좋게)
        img_color = img.convert('RGB')
        img_array = np.array(img_color)
        
        # 히트맵 스타일로 변환 (파란색 → 빨간색)
        normalized = image_data.astype(np.float32) / 255.0
        
        # RGB 채널 생성
        r_channel = (normalized * 255).astype(np.uint8)
        g_channel = ((1 - normalized) * 255).astype(np.uint8)
        b_channel = (128 * np.ones_like(normalized)).astype(np.uint8)
        
        img_colored = np.stack([r_channel, g_channel, b_channel], axis=2)
        img_colored = Image.fromarray(img_colored, mode='RGB')
        
        return img_colored
    
    except Exception as e:
        st.error(f"이미지 변환 오류: {e}")
        return None


def load_ciphertext_info():
    """암호문 정보 파일 읽기"""
    info_path = os.path.join(SHARED_PATH, "ciphertext_info.txt")
    size_path = os.path.join(SHARED_PATH, "ciphertext_size.txt")
    binary_path = os.path.join(SHARED_PATH, "ciphertext_binary.dat")
    
    info = {}
    
    # 디버깅: 파일 존재 여부 확인
    info['debug'] = {
        'info_exists': os.path.exists(info_path),
        'size_exists': os.path.exists(size_path),
        'binary_exists': os.path.exists(binary_path),
        'shared_channel_exists': os.path.exists(SHARED_PATH)
    }
    
    # Shared_Channel 디렉토리의 파일 목록
    if os.path.exists(SHARED_PATH):
        try:
            files = os.listdir(SHARED_PATH)
            info['debug']['files_in_channel'] = files
        except:
            info['debug']['files_in_channel'] = []
    
    if os.path.exists(info_path):
        with open(info_path, 'r') as f:
            info['text'] = f.read()
    
    if os.path.exists(size_path):
        with open(size_path, 'r') as f:
            size_str = f.read().strip()
            try:
                info['size_bytes'] = int(size_str)
                info['size_kb'] = info['size_bytes'] / 1024
                info['size_mb'] = info['size_kb'] / 1024
            except:
                info['size_bytes'] = 0
    
    return info


# --- 웹 페이지 설정 ---
st.set_page_config(page_title="Privacy-Preserving AI", layout="wide")

st.title("🏥 프라이버시 보존형 AI 의료 진단 시스템")
st.markdown("### Homomorphic Encryption (CKKS) based Pneumonia Detection")
st.write("환자의 **흉부 X-ray 이미지**는 **동형암호화**되어 서버로 전송되며, 서버는 내용을 볼 수 없습니다.")

col1, col2 = st.columns([1, 1])

# --- [왼쪽] 병원: 이미지 업로드 ---
with col1:
    st.header("1. 흉부 X-ray 이미지 업로드 (Hospital)")
    with st.container(border=True):
        uploaded_file = st.file_uploader(
            "X-ray 이미지 파일을 업로드하세요",
            type=['png', 'jpg', 'jpeg'],
            help="32x32 Grayscale 이미지로 자동 변환됩니다"
        )
        
        if uploaded_file is not None:
            # 이미지 로드 및 표시 (크기 축소)
            image = Image.open(uploaded_file)
            # 이미지 크기 조정 (최대 너비 300px)
            max_width = 300
            if image.width > max_width:
                ratio = max_width / image.width
                new_height = int(image.height * ratio)
                image = image.resize((max_width, new_height), Image.Resampling.LANCZOS)
            st.image(image, caption="업로드된 이미지", width=max_width)
            
            # 이미지 전처리
            processed_pixels = preprocess_image(image)
            
            # 전처리된 이미지 표시 (32x32, 크기 축소)
            processed_img = Image.fromarray((processed_pixels.reshape(32, 32) * 255).astype(np.uint8), mode='L')
            st.image(processed_img, caption="전처리된 이미지 (32x32 Grayscale)", width=200)

            st.info(f"픽셀 수: {len(processed_pixels)}개 (32x32)")
        
        if st.button("🔒 암호화 진단 요청 (Run Secure AI)", use_container_width=True, disabled=uploaded_file is None):
            if uploaded_file is None:
                st.error("먼저 이미지를 업로드해주세요.")
            else:
                # 1. 기존 결과 파일 삭제 (초기화)
                if os.path.exists(RESULT_PATH):
                    os.remove(RESULT_PATH)

                # 2. 전처리된 픽셀 값을 파일로 저장
                with open(RAW_DATA_PATH, "w") as f:
                    for i, pixel_val in enumerate(processed_pixels):
                        f.write(f"{pixel_val:.6f}")
                        if i < len(processed_pixels) - 1:
                            f.write("\n")

                st.info(f"📝 이미지 전처리 완료: {len(processed_pixels)}개 픽셀")
                st.info("🔐 암호화 엔진(C++)을 실행합니다...")
                
                # 3. C++ Client 실행
                try:
                    if not os.path.exists(CLIENT_EXE_PATH):
                        st.error(f"실행 파일을 찾을 수 없습니다: {CLIENT_EXE_PATH}")
                    else:
                        # cwd=os.getcwd() : 현재 app.py가 있는 폴더를 기준(Root)으로 실행
                        process = subprocess.Popen([CLIENT_EXE_PATH], cwd=os.getcwd())
                        
                        # C++이 종료될 때까지 대기 (최대 60초 - 이미지 처리 시간 고려)
                        max_wait_time = 60
                        elapsed_time = 0
                        with st.spinner('서버(Cloud)와 동형암호 통신 중...'):
                            while process.poll() is None and elapsed_time < max_wait_time:
                                time.sleep(0.5)
                                elapsed_time += 0.5
                        
                        # 프로세스가 아직 실행 중이면 타임아웃
                        if process.poll() is None:
                            process.terminate()
                            st.error(f"⏱️ 타임아웃: 서버 응답을 {max_wait_time}초 내에 받지 못했습니다.")
                            st.info("💡 서버(Server_AI.exe)가 실행 중인지 확인해주세요.")
                        else:
                            # 프로세스 종료 코드 확인
                            return_code = process.returncode
                            if return_code != 0:
                                st.warning(f"⚠️ 클라이언트가 비정상 종료되었습니다. (종료 코드: {return_code})")
                                st.info("💡 콘솔 출력을 확인하여 오류를 확인해주세요.")
                            
                            # 4. 결과 파일 읽기
                            if os.path.exists(RESULT_PATH):
                                with open(RESULT_PATH, "r") as f:
                                    score_str = f.read().strip()
                                
                                if not score_str:
                                    st.error("결과 파일이 비어있습니다.")
                                else:
                                    try:
                                        score = float(score_str)
                                        st.success("진단 완료!")
                                        
                                        # O/X 판단 (sigmoid 결과: 0~1 사이의 확률 값)
                                        # Logistic Regression 모델의 출력: sigmoid(Wx + b) ≈ 0.5 + 0.25z - (1/48)z³
                                        # score > 0.5: Pneumonia (O)
                                        # score <= 0.5: Normal (X)
                                        is_pneumonia = score > 0.5
                                        
                                        if is_pneumonia:
                                            st.error("⚠️ **폐렴 감지됨 (O)**")
                                            st.metric(label="AI 판단", value="폐렴 (Pneumonia)", delta="정밀 검사 필요")
                                        else:
                                            st.success("✅ **정상 (X)**")
                                            st.metric(label="AI 판단", value="정상 (Normal)", delta="정상 범위")
                                        
                                        st.info(f"모델 출력값 (sigmoid 확률): {score:.6f} (0.5보다 크면 폐렴, 작거나 같으면 정상)")
                                        
                                    except ValueError:
                                        st.error(f"결과 파일 형식이 잘못되었습니다: {score_str}")
                            else:
                                st.error("오류: 결과 파일(result.txt)이 생성되지 않았습니다.")
                                st.info("💡 다음을 확인해주세요:")
                                st.info("1. 서버(Server_AI.exe)가 실행 중인지 확인")
                                st.info("2. Shared_Channel 폴더가 존재하는지 확인")
                                st.info("3. weights.txt와 bias.txt 파일이 루트 디렉토리에 있는지 확인")

                except Exception as e:
                    st.error(f"실행 오류: {e}")

# --- [오른쪽] 서버 상태 모니터링 ---
with col2:
    st.header("2. AI 서버 상태 (Cloud)")
    
    # 서버 폴더 감시
    req_file = os.path.join(SHARED_PATH, "request.txt")
    res_file = os.path.join(SHARED_PATH, "response.txt")
    
    if os.path.exists(req_file):
        st.warning("📡 [DETECTED] 암호화된 요청이 감지되었습니다!")
        st.code("Processing Homomorphic Encryption...\nEvaluating Linear Model...", language="bash")
    elif os.path.exists(res_file):
        st.success("✅ [SENT] 연산 결과가 병원으로 전송되었습니다.")
    else:
        st.info("💤 서버 대기 중 (Waiting for request)...")
    
    st.markdown("### 📋 시스템 정보")
    st.info("""
    **데이터셋**: PneumoniaMNIST (32x32 Grayscale)
    
    **모델**: Linear Layer (1024 → 2)
    
    **Poly Modulus Degree**: 4096 (슬롯 2048개)
    
    **Coeff Modulus**: {50, 40, 40, 40, 40, 50} (6개)
    
    **암호화**: CKKS Homomorphic Encryption
    
    **판단 기준**: 
    - sigmoid 확률 > 0.5: 폐렴 (O)
    - sigmoid 확률 ≤ 0.5: 정상 (X)
    
    **수식**: 
    - z = Wx + b (선형 예측)
    - sigmoid(z) ≈ 0.5 + 0.25z - (1/48)z³ (다항식 근사)
    """)
    
    # --- 암호문 시각화 섹션 (서버 영역 하단) ---
    st.divider()
    st.subheader("🔐 암호화된 데이터 시각화")
    
    # 암호문 정보 로드
    cipher_info = load_ciphertext_info()
    
    if cipher_info:
        # 1. 암호문 정보 텍스트 표시
        with st.expander("📊 암호문 정보 (숫자)", expanded=False):
            if 'text' in cipher_info:
                st.text(cipher_info['text'])
            
            if 'size_bytes' in cipher_info and cipher_info['size_bytes'] > 0:
                col_size1, col_size2, col_size3 = st.columns(3)
                with col_size1:
                    st.metric("암호문 크기 (Bytes)", f"{cipher_info['size_bytes']:,}")
                with col_size2:
                    st.metric("암호문 크기 (KB)", f"{cipher_info['size_kb']:.2f}")
                with col_size3:
                    st.metric("암호문 크기 (MB)", f"{cipher_info['size_mb']:.4f}")
        
        # 2. 암호문 바이너리를 이미지로 시각화
        binary_path = os.path.join(SHARED_PATH, "ciphertext_binary.dat")
        if os.path.exists(binary_path):
            st.subheader("🎨 암호문 바이너리 시각화 (픽셀 이미지)")
            st.caption("암호문의 바이너리 데이터를 픽셀 값으로 변환하여 색상으로 표현합니다.")
            
            # 이미지 크기 선택
            img_size = st.selectbox("이미지 크기 선택", [128, 256, 512], index=1, key="cipher_img_size")
            
            cipher_img = visualize_ciphertext_binary(binary_path, width=img_size, height=img_size)
            
            if cipher_img:
                st.image(cipher_img, caption=f"암호문 바이너리 데이터 ({img_size}x{img_size} 픽셀)", width=300)
                st.caption("💡 각 픽셀의 색상은 암호문 바이너리 데이터의 바이트 값을 나타냅니다.")
            else:
                st.warning("이미지 변환에 실패했습니다.")
    else:
        st.info("암호문 정보를 찾을 수 없습니다. 서버가 암호화를 완료했는지 확인해주세요.")
