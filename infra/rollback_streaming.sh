#!/bin/bash
set -e

echo "🚨 [FALLBACK] Initiating emergency streaming pipeline rollback..."

# 1. Delete the streaming deployments/statefulsets
echo "🧹 Deleting streaming resources from Kubernetes..."
kubectl delete -f infra/manifests/kafka-kraft.yaml --ignore-not-found=true
kubectl delete deployment/spark-streaming-job -n blearn-medallion --ignore-not-found=true

# 2. Revert the code changes in the active app.py to previous stable HEAD
echo "🔄 Reverting dashboard/app.py changes..."
git checkout HEAD -- dashboard/app.py

# 3. Restart the Streamlit UI to pick up the stable code
echo "🚀 Performing rollout restart of blearn-streamlit-ui..."
kubectl rollout restart deployment/blearn-streamlit-ui -n blearn-medallion

echo "🚨 [FALLBACK ACTIVATED] Đã dọn dẹp cụm Stream do giới hạn phần cứng Cloud, hệ thống quay về bản Batch mượt mà an toàn."
