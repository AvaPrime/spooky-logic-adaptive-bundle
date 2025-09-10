from fastapi import APIRouter, HTTPException
from datetime import datetime
from typing import Dict, List
from models.marketplace import (
    MarketplaceInstallRequest, MarketplaceInstallResponse,
    MarketplaceSearchRequest, MarketplaceSearchResponse,
    MarketplaceListResponse, MarketplaceStatusRequest, MarketplaceStatusResponse,
    MarketplaceManifest
)
from models.base import ErrorResponse
import uuid
from datetime import datetime

router = APIRouter(prefix="/marketplace", tags=["marketplace"])

# In-memory storage (replace with database in production)
INSTALLED_PACKAGES = {}
AVAILABLE_PACKAGES = {
    "ml-toolkit": {
        "name": "ml-toolkit",
        "version": "1.0.0",
        "description": "Machine learning utilities and algorithms",
        "category": "ml",
        "author": "ML Team",
        "public_key": "ssh-rsa AAAAB3NzaC1yc2EAAAADAQABAAABAQ...",
        "capabilities": ["training", "inference", "evaluation"],
        "dependencies": ["numpy>=1.20.0", "scikit-learn>=1.0.0"],
        "size_mb": 45.2,
        "download_url": "https://marketplace.example.com/packages/ml-toolkit-1.0.0.tar.gz",
        "checksum": "sha256:a1b2c3d4e5f6...",
        "created_at": datetime.utcnow(),
        "updated_at": datetime.utcnow()
    },
    "data-processor": {
        "name": "data-processor",
        "version": "2.1.0",
        "description": "Advanced data processing and transformation tools",
        "category": "data",
        "author": "Data Team",
        "public_key": "ssh-rsa AAAAB3NzaC1yc2EAAAADAQABAAABAQ...",
        "capabilities": ["etl", "validation", "transformation"],
        "dependencies": ["pandas>=1.3.0", "pydantic>=1.8.0"],
        "size_mb": 32.8,
        "download_url": "https://marketplace.example.com/packages/data-processor-2.1.0.tar.gz",
        "checksum": "sha256:b2c3d4e5f6a1...",
        "created_at": datetime.utcnow(),
        "updated_at": datetime.utcnow()
    }
}

@router.post("/install", response_model=MarketplaceInstallResponse)
async def install_package(request: MarketplaceInstallRequest):
    """Install a package from the marketplace"""
    try:
        # Check if package exists in marketplace
        if request.package_name not in AVAILABLE_PACKAGES:
            raise HTTPException(status_code=404, detail="Package not found in marketplace")
        
        package_info = AVAILABLE_PACKAGES[request.package_name]
        
        # Check version compatibility if specified
        if request.version and request.version != package_info["version"]:
            raise HTTPException(status_code=400, detail=f"Version {request.version} not available")
        
        # Check if already installed
        install_key = f"{request.package_name}-{package_info['version']}"
        if install_key in INSTALLED_PACKAGES:
            existing_install = INSTALLED_PACKAGES[install_key]
            if existing_install["status"] == "installed":
                return MarketplaceInstallResponse(
                    installation_id=existing_install["installation_id"],
                    package_name=request.package_name,
                    version=package_info["version"],
                    status="already_installed",
                    message="Package is already installed",
                    install_path=existing_install["install_path"],
                    installed_at=existing_install["installed_at"]
                )
        
        # Simulate installation process
        installation_id = f"install-{len(INSTALLED_PACKAGES) + 1}"
        install_path = f"{request.destination_directory}/{request.package_name}"
        
        # Create installation record
        installation_record = {
            "installation_id": installation_id,
            "package_name": request.package_name,
            "version": package_info["version"],
            "status": "installed",
            "install_path": install_path,
            "installed_at": datetime.utcnow(),
            "verify_signature": request.verify_signature,
            "auto_update": request.auto_update,
            "package_info": package_info
        }
        
        INSTALLED_PACKAGES[install_key] = installation_record
        
        return MarketplaceInstallResponse(
             installation_id=installation_id,
             package_name=request.package_name,
             version=package_info["version"],
             status="installed",
             message="Package successfully installed",
             install_path=install_path,
             installed_at=installation_record["installed_at"]
         )
     except HTTPException:
         raise
     except Exception as e:
         raise HTTPException(status_code=500, detail=str(e))

@router.post("/search", response_model=MarketplaceSearchResponse)
async def search_packages(request: MarketplaceSearchRequest):
    """Search for packages in the marketplace"""
    try:
        # Filter packages based on search criteria
        filtered_packages = []
        
        for package_name, package_info in AVAILABLE_PACKAGES.items():
            # Apply filters
            if request.query and request.query.lower() not in package_name.lower() and request.query.lower() not in package_info["description"].lower():
                continue
            
            if request.category and request.category != package_info["category"]:
                continue
            
            if request.author and request.author.lower() != package_info["author"].lower():
                continue
            
            # Convert to manifest format
            manifest = MarketplaceManifest(
                name=package_info["name"],
                version=package_info["version"],
                description=package_info["description"],
                category=package_info["category"],
                author=package_info["author"],
                public_key=package_info["public_key"],
                capabilities=package_info["capabilities"],
                dependencies=package_info["dependencies"],
                size_mb=package_info["size_mb"],
                download_url=package_info["download_url"],
                checksum=package_info["checksum"],
                created_at=package_info["created_at"],
                updated_at=package_info["updated_at"]
            )
            
            filtered_packages.append(manifest)
        
        # Apply pagination
        start_idx = (request.page - 1) * request.limit
        end_idx = start_idx + request.limit
        paginated_packages = filtered_packages[start_idx:end_idx]
        
        return MarketplaceSearchResponse(
            packages=paginated_packages,
            total_count=len(filtered_packages),
            page=request.page,
            limit=request.limit,
            has_more=end_idx < len(filtered_packages)
        )
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@router.get("/list", response_model=MarketplaceListResponse)
async def list_packages():
    """List all available packages in the marketplace"""
    try:
        packages = []
        
        for package_name, package_info in AVAILABLE_PACKAGES.items():
            manifest = MarketplaceManifest(
                name=package_info["name"],
                version=package_info["version"],
                description=package_info["description"],
                category=package_info["category"],
                author=package_info["author"],
                public_key=package_info["public_key"],
                capabilities=package_info["capabilities"],
                dependencies=package_info["dependencies"],
                size_mb=package_info["size_mb"],
                download_url=package_info["download_url"],
                checksum=package_info["checksum"],
                created_at=package_info["created_at"],
                updated_at=package_info["updated_at"]
            )
            packages.append(manifest)
        
        # Group by category
        categories = {}
        for package in packages:
            if package.category not in categories:
                categories[package.category] = []
            categories[package.category].append(package)
        
        return MarketplaceListResponse(
            packages=packages,
            total_count=len(packages),
            categories=list(categories.keys()),
            packages_by_category=categories
        )
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@router.post("/status", response_model=MarketplaceStatusResponse)
async def get_installation_status(request: MarketplaceStatusRequest):
    """Get the installation status of a package"""
    try:
        # Find installation by package name or installation ID
        installation_record = None
        
        if request.installation_id:
            # Search by installation ID
            for install_key, record in INSTALLED_PACKAGES.items():
                if record["installation_id"] == request.installation_id:
                    installation_record = record
                    break
        elif request.package_name:
            # Search by package name (get latest version)
            for install_key, record in INSTALLED_PACKAGES.items():
                if record["package_name"] == request.package_name:
                    if not installation_record or record["installed_at"] > installation_record["installed_at"]:
                        installation_record = record
        
        if not installation_record:
            raise HTTPException(status_code=404, detail="Installation not found")
        
        # Check if package is still available in marketplace
        package_available = installation_record["package_name"] in AVAILABLE_PACKAGES
        
        # Calculate installation health
        current_time = datetime.utcnow()
        install_age_hours = (current_time - installation_record["installed_at"]).total_seconds() / 3600
        
        health_status = "healthy"
        if install_age_hours > 24 * 30:  # Older than 30 days
            health_status = "outdated"
        elif not package_available:
            health_status = "orphaned"
        
        return MarketplaceStatusResponse(
            installation_id=installation_record["installation_id"],
            package_name=installation_record["package_name"],
            version=installation_record["version"],
            status=installation_record["status"],
            install_path=installation_record["install_path"],
            installed_at=installation_record["installed_at"],
            last_updated=installation_record["installed_at"],
            health_status=health_status,
            package_available=package_available,
            auto_update_enabled=installation_record.get("auto_update", False)
        )
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))
