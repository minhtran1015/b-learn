# Huong Dan Kiem Thu Demo va Muc Tieu Giao Dien

Tai lieu nay chuan hoa quy trinh demo frontend-demo cho hoi dong cham diem theo mo hinh 3 man hinh song song va chu trinh Closed-Loop Validation.

## 1. Muc tieu kiem thu

- Xac nhan frontend-demo dang nhap thanh cong va nhan JWT token hop le.
- Xac nhan su kien nop bai tap duoc day vao Kafka theo thoi gian thuc.
- Xac nhan trang Analytics cap nhat dong xac suat rui ro bo hoc va ty le do.
- Xac nhan dashboard giang vien (Streamlit) hien thi Live Grafana va luoi canh bao SLA Drift.

## 2. Kich ban Live 3-Window Topology

### Man hinh 1 - Trinh duyet Hoc vien (frontend-demo)

- Mo giao dien hoc vien: `http://localhost:8080` (sau khi da chay `make demo-connect`).
- Dang nhap voi vai tro hoc vien.
- Vao khu vuc tai lieu hoc tap de tao luu luong tuong tac.
- Vao bai quiz 20 cau (trang DoAssignmentPage) va nop bai.

### Man hinh 2 - Terminal giam sat message stream

Chay lenh:

```bash
make kafka-consume-stream
```

Ky vong:

- Terminal hien dong thong bao theo doi topic `learning-events`.
- Khi hoc vien nop bai, su kien `assessment_submission` xuat hien ngay trong luong message.

### Man hinh 3 - Trinh duyet Giang vien (dashboard/app.py)

- Mo Streamlit dashboard giang vien (dia chi local hoac service da expose tu AKS).
- Truy cap tab `System & Infrastructure` de theo doi:
- `Live Grafana Dashboard` (iframe).
- Bang `MLOps Data Quality Guardrails` (luoi canh bao SLA Drift).

## 3. Quy trinh thuc hien demo tung buoc

1. Khoi dong tai nguyen va cac thanh phan streaming.

```bash
make aks-start
make streaming-resume
make demo-connect
```

2. Xac nhan tunnel local:
- Frontend: `http://localhost:8080`
- API Gateway: `http://localhost:8000/docs`

3. Dang nhap tren frontend-demo.
- Mo DevTools > Network.
- Xac nhan request `POST /login` tra ve `access_token` va `token_type: bearer`.

4. Vao trang Analytics de ghi nhan baseline ban dau.
- Cong thuc hien thi: `pass_rate = (1 - dropout_probability) * 100`.
- Gia tri mac dinh trong frontend la `dropout_probability = 0.15` => ty le do xap xi 85%.

5. Chay terminal giam sat Kafka (`make kafka-consume-stream`) va giu nguyen cua so theo doi.

6. Vao trang quiz 20 cau, thuc hien 2 nhanh kiem thu ben duoi.

## 4. Closed-Loop Validation Steps

### Nhanh A - Ket qua dat (score >= 50%)

1. Lam dung toi thieu 10/20 cau, nen demo 15/20 (75%) de de nhin.
2. Bam `Nop bai`.
3. Kiem tra 3 dau ra dong bo:
- Frontend hien thong bao thanh cong va noi dung giam rui ro.
- Terminal Kafka xuat hien event `assessment_submission` voi `score >= 50`.
- Quay lai trang Analytics, o du doan cap nhat theo huong:
- `dropout_probability` giam.
- Ty le do tang ro ret (vi du tu ~85% len ~90%).

### Nhanh B - Ket qua khong dat (score < 50%)

1. Co tinh chon sai de diem < 50% (vi du 2/20 = 10%).
2. Bam `Nop bai`.
3. Kiem tra 3 dau ra dong bo:
- Frontend hien thong bao canh bao nguy co bo hoc tang cao.
- Terminal Kafka xuat hien event `assessment_submission` voi `score < 50`.
- Quay lai trang Analytics, o du doan cap nhat theo huong:
- `dropout_probability` tang.
- Ty le do giam ro ret (vi du ~90% xuong ~80%).

## 5. Acceptance Criteria (Nghiem thu bat buoc)

Danh dau Dat/Khong dat cho tung muc:

- [ ] Dang nhap frontend-demo sinh JWT token (`POST /login` thanh cong, co `access_token`).
- [ ] Quiz 20 cau nop bai thanh cong, khong treo giao dien.
- [ ] Trong <= 5 giay sau khi nop bai, terminal Kafka nhan duoc event `assessment_submission`.
- [ ] Nhanh score >= 50%: UI hien thi giam rui ro, ty le do tang.
- [ ] Nhanh score < 50%: UI hien thi canh bao rui ro tang, ty le do giam.
- [ ] Dashboard giang vien hien thi duoc ca `Live Grafana` va luoi canh bao `SLA Drift`.
- [ ] Chu trinh phan hoi du lieu theo huong UI -> API -> Kafka -> Analytics duoc quan sat ro tren 3 man hinh.

## 6. Luu y de demo lap lai nhieu lan

- Neu can reset trang thai rui ro de chay lai cho nhom cham khac, su dung:

```bash
make demo-reset
```

- Lenh tren xoa cac thay doi tam trong bo nho (`_assessment_shifts`) va nap lai baseline du lieu rui ro.

## 7. Ban Do Chuoi Demo Tu Codebase That

### Frontend-demo routes can canh

`frontend-demo/src/App.jsx` khai bao cac nhom route sau:

- `login` va `register`: trang xac thuc (`AuthPage`).
- `courses`: danh sach khoa hoc.
- `courses/:courseId`: khung khoa hoc.
- `courses/:courseId/materials`: danh sach hoc lieu.
- `courses/:courseId/materials/:materialId`: trang hoc lieu chi tiet.
- `courses/:courseId/assignments`: danh sach bai tap.
- `courses/:courseId/assignments/:assignmentId`: trang mo ta bai tap.
- `courses/:courseId/assignments/:assignmentId/do`: trang quiz 20 cau.
- `courses/:courseId/analytics`: trang phan tich hoc tap.
- `calendar`, `messages`, `help`, `settings`, `profile`, `discussions`: cac trang ho tro trong luong user.

### Luong nguoi dung frontend that

- Dang nhap/tao tai khoan duoc quan ly bang `AuthContext` va luu tam vao `localStorage`.
- Form login mac dinh dung tai khoan demo `quan@blearn.test / 123456`.
- Sau khi dang nhap, app goi `ensureGatewaySession()` de lay JWT tu Gateway.
- `MaterialsPage` goi `fetchRecommendations()` de lay tai lieu ca nhan hoa va `trackStudentClick()` khi hoc vien mo tai lieu.
- `AssignmentsPage` doc `blearn.submitted_assignments` trong `localStorage` de danh dau bai da nop.
- `DoAssignmentPage` tinh diem tu 20 cau co san, sau do POST len `/submit-assessment`.
- `AnalyticsPage` goi `/recommendations/{studentHash}` va quy doi `dropout_probability` thanh `passRate`.

### Toan bo trang co gia tri demo

- `CoursesPage`: co shortcut di nhanh sang Materials, Assignments, Discussions, Analytics.
- `CourseOverviewPage`: hien lo trinh, summary kho hoc, va diem vao trang tai lieu.
- `MaterialDetailPage`: co play button, tabs tong quan/ban ghi/ghi chu, nut hoan thanh tai lieu.
- `AssignmentDetailPage`: mo ta bai tap, muc tieu hoc tap, passing score, nut bat dau.
- `ProfilePage`: sua ho so, cap nhat nhan khau hoc, logout.

## 8. Hop Dong Du Lieu Giua Frontend va Gateway

### JWT va session

- `frontend-demo/src/api/gateway.js` luu JWT vao `blearn.gatewayToken`.
- `student_id_hash` luu trong `blearn.studentHash`.
- Tai lieu da goi duoc luu cache trong `blearn.recommendationMaterials`.
- `AuthContext` luu danh sach user tam trong `blearn.tempUsers` va session hien tai trong `blearn.currentUserId`.

### Endpoint that su dung trong demo

- `POST /login`: cap JWT.
- `POST /track-click`: nhan clickstream tu hoc vien, day vao Kafka topic `learning-events`.
- `GET /recommendations/{student_id_hash}`: tra ve do rui ro va danh sach goi y.
- `POST /submit-assessment`: nhan ket qua quiz, cap nhat rui ro ngay lap tuc.
- `POST /reset-assessment-shifts`: reset tinh trang demo ve baseline.

### Payload thuc te khi nop bai

- `student_id_hash`: hash SHA-256 cua hoc vien.
- `assignment_id`: ma bai tap.
- `score`: diem so tinh theo ty le cau dung.

### Su kien Kafka sinh ra

- Su kien click: `event_type = click`.
- Su kien nop bai: `event_type = assessment_submission`.

## 9. Trace Kiep Mot Lan Nop Bai

1. Hoc vien vao quiz 20 cau va bam `Nop bai`.
2. Frontend tinh `calculatedScore = round(correctCount / 20 * 100)`.
3. Frontend POST len Gateway `/submit-assessment` voi Bearer token.
4. Gateway them ban ghi vao `_assessment_shifts` va cap nhat `df_risk` trong RAM.
5. Gateway day event `assessment_submission` vao Kafka bang `BackgroundTasks`.
6. `kafka-consume-stream` bat event ngay lap tuc neu terminal giam sat dang mo.
7. Quay lai `AnalyticsPage`, app fetch lai recommendations va thay `dropout_probability` moi.

## 10. Nguong Nghiem Thu Chi Tiet Hon

- [ ] Login thanh cong va co JWT token hop le trong localStorage.
- [ ] `MaterialsPage` load duoc recommendations hoac fallback local data khi gateway khong san sang.
- [ ] `MaterialDetailPage` va `DoAssignmentPage` phat ra event click/nop bai khi co tuong tac.
- [ ] `AnalyticsPage` hien pass rate duoc cap nhat sau submit.
- [ ] `ProfilePage` chinh sua duoc thong tin va luu lai trong browser.
- [ ] Cua so Terminal giu `make kafka-consume-stream` khong bi dong khi demo dang chay.

## 11. Benchmark Artifact Flow

- `python run_ingestion_bench.py ingestion` chay ingest benchmark va ghi `throughput_benchmark.json`.
- `python benchmark_suite.py gateway` chay stress test gateway va ghi `latency_stress_test.csv` + `load_*.txt`.
- `python benchmark_suite.py fault-tolerance` mo phong crash Kafka va ghi `fault_tolerance_log.json`.
- `python benchmark_suite.py greenops` thu thap baseline / suspend metrics va ghi `greenops_metrics.csv`.
- `python benchmark_suite.py verify` kiem tra 4 artifact co ton tai tai root project.

## 12. Nhom can chu y

- Dung ten cluster va resource group theo repo: `aks-blearn-dev` va `RG-BLEarn-Compute`, tru khi co env override.
- `make demo-connect` phai duoc chay sau khi cluster va pod da san sang, neu khong local port 8000/8080 se khong mo.
- Poison-pill benchmark gio phu thuoc vao `_corrupt_record` va validation `clicks` khong hop le trong Spark streaming job.
- `kubectl top` co the can metrics-server; neu khong co, lay so lieu benchmark ngay sau khi metrics-server san sang.