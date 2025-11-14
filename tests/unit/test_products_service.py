from pytest_mock import MockerFixture
from decimal import Decimal

from app.api.v1.products.service import ReviewService
from app.models.product import Product
from app.models.review import Review

def test_update_product_rating(mocker: MockerFixture):
    """
    Prueba unitaria: Verifica que el rating promedio se calcula y actualiza
    correctamente en el producto.
    """
    # 1. Setup
    mock_db = mocker.MagicMock()
    product_id = 1
    
    # Mockear el producto que se va a actualizar
    mock_product = Product(product_id=product_id, average_rating=None)
    mock_db.query.return_value.filter.return_value.first.return_value = mock_product
    
    # Mockear el cálculo del promedio de la BD
    # Simulamos que la BD devuelve un promedio de 4.333
    mock_avg_rating = Decimal('4.3333')
    mock_db.query.return_value.filter.return_value.scalar.return_value = mock_avg_rating

    # 2. Act
    # Llamamos al método privado (normalmente no se hace, pero aquí es clave)
    ReviewService._update_product_rating(db=mock_db, product_id=product_id)

    # 3. Assert
    # El producto debe tener su rating actualizado y redondeado
    assert mock_product.average_rating == 4.3333