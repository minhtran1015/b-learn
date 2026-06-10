# Huong Dan Van Hanh va Xu Ly Su Co

Tai lieu nay chuan hoa quy trinh GreenOps cho demo va playbook xu ly su co nhanh tren cum AKS/Kafka/Spark.

## 1. Chu trinh GreenOps bat/tat toi uu chi phi

## 1.1 Khoi dong truoc demo (Wake-up sequence)

1. Danh thuc ha tang AKS:

```bash
make aks-start
```

2. Bat cac thanh phan streaming va MLOps (Kafka, Spark Streaming, API Gateway, Grafana/Prometheus):

```bash
make streaming-resume
```

3. Tao local tunnel phuc vu trinh dien:

```bash
make demo-connect
```

Ket qua mong doi:
- Port-forward API Gateway: `localhost:8000`.
- Port-forward Frontend Demo: `localhost:8080`.
- Port-forward Redis: `localhost:6379`.
- Port-forward MLflow: `localhost:5005`.
- Port-forward Nessie: `localhost:19120`.

## 1.2 Ngu dong sau demo (Hibernate sequence)

1. Ha replica ve 0 de dung toan bo streaming stack:

```bash
make streaming-suspend
```

2. Tat nguon vat ly AKS de dua chi phi ve muc toi thieu:

```bash
make aks-stop
```

## 2. Kiem tra nhanh tinh trang van hanh

- Kiem tra tai nguyen namespace:

```bash
kubectl get jobs,pods -n blearn-medallion
```

- Kiem tra topic Kafka dang ton tai:

```bash
make kafka-topics-list
```

- Theo doi su kien runtime:

```bash
make kafka-consume-stream
```

## 3. Troubleshooting Playbook

## Su co 1: `lost connection to pod` hoac `sandbox not found`

Trieu chung:
- Trinh duyet/API dang hoat dong thi ngat ket noi dot ngot.
- Terminal port-forward bao mat ket noi hoac khong tim thay pod.

Nguyen nhan goc:
- Da chay `kubectl rollout restart` hoac scale, lam Pod UID thay doi.
- Tunnel cu van tro vao pod da bi thay the.

Cach xu ly nhanh:
1. Dung toan bo terminal dang giu port-forward cu.
2. Chay lai tunnel tu dau:

```bash
make demo-connect
```

3. Kiem tra lai truy cap:
- `http://localhost:8000/docs`
- `http://localhost:8080`

## Su co 2: Kafka bao `UNKNOWN_TOPIC_OR_PARTITION`

Trieu chung:
- Producer/consumer fail voi loi khong tim thay topic.
- Thuong gap sau khi ngu dong va bat lai cum.

Nguyen nhan goc:
- Metadata topic luu RAM bi mat trong chu trinh suspend/resume.

Cach xu ly nhanh:
- Chay lenh co co che tu tao topic phong ve trong Makefile:

```bash
make kafka-consume-stream
```

Giai thich:
- Target nay goi `kafka-topics.sh --create --if-not-exists` cho topic `learning-events` truoc khi consume.
- Sau do he thong tiep tuc nghe stream binh thuong.

## Su co 3: Spark stream gian doan voi `Partition offset changed`

Trieu chung:
- Spark Structured Streaming canh bao thay doi offset hoac mat offset cu.
- Job co nguy co dung neu ap dung che do fail cung.

Co che phong ve da tich hop:
- Pipeline stream cau hinh doc Kafka voi:
- `.option("failOnDataLoss", "false")`

Y nghia van hanh:
- Khi broker restart hoac offset metadata bi xao tron, stream khong bi crash ngay.
- Job tiep tuc xu ly offset hien co de bao toan tinh lien tuc demo.

Khuyen nghi:
- Van can theo doi metric data freshness va so luong ban ghi de dam bao chat luong du lieu dau ra.

## 4. Checklist truoc khi vao phong bao ve

- [ ] Da chay xong `make aks-start`.
- [ ] Da chay xong `make streaming-resume`.
- [ ] Da chay xong `make demo-connect` va truy cap duoc cong 8000/8080.
- [ ] Terminal theo doi Kafka dang mo (`make kafka-consume-stream`).
- [ ] Dashboard giang vien hien thi Grafana va bang SLA Drift.

## 5. Checklist ket thuc phien demo

- [ ] Da chay `make streaming-suspend`.
- [ ] Da chay `make aks-stop`.
- [ ] Khong con terminal port-forward/consumer thua tren may demo.

## 6. Ban Do Thanh Phan Van Hanh

### Kubernetes objects that

- `blearn-frontend-demo` / `blearn-frontend-service`: giao dien React.
- `blearn-api-gateway` / `blearn-api-service-gateway`: FastAPI gateway cho click/recommendation/assessment.
- `blearn-api-serving` / `blearn-api-service`: REST serving layer doc du lieu Gold.
- `blearn-streamlit-ui` / `blearn-streamlit-service`: dashboard giang vien.
- `spark-streaming-job`: Spark Structured Streaming xu ly `learning-events`.
- `kafka-stream` / `kafka-service`: Kafka KRaft broker/controller.

### Khac nhau giua cac lenh bat day

- `make aks-start`: chi bat phan cứng AKS.
- `make streaming-resume`: scale up Kafka/Spark/Gateway/Grafana/Prometheus len 1.
- `make demo-prep`: bat AKS va scale gateway/frontend/streaming core len 1.
- `make demo-connect`: tao port-forward local 8000 va 8080, dong tunnel cu truoc khi mo tunnel moi.

### Dung service nao cho tung muc

- Demo hoc vien dung `blearn-frontend-demo`.
- Dashboard giang vien dung `blearn-streamlit-ui`.
- API phuc vu quiz/assessment/recommendation dung `blearn-api-gateway`.
- API doc du lieu Gold dung `blearn-api-serving`.

## 7. Playbook Bat/Tat Theo Thu Tu An Toan

### Khoi dong an toan

1. `make aks-start`
2. Cho AKS tro lai Running.
3. `make streaming-resume`
4. `make demo-prep`
5. `make demo-connect`

### Tat an toan

1. Dong terminal port-forward va consumer.
2. `make streaming-suspend`
3. `make aks-stop`

### Neu chi restart mot phan

- Neu restart deployment hoac rollout, phai chay lai `make demo-connect` vi port-forward cu se tro vao Pod UID cu.
- Neu chi can xem ingestion/streaming, co the dung `make kafka-consume-stream` ma khong can mo frontend.
- Neu can reset baseline nhanh cho demo, dung `make demo-reset`.
- Neu can dọn sâu checkpoint va state streaming, dung `make demo-reset-deep`.

## 8. Troubleshooting Playbook Mo Rong

### Su co 1: `lost connection to pod` / `sandbox not found`

- Doi khi xuat hien sau `rollout restart` hoac scale deployment.
- Nguyen nhan: port-forward dang tro vao Pod da bi thay the.
- Cach fix: kill terminal cu, chay lai `make demo-connect`.
- Kiem tra lai: `kubectl get pods -n blearn-medallion` va mo lai `http://localhost:8000/docs`.

### Su co 2: `UNKNOWN_TOPIC_OR_PARTITION`

- Thuong gap sau khi suspend/resume hoac khi topic chua duoc khoi tao.
- Target `make kafka-consume-stream` tu dong tao `learning-events` voi `--if-not-exists`.
- Neu van loi, kiem tra broker da chay chua bang `make k8s-status` va `kubectl get pods -n blearn-medallion`.

### Su co 3: Spark offset thay doi / mat offset

- Stream clickstream co `failOnDataLoss=false` nen broker restart khong lam job crash ngay.
- Neu van bi tre, check checkpoint path va tinh trang pod spark-streaming-job.
- Kiem tra log: `kubectl logs deployment/spark-streaming-job -n blearn-medallion`.

### Su co 4: AKS API DNS `NXDOMAIN`

- Trieu chung nay co the xuat hien khi cluster da stop hoac chua start xong.
- Cac ban ghi quac trinh cho thay can bat AKS truoc, sau do moi resume streaming.
- Cach xu ly: `make aks-start` truoc, doi cluster sang Running, roi moi `make streaming-resume`.

## 9. Lenh Chan Doan Nhanh

- `make k8s-status`: xem job/pod trong namespace.
- `make kafka-topics-list`: xem danh sach topic Kafka.
- `make kafka-consume-stream`: theo doi event `learning-events`.
- `kubectl logs -f deployment/blearn-streamlit-ui -n blearn-medallion`: xem dashboard log.
- `kubectl logs -f deployment/blearn-api-gateway -n blearn-medallion`: xem Gateway log.
- `kubectl logs -f deployment/spark-streaming-job -n blearn-medallion`: xem streaming job log.

## 10. Checklist Hoi Dong Hay Gap

- [ ] Frontend 8080 tra ra giao dien.
- [ ] API Gateway 8000 tra ra swagger/docs.
- [ ] Kafka topic `learning-events` ton tai.
- [ ] Streamlit dashboard hien grafana iframe va bang drift.
- [ ] Sau demo co the tat hoan toan bang `make streaming-suspend` va `make aks-stop`.
