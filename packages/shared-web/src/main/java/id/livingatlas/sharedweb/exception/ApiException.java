package id.livingatlas.sharedweb.exception;

import lombok.Getter;
import org.springframework.http.HttpStatus;

/**
 * Base exception for all API errors.
 * Each exception has a standard error code and HTTP status.
 */
@Getter
public class ApiException extends RuntimeException {

    private final String code;
    private final HttpStatus httpStatus;

    public ApiException(String code, String message, HttpStatus httpStatus) {
        super(message);
        this.code = code;
        this.httpStatus = httpStatus;
    }

    public static ApiException badRequest(String message) {
        return new ApiException("VALIDATION_ERROR", message, HttpStatus.BAD_REQUEST);
    }

    public static ApiException unauthorized(String message) {
        return new ApiException("UNAUTHORIZED", message, HttpStatus.UNAUTHORIZED);
    }

    public static ApiException forbidden(String message) {
        return new ApiException("FORBIDDEN", message, HttpStatus.FORBIDDEN);
    }

    public static ApiException notFound(String message) {
        return new ApiException("NOT_FOUND", message, HttpStatus.NOT_FOUND);
    }

    public static ApiException conflict(String message) {
        return new ApiException("CONFLICT", message, HttpStatus.CONFLICT);
    }

    public static ApiException rateLimited(String message) {
        return new ApiException("RATE_LIMITED", message, HttpStatus.TOO_MANY_REQUESTS);
    }

    public static ApiException internalError(String message) {
        return new ApiException("INTERNAL_ERROR", message, HttpStatus.INTERNAL_SERVER_ERROR);
    }
}