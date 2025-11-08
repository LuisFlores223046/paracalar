from pydantic import BaseModel, Field, field_validator
from typing import Optional, List
from datetime import datetime


# ============ CATEGORY SCHEMAS ============
class CategoryBase(BaseModel):
    name: str = Field(..., min_length=1, max_length=100)
    description: Optional[str] = None
    image_url: Optional[str] = None


class CategoryResponse(CategoryBase):
    category_id: int
    is_active: bool
    created_at: datetime
    updated_at: datetime

    class Config:
        from_attributes = True


# ============ PRODUCT IMAGE SCHEMAS ============
class ProductImageBase(BaseModel):
    image_url: str
    is_primary: bool = False
    display_order: int = 0


class ProductImageCreate(ProductImageBase):
    pass


class ProductImageResponse(ProductImageBase):
    image_id: int
    product_id: int
    created_at: datetime

    class Config:
        from_attributes = True


# ============ PRODUCT SCHEMAS ============
class ProductBase(BaseModel):
    name: str = Field(..., min_length=1, max_length=255)
    description: Optional[str] = None
    price: float = Field(..., gt=0)
    stock: int = Field(default=0, ge=0)
    category_id: Optional[int] = None  # ✅ Ahora es opcional
    fitness_objective: Optional[str] = Field(None, max_length=100)
    physical_activity: Optional[str] = Field(None, max_length=100)
    sku: Optional[str] = Field(None, max_length=100)
    brand: Optional[str] = Field(None, max_length=100)


class ProductCreate(ProductBase):
    images: Optional[List[ProductImageCreate]] = []


class ProductUpdate(BaseModel):
    name: Optional[str] = Field(None, min_length=1, max_length=255)
    description: Optional[str] = None
    price: Optional[float] = Field(None, gt=0)
    stock: Optional[int] = Field(None, ge=0)
    category_id: Optional[int] = None
    fitness_objective: Optional[str] = Field(None, max_length=100)
    physical_activity: Optional[str] = Field(None, max_length=100)
    sku: Optional[str] = Field(None, max_length=100)
    brand: Optional[str] = Field(None, max_length=100)
    is_active: Optional[bool] = None


class ProductResponse(ProductBase):
    product_id: int
    average_rating: float
    is_active: bool
    created_at: datetime
    updated_at: datetime
    category: Optional[CategoryResponse] = None  # ✅ Ahora es opcional
    images: List[ProductImageResponse] = []

    class Config:
        from_attributes = True


class ProductListResponse(BaseModel):
    product_id: int
    name: str
    price: float
    stock: int
    average_rating: float
    brand: Optional[str]
    category: Optional[CategoryResponse] = None  # ✅ Ahora es opcional
    primary_image: Optional[str] = None

    class Config:
        from_attributes = True


# ============ REVIEW SCHEMAS ============
class ReviewBase(BaseModel):
    rating: int = Field(..., ge=1, le=5)
    review_text: Optional[str] = None


class ReviewCreate(ReviewBase):
    pass


class ReviewUpdate(BaseModel):
    rating: Optional[int] = Field(None, ge=1, le=5)
    review_text: Optional[str] = None


class ReviewResponse(ReviewBase):
    review_id: int
    product_id: int
    user_id: int
    date_created: datetime
    updated_at: datetime
    user_name: Optional[str] = None  # Se llena en el service

    class Config:
        from_attributes = True


# ============ PAGINATION ============
class PaginationParams(BaseModel):
    page: int = Field(default=1, ge=1)
    limit: int = Field(default=10, ge=1, le=100)


class PaginatedResponse(BaseModel):
    items: List[ProductListResponse]
    total: int
    page: int
    limit: int
    total_pages: int
