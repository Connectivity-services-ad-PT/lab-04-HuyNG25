# RUN_LOCAL.md – Notification Service (B7) Lab 04

Hướng dẫn chạy lại toàn bộ Lab 04 từ đầu trong **5 bước**.

---

## Yêu cầu cài trước

- [Docker Desktop](https://www.docker.com/products/docker-desktop/) hoặc Docker Engine
- [Node.js 20 LTS](https://nodejs.org/) + npm
- Git

---

## Bước 1 – Clone repo và cài dependencies

```bash
git clone <repo-url>
cd lab-04-HuyNG25
npm install
```

---

## Bước 2 – Build Docker image

```bash
docker build -t fit4110/notification-service:lab04 .
```

Kiểm tra image đã build:

```bash
docker images | grep notification-service
```

---

## Bước 3 – Chạy container

```bash
docker run --rm \
  --name fit4110-notify-lab04 \
  -p 8000:8000 \
  --env-file .env.example \
  fit4110/notification-service:lab04
```

Kiểm tra container đang chạy và `/health` trả `200`:

```bash
curl http://localhost:8000/health
```

Kết quả mong đợi:

```json
{"status": "ok", "service": "notification-service", "time": "..."}
```

---

## Bước 4 – Chạy Newman tests

Mở terminal mới (giữ container chạy ở terminal cũ), rồi:

```bash
npm run test:local
```

Hoặc dùng script:

```bash
bash scripts/run-newman.sh local
```

---

## Bước 5 – Xem report

Report được sinh ra tại:

```
reports/newman-lab04-local.xml
reports/newman-lab04-local.html
```

Mở file HTML trong trình duyệt để xem kết quả trực quan.

---

## Lệnh nhanh

```bash
# Dừng container
docker stop fit4110-notify-lab04

# Chạy lại test trên mock server (không cần Docker)
npm run mock:notify          # terminal 1
npm run test:mock            # terminal 2

# Dọn report cũ
make clean-reports
```

---

## Tag image (nộp bài)

```bash
docker tag fit4110/notification-service:lab04 \
  ghcr.io/<owner>/team-notify:v0.1.0-team-notify

docker push ghcr.io/<owner>/team-notify:v0.1.0-team-notify
```
