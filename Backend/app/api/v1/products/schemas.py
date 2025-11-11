from pydantic import BaseModel, Field
from typing import Optional, List
from datetime import datetime


# ============ PRODUCT IMAGE SCHEMAS ============
class ProductImageBase(BaseModel):
    image_path: str
    is_primary: bool = False


class ProductImageCreate(ProductImageBase):
    pass


class ProductImageResponse(ProductImageBase):
    image_id: int
    product_id: int

    class Config:
        from_attributes = True


# ============ PRODUCT SCHEMAS ============
class ProductBase(BaseModel):
    name: str = Field(..., min_length=1, max_length=255)
    description: Optional[str] = None
    brand: str = Field(..., min_length=1, max_length=100)
    category: str = Field(..., min_length=1, max_length=100)
    physical_activities: List[str] = Field(default_factory=list)
    fitness_objectives: List[str] = Field(default_factory=list)
    nutritional_value: str
    price: float = Field(..., gt=0)
    stock: int = Field(default=0, ge=0)


class ProductCreate(ProductBase):
    product_images: Optional[List[ProductImageCreate]] = []


class ProductUpdate(BaseModel):
    name: Optional[str] = Field(None, min_length=1, max_length=255)
    description: Optional[str] = None
    brand: Optional[str] = Field(None, min_length=1, max_length=100)
    category: Optional[str] = Field(None, min_length=1, max_length=100)
    physical_activities: Optional[List[str]] = None
    fitness_objectives: Optional[List[str]] = None
    nutritional_value: Optional[str] = None
    price: Optional[float] = Field(None, gt=0)
    stock: Optional[int] = Field(None, ge=0)
    is_active: Optional[bool] = None


class ProductResponse(ProductBase):
    product_id: int
    average_rating: Optional[float]
    is_active: bool
    created_at: datetime
    updated_at: datetime
    product_images: List[ProductImageResponse] = []

    class Config:
        from_attributes = True


class ProductListResponse(BaseModel):
    """Schema simplificado para listado de productos"""
    product_id: int
    name: str
    brand: str
    category: str
    price: float
    stock: int
    average_rating: Optional[float]
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
    user_name: Optional[str] = None

    class Config:
        from_attributes = True