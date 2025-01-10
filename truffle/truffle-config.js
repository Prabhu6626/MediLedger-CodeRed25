// truffle/truffle-config.js
require('dotenv').config();
const HDWalletProvider = require('@truffle/hdwallet-provider');

const { MNEMONIC, INFURA_PROJECT_ID } = process.env;

module.exports = {
  networks: {
    development: {
      host: "127.0.0.1",
      port: 7545, // Default Ganache port
      network_id: "*",
    },
    rinkeby: {
      provider: () => new HDWalletProvider(
        MNEMONIC,
        `https://rinkeby.infura.io/v3/${INFURA_PROJECT_ID}`
      ),
      network_id: 4,       // Rinkeby's network ID
      gas: 5500000,        // Gas limit
      confirmations: 2,    // # of confs to wait between deployments
      timeoutBlocks: 200,  // # of blocks before a deployment times out
      skipDryRun: true     // Skip dry run before migrations
    },
  },
  compilers: {
    solc: {
      version: "0.8.0",    // Solidity version
      settings: {
        optimizer: {
          enabled: true,
          runs: 200
        }
      }
    }
  },
};
