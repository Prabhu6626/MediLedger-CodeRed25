import hashlib
import json
from time import time
from datetime import datetime


class Blockchain:
    def __init__(self):
        self.chain = []
        self.current_transactions = []
        self.new_block(previous_hash='1', proof=100) 

    def new_block(self, proof, previous_hash=None):
        """
        Creates a new Block and adds it to the chain.
        :param proof: The proof given by the Proof of Work algorithm
        :param previous_hash: (Optional) Hash of the previous Block
        :return: New Block
        """
        block = {
            'index': len(self.chain) + 1,
            'timestamp': str(datetime.now()),
            'transactions': self.current_transactions,
            'proof': proof,
            'previous_hash': previous_hash or self.hash(self.chain[-1]),
        }

        self.current_transactions = [] 
        self.chain.append(block)  
        return block

    def new_transaction(self, sender, recipient, product_id, status):
        """
        Adds a new transaction to the list of transactions.
        :param sender: Address of the sender (Manufacturer/Distributor)
        :param recipient: Address of the recipient (Pharmacy)
        :param product_id: Product ID for tracking
        :param status: The current status of the product (Received, Ready for Transport)
        :return: The index of the block that will contain this transaction
        """
        self.current_transactions.append({
            'sender': sender,
            'recipient': recipient,
            'product_id': product_id,
            'status': status,
            'timestamp': str(datetime.now())
        })

        return self.last_block['index'] + 1

    def proof_of_work(self, last_proof):
        """
        Simple Proof of Work Algorithm:
        - Find a number p' such that hash(pp') contains 4 leading zeroes.
        - p is the previous proof, and p' is the new proof.
        :param last_proof: Previous proof
        :return: New proof
        """
        proof = 0
        while self.valid_proof(last_proof, proof) is False:
            proof += 1
        return proof

    def valid_proof(self, last_proof, proof):
        """
        Validates the proof: Does hash(last_proof, proof) contain 4 leading zeroes?
        :param last_proof: Previous proof
        :param proof: Current proof
        :return: True if the proof is valid, False otherwise
        """
        guess = f'{last_proof}{proof}'.encode()
        guess_hash = hashlib.sha256(guess).hexdigest()
        return guess_hash[:4] == "0000"

    @staticmethod
    def hash(block):
        """
        Creates a SHA-256 hash of a Block
        :param block: Block
        :return: SHA-256 hash string
        """
        block_string = json.dumps(block, sort_keys=True).encode()
        return hashlib.sha256(block_string).hexdigest()

    @property
    def last_block(self):
        return self.chain[-1]

    def validate_chain(self):
        """
        Check the validity of the chain.
        :return: True if the blockchain is valid, False otherwise
        """
        last_block = self.chain[0]
        current_index = 1

        while current_index < len(self.chain):
            block = self.chain[current_index]
            if block['previous_hash'] != self.hash(last_block):
                return False
            if not self.valid_proof(last_block['proof'], block['proof']):
                return False
            last_block = block
            current_index += 1

        return True

    def get_blockchain_data(self):
        """
        Returns the entire blockchain data as a list of dictionaries
        :return: List of blocks
        """
        blockchain_data = []
        for block in self.chain:
            block_data = {
                'index': block['index'],
                'timestamp': block['timestamp'],
                'transactions': block['transactions'],
                'proof': block['proof'],
                'previous_hash': block['previous_hash'],
            }
            blockchain_data.append(block_data)

        return blockchain_data


# Example Usage:
if __name__ == "__main__":
    blockchain = Blockchain()
    
    # Add transactions
    blockchain.new_transaction('Manufacturer', 'Distributor', 'Product-1', 'Received')
    blockchain.new_transaction('Distributor', 'Pharmacy', 'Product-1', 'Ready for Transport')

    # Perform proof of work to create a new block
    proof = blockchain.proof_of_work(blockchain.last_block['proof'])
    blockchain.new_block(proof)

    # Display blockchain data
    for block in blockchain.get_blockchain_data():
        print(block)
