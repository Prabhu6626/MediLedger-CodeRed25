// truffle/migrations/2_deploy_tracking.js
const Tracking = artifacts.require("Tracking");

module.exports = function (deployer) {
  deployer.deploy(Tracking);
};
