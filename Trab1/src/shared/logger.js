function createLogger(serviceName) {
  function format(level, message) {
    const timestamp = new Date().toISOString();
    return `[${timestamp}] [${serviceName}] [${level}] ${message}`;
  }

  return {
    info(message) {
      console.log(format("INFO", message));
    },
    warn(message) {
      console.warn(format("WARN", message));
    },
    error(message) {
      console.error(format("ERROR", message));
    }
  };
}

module.exports = { createLogger };
