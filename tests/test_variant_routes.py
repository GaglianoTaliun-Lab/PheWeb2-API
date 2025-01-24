import pytest
from flask import g
from unittest.mock import MagicMock
from app import app  # Import your Flask app from app.py

import request, os


@pytest.fixture
def client():
    """
    Fixture for Flask test client with application context.
    """
    with app.app_context():  # Activate the app context
        with app.test_client() as client:  # Create the test client
            yield client  # Provide the test client to the test


@pytest.fixture
def mock_variant():
    """
    Fixture for mocking the variant object in Flask's `g`.
    """
    with app.app_context():  # Activate the app context
        g.variant = MagicMock()  # Mock the `variant` object
        yield g.variant  # Provide the mock object to the test
        
        
def test_get_stratification_list_success(client, mock_variant):
    """
    Test a successful response for getting the stratification list.
    """
    def mock_get_stratifications():
        data_dir = os.getenv("PHENOTYPES_DIR")
    
    mock_variant.get_stratifications.side_effect = mock_get_stratifications

    # Make the GET request
    response = client.get("/variant/stratification_list")

    # Debugging prints
    print(f"{response.status_code=}")
    print(f"{response.json=}")

    # Assertions
    assert response.status_code == 200
    assert response.json == ["Strat1", "Strat2"]
    mock_variant.get_stratifications.assert_called_once()


def test_get_stratification_list_not_found(client, mock_variant):
    """
    Test a 404 response when stratifications are not found.
    """
    # Simulate no data being available
    def mock_get_stratifications():
        return None  # Simulate no stratifications found

    # Attach the side effect to the mock
    mock_variant.get_stratifications.side_effect = mock_get_stratifications

    # Make the GET request
    response = client.get("/variant/stratification_list")

    # Debugging prints
    print(f"{response.status_code=}")
    print(f"{response.json=}")

    # Assertions
    assert response.status_code == 404
    assert response.json == {
        "message": "Could not fetch the list of stratifications within data. Please check phenotypes.json file."
    }
    mock_variant.get_stratifications.assert_called_once()
    
def test_get_variant_success(client, mock_variant):
    """
    Test a successful response for getting variant data.
    """
    # Set a JSON-serializable return value for the mock
    mock_variant.get_variant.return_value = {"data": "PheWAS data"}  # Use a dictionary
    
    # Make the GET request
    response = client.get("/variant/1-196698298-A-T/European.Male")
    
    # Print the response for debugging
    print(f"{response=}, {response.status_code=}, {response.json=}")
    
    # Assert the response
    assert response.status_code == 200
    assert response.json == {"data": "PheWAS data"}
    
    # Ensure the mock was called with the expected arguments
    mock_variant.get_variant.assert_called_once_with("1-196698298-A-T", "European.Male")
