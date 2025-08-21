import pytest

def test_get_phenotypes(client):
    """
    Test a successful response for getting the phenotypes.
    """
    response = client.get("/phenotypes/")
    assert response.status_code == 200

    data = response.json
    assert isinstance(data, list)
    assert len(data) == 11

def test_get_gene_names(client):
    """
    Test a successful response for getting the gene names.
    """
    response = client.get("/gene/")
    assert response.status_code == 200

    data = response.json
    assert isinstance(data, list)
    assert len(data) == 20371
    assert "PCSK9" in data

def test_get_gene_PCSK9(client):
    """
    Test a successful response for getting the gene PCSK9.
    """
    response = client.get("/gene/PCSK9")
    assert response.status_code == 200
    
    data = response.json
    assert isinstance(data, dict)
    assert data["gene"] == "PCSK9"
    assert isinstance(data["data"], list)
    assert len(data["data"]) == 11

def test_get_tophits(client):
    """
    Test a successful response for getting the tophits.
    """
    response = client.get("/phenotypes/tophits")
    assert response.status_code == 200
    
    data = response.json
    assert isinstance(data, list)
    assert len(data) == 161
    assert '10-112999020-G-T' in [f'{x["chrom"]}-{x["pos"]}-{x["ref"]}-{x["alt"]}' for x in data]

def test_get_stratifications(client):
    """
    Test a successful response for getting the stratifications.
    """
    response = client.get("/variant/stratification_list")
    assert response.status_code == 200

    data = response.json
    assert isinstance(data, list)
    assert len(data) == 3
    assert all(x in data for x in ["european.both", "european.male", "european.female"])

def test_get_variant_10_112999020_G_T(client):
    """
    Test a successful response for getting the variant 10-112999020-G-T.
    """
    response = client.get("/variant/10-112999020-G-T/european.both")
    assert response.status_code == 200
    
    data = response.json
    assert isinstance(data, dict)
    assert len(data) > 0
    
    



# def test_get_stratification_list_not_found(client, mock_variant):
#     """
#     Test a 404 response when stratifications are not found.
#     """
#     # Simulate no data being available
#     def mock_get_stratifications():
#         return None  # Simulate no stratifications found

#     # Attach the side effect to the mock
#     mock_variant.get_stratifications.side_effect = mock_get_stratifications

#     # Make the GET request
#     response = client.get("/variant/stratification_list")

#     # Debugging prints
#     print(f"{response.status_code=}")
#     print(f"{response.json=}")

#     # Assertions
#     assert response.status_code == 404
#     assert response.json == {
#         "message": "Could not fetch the list of stratifications within data. Please check phenotypes.json file."
#     }
#     mock_variant.get_stratifications.assert_called_once()
    
# def test_get_variant_success(client, mock_variant):
#     """
#     Test a successful response for getting variant data.
#     """
#     # Set a JSON-serializable return value for the mock
#     mock_variant.get_variant.return_value = {"data": "PheWAS data"}  # Use a dictionary
    
#     # Make the GET request
#     response = client.get("/variant/1-196698298-A-T/European.Male")
    
#     # Print the response for debugging
#     print(f"{response=}, {response.status_code=}, {response.json=}")
    
#     # Assert the response
#     assert response.status_code == 200
#     assert response.json == {"data": "PheWAS data"}
    
#     # Ensure the mock was called with the expected arguments
#     mock_variant.get_variant.assert_called_once_with("1-196698298-A-T", "European.Male")
