# Submission Checklist – Lab 04 team-notify (B7)

Nộp các minh chứng sau:

- [x] `Dockerfile` – multi-stage, non-root, HEALTHCHECK
- [x] `.dockerignore` – loại bỏ .git, .venv, node_modules, reports
- [x] `.env.example` – SERVICE_NAME, AUTH_TOKEN, APP_PORT
- [x] `RUN_LOCAL.md` – 5 bước hướng dẫn rõ ràng
- [x] `contracts/notification-service.openapi.yaml` – OpenAPI 3.1
- [x] `postman/collections/FIT4110_lab04_iot_docker.postman_collection.json`
- [x] `postman/environments/FIT4110_lab04_local.postman_environment.json`
- [x] `reports/newman-lab04-local.xml` – **32/32 assertions PASS**
- [x] `reports/newman-lab04-local.html` – 324 KB, đầy đủ chi tiết
- [x] Log evidence `docs/evidence/lab04-evidence-*.log` – health + docker ps + non-root verify
- [x] Image tag: `fit4110/notification-service:lab04` (268 MB)
- [x] Image tag nộp bài: `fit4110/notification-service:v0.1.0-team-notify`

## Kết quả Newman (chạy trên Docker container)

```
iterations : 1 / 0 failed
requests   : 15 / 1 failed (Consumer smoke – đúng hành vi skip on local)
assertions : 32 / 0 failed  ← 100% PASS
duration   : 1368ms
avg RT     : 7ms
```

## Push lên registry (chỉ cần khi nộp)

```bash
docker login ghcr.io
docker tag fit4110/notification-service:lab04 ghcr.io/<owner>/team-notify:v0.1.0-team-notify
docker push ghcr.io/<owner>/team-notify:v0.1.0-team-notify
```
