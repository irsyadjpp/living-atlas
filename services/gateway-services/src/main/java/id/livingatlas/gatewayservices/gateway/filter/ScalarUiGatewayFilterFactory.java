package id.livingatlas.gatewayservices.gateway.filter;

import lombok.RequiredArgsConstructor;
import org.springframework.cloud.gateway.filter.GatewayFilter;
import org.springframework.cloud.gateway.filter.factory.AbstractGatewayFilterFactory;
import org.springframework.core.io.ClassPathResource;
import org.springframework.core.io.Resource;
import org.springframework.http.HttpHeaders;
import org.springframework.http.MediaType;
import org.springframework.http.codec.HttpMessageWriter;
import org.springframework.stereotype.Component;
import reactor.core.publisher.Mono;

import java.nio.charset.StandardCharsets;
import java.util.Collections;
import java.util.List;

@Component
@RequiredArgsConstructor
public class ScalarUiGatewayFilterFactory extends AbstractGatewayFilterFactory<Object> {

    private static final String SCALAR_HTML = loadScalarHtml();

    private static String loadScalarHtml() {
        try {
            Resource resource = new ClassPathResource("static/scalar/index.html");
            return new String(resource.getContentAsByteArray(), StandardCharsets.UTF_8);
        } catch (Exception e) {
            return "<html><body>Error loading Scalar UI</body></html>";
        }
    }

    @Override
    public GatewayFilter apply(Object config) {
        return (exchange, chain) -> {
            exchange.getResponse().getHeaders().setContentType(MediaType.TEXT_HTML);
            exchange.getResponse().getHeaders().set(HttpHeaders.CONTENT_LENGTH, String.valueOf(SCALAR_HTML.getBytes(StandardCharsets.UTF_8).length));
            
            return exchange.getResponse().writeWith(
                Mono.just(exchange.getResponse().bufferFactory().wrap(
                    SCALAR_HTML.getBytes(StandardCharsets.UTF_8)
                ))
            );
        };
    }

    @Override
    public List<String> shortcutFieldOrder() {
        return Collections.emptyList();
    }
}
