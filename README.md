# FIT4110_lab04_docker_packaging – B7 Notification Service

**Học phần:** FIT4110 – Dịch vụ kết nối và Công nghệ nền tảng  
**Buổi 4:** Đóng gói service với Docker & tư duy công nghệ nền tảng  
**Nhóm:** `team-notify` – Phân hệ B7 Multi-Channel Alert Service  
**Repo nền:** `FIT4110_lab03_postman_mock_testing`

> Lab 03 đã có OpenAPI contract, Postman Collection, Mock Server và Newman report.  
> Lab 04 dùng lại logic đó để kiểm tra một điều mới: **service có chạy ổn khi được đóng gói thành Docker container không?**

---

## 1. Ý tưởng nối tiếp từ Lab 03 sang Lab 04

Ở Lab 03, luồng làm việc là:

```text
OpenAPI Contract → Mock Server → Postman Test → Newman Report → CI Evidence
```

Ở Lab 04, luồng đó được mở rộng thành:

```text
OpenAPI Contract
→ Service thật
→ Dockerfile
→ Docker Image
→ Docker Container
→ Postman/Newman chạy lại trên container
→ Evidence
```

Lab 04 đã đồng bộ lại với contract B7 Notification Service của Lab 03 theo payload:

```json
{
  "eventId": "0196fb3d-4ad7-7d1e-9f49-5d5148d2babc",
  "eventType": "core.alert.created",
  "occurredAt": "2026-06-08T23:15:00Z",
  "correlationId": "0196fb3d-4ad7-7d1e-9f49-5d5148d2aaaa",
  "source": "core-business",
  "data": {
    "alertId": "0196fb3d-4ad7-7d1e-9f49-5d5148d2bcde",
    "severity": "HIGH",
    "message": "Phát hiện xâm nhập trái phép tại khu vực cổng chính tòa IT",
    "targetUserId": "SV-12345"
  }
}
```

Boundary dùng trong bài:

```text
message: minLength=5
severity: LOW | MEDIUM | HIGH | CRITICAL
```

Thông điệp chính của buổi học:

> Một API pass Postman trên máy cá nhân chưa đủ.  
> Service cần được đóng gói thành container để người khác có thể chạy lại nhất quán.

---

## 2. Mục tiêu sau buổi lab

Sau khi hoàn thành Lab 04, mỗi nhóm cần làm được:

- Viết được `Dockerfile` cho service của nhóm.
- Dùng `.dockerignore` để giảm context build.
- Tách cấu hình runtime qua `.env.example`.
- Không commit secret thật vào repo.
- Chạy app bằng user non-root trong container.
- Có `HEALTHCHECK` gọi `GET /health`.
- Build được Docker image.
- Run được container từ image.
- Chạy lại Postman Collection của Lab 03 trên container.
- Kiểm tra được functional, auth, negative, boundary và schema lỗi `ProblemDetails`.
- Xuất Newman report làm bằng chứng.
- Viết được `RUN_LOCAL.md` hướng dẫn người khác chạy lại trong 3–5 bước.

---

## 3. Cấu trúc repo

```text
FIT4110_lab04_docker_packaging/
├── README.md
├── RUN_LOCAL.md
├── Dockerfile
├── .dockerignore
├── .env.example
├── .gitignore
├── Makefile
├── package.json
├── requirements.txt
├── src/
│   └── notification_app/
│       ├── __init__.py
│       └── main.py
├── contracts/
│   └── notification-service.openapi.yaml
├── postman/
│   ├── collections/
│   │   └── FIT4110_lab04_iot_docker.postman_collection.json
│   └── environments/
│       ├── FIT4110_lab04_mock.postman_environment.json
│       └── FIT4110_lab04_local.postman_environment.json
├── mock-data/
├── scripts/
├── docs/
├── checklists/
├── templates/
├── reports/
└── .github/
    └── workflows/
        └── docker-newman.yml
```

---

## 4. Chuẩn bị môi trường

Cần cài trước:

- Git
- Docker Desktop hoặc Docker Engine
- Node.js 20.x LTS
- npm
- Postman Desktop hoặc Postman Web

Cài dependencies phục vụ Prism, Spectral, Newman:

```bash
npm install
```

Kiểm tra:

```bash
docker --version
docker info
node --version
npx newman --version
npx prism --version
```

---

## 5. Chạy service local không dùng Docker

Cài Python dependencies:

```bash
python -m venv .venv
source .venv/bin/activate
pip install -r requirements.txt
```

Chạy API:

```bash
uvicorn notification_app.main:app --app-dir src --host 0.0.0.0 --port 8000
```

Kiểm tra:

```bash
curl http://localhost:8000/health
```

---

## 6. Build và chạy bằng Docker

Build image:

```bash
docker build -t fit4110/notification-service:lab04 .
```

Run container:

```bash
docker run --rm \
  --name fit4110-notify-lab04 \
  -p 8000:8000 \
  --env-file .env.example \
  fit4110/notification-service:lab04
```

Kiểm tra health:

```bash
curl http://localhost:8000/health
```

---

## 7. Chạy lại Postman Collection trên container

Chạy Newman với local environment:

```bash
npm run test:local
```

Hoặc dùng script:

```bash
bash scripts/run-newman.sh local
```

Report được sinh trong:

```text
reports/
```

---

## 8. Các lệnh nhanh bằng Makefile

```bash
make install
make lint
make mock
make test-mock
make build
make run
make test-docker
make stop
```

---

## 9. Bài làm của từng nhóm

Mỗi nhóm dùng repo này làm mẫu, sau đó thay phần IoT bằng service của mình.

| Nhóm | Cần thay đổi |
|---|---|
| `team-iot` | Có thể dùng mẫu này trực tiếp, mở rộng thêm endpoint từ Lab 03 |
| `team-camera` | Thay `src/` bằng Camera Stream service, thêm OpenCV headless |
| `team-gate` | Thay bằng Access Gate service, lưu ý biến môi trường DB |
| `team-vision` | Thay bằng AI Vision service, chuẩn bị model YOLOv8n hoặc mock model |
| `team-analytics` | Thay bằng Analytics service, chưa bắt buộc TimescaleDB trong Lab 04 |
| `team-core` | Thay bằng Core Business policy engine |
| `team-notify` | Thay bằng Notification service, không commit token thật |

---

## 10. Điều kiện hoàn thành Lab 04

Một nhóm được xem là hoàn thành khi:

- `Dockerfile` build được image.
- Image chạy được container.
- Container có `GET /health` trả `200`.
- Service chạy bằng non-root user.
- Có `.dockerignore`.
- Có `.env.example`.
- Có `RUN_LOCAL.md`.
- Chạy lại Postman/Newman pass trên container.
- Có test cho functional, auth, negative, boundary.
- Error response trả đúng dạng `ProblemDetails`.
- Có report trong `reports/`.
- Có bằng chứng image tag đúng quy ước.

Tag gợi ý:

```text
v0.1.0-<team>
```

Ví dụ:

```bash
docker tag fit4110/notification-service:lab04 ghcr.io/<owner>/team-notify:v0.1.0-team-notify
```

---

## 11. Artefact cần nộp

```text
Dockerfile
.dockerignore
.env.example
RUN_LOCAL.md
contracts/notification-service.openapi.yaml
postman/collections/FIT4110_lab04_iot_docker.postman_collection.json
postman/environments/FIT4110_lab04_local.postman_environment.json
reports/newman-lab04-local.xml
reports/newman-lab04-local.html
ảnh chụp /health hoặc log container
tag image đã push lên registry (fit4110/notification-service:lab04)
```

---

## 12. Rubric gợi ý

| Tiêu chí | Điểm |
|---|---:|
| Dockerfile đúng, build được | 2.0 |
| Container chạy được và `/health` pass | 2.0 |
| Non-root, `.dockerignore`, `.env.example` tốt | 2.0 |
| Newman/Postman test pass trên container | 2.0 |
| RUN_LOCAL.md rõ ràng, người khác chạy lại được | 1.0 |
| Evidence đầy đủ: log/report/image tag | 1.0 |
| **Tổng** | **10.0** |

---

## 13. Tinh thần của buổi học

Sau Buổi 3, nhóm đã chứng minh:

```text
API đúng contract khi kiểm thử bằng Postman/Newman.
```

Sau Buổi 4, nhóm cần chứng minh thêm:

```text
API đó có thể được đóng gói, chạy lại và kiểm thử trong container.
```

Đây là bước đệm trực tiếp cho Buổi 5:

```text
Docker container đơn lẻ → Docker Compose nhiều service → Plug-a-thon.
```
