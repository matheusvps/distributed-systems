const { LOG_LEVELS } = require("./constants");

function createLogger(serviceName) {
  function format(level, message) {
    const timestamp = new Date().toISOString();
    const safeLevel = Object.values(LOG_LEVELS).includes(level) ? level : LOG_LEVELS.INFO;
    return `[${timestamp}] [${serviceName}] [${safeLevel}] ${message}`;
  }

  return {
    info(message) {
      console.log(format(LOG_LEVELS.INFO, message));
    },
    warn(message) {
      console.warn(format(LOG_LEVELS.WARN, message));
    },
    error(message) {
      console.error(format(LOG_LEVELS.ERROR, message));
    }
  };
}

module.exports = { createLogger };
