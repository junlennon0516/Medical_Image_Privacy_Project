import numpy as np
from PIL import Image
import os

# npz 파일 로드
print("npz 파일 로드 중...")
data = np.load('pneumoniamnist_64.npz')

# 출력 폴더 생성
output_dir = 'pneumoniamnist_images'
os.makedirs(output_dir, exist_ok=True)

# 각 split에 대해 이미지 저장
splits = ['train', 'val', 'test']

for split in splits:
    images_key = f'{split}_images'
    labels_key = f'{split}_labels'
    
    if images_key not in data:
        print(f"{images_key}가 없습니다. 건너뜁니다.")
        continue
    
    images = data[images_key]
    labels = data[labels_key]
    
    # split별 폴더 생성
    split_dir = os.path.join(output_dir, split)
    os.makedirs(split_dir, exist_ok=True)
    
    # 라벨별 폴더 생성 (0: 정상, 1: 폐렴)
    normal_dir = os.path.join(split_dir, 'normal')
    pneumonia_dir = os.path.join(split_dir, 'pneumonia')
    os.makedirs(normal_dir, exist_ok=True)
    os.makedirs(pneumonia_dir, exist_ok=True)
    
    print(f"\n{split} 이미지 저장 중... ({len(images)}개)")
    
    for i, (img, label) in enumerate(zip(images, labels)):
        # 라벨 추출 (1D 배열인 경우)
        label_val = label[0] if isinstance(label, np.ndarray) and label.ndim > 0 else label
        
        # 이미지를 PIL Image로 변환
        # 이미지가 0-255 범위인지 0-1 범위인지 확인
        if img.max() <= 1.0:
            img_array = (img * 255).astype(np.uint8)
        else:
            img_array = img.astype(np.uint8)
        
        pil_img = Image.fromarray(img_array, mode='L')
        
        # 라벨에 따라 폴더 선택
        if label_val == 0:
            save_dir = normal_dir
            label_name = 'normal'
        else:
            save_dir = pneumonia_dir
            label_name = 'pneumonia'
        
        # 파일명: {split}_{index}_{label}.png
        filename = f'{split}_{i:05d}_{label_name}.png'
        filepath = os.path.join(save_dir, filename)
        
        pil_img.save(filepath)
        
        if (i + 1) % 500 == 0:
            print(f"  진행: {i + 1}/{len(images)}")
    
    print(f"  완료: {split} 이미지 {len(images)}개 저장됨")
    print(f"    - 정상: {len([l for l in labels if (l[0] if isinstance(l, np.ndarray) and l.ndim > 0 else l) == 0])}개")
    print(f"    - 폐렴: {len([l for l in labels if (l[0] if isinstance(l, np.ndarray) and l.ndim > 0 else l) == 1])}개")

print(f"\n모든 이미지 추출 완료!")
print(f"출력 폴더: {output_dir}/")
print(f"  - train/ (학습용)")
print(f"  - val/ (검증용)")
print(f"  - test/ (테스트용)")

