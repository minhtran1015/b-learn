FROM python:3.12-slim-bookworm

# Prevent interactive prompts during package installations
ENV DEBIAN_FRONTEND=noninteractive

# Install Java runtime (required by PySpark) and libgomp1 (required by LightGBM OpenMP)
RUN apt-get update && \
    apt-get install -y --no-install-recommends default-jdk-headless ca-certificates libgomp1 && \
    rm -rf /var/lib/apt/lists/*

# Set Java home environment variables
ENV JAVA_HOME=/usr/lib/jvm/default-java
ENV PATH=$JAVA_HOME/bin:$PATH

# Establish app directory
WORKDIR /app

# Install requirements first to utilize Docker build cache
COPY data_pipeline/requirements.txt /app/data_pipeline/requirements.txt
RUN pip install --no-cache-dir --upgrade pip && \
    pip install --no-cache-dir -r /app/data_pipeline/requirements.txt

# Copy the data_pipeline package
COPY data_pipeline/ /app/data_pipeline/

# Copy manifest files
COPY *manifest.json /app/

# Set Python path to ensure module imports resolve correctly
ENV PYTHONPATH=/app

# Default command (can be overridden in AKS Job)
CMD ["python", "-m", "data_pipeline.silver.oulad"]
