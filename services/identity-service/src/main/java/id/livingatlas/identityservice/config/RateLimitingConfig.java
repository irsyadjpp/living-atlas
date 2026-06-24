package id.livingatlas.identityservice.config;

import io.github.bucket4j.Bandwidth;
import io.github.bucket4j.Bucket;
import io.github.bucket4j.Refill;
import org.springframework.context.annotation.Bean;
import org.springframework.context.annotation.Configuration;

import java.time.Duration;

/**
 * Rate limiting configuration for brute force protection (OWASP ASVS 2.2, UU PDP Pasal 20).
 */
@Configuration
public class RateLimitingConfig {

    @Bean
    public Bucket loginBucket() {
        Bandwidth limit = Bandwidth.classic(5, Refill.greedy(5, Duration.ofMinutes(1)));
        return Bucket.builder().addLimit(limit).build();
    }

    @Bean
    public Bucket registerBucket() {
        Bandwidth limit = Bandwidth.classic(3, Refill.greedy(3, Duration.ofMinutes(1)));
        return Bucket.builder().addLimit(limit).build();
    }
}