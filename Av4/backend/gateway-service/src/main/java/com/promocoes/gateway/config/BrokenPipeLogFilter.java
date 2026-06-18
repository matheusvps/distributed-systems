package com.promocoes.gateway.config;

import ch.qos.logback.classic.Level;
import ch.qos.logback.classic.Logger;
import ch.qos.logback.classic.turbo.TurboFilter;
import ch.qos.logback.core.spi.FilterReply;
import org.slf4j.Marker;

import java.io.IOException;

public class BrokenPipeLogFilter extends TurboFilter {

    @Override
    public FilterReply decide(Marker marker, Logger logger, Level level,
                              String format, Object[] params, Throwable t) {
        if (t != null && isBrokenPipe(t)) {
            return FilterReply.DENY;
        }
        return FilterReply.NEUTRAL;
    }

    private boolean isBrokenPipe(Throwable t) {
        for (Throwable cause = t; cause != null; cause = cause.getCause()) {
            if (cause instanceof IOException) {
                String message = cause.getMessage();
                if (message != null && message.contains("Broken pipe")) {
                    return true;
                }
            }
        }
        return false;
    }
}
