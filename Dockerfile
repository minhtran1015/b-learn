FROM acrblearnminh2026.azurecr.io/b-learn-base:1.0.0

# Establish app directory
WORKDIR /app

# Copy the backend-api package
COPY backend-api/ /app/backend-api/

# Copy the data_pipeline package
COPY data_pipeline/ /app/data_pipeline/

# Copy the Streamlit dashboard
COPY dashboard/ /app/dashboard/

# Copy manifest files
COPY *manifest.json /app/

# Set Python path to ensure module imports resolve correctly
ENV PYTHONPATH=/app

# Default command (can be overridden in AKS Job)
CMD ["python", "-m", "data_pipeline.silver.oulad"]
