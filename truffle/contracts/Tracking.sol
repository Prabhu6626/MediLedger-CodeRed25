// truffle/contracts/Tracking.sol
// SPDX-License-Identifier: MIT
pragma solidity ^0.8.0;

contract Tracking {
    struct Product {
        string productId;
        string currentLocation;
        bool isDelivered;
    }

    mapping(string => Product) public products;

    event ProductUpdated(string productId, string location, bool delivered);

    function addProduct(string memory _productId, string memory _initialLocation) public {
        products[_productId] = Product(_productId, _initialLocation, false);
        emit ProductUpdated(_productId, _initialLocation, false);
    }

    function updateLocation(string memory _productId, string memory _newLocation) public {
        require(bytes(products[_productId].productId).length != 0, "Product does not exist");
        require(!products[_productId].isDelivered, "Product already delivered");
        products[_productId].currentLocation = _newLocation;
        emit ProductUpdated(_productId, _newLocation, products[_productId].isDelivered);
    }

    function markAsDelivered(string memory _productId) public {
        require(bytes(products[_productId].productId).length != 0, "Product does not exist");
        products[_productId].isDelivered = true;
        emit ProductUpdated(_productId, products[_productId].currentLocation, true);
    }

    function getLocation(string memory _productId) public view returns (string memory) {
        require(bytes(products[_productId].productId).length != 0, "Product does not exist");
        return products[_productId].currentLocation;
    }
}
