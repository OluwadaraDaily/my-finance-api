import pytest
from datetime import datetime
from services.category_service import CategoryService
from schemas.category import CategoryCreate, CategoryUpdate
from db.models.category import Category
from fastapi import HTTPException

def test_get_categories(db_session, test_user):
    category_service = CategoryService(db_session)
    
    # Create test categories
    category1 = Category(name="Test Category 1", user_id=test_user.id)
    category2 = Category(name="Test Category 2", user_id=test_user.id)
    db_session.add_all([category1, category2])
    db_session.commit()

    # Get categories
    categories = category_service.get_categories(test_user.id)
    assert len(categories) == 2
    assert categories[0].name == "Test Category 1"
    assert categories[1].name == "Test Category 2"
    assert all(cat.user_id == test_user.id for cat in categories)

def test_create_category(db_session, test_user):
    category_service = CategoryService(db_session)
    category_data = CategoryCreate(name="Test Category", color="#FF0000")

    # Create category
    category = category_service.create_category(test_user.id, category_data)
    db_session.refresh(category)
    
    assert category.name == "Test Category"
    assert category.user_id == test_user.id
    assert category.color == "#FF0000"
    assert category.id is not None
    assert category.created_at is not None

def test_create_duplicate_category(db_session, test_user):
    category_service = CategoryService(db_session)
    category_data = CategoryCreate(name="Test Category")

    # Create first category
    category_service.create_category(test_user.id, category_data)

    # Try to create duplicate category
    with pytest.raises(HTTPException) as exc_info:
        category_service.create_category(test_user.id, category_data)
    assert exc_info.value.status_code == 400
    assert exc_info.value.detail == "Category already exists"

def test_update_category(db_session, test_user):
    category_service = CategoryService(db_session)
    
    # Create initial category
    category = Category(name="Old Name", user_id=test_user.id)
    db_session.add(category)
    db_session.commit()
    
    # Update category
    update_data = CategoryUpdate(name="New Name", color="#00FF00")
    updated_category = category_service.update_category(category.id, test_user.id, update_data)
    
    db_session.refresh(updated_category)

    assert updated_category.name == "New Name"
    assert updated_category.color == "#00FF00"
    
    # Verify database persistence
    assert updated_category.updated_at is not None

def test_delete_category(db_session, test_user):
    category_service = CategoryService(db_session)
    
    # Create category to delete
    category = Category(name="To Delete", user_id=test_user.id)
    db_session.add(category)
    db_session.commit()
    category_id = category.id
    
    # Delete category
    result = category_service.delete_category(category_id, test_user.id)
    assert result is True
    
    # Verify deletion
    deleted_category = db_session.query(Category).filter(Category.id == category_id).first()
    assert deleted_category is None

def test_get_category_not_found(db_session, test_user):
    category_service = CategoryService(db_session)
    
    with pytest.raises(HTTPException) as exc_info:
        category_service.get_category(999, test_user.id)
    
    assert exc_info.value.status_code == 404
    assert exc_info.value.detail == "Category not found"

def test_update_nonexistent_category(db_session, test_user):
    category_service = CategoryService(db_session)
    update_data = CategoryUpdate(name="New Name")
    
    with pytest.raises(HTTPException) as exc_info:
        category_service.update_category(999, test_user.id, update_data)
    
    assert exc_info.value.status_code == 404
    assert exc_info.value.detail == "Category not found"

def test_delete_nonexistent_category(db_session, test_user):
    category_service = CategoryService(db_session)
    
    with pytest.raises(HTTPException) as exc_info:
        category_service.delete_category(999, test_user.id)
    
    assert exc_info.value.status_code == 404
    assert exc_info.value.detail == "Category not found" 