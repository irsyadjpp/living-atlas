package id.livingatlas.sharedweb.response;

import com.fasterxml.jackson.annotation.JsonInclude;

/**
 * Standard API response wrapper.
 * All backend services must use this format for single-object responses.
 *
 * @param <T> The data type
 */
@JsonInclude(JsonInclude.Include.NON_NULL)
public class ApiResponse<T> {

    private T data;

    public ApiResponse() {}

    public ApiResponse(T data) {
        this.data = data;
    }

    public T getData() { return data; }
    public void setData(T data) { this.data = data; }

    /**
     * Create a success response with data.
     */
    public static <T> ApiResponse<T> success(T data) {
        return new ApiResponse<>(data);
    }

    /**
     * Create a success response with data for 201 Created.
     */
    public static <T> ApiResponse<T> created(T data) {
        return new ApiResponse<>(data);
    }

    /**
     * Create an empty success response for 204 No Content.
     */
    public static <T> ApiResponse<T> noContent() {
        return new ApiResponse<>(null);
    }
}