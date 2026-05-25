# infra/main.tf
terraform {
  required_providers {
    azurerm = {
      source  = "hashicorp/azurerm"
      version = "~> 3.0"
    }
    kubernetes = {
      source  = "hashicorp/kubernetes"
      version = "~> 2.30"
    }
  }

  # Cấu hình lưu trữ state trên Azure Storage vừa tạo ở Bước 3
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

variable "oulad_repo_url" {
  type        = string
  default     = "https://github.com/minhtran1015/b-learn.git"
  description = "Git repository that the AKS pipeline job clones at runtime."
}

variable "oulad_git_ref" {
  type        = string
  default     = "main"
  description = "Git ref used by the AKS pipeline job."
}

variable "oulad_cron_schedule" {
  type        = string
  default     = "0 3 * * *"
  description = "UTC cron schedule for the OULAD medallion job."
}

variable "oulad_runner_image" {
  type        = string
  default     = "acrblearnminh2026.azurecr.io/oulad-medallion:latest"
  description = "Container image used by the AKS job to run the pipeline."
}

variable "github_token" {
  type        = string
  default     = ""
  sensitive   = true
  description = "GitHub token used by the AKS job to clone the private repository."
}

# Tạo Resource Group đầu tiên cho Compute (AKS)
resource "azurerm_resource_group" "compute" {
  name     = "RG-BLEarn-Compute"
  location = "Southeast Asia"
}

# 1. Tạo Mạng ảo (VNET)
resource "azurerm_virtual_network" "blearn_vnet" {
  name                = "vnet-blearn-dev"
  address_space       = ["10.0.0.0/16"]
  location            = azurerm_resource_group.compute.location
  resource_group_name = azurerm_resource_group.compute.name
}

# 2. Tạo Subnet cho AKS (Nơi chạy Spark/Kafka)
resource "azurerm_subnet" "aks_subnet" {
  name                 = "snet-aks"
  resource_group_name  = azurerm_resource_group.compute.name
  virtual_network_name = azurerm_virtual_network.blearn_vnet.name
  address_prefixes     = ["10.0.1.0/24"]
}

# --- 1. STORAGE CHO MEDALLION LAYERS ---
resource "azurerm_storage_account" "data_storage" {
  # Hãy đổi tên này nếu bị báo lỗi "already exists"
  name                     = "stblearnminhdata2026" 
  resource_group_name      = azurerm_resource_group.compute.name
  location                 = azurerm_resource_group.compute.location
  account_tier             = "Standard"
  account_replication_type = "LRS"
}

resource "azurerm_storage_container" "layers" {
  for_each              = toset(["bronze", "silver", "gold"])
  name                  = each.key
  storage_account_name  = azurerm_storage_account.data_storage.name
  container_access_type = "private"
}

# --- CỤM KUBERNETES (AKS) ---
resource "azurerm_kubernetes_cluster" "aks" {
  name                = "aks-blearn-dev"
  location            = azurerm_resource_group.compute.location
  resource_group_name = azurerm_resource_group.compute.name
  dns_prefix          = "blearn"

	oidc_issuer_enabled = true # Phải giữ là true để tránh lỗi này

  default_node_pool {
    name       = "default"
    node_count = 2 # Giữ nguyên số lượng bạn muốn mở rộng
    vm_size    = "Standard_D2s_v3"
    
    # Đảm bảo vnet_subnet_id vẫn được khai báo để tránh lỗi network
    vnet_subnet_id = azurerm_subnet.aks_subnet.id 
  }

  identity {
    type = "SystemAssigned"
  }

  network_profile {
    network_plugin     = "azure"
    load_balancer_sku  = "standard"
    
    # THÊM 3 DÒNG NÀY ĐỂ TRÁNH TRÙNG LẶP:
    service_cidr       = "10.1.0.0/16"    # Dải IP cho các Service (ClusterIP)
    dns_service_ip     = "10.1.0.10"     # IP của dịch vụ DNS nội bộ (phải nằm trong service_cidr)
  }
}

resource "azurerm_container_registry" "acr" {
  name                = "acrblearnminh2026"
  resource_group_name = azurerm_resource_group.compute.name
  location            = azurerm_resource_group.compute.location
  sku                 = "Basic"
  admin_enabled       = true
}

resource "azurerm_role_assignment" "aks_acr" {
  principal_id                     = azurerm_kubernetes_cluster.aks.kubelet_identity[0].object_id
  role_definition_name             = "AcrPull"
  scope                            = azurerm_container_registry.acr.id
  skip_service_principal_aad_check = true
}

provider "kubernetes" {
  host                   = azurerm_kubernetes_cluster.aks.kube_config[0].host
  client_certificate     = base64decode(azurerm_kubernetes_cluster.aks.kube_config[0].client_certificate)
  client_key             = base64decode(azurerm_kubernetes_cluster.aks.kube_config[0].client_key)
  cluster_ca_certificate = base64decode(azurerm_kubernetes_cluster.aks.kube_config[0].cluster_ca_certificate)
}

resource "kubernetes_namespace_v1" "medallion" {
  metadata {
    name = "blearn-medallion"
  }
}

resource "kubernetes_secret_v1" "oulad_runtime" {
  metadata {
    name      = "oulad-runtime"
    namespace = kubernetes_namespace_v1.medallion.metadata[0].name
  }

  type = "Opaque"

  data = {
    AZURE_STORAGE_ACCOUNT = azurerm_storage_account.data_storage.name
    AZURE_STORAGE_KEY     = azurerm_storage_account.data_storage.primary_access_key
  }
}

resource "kubernetes_cron_job_v1" "oulad_medallion" {
  metadata {
    name      = "oulad-medallion-pipeline"
    namespace = kubernetes_namespace_v1.medallion.metadata[0].name
    labels = {
      app = "oulad-medallion"
    }
  }

  spec {
    schedule                      = var.oulad_cron_schedule
    concurrency_policy            = "Forbid"
    successful_jobs_history_limit = 1
    failed_jobs_history_limit      = 1

    job_template {
      metadata {
        labels = {
          app = "oulad-medallion"
        }
      }

      spec {
        backoff_limit = 1

        template {
          metadata {
            labels = {
              app = "oulad-medallion"
            }
          }

          spec {
            restart_policy = "Never"

            container {
              name              = "runner"
              image             = var.oulad_runner_image
              image_pull_policy = "Always"

              command = ["/bin/bash", "-c"]
              args = [<<-EOT
                set -euo pipefail
                export SPARK_DRIVER_MEMORY=4g

                python -m data_pipeline.silver.oulad \
                  --input-catalog bronze_catalog \
                  --input-namespace full_db \
                  --output-catalog silver_catalog \
                  --output-namespace silver \
                  --output-root "abfss://silver@$AZURE_STORAGE_ACCOUNT.dfs.core.windows.net/iceberg_warehouse/silver/" \
                  --input-container bronze \
                  --output-container silver

                python -m data_pipeline.gold.oulad \
                  --input-catalog silver_catalog \
                  --input-namespace silver_db \
                  --output-catalog gold_catalog \
                  --output-namespace gold \
                  --output-root "abfss://gold@$AZURE_STORAGE_ACCOUNT.dfs.core.windows.net/iceberg_warehouse/gold/" \
                  --input-container silver \
                  --output-container gold
EOT
              ]

              env {
                name = "AZURE_STORAGE_ACCOUNT"
                value_from {
                  secret_key_ref {
                    name = kubernetes_secret_v1.oulad_runtime.metadata[0].name
                    key  = "AZURE_STORAGE_ACCOUNT"
                  }
                }
              }

              env {
                name = "AZURE_STORAGE_KEY"
                value_from {
                  secret_key_ref {
                    name = kubernetes_secret_v1.oulad_runtime.metadata[0].name
                    key  = "AZURE_STORAGE_KEY"
                  }
                }
              }

              resources {
                limits = {
                  cpu    = "2"
                  memory = "6Gi"
                }
                requests = {
                  cpu    = "500m"
                  memory = "2Gi"
                }
              }
            }
          }
        }
      }
    }
  }
}

output "storage_account_key" {
  value     = azurerm_storage_account.data_storage.primary_access_key
  sensitive = true
}