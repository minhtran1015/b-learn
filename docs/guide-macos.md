# Hướng dẫn thiết lập Hạ tầng B-LEARN (macOS)

Tài liệu này ghi lại các bước thiết lập ban đầu cho dự án **B-LEARN**, tập trung vào việc cấu hình Infrastructure as Code (IaC) sử dụng Terraform và Azure CLI.

---

## 1. Cài đặt Công cụ Local

Sử dụng **Homebrew** để cài đặt các công cụ quản lý chính thức:

```bash
# Cài đặt Azure CLI
brew install azure-cli

# Cài đặt Terraform (Hashicorp chính hãng)
brew tap hashicorp/tap
brew install hashicorp/tap/terraform
```

## 2. Xác thực tài khoản Azure

Đảm bảo bạn đang làm việc trên đúng Subscription của dự án (Azure for Students):

```bash
# Đăng nhập
az login

# Kiểm tra danh sách Subscription
az account list --output table

# Thiết đặt Subscription mặc định (Dùng ID từ lệnh trên)
az account set --subscription "YOUR_SUBSCRIPTION_ID"
```

## 3. Khởi tạo Backend (Bootstrap)

Đây là bước tạo nền tảng thủ công để lưu trữ file trạng thái hạ tầng (tfstate) dùng chung cho cả team:

```bash
# 1. Tạo Resource Group cho Terraform
az group create --name RG-BLEarn-Terraform --location southeastasia

# 2. Tạo Storage Account (Tên phải duy nhất toàn cầu)
az storage account create \
  --name stblearnterraform \
  --resource-group RG-BLEarn-Terraform \
  --location southeastasia \
  --sku Standard_LRS \
  --allow-blob-public-access false

# 3. Tạo Blob Container để chứa file state
az storage container create --name tfstate --account-name stblearnterraform
```

## 4. Cấu hình Terraform (Monorepo)

Cấu trúc thư mục hiện tại của dự án:

- `infra/`: Chứa mã nguồn Terraform.
- `data-pipeline/`: Code xử lý Big Data (Spark/BKT).
- `backend-api/` & `frontend-dashboard/`: Ứng dụng người dùng.

File cấu hình tại `infra/main.tf`:

```terraform
terraform {
  required_providers {
    azurerm = {
      source  = "hashicorp/azurerm"
      version = "~> 3.0"
    }
  }

  backend "azurerm" {
    resource_group_name  = "RG-BLEarn-Terraform"
    storage_account_name = "stblearnterraform"
    container_name       = "tfstate"
    key                  = "dev.terraform.tfstate"
  }
}

provider "azurerm" {
  features {}
}
```

## 5. Khởi tạo Terraform

Lệnh này kết nối máy tính cá nhân với hạ tầng Azure:

```bash
cd infra
terraform init -reconfigure
```

Lưu ý: Luôn đảm bảo không push file .tfstate lên GitHub bằng cách sử dụng .gitignore. Mọi thay đổi hạ tầng từ nay sẽ được thực hiện qua terraform plan và terraform apply[cite: 1].

## 6. Triển khai Hạ tầng Compute (AKS)

Sử dụng Terraform để tạo cụm AKS tối ưu cho tài khoản Azure for Students (giới hạn 1 node để tiết kiệm chi phí).

```bash
# Kiểm tra các thay đổi dự kiến
terraform plan

# Triển khai hạ tầng
terraform apply -auto-approve
```

Lưu ý: Quá trình này thường mất từ 5-7 phút. Khi hoàn tất, bạn sẽ có một Resource Group mới (ví dụ: RG-BLEarn-Compute) chứa cụm AKS.

## 7. Kết nối và Kiểm tra Cluster

Sau khi Terraform hoàn tất, cấu hình kubectl trên macOS để điều khiển cụm:

```bash
# Lấy chứng chỉ kết nối (Thay đổi tên Cluster và RG tương ứng)
az aks get-credentials --resource-group RG-BLEarn-Compute --name aks-blearn-dev

# Kiểm tra trạng thái Node
kubectl get nodes
```

Trạng thái phải là Ready trước khi tiếp tục.

## 8. Cài đặt Apache Kafka (Messaging Layer) - Bản Stable 1-Node

Để xử lý dữ liệu từ EdNet/OULAD trên cụm 1-node mà không bị lỗi treo metadata, bắt buộc phải sử dụng lệnh `upgrade --install` kèm theo việc ép kiểu dữ liệu chuỗi (`--set-string`) cho các biến môi trường.

```bash
# Cài đặt/Cập nhật Kafka với cấu hình ép Replication = 1 cho toàn bộ hệ thống
helm upgrade --install blearn-kafka bitnami/kafka \
  --set global.security.allowInsecureImages=true \
  --set image.registry=public.ecr.aws \
  --set image.repository=bitnami/kafka \
  --set image.tag=4.0.0 \
  --set controller.replicaCount=1 \
  --set zookeeper.enabled=false \
  --set persistence.size=5Gi \
  --set-string "extraEnvVars[0].name=KAFKA_CFG_OFFSETS_TOPIC_REPLICATION_FACTOR" \
  --set-string "extraEnvVars[0].value=1" \
  --set-string "extraEnvVars[1].name=KAFKA_CFG_TRANSACTION_STATE_LOG_REPLICATION_FACTOR" \
  --set-string "extraEnvVars[1].value=1" \
  --set-string "extraEnvVars[2].name=KAFKA_CFG_TRANSACTION_STATE_LOG_MIN_ISR" \
  --set-string "extraEnvVars[2].value=1"
```

Lưu ý: Trên macOS (zsh), các tham số `extraEnvVars` phải được bọc trong dấu nháy kép `"` để tránh lỗi `no matches found`.

## 9. Cấu hình Topic và Fix lỗi Treo Consumer

Sau khi cài đặt, khởi tạo các topic nội bộ cần thiết.

### Bước 9.1: Lấy mật khẩu và chuẩn bị Client

```bash
# Lấy mật khẩu (Đã lọc bỏ ký tự % dư thừa của zsh)
kubectl get secret blearn-kafka-user-passwords -o jsonpath='{.data.client-passwords}' | base64 -d | cut -d , -f 1 | tr -d '%'
```

### Bước 9.2: Khởi tạo topic hệ thống

Để tránh consumer bị treo, cần tạo thủ công topic quản lý vị trí đọc (`__consumer_offsets`) với 1 bản sao.

```bash
# 1. Tạo Topic dữ liệu chính
kubectl exec -it blearn-kafka-client -- kafka-topics.sh \
  --bootstrap-server blearn-kafka.default.svc.cluster.local:9092 \
  --command-config /tmp/client.properties \
  --create --topic learning-events --partitions 1 --replication-factor 1

# 2. Khởi tạo topic quản lý offset thủ công
kubectl exec -it blearn-kafka-client -- kafka-topics.sh \
  --bootstrap-server blearn-kafka.default.svc.cluster.local:9092 \
  --command-config /tmp/client.properties \
  --create --topic __consumer_offsets \
  --partitions 50 --replication-factor 1 \
  --config cleanup.policy=compact
```

## 10. Tự động hóa với Shell Script

Để tái tạo nhanh môi trường Bronze Layer, sử dụng script `deploy-kafka.sh` (đã lưu trong thư mục `infra/`). Script này tự động thực hiện:

- Ghi đè cấu hình Replication factor về 1.
- Đợi Broker sẵn sàng (`kubectl wait`).
- Tự động lấy mật khẩu từ Secret và tạo `client.properties`.
- Khởi tạo sẵn topic `learning-events` và `__consumer_offsets`.
- Đẩy `client.properties` vào Pod client đã tồn tại sẵn.

Lưu ý: Script yêu cầu Pod `blearn-kafka-client` đã được tạo trước đó, vì nó sử dụng `kubectl cp` và `kubectl exec` trên Pod này.

Quy trình tái dựng sau khi `terraform destroy` là:

1. Chạy `terraform apply -auto-approve` để dựng lại AKS.
2. Chạy `az aks get-credentials --resource-group RG-BLEarn-Compute --name aks-blearn-dev` để cập nhật kubeconfig.
3. Tạo Pod client tạm thời:

```bash
kubectl run blearn-kafka-client --restart='Never' --image public.ecr.aws/bitnami/kafka:4.0.0 --namespace default --command -- sleep infinity
```

4. Chạy `./deploy-kafka.sh` để cài Kafka, tạo client.properties và khởi tạo các topic nội bộ.

Cách dùng:

```bash
chmod +x deploy-kafka.sh
./deploy-kafka.sh
```

## 11. Troubleshooting (Bổ sung mới)

| Sự cố | Nguyên nhân | Cách khắc phục |
| --- | --- | --- |
| zsh: no matches found | Dấu `[]` trong lệnh Helm bị hiểu nhầm là globbing. | Bọc tham số trong dấu nháy kép `"extraEnvVars[0]..."`. |
| expected string, got int | Kubernetes yêu cầu biến môi trường là chuỗi. | Dùng `--set-string` thay cho `--set` cho các giá trị số `1`. |
| Consumer không phản hồi | Topic `__consumer_offsets` đang đợi đủ 3 nodes. | Chạy lệnh tạo thủ công `__consumer_offsets` với `--replication-factor 1`. |
| Unable to use a TTY | Đẩy dữ liệu bằng `<<EOF` vào lệnh có cờ `-it`. | Bỏ qua cảnh báo, dữ liệu vẫn Broker 100%. |

## 12. Bàn giao cho Data Engineering (San)

Hạ tầng Bronze Layer hiện đáp ứng các yêu cầu cơ bản sau:

- Spark Structured Streaming: Đã kiểm chứng Consumer Group với offset persistence.
- Security: cấu hình SASL/SCRAM.
- Data Integrity: đẩy lô (Batch) thành công.

Khi cần giải phóng tài nguyên, thực hiện lệnh sau để xóa cụm AKS:

```bash
terraform destroy -target="azurerm_kubernetes_cluster.aks" -auto-approve
```

Khi cần khôi phục môi trường, quay lại Mục 10 và thực hiện theo đúng thứ tự: `terraform apply` -> `az aks get-credentials` -> tạo Pod client -> chạy `./deploy-kafka.sh`.

Quy trình này áp dụng cho giai đoạn Phase 0.1 của B-LEARN.