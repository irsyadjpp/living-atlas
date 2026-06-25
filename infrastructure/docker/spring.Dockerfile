# ============================================================
# Living Atlas — Spring Boot Service (Generic)
# ============================================================
# Build:
#   docker build -f infrastructure/docker/spring.Dockerfile \
#     --build-arg SERVICE_DIR=content-service \
#     -t living-atlas/content-service .
#
# Args: SERVICE_DIR = one of: identity-service, content-service,
#                         knowledge-service, research-service,
#                         workflow-service, gateway-services
# ============================================================
# Builder: Maven 3.9.16 + Amazon Corretto JDK 25 (compile)
# Runtime: Eclipse Temurin JRE 25 (run)
# ============================================================

ARG MAVEN_VERSION=3.9.16
ARG RUNTIME_JAVA=25

# ---- Builder Stage ----
FROM docker.io/maven:${MAVEN_VERSION}-amazoncorretto-${RUNTIME_JAVA}-alpine AS builder

WORKDIR /app

# Copy and install shared packages (Docker layer cache)
COPY packages ./packages/

RUN cd packages/shared-events && mvn install -DskipTests -q || true
RUN cd packages/shared-web && mvn install -DskipTests -q || true

# Copy service source
ARG SERVICE_DIR
COPY services/${SERVICE_DIR}/pom.xml services/${SERVICE_DIR}/
COPY services/${SERVICE_DIR}/src/ services/${SERVICE_DIR}/src/

# Build service
RUN cd services/${SERVICE_DIR} && mvn package -DskipTests -q

# ---- Runtime Stage ----
FROM docker.io/eclipse-temurin:${RUNTIME_JAVA}-jre-alpine

RUN apk add --no-cache curl ca-certificates
WORKDIR /app

ARG SERVICE_DIR
COPY --from=builder /app/services/${SERVICE_DIR}/target/*.jar app.jar

RUN addgroup -S appuser && adduser -S -G appuser appuser \
    && chown -R appuser:appuser /app
USER appuser

EXPOSE 8080

HEALTHCHECK --interval=15s --timeout=5s --start-period=60s --retries=3 \
    CMD curl -f http://localhost:8080/actuator/health || exit 1

ENTRYPOINT ["java", "-jar", "app.jar"]