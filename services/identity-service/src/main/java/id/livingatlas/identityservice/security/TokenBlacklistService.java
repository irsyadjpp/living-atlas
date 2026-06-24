package id.livingatlas.identityservice.security;

import org.springframework.stereotype.Service;

import java.util.Map;
import java.util.concurrent.ConcurrentHashMap;

/**
 * Token blacklist service.
 * Production: replace with Redis implementation.
 */
@Service
public class TokenBlacklistService {

    private final Map<String, Long> blacklistedTokens = new ConcurrentHashMap<>();

    public void blacklist(String token, long expirationMs) {
        blacklistedTokens.put(token, System.currentTimeMillis() + expirationMs);
    }

    public boolean isBlacklisted(String token) {
        cleanup();
        return blacklistedTokens.containsKey(token);
    }

    private void cleanup() {
        long now = System.currentTimeMillis();
        blacklistedTokens.entrySet().removeIf(entry -> entry.getValue() < now);
    }
}