#!/bin/bash

# --- CONFIGURATION ---
RELEASE_NAME="blearn-kafka"
NAMESPACE="default"
TOPIC_NAME="learning-events"
CLIENT_POD="blearn-kafka-client"

echo "🚀 Starting B-LEARN Kafka Deployment..."

# 1. Dọn dẹp môi trường cũ (Optional - nếu muốn làm mới hoàn toàn)
echo "🧹 Cleaning up old deployment..."
helm uninstall $RELEASE_NAME 2>/dev/null
kubectl delete pvc data-$RELEASE_NAME-controller-0 2>/dev/null

# 2. Cài đặt Kafka với cấu hình ép Replication = 1
echo "📦 Installing Kafka with 1-node optimized config..."
helm upgrade --install $RELEASE_NAME bitnami/kafka \
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

# 3. Chờ Broker sẵn sàng
echo "⏳ Waiting for Kafka Broker to be ready..."
kubectl wait --for=condition=Ready pod/$RELEASE_NAME-controller-0 --timeout=300s

# 4. Lấy mật khẩu và tạo file client.properties
echo "🔑 Configuring Authentication..."
# Lấy password và xóa ký tự % (nếu có từ zsh)
KAFKA_PASSWORD=$(kubectl get secret ${RELEASE_NAME}-user-passwords -o jsonpath='{.data.client-passwords}' | base64 -d | cut -d , -f 1 | tr -d '%')

cat <<EOF > client.properties
security.protocol=SASL_PLAINTEXT
sasl.mechanism=SCRAM-SHA-256
sasl.jaas.config=org.apache.kafka.common.security.scram.ScramLoginModule required username="user1" password="${KAFKA_PASSWORD}";
EOF

# 5. Đẩy file vào Client Pod (Giả định Pod đã tồn tại)
kubectl cp client.properties ${CLIENT_POD}:/tmp/client.properties

# 6. KHỞI TẠO TOPIC - Bước quan trọng nhất để tránh treo
echo "🏗️ Initializing Topics..."

# Tạo topic dữ liệu
kubectl exec $CLIENT_POD -- kafka-topics.sh \
  --bootstrap-server ${RELEASE_NAME}.${NAMESPACE}.svc.cluster.local:9092 \
  --command-config /tmp/client.properties \
  --create --topic $TOPIC_NAME --partitions 1 --replication-factor 1 2>/dev/null || echo "Topic $TOPIC_NAME already exists."

# Tạo topic Offset nội bộ (Fix triệt để lỗi không phản hồi)
kubectl exec $CLIENT_POD -- kafka-topics.sh \
  --bootstrap-server ${RELEASE_NAME}.${NAMESPACE}.svc.cluster.local:9092 \
  --command-config /tmp/client.properties \
  --create --topic __consumer_offsets --partitions 50 --replication-factor 1 \
  --config cleanup.policy=compact 2>/dev/null || echo "Topic __consumer_offsets already exists."

echo "✅ Deployment Complete! Test with your consumer/producer commands."