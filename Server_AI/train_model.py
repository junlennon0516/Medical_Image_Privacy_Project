import sys
import io

sys.stdout = io.TextIOWrapper(sys.stdout.detach(), encoding='utf-8')
sys.stderr = io.TextIOWrapper(sys.stderr.detach(), encoding='utf-8')

import numpy as np
import torch
import torch.nn as nn
import torch.optim as optim
from torch.utils.data import Dataset, DataLoader
from sklearn.metrics import accuracy_score, classification_report
from PIL import Image
import torchvision.transforms as transforms
import os

# 32x32 이미지 사용 (poly_modulus_degree 4096에 맞춤, 슬롯 수 2048개)
IMAGE_SIZE = 32
INPUT_SIZE = IMAGE_SIZE * IMAGE_SIZE  # 32 * 32 = 1024

# MedMNIST는 이진 분류 (정상/폐렴)
num_classes = 2
print(f"클래스 수: {num_classes} (정상/폐렴)")
print(f"이미지 크기: {IMAGE_SIZE}x{IMAGE_SIZE} Grayscale (poly_modulus_degree 4096, 슬롯 2048개)")
print(f"입력 크기: {INPUT_SIZE} 픽셀")

# npz 파일에서 직접 로드
print("\nnpz 파일 로드 중...")
npz_path = '../pneumoniamnist_64.npz'
if not os.path.exists(npz_path):
    npz_path = 'pneumoniamnist_64.npz'  # 현재 디렉토리에서 찾기
data = np.load(npz_path)

# 커스텀 데이터셋 클래스
class PneumoniaDataset(Dataset):
    def __init__(self, images, labels, transform=None):
        self.images = images
        self.labels = labels
        self.transform = transform
    
    def __len__(self):
        return len(self.images)
    
    def __getitem__(self, idx):
        image = self.images[idx]
        label = self.labels[idx]
        
        # 이미지를 PIL Image로 변환
        if image.max() <= 1.0:
            image = (image * 255).astype(np.uint8)
        else:
            image = image.astype(np.uint8)
        
        image = Image.fromarray(image, mode='L')
        
        if self.transform:
            image = self.transform(image)
        
        # 라벨을 1D로 변환
        label = label[0] if isinstance(label, np.ndarray) and label.ndim > 0 else label
        
        return image, label

# 데이터 변환 (32x32로 리사이즈 및 정규화: 0~1)
transform = transforms.Compose([
    transforms.Resize((IMAGE_SIZE, IMAGE_SIZE)),  # 32x32로 리사이즈
    transforms.ToTensor(),  # PIL Image -> Tensor, 자동으로 0~1 정규화
])

# 데이터셋 로드
train_images = data['train_images']
train_labels = data['train_labels']
test_images = data['test_images']
test_labels = data['test_labels']

train_dataset = PneumoniaDataset(train_images, train_labels, transform=transform)
test_dataset = PneumoniaDataset(test_images, test_labels, transform=transform)

print(f"\n학습 데이터: {len(train_dataset)}개")
print(f"테스트 데이터: {len(test_dataset)}개")

# DataLoader 생성
train_loader = DataLoader(train_dataset, batch_size=64, shuffle=True)
test_loader = DataLoader(test_dataset, batch_size=64, shuffle=False)

# 모델 정의: 단순 Linear Layer (필터 1개)
# 32x32 = 1024 픽셀을 모두 한 번에 처리
class SimpleLinearModel(nn.Module):
    def __init__(self, input_size=32*32, num_classes=2):
        super(SimpleLinearModel, self).__init__()
        self.fc = nn.Linear(input_size, num_classes)
    
    def forward(self, x):
        # Flatten: [batch, 1, 32, 32] -> [batch, 1024]
        x = x.view(x.size(0), -1)
        # Linear: [batch, 1024] -> [batch, 2]
        x = self.fc(x)
        return x

# 모델 생성
model = SimpleLinearModel(input_size=INPUT_SIZE, num_classes=num_classes)
criterion = nn.CrossEntropyLoss()
optimizer = optim.Adam(model.parameters(), lr=0.001)

print("\n==모델 학습 시작==")
num_epochs = 10

for epoch in range(num_epochs):
    model.train()
    train_loss = 0.0
    train_correct = 0
    train_total = 0
    
    for images, labels in train_loader:
        # labels는 tuple 형태일 수 있음 (MedMNIST 특성)
        if isinstance(labels, tuple):
            labels = labels[0]
        
        # labels를 1D 텐서로 변환 (2D인 경우)
        if labels.dim() > 1:
            labels = labels.squeeze()
        # Long 타입으로 변환
        labels = labels.long()
        
        optimizer.zero_grad()
        outputs = model(images)
        loss = criterion(outputs, labels)
        loss.backward()
        optimizer.step()
        
        train_loss += loss.item()
        _, predicted = torch.max(outputs.data, 1)
        train_total += labels.size(0)
        train_correct += (predicted == labels).sum().item()
    
    train_acc = 100 * train_correct / train_total
    print(f"Epoch [{epoch+1}/{num_epochs}], Loss: {train_loss/len(train_loader):.4f}, Accuracy: {train_acc:.2f}%")

print("\n==테스트 평가==")
model.eval()
test_correct = 0
test_total = 0
all_preds = []
all_labels = []

with torch.no_grad():
    for images, labels in test_loader:
        if isinstance(labels, tuple):
            labels = labels[0]
        
        # labels를 1D 텐서로 변환 (2D인 경우)
        if labels.dim() > 1:
            labels = labels.squeeze()
        # Long 타입으로 변환
        labels = labels.long()
        
        outputs = model(images)
        _, predicted = torch.max(outputs.data, 1)
        test_total += labels.size(0)
        test_correct += (predicted == labels).sum().item()
        
        all_preds.extend(predicted.cpu().numpy())
        all_labels.extend(labels.cpu().numpy())

test_acc = 100 * test_correct / test_total
print(f"테스트 정확도: {test_acc:.2f}%")
print("\n분류 리포트:")
print(classification_report(all_labels, all_preds, target_names=['Normal', 'Pneumonia']))

# 가중치와 bias 추출
# 모델의 첫 번째 레이어 (Linear)의 가중치와 bias
weights = model.fc.weight.data[1].cpu().numpy()  # 클래스 1 (Pneumonia)에 대한 가중치
bias = model.fc.bias.data[1].item()  # 클래스 1에 대한 bias

# 가중치를 4096개 픽셀에 맞게 확인
print(f"\n가중치 shape: {weights.shape} (예상: {INPUT_SIZE})")
print(f"Bias: {bias:.6f}")

# 파일 저장 (동형암호 연산을 위해)
# 루트 디렉토리에 저장 (서버가 읽는 위치)
weights_path = '../weights.txt'
bias_path = '../bias.txt'

# 현재 디렉토리가 루트인 경우
if not os.path.exists('../weights.txt'):
    weights_path = 'weights.txt'
    bias_path = 'bias.txt'

# weights.txt: 4096개의 가중치를 공백으로 구분
np.savetxt(weights_path, weights, fmt='%.6f', newline=' ')

# bias.txt: 단일 값
with open(bias_path, 'w') as f:
    f.write(f"{bias:.6f}")

print("\n파일 저장 완료:")
print(f"- weights.txt: {len(weights)}개 가중치")
print(f"- bias.txt: bias = {bias:.6f}")
