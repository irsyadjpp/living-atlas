package id.livingatlas.sharedweb.response;

import com.fasterxml.jackson.annotation.JsonInclude;
import java.util.List;

@JsonInclude(JsonInclude.Include.NON_NULL)
public class ErrorResponse {

    private ErrorDetail error;

    public ErrorResponse() {}

    public ErrorResponse(ErrorDetail error) { this.error = error; }

    public ErrorDetail getError() { return error; }
    public void setError(ErrorDetail error) { this.error = error; }

    public static ErrorResponse validation(String message, List<ErrorDetailItem> details) {
        ErrorDetail detail = new ErrorDetail("VALIDATION_ERROR", message, details, null);
        return new ErrorResponse(detail);
    }

    public static ErrorResponse of(String code, String message) {
        return new ErrorResponse(new ErrorDetail(code, message, null, null));
    }

    public static ErrorResponse unauthorized(String msg) { return of("UNAUTHORIZED", msg); }
    public static ErrorResponse forbidden(String msg) { return of("FORBIDDEN", msg); }
    public static ErrorResponse notFound(String msg) { return of("NOT_FOUND", msg); }
    public static ErrorResponse conflict(String msg) { return of("CONFLICT", msg); }
    public static ErrorResponse rateLimited(String msg) { return of("RATE_LIMITED", msg); }
    public static ErrorResponse internalError(String msg) { return of("INTERNAL_ERROR", msg); }

    @JsonInclude(JsonInclude.Include.NON_NULL)
    public static class ErrorDetail {
        private String code;
        private String message;
        private List<ErrorDetailItem> details;
        private String traceId;

        public ErrorDetail() {}
        public ErrorDetail(String code, String message, List<ErrorDetailItem> details, String traceId) {
            this.code = code; this.message = message; this.details = details; this.traceId = traceId;
        }
        public String getCode() { return code; }
        public String getMessage() { return message; }
        public List<ErrorDetailItem> getDetails() { return details; }
        public String getTraceId() { return traceId; }
        public void setCode(String c) { code = c; }
        public void setMessage(String m) { message = m; }
        public void setDetails(List<ErrorDetailItem> d) { details = d; }
        public void setTraceId(String t) { traceId = t; }
    }

    @JsonInclude(JsonInclude.Include.NON_NULL)
    public static class ErrorDetailItem {
        private String field;
        private String message;

        public ErrorDetailItem() {}
        public ErrorDetailItem(String field, String message) { this.field = field; this.message = message; }
        public String getField() { return field; }
        public String getMessage() { return message; }
        public void setField(String f) { field = f; }
        public void setMessage(String m) { message = m; }
    }
}