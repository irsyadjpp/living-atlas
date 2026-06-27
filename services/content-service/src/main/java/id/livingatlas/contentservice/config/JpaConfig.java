package id.livingatlas.contentservice.config;

import org.springframework.boot.persistence.autoconfigure.EntityScan;
import org.springframework.context.annotation.Configuration;
import org.springframework.data.jpa.repository.config.EnableJpaAuditing;
import org.springframework.data.jpa.repository.config.EnableJpaRepositories;
import org.springframework.transaction.annotation.EnableTransactionManagement;

@Configuration
@EnableJpaAuditing
@EnableJpaRepositories(basePackages = "id.livingatlas")
@EnableTransactionManagement
@EntityScan({
        "id.livingatlas.contentservice",
        "id.livingatlas.sharedweb"
})
public class JpaConfig {
}
