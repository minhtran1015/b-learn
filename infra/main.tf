# infra/main.tf
terraform {
  required_providers {
    azurerm = {
      source  = "hashicorp/azurerm"
      version = "~> 3.0"
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

output "storage_account_key" {
  value     = azurerm_storage_account.data_storage.primary_access_key
  sensitive = true
}